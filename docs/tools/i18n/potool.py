#!/usr/bin/env python3
"""Helper for batch-translating Sphinx .po files safely via polib.

Agents never hand-edit .po files. Instead:

  1. dump  -- list every untranslated (empty msgstr) entry, in file order,
              as JSON: {"<po_path>": ["<msgid>", ...], ...}
  2. apply -- read a JSON file {"<po_path>": ["<translation>", ...], ...}
              and write each translation into the matching entry's msgstr,
              in the SAME order dump produced. polib re-serializes safely so
              msgid content and markup are never altered.

An empty-string translation ("") is left untranslated (English fallback) --
use it for entries that are pure code/markup with no translatable prose.

Usage:
  python3 i18n_potool.py dump  --out dump.json  <file1.po> <file2.po> ...
  python3 i18n_potool.py apply --json trans.json
"""
import argparse
import json
import re
import sys

import polib

# Keep polib's wrapping close to sphinx-intl's default so diffs stay small.
WRAPWIDTH = 78

# Characters that, when directly against reST inline markup, make docutils fail
# to parse the markup: it only accepts ASCII whitespace + a fixed punctuation
# set around delimiters. Covers CJK ideographs/kana/hangul AND CJK & fullwidth
# punctuation (the ideographic comma, fullwidth parens, etc.), which break a
# role/literal that abuts them just as ideographs do. Built from codepoints to
# avoid embedding literal CJK in the source.
_CJK_RE = re.compile('[' + ''.join([
    '\u2014\u2026',                  # em dash, horizontal ellipsis
    '\u2e80-\u9fff',                 # CJK radicals .. symbols/punct .. kana .. extA .. unified
    '\uac00-\ud7ff',                 # hangul
    '\uf900-\ufaff',                 # CJK compatibility ideographs
    '\uff00-\uffef',                 # halfwidth & fullwidth forms
]) + ']')

# All inline-markup constructs whose outer edges must be separated from CJK.
# Order matters: roles and double-backtick literals before single backticks.
_INLINE_RE = re.compile(
    r'``.+?``'                               # ``inline literal`` (may hold a single `)
    r'|:[a-zA-Z][a-zA-Z0-9_+.:-]*:`[^`]+`'  # :role:`...` (with optional <target>)
    r'|\*\*[^*]+\*\*'                        # **strong**
    r'|\*[^*\s][^*]*\*'                      # *emphasis*
    r'|`[^`]+`__?'                           # `link`_ / `anon`__
    r'|`[^`]+`'                              # `interpreted`
)

# Tokens that must be byte-identical between msgid and msgstr (never translated
# or dropped): inline literals, and the *target* of every role.
_LITERAL_RE = re.compile(r'``.+?``')
_ROLE_RE = re.compile(r':[a-zA-Z][a-zA-Z0-9_+.:-]*:`([^`]+)`')


def untranslated_entries(po):
    # entries with a real msgid and an empty msgstr, in file order
    return [e for e in po if e.msgid and not e.msgstr]


# reST escaped-space: a separator docutils accepts around inline markup but
# that renders to nothing -- so CJK typography stays tight (字``code``字 ->
# 字\ ``code``\ 字 displays as 字code字, no visible gap) while parsing cleanly.
_SEP = '\\ '


def cjk_pad(s):
    """Insert a reST escaped-space wherever inline markup butts directly
    against a CJK ideograph/kana/hangul/punctuation char, so docutils can
    parse the markup. Invisible in output. Idempotent: skips edges that are
    already preceded/followed by whitespace (incl. an existing escaped-space)."""
    spans = [(m.start(), m.end()) for m in _INLINE_RE.finditer(s)]
    if not spans:
        return s
    # A markup edge needs a separator unless its neighbour is already a boundary
    # docutils accepts. Rather than enumerate that (asymmetric, partly Unicode-
    # category) set, pad against ANY non-whitespace neighbour: the escaped-space
    # is invisible so over-separating is harmless, and this catches every case a
    # translator makes by dropping the source's ASCII space around markup -- CJK
    # text, ASCII/fullwidth punctuation, curly quotes, and adjacent markup
    # (**bold**``code``). Backslash is excluded so re-runs stay idempotent (the
    # inserted '\\ ' begins with a backslash).
    def needs(ch):
        return not ch.isspace() and ch != '\\'

    pts = []
    for a, b in spans:
        if a > 0 and not s[a - 1].isspace() and needs(s[a - 1]):
            pts.append(a)
        if b < len(s) and not s[b].isspace() and needs(s[b]):
            pts.append(b)
    if not pts:
        return s
    out = []
    prev = 0
    for p in sorted(set(pts)):
        out.append(s[prev:p])
        out.append(_SEP)
        prev = p
    out.append(s[prev:])
    return ''.join(out)


