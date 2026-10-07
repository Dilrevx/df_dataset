import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from normalize_df_dataset import generate, emit
from df_format import LATEST, WORKBOOKS, xlsx_rows


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = generate(ROOT)

    def test_real_inventory(self):
        summary = json.loads(self.payload['summary.json'])
        self.assertEqual(summary['counts'], dict(catalog_rows=108, distinct_nonempty_cve_values=103,
            linux_catalog_rows=20, workbook_versions=3, bound_locations=0, bound_source_snapshots=0))
        self.assertEqual([summary['versions'][n]['numbered_rows'] for n in WORKBOOKS], [91, 102, 108])

    def test_byte_reproduction(self):
        emit(ROOT / 'datasets/df-dataset', self.payload, check=True)
        self.assertEqual(generate(ROOT), self.payload)

    def test_no_source_prose_or_model_input(self):
        cases = [json.loads(line) for line in self.payload['cases.jsonl'].splitlines()]
        self.assertEqual(len(cases), len({r['case_id'] for r in cases}))
        for case in cases:
            self.assertNotIn('model_input', case)
            self.assertNotIn('Description', case['evaluator_only'])
            self.assertEqual(case['status']['source_binding'], 'not_bound')

    def test_new_output_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'catalog'
            emit(path, self.payload)
            emit(path, self.payload, check=True)
            with self.assertRaises(FileExistsError):
                emit(path, self.payload)


if __name__ == '__main__':
    unittest.main()
