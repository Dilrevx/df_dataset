# Double-fetch catalog adaptation

This additive layer preserves the original three XLSX workbooks and upstream
history unchanged at `ce9ec83d5902a7e132f573fb218d379fd4666c23`.
The latest 2019 workbook is the active catalog. Earlier files are overlapping
versions, not additional independent examples.

Run the standard-library normalizer without executing target code:

```sh
python3 tools/normalize_df_dataset.py --check
python3 -m unittest discover -s tests -p 'test_*.py'
```

The included catalog has 108 numbered records, 103 distinct nonempty CVE values
and 20 records whose platform is Linux. These are metadata counts, not 108
source-bound or runnable evaluation cases. Windows and proprietary product
records are retained, not silently excluded to inflate coverage.

`datasets/df-dataset/cases.jsonl` provides stable row-hash identifiers, exact
workbook/sheet/row references and evaluator-only catalog facts. Long source
descriptions and consequence prose are not copied into derived files.
`source.json` records the three original binary hashes. `summary.json` records
separate version counts and source-binding status. See [contract](docs/DATA_CONTRACT.md).

The original repository at the pinned revision has no explicit license file.
We preserve original attribution, make no blanket licensing grant over the
workbooks, and do not redistribute them within embed. The normalizer does not
modify, recalculate or export Excel files. Target source, when separately
acquired, retains its own license.

Before retrieval evaluation, each admitted record needs a verified repository
and full vulnerable/fixed commits, independently reviewed check/use locations,
and a candidate pool built without using those answers. Missing data remains
missing; this catalog supplies neither code nor runtime oracles. No target
programs, PoCs, model services or containers were executed by this adaptation.
