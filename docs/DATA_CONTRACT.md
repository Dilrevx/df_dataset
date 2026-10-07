# df-dataset-catalog-v1

All inputs are read from fixed Git objects, not mutable workbook files.
Selected source: `double-fetch vulnerability dataset-2019.xlsx`, first sheet
`工作表2`, columns A:K. Only positive integer `No.` rows count as catalog records;
the summary sheet, decorative formatting and trailing annotations are excluded.
There are 91/102/108 records in the original/2018/2019 versions; do not add them.

The XML reader resolves shared strings and rich text, preserves physical Excel
row numbers and raw scalar types, and refuses formulas in the inspected range,
duplicate cells, duplicate row numbers, unsafe package paths and oversized
archives. No macros, external relationships or spreadsheet formulas execute.
For each raw row, hash the JSON object of the eleven original column/value
pairs with UTF-8, sorted keys, compact separators and no trailing newline.
Case ID is `df2019-` plus the first 20 hex characters of this SHA-256.
The original XLSX binary hashes independently protect all unparsed details.

Every case has `case_id`, `status`, and `evaluator_only`. Status is exactly
`source_binding=not_bound`, `candidate_pool=not_built`, `evaluation=not_run`.
Evaluator-only fields are raw reference, catalog number, CVE text, platform,
reported version, driver/type/file metadata and extracted source URLs.
Missing entries stay null or empty lists. A Source URL is an advisory or other
reference, not proof of acquired source code. Reported file names are labels,
not safe paths to execute or implicit full-repository search inputs.

No model-input projection is available before source binding. Attempting to
export a catalog record as a runnable source request must fail clearly.
Later source-bound additions require a new schema/version and their own
receipts; do not edit the historical zero-bound-location claim in place.

Standalone JSON uses sorted keys/two-space indent/newline; JSONL uses canonical
one-record-per-line encoding. `cases.jsonl`, `source.json`, `summary.json` are
generated together; `--check` reconstructs and compares bytes. Export requires
a new directory and never overwrites existing data. Original workbooks remain
unaltered; no source Description/Consequence prose is copied into JSON.
