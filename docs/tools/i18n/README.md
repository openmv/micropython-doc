# Documentation translation (i18n) tooling

Tooling that produces the per-language `.po` catalogs under `docs/locale/<lang>/`
for the multi-language docs build. The language list, switcher, and the
`navigator.language` auto-redirect live in `docs/conf.py` and
`docs/static/lang-redirect.js`.

All commands are run from the `docs/` directory.

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
