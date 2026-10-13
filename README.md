# Double fetch report dataset

108 rows from the 2019 double-fetch catalogue. The two earlier workbooks are overlapping catalogue versions, not additional cases.

[Cases](dataset/cases.jsonl) and [manifest](dataset/manifest.json) are the data entry points. Descriptions, consequences, bulletins, reported versions/files and source citations are structured facts; all three original workbooks are preserved as hash-bound evidence. Reported filenames are not verified source coordinates.

From [embed](https://github.com/Dilrevx/embed/tree/spec-audit-ab):

```sh
PYTHONPATH=src python3 -m embedbench validate-dataset \\
  --benchmark-checkout ../df_dataset --lock benchmarks/df-dataset/dataset-lock.json
```

The [fixed dataset lock](https://github.com/Dilrevx/embed/blob/spec-audit-ab/benchmarks/df-dataset/dataset-lock.json) and [shared runner](https://github.com/Dilrevx/embed/blob/spec-audit-ab/docs/method-runner.md) define evaluation inputs and label handling.

Native input: [0100727430d66ecf4d52b0566aec5bdadd8c81ae](https://github.com/Dilrevx/df_dataset/tree/0100727430d66ecf4d52b0566aec5bdadd8c81ae). Source snapshots are not supplied by this catalogue. No explicit upstream licence was found; retaining evidence does not grant a new redistribution licence.
