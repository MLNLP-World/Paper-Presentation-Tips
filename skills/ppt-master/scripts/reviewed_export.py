#!/usr/bin/env python3
"""Chat-profile native export, gated on the approved reference snapshot.

The original svg_to_pptx.py remains an upstream utility, including for template
tooling. This profile's documented final-delivery entry is this wrapper.
"""
import argparse
import subprocess
import sys
from pathlib import Path

from attribution_guard import require_skill_integrity
from console_encoding import configure_utf8_stdio
from reference_review import ReviewError, check


def main(argv=None):
    configure_utf8_stdio()
    argv = list(sys.argv[1:] if argv is None else argv)
    exporter = Path(__file__).with_name('svg_to_pptx.py')
    if '-h' in argv or '--help' in argv:
        return subprocess.call([sys.executable, str(exporter), *argv])
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('project_path')
    parser.add_argument('-s', '--source')
    parser.add_argument('--roundtrip', action='store_true')
    args, _ = parser.parse_known_args(argv)
    source = args.source or ('authoring-svg-flat' if args.roundtrip else 'svg_output')
    try:
        result = check(args.project_path, source)
    except (ReviewError, OSError, ValueError, KeyError) as exc:
        print(f'REFERENCE REVIEW BLOCKED: {exc}', file=sys.stderr)
        return 2
    print(f"[CHAT REFERENCE] revision {result['version']}, {result['page_count']} approved pages")
    return subprocess.call([sys.executable, str(exporter), *argv])


if __name__ == '__main__':
    require_skill_integrity()
    raise SystemExit(main())
