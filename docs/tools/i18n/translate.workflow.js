export const meta = {
  name: 'i18n-translate-language',
  description: 'Translate all OpenMV/MicroPython .po files for one language (glossary + fan-out batches)',
  phases: [
    { title: 'Glossary', detail: 'build a canonical term glossary for the language' },
    { title: 'Translate', detail: 'one agent per ~2500-word batch, applied in place via polib' },
  ],
}

// Absolute path to the Sphinx docs dir for this checkout (workflow agents cd
// here and call the helpers below). Edit this one line for a different machine.
const DOCS = '/home/kwagyeman/github/openmv-doc/micropython/docs'
const I18N = `${DOCS}/tools/i18n`
const POTOOL = `${I18N}/potool.py`
const MANIFEST = `${I18N}/batches.json`

const A = (typeof args === 'string') ? JSON.parse(args) : args
const code = A.code
const native = A.native
const nbatches = A.nbatches
const MODEL = A.model || undefined   // e.g. "sonnet" to translate cheaper; omit to inherit
log(`JOB code=${code} native=${native} nbatches=${nbatches} model=${MODEL || 'inherit'}`)

const RULES = `
- Translate the PROSE only. Produce natural, fluent technical writing in ${native} -- not literal word-for-word.
- Preserve ALL reStructuredText markup byte-for-byte:
  - Roles and their targets: :func:\`x\`, :meth:\`a.b\`, :class:\`X\`, :mod:\`m\`, :doc:\`path\`, :ref:\`label\`, :data:\`None\`, etc. Translate the visible text ONLY when there is a custom label (:doc:\`Visible <target>\`); NEVER translate the target.
  - Inline literals \`\`like_this\`\` and code stay verbatim.
  - Hyperlinks: translate the link text, NEVER the URL.
  - Directive names, options, and admonition labels (.. note::, .. warning::) stay as-is.
- DO NOT translate, transliterate, or alter: code, identifiers, API names, CLI flags (--port, --script), file paths, /rom/..., version strings, numbers.
- DO NOT translate product / proper names: OpenMV, OpenMV Cam, MicroPython, Python, Arduino, BlazeFace, ROMFS, Roboflow, Edge Impulse, FOMO, YOLO, Qt, Vela, ST Edge AI, J-Link, DFU. (For CJK languages you MAY add a native gloss in parentheses on first use if it reads naturally, but keep the original term.)
- Keep printf/format placeholders (%s, %d, {}, {0}) intact and in an order valid for the sentence.
- Match the msgid's leading/trailing whitespace and newlines in the translation.
- Headings/titles: translate naturally and concisely.
- Use the GLOSSARY below consistently everywhere.
- CRITICAL -- preserve EVERY cross-reference and code token: every :role:\`...\` (with its target unchanged) and every \`\`literal\`\` in the msgid MUST appear in your translation. Do not drop, merge, reorder-away, or duplicate any of them. The count must match exactly. (Spacing between CJK text and markup is added automatically afterwards -- just write naturally; do NOT insert your own spaces or backslashes around markup.)
- If a msgid is pure code/markup/proper-noun with NO translatable prose, output an empty string "" for that slot (it falls back to English) rather than risk corrupting it.
- NEVER change a msgid. You only ever produce msgstr translations.`

phase('Glossary')
const glossary = await agent(
  `You are a senior ${native} (${code}) technical translator for the OpenMV machine-vision + MicroPython documentation.
Produce a concise glossary giving the SINGLE canonical ${native} rendering for each of these recurring technical terms, to be reused consistently across the whole manual:
frame buffer, machine vision, snapshot, blob, threshold, image, frame, sensor, camera, pixel, grayscale, color, resolution, firmware, bootloader, flash, sketch, script, REPL, exposure, gain, region of interest (ROI), histogram, contour, edge, feature, model (ML), inference, neural network, dataset, label, bounding box, classification, detection, segmentation, keypoint, descriptor, draw, overlay, buffer, callback, interrupt, peripheral, register, pin, timer, baud rate, throughput, latency.
Also give a short list of terms to ALWAYS keep in English (product/proper names + APIs).
Output as compact markdown: a "Term | ${native}" table, then a "Keep in English:" line. No preamble.`,
  { label: `glossary:${code}`, phase: 'Glossary', model: MODEL }
)

phase('Translate')
const batchPrompt = (i) => `You are a professional ${native} (${code}) technical translator for the OpenMV / MicroPython documentation. Work entirely inside ${DOCS}. Your batch index is ${i}.

## Step 1 - dump the strings to translate
Run exactly:
  cd ${DOCS} && python3 ${POTOOL} dump --manifest ${MANIFEST} --lang ${code} --index ${i} --out /tmp/dump_${code}_${i}.json
Then Read /tmp/dump_${code}_${i}.json . It is a JSON object {"<po_path>": ["<msgid>", ...], ...} listing every UNTRANSLATED string in order. (It may be empty {} or have empty lists if this batch is already done -- if so, report applied 0 and stop.)

## Step 2 - translate into ${native}
Create /tmp/trans_${code}_${i}.json with the SAME keys, and for each key a JSON list of translations with EXACTLY the same length and order as the dump list for that key. Translate every entry into natural, fluent ${native}.

### RULES (follow exactly -- quality is the entire point)
${RULES}

### GLOSSARY
${glossary}

## Step 3 - apply (safe, via polib -- never hand-edit .po)
Run:
  python3 ${POTOOL} apply --json /tmp/trans_${code}_${i}.json
- If it prints "COUNT MISMATCH" for a file, your list length/order for that file is wrong: re-Read the dump, fix that key's list, rewrite the json, apply again.
- If it prints "REJECTED <path>[<i>]: ..." lines, those translations dropped/altered a \`\`literal\`\` or a :role:\` target. Re-translate exactly those slots preserving every code token and reference, rewrite the json, apply again. (Re-running dump will only return the still-untranslated slots, so you can iterate.)
- If it prints a JSON decode error, fix your JSON syntax (watch quotes/backslashes inside reST like \`\`code\`\` and \\n) and apply again.
- Do NOT finish until apply exits cleanly with no ERROR or REJECTED lines.

## Step 4 - report
Return the counts that apply printed.`

const SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    applied: { type: 'integer' },
    leftEmpty: { type: 'integer' },
    error: { type: ['string', 'null'] },
  },
  required: ['applied', 'leftEmpty', 'error'],
}

const idx = Array.from({ length: nbatches }, (_, i) => i)
const results = await parallel(
  idx.map((i) => () =>
    agent(batchPrompt(i), { label: `tr:${code}:${i}`, phase: 'Translate', schema: SCHEMA, model: MODEL })
  )
)

const ok = results.filter(Boolean)
const failed = results.length - ok.length
const applied = ok.reduce((s, r) => s + (r.applied || 0), 0)
const leftEmpty = ok.reduce((s, r) => s + (r.leftEmpty || 0), 0)
const withError = ok.filter((r) => r.error).map((r, i) => r.error)
log(`${code}: batches ok=${ok.length} failed=${failed}, applied=${applied}, leftEmpty=${leftEmpty}`)
return { code, nbatches, batchesOk: ok.length, batchesFailed: failed, applied, leftEmpty, errors: withError.slice(0, 20) }