def _role_target(inner):
    """The must-preserve token of a role body: the <target> if present, else
    the whole body (translatable label text inside <...> is allowed to vary)."""
    m = re.search(r'<([^>`]+)>\s*$', inner)
    return m.group(1) if m else inner


def markup_problems(msgid, msgstr):
    """Return a list of invariant violations (dropped/altered code or refs)."""
    probs = []
    if sorted(_LITERAL_RE.findall(msgid)) != sorted(_LITERAL_RE.findall(msgstr)):
        probs.append('inline literals (``code``) differ')
    id_targets = sorted(_role_target(x) for x in _ROLE_RE.findall(msgid))
    str_targets = sorted(_role_target(x) for x in _ROLE_RE.findall(msgstr))
    if id_targets != str_targets:
        probs.append(f'role targets differ: {id_targets} vs {str_targets}')
    return probs


def _resolve_files(args):
    """Either explicit files, or a (manifest, lang, index) batch selection."""
    if args.manifest is not None:
        batches = json.load(open(args.manifest, encoding='utf-8'))
        rels = batches[args.index]
        return [f"locale/{args.lang}/LC_MESSAGES/{r}" for r in rels]
    return args.files


def cmd_dump(args):
    out = {}
    for path in _resolve_files(args):
        po = polib.pofile(path, wrapwidth=WRAPWIDTH)
        out[path] = [e.msgid for e in untranslated_entries(po)]
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            f.write(text)
        total = sum(len(v) for v in out.values())
        print(f"dumped {total} untranslated entries from {len(out)} files -> {args.out}")
    else:
        print(text)


def cmd_apply(args):
    with open(args.json, encoding='utf-8') as f:
        data = json.load(f)
    applied = 0
    skipped = 0
    errors = []
    rejected = []
    for path, translations in data.items():
        po = polib.pofile(path, wrapwidth=WRAPWIDTH)
        unt = untranslated_entries(po)
        if len(translations) != len(unt):
            errors.append(
                f"{path}: COUNT MISMATCH -- file has {len(unt)} untranslated "
                f"entries but got {len(translations)} translations. NOT saved."
            )
            continue
        changed = False
        for i, (entry, tr) in enumerate(zip(unt, translations)):
            if tr == "" or tr is None:
                skipped += 1
                continue
            fixed = cjk_pad(tr)
            probs = markup_problems(entry.msgid, fixed)
            if probs:
                rejected.append(f"{path}[{i}]: {'; '.join(probs)}")
                continue  # leave empty -> retried on next dump
            entry.msgstr = fixed
            applied += 1
            changed = True
        if changed:
            po.save(path)
    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        print(f"applied {applied}, skipped {skipped}, FILES WITH ERRORS {len(errors)}",
              file=sys.stderr)
        sys.exit(2)
    if rejected:
        for r in rejected[:50]:
            print("REJECTED:", r, file=sys.stderr)
        print(f"applied {applied}, left {skipped} empty, REJECTED {len(rejected)} "
              f"(markup invariant violated -- fix and re-run those entries)",
              file=sys.stderr)
        sys.exit(3)
    print(f"applied {applied} translations, left {skipped} empty (fallback)")


def cmd_normalize(args):
    """Re-apply cjk_pad + invariant check to already-translated entries.
    Entries that violate markup invariants are CLEARED (set back to empty) so
    they get re-translated, and reported."""
    import glob
    files = args.files
    if args.glob:
        files = glob.glob(args.glob, recursive=True)
    padded = 0
    cleared = []
    for path in files:
        po = polib.pofile(path, wrapwidth=WRAPWIDTH)
        changed = False
        for e in po:
            if not e.msgid or not e.msgstr:
                continue
            fixed = cjk_pad(e.msgstr)
            probs = markup_problems(e.msgid, fixed)
            if probs:
                cleared.append(f"{path}: {probs[0]}")
                e.msgstr = ""
                changed = True
            elif fixed != e.msgstr:
                e.msgstr = fixed
                padded += 1
                changed = True
        if changed:
            po.save(path)
    for c in cleared[:50]:
        print("CLEARED:", c, file=sys.stderr)
    print(f"padded {padded} entries, cleared {len(cleared)} invalid entries "
          f"(now empty -> will be re-translated)")


