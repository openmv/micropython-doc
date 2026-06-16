# Documentation translation (i18n) tooling

Tooling that produces the per-language `.po` catalogs under `docs/locale/<lang>/`
for the multi-language docs build. The language list, switcher, and the
`navigator.language` auto-redirect live in `docs/conf.py` and
`docs/static/lang-redirect.js`.

All commands are run from the `docs/` directory.

## RTL languages (he, ar) — translated but NOT in the switcher

Hebrew (`he`) and Arabic (`ar`) are fully translated and committed under
`locale/he/` and `locale/ar/`, and they build cleanly (no markup errors). They
are deliberately **left out of `conf.py`'s `html_context["languages"]` switcher
and out of `static/lang-redirect.js`** because the Shibuya theme has no RTL
support:

- The build emits `<html lang="he">` / `lang="ar"` but **never sets `dir="rtl"`**,
  and the theme ships **no RTL stylesheet** (no `[dir=rtl]` rules, no
  `:lang(he|ar)` rules). Verified: zero `dir=` attributes in the `he`/`ar` HTML.
- Result: the page renders with **LTR chrome** (sidebar, navbar, text-align,
  next-steps/changelog cards, list indentation all on the left); only the
  individual Hebrew/Arabic text runs get the browser's per-run bidi. That is a
  broken right-to-left reading experience, not a mirrored layout.

To enable them later (theme/CSS work, then uncomment the two entries in
`conf.py` and `lang-redirect.js`'s `SUBDIRS`/`MAP`):

1. Set `dir="rtl"` on `<html>` for RTL languages — override the theme's
   `layout.html` (or a `conf.py` hook) keyed on `language in {"he","ar"}`.
2. Add RTL CSS so the layout mirrors — prefer CSS logical properties
   (`margin-inline-*`, `padding-inline-*`, `inset-inline-*`) or `[dir=rtl]`
   overrides for the navbar, sidebar, cards, and figures.
3. Force `dir="ltr"` on code (`.highlight`, `code`, inline literals) and other
   LTR snippets so they don't reflow inside the RTL flow.

## Files

| file | role | committed? |
|------|------|------------|
| `potool.py` | dump/apply/normalize/autoclear/manifest for `.po` files (via polib) | yes |
| `translate.workflow.js` | Claude Code Workflow: glossary + one agent per batch, applied in place | yes |
| `finalize.sh` | normalize markup, build, auto-clear residual warnings until the build is clean | yes |
| `buildcheck.sh` | build one language and diff warnings against the English baseline | yes |
| `batches.json` | generated fan-out manifest (`potool.py manifest`) | no (gitignored) |
| `baseline_warnings.txt` | generated English-build warning baseline | no (gitignored) |

## One-time setup

```sh
cd docs
pip install sphinx-intl polib
python3 -m sphinx -b gettext . _build/gettext
sphinx-intl update -p _build/gettext -l zh_CN -l zh_TW -l de -l ja -l es \
  -l ru -l fr -l ko -l it -l pt_BR -l nl
python3 tools/i18n/potool.py manifest          # (re)generate batches.json
```

## Translate a language

Edit the `DOCS` constant in `translate.workflow.js` for your checkout, then run
the workflow (Claude Code) with `args` `{"code":"de","native":"German (Deutsch)","nbatches":239}`.
It dumps untranslated strings per batch, translates them, and applies them with
`potool.py apply` (which auto-separates inline reST markup from adjacent CJK /
punctuation with an escaped-space, and rejects any translation that drops a
`` ``literal`` `` or `:role:` target). Re-running only touches still-empty
entries, so it is fully resumable.

## Finalize + verify

```sh
cd docs
bash tools/i18n/finalize.sh de     # normalize, build, auto-clear residual warnings -> clean
```

`finalize.sh` reverts the small tail of structurally-mistranslated strings to the
English fallback so the build has no new warnings beyond the baseline. Commit the
resulting `docs/locale/<lang>/` afterwards.
