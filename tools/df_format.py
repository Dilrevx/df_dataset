"""Deterministic metadata-only df_dataset XLSX reader (standard library)."""
from collections import Counter
import hashlib
import io
import json
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

UPSTREAM = "ce9ec83d5902a7e132f573fb218d379fd4666c23"
REPOSITORY = "https://github.com/wpengfei/df_dataset"
ADAPTER = "df-dataset-catalog-v1"
WORKBOOKS = ("double-fetch vulnerability dataset.xlsx",
             "double-fetch vulnerability dataset-2018.xlsx",
             "double-fetch vulnerability dataset-2019.xlsx")
LATEST = WORKBOOKS[-1]
FIELDS = ("No.", "CVE", "Platform", "Version", "IsDriver", "Type", "Bulletin",
          "File", "Description", "Consequence", "Source")
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
OUTPUTS = ("cases.jsonl", "source.json", "summary.json")
STATE = {"source_binding": "not_bound", "candidate_pool": "not_built", "evaluation": "not_run"}

def require(ok, message):
    if not ok:
        raise ValueError(message)

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode()

def sha(body):
    return hashlib.sha256(body).hexdigest()

def pretty(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode()

def xlsx_rows(body):
    require(len(body) <= 8_000_000, "Workbook exceeds size limit")
    with zipfile.ZipFile(io.BytesIO(body)) as book:
        infos = book.infolist()
        require(len({i.filename for i in infos}) == len(infos), "Duplicate ZIP entries")
        require(sum(i.file_size for i in infos) <= 32_000_000, "Workbook expansion exceeds limit")
        for i in infos:
            require(not i.filename.startswith("/") and ".." not in i.filename.split("/"),
                    "Unsafe workbook member path")
        def xml(path):
            data = book.read(path)
            require(b"<!DOCTYPE" not in data.upper() and b"<!ENTITY" not in data.upper(),
                    "XML declarations are not permitted")
            return ET.fromstring(data)
        shared = []
        if "xl/sharedStrings.xml" in book.namelist():
            shared = ["".join(e.itertext()) if not e.findall(".//s:t", NS)
                      else "".join(t.text or "" for t in e.findall(".//s:t", NS))
                      for e in xml("xl/sharedStrings.xml").findall("s:si", NS)]
        sheet = xml("xl/workbook.xml").find("s:sheets/s:sheet", NS)
        require(sheet is not None, "Workbook has no sheet")
        relationships = xml("xl/_rels/workbook.xml.rels")
        mapping = {r.attrib["Id"]: r for r in relationships}
        relation = mapping[sheet.attrib["{" + NS["r"] + "}id"]]
        require(relation.attrib.get("TargetMode") != "External", "External worksheet reference")
        target = relation.attrib["Target"]
        path = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
        require(path.startswith("xl/") and ".." not in path.split("/"), "Unsafe worksheet path")
        records, seen = [], set()
        for row in xml(path).findall("s:sheetData/s:row", NS):
            row_no = int(row.attrib["r"])
            require(row_no > 0 and row_no not in seen, "Duplicate or invalid sheet row")
            seen.add(row_no)
            values, seen_cells = [None] * 11, set()
            for cell in row.findall("s:c", NS):
                address = cell.attrib["r"]
                match = re.fullmatch(r"([A-Z]+)([1-9][0-9]*)", address)
                require(match is not None and int(match[2]) == row_no
                        and address not in seen_cells, "Invalid or duplicate cell address")
                seen_cells.add(address)
                col = 0
                for char in match[1]:
                    col = col * 26 + ord(char) - 64
                if col > 11:
                    continue
                require(cell.find("s:f", NS) is None, "Formula in source data; explicit review required")
                value = cell.find("s:v", NS)
                raw = value.text if value is not None else None
                typ = cell.attrib.get("t", "n")
                if typ == "s" and raw is not None:
                    index = int(raw)
                    require(0 <= index < len(shared), "Invalid shared string index")
                    result = shared[index]
                elif typ == "inlineStr":
                    result = "".join(t.text or "" for t in cell.findall(".//s:t", NS))
                elif typ in ("str", "e"):
                    require(typ != "e", "Spreadsheet error cell")
                    result = raw
                elif typ == "b":
                    require(raw in ("0", "1"), "Invalid boolean cell")
                    result = raw == "1"
                elif raw is None:
                    result = None
                else:
                    require(typ == "n", "Unsupported cell type")
                    number = float(raw)
                    result = int(number) if number.is_integer() else number
                values[col - 1] = result
            records.append((row_no, values))
        require(records and tuple(records[0][1]) == FIELDS, "Unexpected data header")
        return sheet.attrib["name"], [(n, dict(zip(FIELDS, r))) for n, r in records[1:]
             if type(r[0]) is int and r[0] > 0]

def trimmed(value):
    return str(value).strip() if value is not None else None

def build(blobs):
    require(set(blobs) == set(WORKBOOKS), "Must provide all three source workbook versions")
    parsed, inventories = {}, {}
    for name in WORKBOOKS:
        sheet, rows = xlsx_rows(blobs[name])
        numbers = [row["No."] for _, row in rows]
        require(numbers and len(numbers) == len(set(numbers)), "Duplicate catalog number")
        require(numbers == list(range(1, len(numbers) + 1)), "Catalog row numbers are not contiguous")
        parsed[name] = (sheet, rows)
        inventories[name] = dict(numbered_rows=len(rows),
            nonempty_cve_values=len({trimmed(row["CVE"]) for _, row in rows if trimmed(row["CVE"])}),
            platforms=dict(sorted(Counter(trimmed(row["Platform"]) for _, row in rows).items())))
    sheet, rows = parsed[LATEST]
    cases = []
    for row_number, row in rows:
        digest = sha(canonical(row))
        reference = dict(path=LATEST, sheet=sheet, row=row_number, row_sha256=digest)
        # The original long Description/Consequence prose is deliberately not re-published.
        cases.append(dict(case_id="df2019-" + digest[:20], status=dict(STATE),
            evaluator_only=dict(raw_ref=reference, catalog_number=row["No."],
                cve=trimmed(row["CVE"]), platform=trimmed(row["Platform"]),
                reported_version=trimmed(row["Version"]), is_driver=trimmed(row["IsDriver"]),
                reported_type=trimmed(row["Type"]), reported_file=trimmed(row["File"]),
                source_urls=re.findall(r"https?://[^\s<>]+", trimmed(row["Source"]) or ""))))
    require(len({r["case_id"] for r in cases}) == len(cases), "Case hash collision")
    source = dict(schema_version=1, adapter=ADAPTER,
        upstream=dict(repository=REPOSITORY, commit=UPSTREAM),
        selected_workbook=LATEST,
        files={path: dict(sha256=sha(blobs[path]), bytes=len(blobs[path])) for path in WORKBOOKS},
        license_status="no_explicit_upstream_license_at_pinned_commit_no_blanket_relicensing",
        model_input="unavailable_until_independent_source_version_and_locations_are_bound",
        source_prose_redistributed=False, source_workbooks_modified=False)
    counts = dict(catalog_rows=len(cases),
        distinct_nonempty_cve_values=inventories[LATEST]["nonempty_cve_values"],
        linux_catalog_rows=inventories[LATEST]["platforms"].get("Linux", 0),
        workbook_versions=len(WORKBOOKS), bound_source_snapshots=0, bound_locations=0)
    summary = dict(schema_version=1, adapter=ADAPTER, counts=counts,
        status=dict(STATE), versions=inventories,
        aggregation="2019_only_older_workbooks_are_overlapping_versions_not_extra_cases")
    return {"cases.jsonl": b"".join(canonical(row) + b"\n" for row in cases),
            "source.json": pretty(source), "summary.json": pretty(summary)}