def cmd_autoclear(args):
    """Given a Sphinx warnings file, revert the offending translated entries to
    empty (English fallback). Maps each '<file>.rst:<line>' warning to the .po
    entry whose source occurrence matches, for the long tail of structurally
    mistranslated strings (illegal nested markup, etc.) that cjk_pad can't fix.
    """
    import os
    base = f"locale/{args.lang}/LC_MESSAGES"
    wants = {}  # po_path -> set(line numbers)
    pat = re.compile(r'^([A-Za-z0-9_][\w./-]*\.rst):(\d+):')
    for line in open(args.warnings, encoding='utf-8'):
        m = pat.match(line)
        if not m:
            continue
        rst, ln = m.group(1), m.group(2)
        po_path = os.path.join(base, rst[:-4] + '.po')
        wants.setdefault(po_path, set()).add(ln)
    cleared = 0
    for po_path, lines in wants.items():
        if not os.path.exists(po_path):
            print(f"WARN: no po for {po_path}", file=sys.stderr)
            continue
        po = polib.pofile(po_path, wrapwidth=WRAPWIDTH)
        changed = False
        for e in po:
            if not e.msgstr:
                continue
            if any(ln in lines for _, ln in e.occurrences):
                e.msgstr = ""
                cleared += 1
                changed = True
        if changed:
            po.save(po_path)
    print(f"autocleared {cleared} entries to English fallback")


def cmd_manifest(args):
    """(Re)generate batches.json: group the .po files into batches of roughly
    --target source words each (balanced fan-out units for translation). The
    grouping is language-independent (msgids are English), so any populated
    locale works as the reference."""
    import os
    import glob
    base = f"locale/{args.lang}/LC_MESSAGES"
    files = sorted(glob.glob(os.path.join(base, "**", "*.po"), recursive=True))
    if not files:
        print(f"ERROR: no .po files under {base} -- run sphinx-intl update first",
              file=sys.stderr)
        sys.exit(2)

    def words(p):
        po = polib.pofile(p, wrapwidth=WRAPWIDTH)
        return sum(len(e.msgid.split()) for e in po if e.msgid)

    items = [(os.path.relpath(f, base), words(f)) for f in files]
    items = [(r, w) for r, w in items if w > 0]
    batches, cur, cw = [], [], 0
    for rel, w in items:
        if cur and cw + w > args.target:
            batches.append(cur)
            cur, cw = [], 0
        cur.append(rel)
        cw += w
    if cur:
        batches.append(cur)
    json.dump(batches, open(args.out, 'w'))
    print(f"wrote {len(batches)} batches ({len(items)} files, "
          f"{sum(w for _, w in items)} source words) -> {args.out}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    m = sub.add_parser('manifest')
    m.add_argument('--lang', default='zh_CN', help='reference locale to size batches from')
    m.add_argument('--target', type=int, default=2500, help='approx source words per batch')
    m.add_argument('--out', default='tools/i18n/batches.json')
    m.set_defaults(func=cmd_manifest)
    d = sub.add_parser('dump')
    d.add_argument('--out')
    d.add_argument('--manifest', help='batches.json (use with --lang/--index)')
    d.add_argument('--lang')
    d.add_argument('--index', type=int)
    d.add_argument('files', nargs='*')
    d.set_defaults(func=cmd_dump)
    a = sub.add_parser('apply')
    a.add_argument('--json', required=True)
    a.set_defaults(func=cmd_apply)
    n = sub.add_parser('normalize')
    n.add_argument('--glob')
    n.add_argument('files', nargs='*')
    n.set_defaults(func=cmd_normalize)
    c = sub.add_parser('autoclear')
    c.add_argument('--lang', required=True)
    c.add_argument('--warnings', required=True)
    c.set_defaults(func=cmd_autoclear)
    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
