#!/usr/bin/env python3
"""Generate a provenance-preserving catalog, never modify an XLSX workbook."""
import argparse
import json
from pathlib import Path
import subprocess
from df_format import OUTPUTS, UPSTREAM, WORKBOOKS, build, require


def generate(repo):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE)
    require(git('rev-parse', UPSTREAM + '^{commit}').decode().strip() == UPSTREAM,
            'Pinned upstream commit unavailable')
    return build({name: git('show', UPSTREAM + ':' + name) for name in WORKBOOKS})


def emit(output, payload, check=False):
    output = Path(output)
    require(not output.is_symlink(), 'Symlink output not permitted')
    if check:
        require(output.is_dir() and {p.name for p in output.iterdir()} == set(OUTPUTS),
                'Unexpected normalized file set')
        for name in OUTPUTS:
            path = output / name
            require(not path.is_symlink() and path.read_bytes() == payload[name],
                    'Normalized data differs: ' + name)
    else:
        output.mkdir(parents=True, exist_ok=False)
        for name in OUTPUTS:
            with (output / name).open('xb') as stream:
                stream.write(payload[name])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--output-dir', type=Path)
    p.add_argument('--check', action='store_true')
    args = p.parse_args()
    payload = generate(args.repo)
    emit(args.output_dir or args.repo / 'datasets/df-dataset', payload, args.check)
    print(json.dumps(dict(status='verified' if args.check else 'created',
        counts=json.loads(payload['summary.json'])['counts'], model_calls=0, target_executions=0)))


if __name__ == '__main__':
    main()
