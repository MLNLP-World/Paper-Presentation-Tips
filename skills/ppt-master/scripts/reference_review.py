#!/usr/bin/env python3
"""Bind chat decisions to exact page references. Receipts attest, never authenticate, user messages.

prepare/check do not claim visual fidelity or native editability. Use actual PPTX
rendering, readback and a visual comparison after the normal exporter postflight.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree as ET

from slide_roster import discover_slide_svgs, _slide_filename_sort_key


class ReviewError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fingerprint(value) -> str:
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False).encode('utf-8'))


def local(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ReviewError(f'Path escapes project: {name}')
    return path


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def generation_snapshot(root: Path, row: dict, policy: str | None):
    """Bind declared generation evidence; this cannot authenticate a tool call.

    Existing v1 rosters without this field remain readable. New AI-reference
    workflows explicitly set reference_generation independently of image_usage.
    """
    methods = {'host_native_image', 'external_image_api', 'native_design', 'provided_frame'}
    if policy is not None and policy not in methods:
        raise ReviewError('Unknown reference_generation method')
    data = row.get('generation')
    if data is None and policy is None:
        return None
    if not isinstance(data, dict) or data.get('method') not in methods:
        raise ReviewError('Reference generation needs a declared method and its evidence')
    method = data['method']
    result = {'method': method, 'policy': policy or method}
    if method in {'host_native_image', 'external_image_api'}:
        if not all(isinstance(data.get(k), str) and data[k].strip()
                   for k in ('tool', 'invocation_ref', 'prompt')):
            raise ReviewError('AI reference needs actual tool, invocation reference and prompt file')
        prompt = local(root, data['prompt'])
        if not prompt.read_text(encoding='utf-8-sig').strip():
            raise ReviewError('Empty full-slide generation prompt')
        result.update({k: data[k] for k in ('tool', 'invocation_ref', 'prompt')})
        result['prompt_sha256'] = digest(prompt.read_bytes())
        if method == 'external_image_api':
            authorization = data.get('authorization', {})
            if not all(isinstance(authorization.get(k), str) and authorization[k].strip()
                       for k in ('message', 'message_id')):
                raise ReviewError('External API reference needs the real user selection')
            if not all(isinstance(data.get(k), str) and data[k].strip()
                       for k in ('provider', 'model')):
                raise ReviewError('External API reference needs actual provider and model')
            result.update({k: data[k] for k in ('provider', 'model')})
            result['authorization'] = {k: authorization[k] for k in ('message', 'message_id')}
    else:
        authorization = data.get('authorization', {})
        if not all(isinstance(authorization.get(k), str) and authorization[k].strip()
                   for k in ('message', 'message_id')):
            raise ReviewError('Native/provided reference needs the real user choice; no silent AI fallback')
        result['authorization'] = {k: authorization[k] for k in ('message', 'message_id')}
    references = data.get('references', [])
    if not isinstance(references, list):
        raise ReviewError('generation.references must be a list')
    result['references'] = []
    for ref in references:
        if not isinstance(ref, dict) or ref.get('role') not in ('background', 'style', 'content_asset'):
            raise ReviewError('Reference image needs a background, style or content_asset role')
        path = local(root, ref['path'])
        if not path.is_file():
            raise ReviewError(f'Missing generation reference image: {ref["path"]}')
        result['references'].append({'path': ref['path'], 'role': ref['role'],
                                     'sha256': digest(path.read_bytes())})
    return result


def snapshot(root: Path, spec: dict) -> list[dict]:
    from PIL import Image
    if not isinstance(spec.get('bindings'), list) or not spec['bindings']:
        raise ReviewError('bindings must name at least one archived source or content file')
    bindings = {}
    for name in spec['bindings']:
        p = local(root, name)
        if not p.is_file():
            raise ReviewError(f'Missing binding: {name}')
        bindings[name] = digest(p.read_bytes())
    rows = []
    ids, names = set(), set()
    for row in spec.get('pages', []):
        if not all(isinstance(row.get(k), str) and row[k].strip()
                   for k in ('id', 'svg', 'reference', 'blueprint')):
            raise ReviewError('Each page needs id, svg basename, reference image and blueprint JSON')
        if row['id'] in ids or row['svg'] in names or Path(row['svg']).name != row['svg']:
            raise ReviewError('Duplicate page id/SVG or non-basename SVG')
        ids.add(row['id']); names.add(row['svg'])
        ref, brief = local(root, row['reference']), local(root, row['blueprint'])
        with Image.open(ref) as im:
            im.verify()
        with Image.open(ref) as im:
            size = list(im.size)
        if not isinstance(load(brief), dict):
            raise ReviewError(f'Blueprint must be a JSON object: {brief}')
        item = {k: row[k] for k in ('id', 'svg', 'reference', 'blueprint')}
        item.update(reference_sha256=digest(ref.read_bytes()),
                    blueprint_sha256=digest(brief.read_bytes()), dimensions=size,
                    bindings=bindings)
        generation = generation_snapshot(root, row, spec.get('reference_generation'))
        if generation is not None:
            item['generation'] = generation
        item['fingerprint'] = fingerprint(item)
        rows.append(item)
    if not rows:
        raise ReviewError('No page references')
    return rows


def prepare(project, pages_file) -> dict:
    root = Path(project).resolve()
    pages_file = Path(pages_file).resolve()
    if not pages_file.is_relative_to(root):
        raise ReviewError('pages JSON must be archived inside project')
    rows = snapshot(root, load(pages_file))
    # The converter uses the same numeric filename ordering. Do not accept a
    # reference order the final file would silently contradict.
    ordered = sorted([Path(row['svg']) for row in rows], key=_slide_filename_sort_key)
    if [p.name for p in ordered] != [r['svg'] for r in rows]:
        raise ReviewError('Reference order must match exporter numeric SVG filename order')
    path = root / 'reference_review/manifest.json'
    old = load(path) if path.exists() else {}
    version = old.get('version', 0) + (old.get('pages') != rows or old.get('pages_file') != pages_file.relative_to(root).as_posix())
    result = {'schema_version': 1, 'version': version,
              'pages_file': pages_file.relative_to(root).as_posix(), 'pages': rows}
    write(path, result)
    return result


def current(root: Path) -> dict:
    path = root / 'reference_review/manifest.json'
    if not path.is_file():
        raise ReviewError('Missing reference_review/manifest.json; prepare and show reference images in chat first')
    manifest = load(path)
    if manifest.get('schema_version') != 1:
        raise ReviewError('Unsupported reference manifest')
    if snapshot(root, load(local(root, manifest['pages_file']))) != manifest['pages']:
        raise ReviewError('Reference, blueprint or source changed: prepare a new revision and reconfirm affected pages')
    return manifest


def record_decision(project, *, version: int, page_ids: list[str], decision: str,
                    message: str, message_id: str) -> dict:
    root = Path(project).resolve()
    manifest = current(root)
    if version != manifest['version']:
        raise ReviewError('Stale review version')
    if decision not in ('approved', 'delegated', 'changes_requested') or not message.strip() or not message_id.strip():
        raise ReviewError('An explicit decision, verbatim user message and message reference are required')
    pages = {p['id']: p for p in manifest['pages']}
    if not page_ids or len(set(page_ids)) != len(page_ids) or set(page_ids) - pages.keys():
        raise ReviewError('List explicit, unique, existing page ids')
    receipt = {'version': version, 'timestamp_utc': datetime.now(timezone.utc).isoformat(),
               'decision': decision, 'message': message, 'message_id': message_id,
               'pages': {p: pages[p]['fingerprint'] for p in page_ids},
               'evidence_scope': 'Agent transcription of a human chat message; not authenticated by this script'}
    path = root / 'reference_review/decisions.jsonl'
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(receipt, ensure_ascii=False) + '\n')
    return receipt


def check(project, source='svg_output', *, require_svgs=True) -> dict:
    root = Path(project).resolve()
    manifest = current(root)
    receipts = root / 'reference_review/decisions.jsonl'
    latest = {}
    if receipts.exists():
        for line in receipts.read_text(encoding='utf-8').splitlines():
            receipt = json.loads(line)
            for page_id, fp in receipt['pages'].items():
                latest[(page_id, fp)] = receipt['decision']
    pending = [p['id'] for p in manifest['pages']
               if latest.get((p['id'], p['fingerprint'])) not in ('approved', 'delegated')]
    if pending:
        raise ReviewError('Explicit chat approval required: ' + ', '.join(pending))
    if require_svgs:
        folder = local(root, source)
        files = discover_slide_svgs(folder)
        if [p.name for p in files] != [p['svg'] for p in manifest['pages']]:
            raise ReviewError('SVG coverage/order differs from approved references')
        forbidden_hashes = {p['reference_sha256'] for p in manifest['pages']}
        for svg in files:
            tree = ET.parse(svg)
            for element in tree.iter():
                if element.tag.rsplit('}', 1)[-1] != 'image':
                    continue
                href = element.get('href') or element.get('{http://www.w3.org/1999/xlink}href', '')
                if href.startswith('data:') and ';base64,' in href:
                    data = base64.b64decode(href.split(',', 1)[1])
                elif href and not urlparse(href).scheme:
                    path = (svg.parent / unquote(href.split('#', 1)[0])).resolve()
                    data = path.read_bytes() if path.is_file() else b''
                else:
                    data = b''
                if data and digest(data) in forbidden_hashes:
                    raise ReviewError(f'{svg.name}: reference bitmap embedded; reconstruct native components')
    return {'status': 'authorized_snapshot_verified', 'version': manifest['version'],
            'page_count': len(manifest['pages']),
            'reference_methods': {p['id']: p.get('generation', {}).get('method', 'legacy_unspecified')
                                  for p in manifest['pages']},
            'limits': 'Approval/version/coverage gate only. Native readback and actual PPTX visual comparison still required.'}


def main(argv=None):
    from console_encoding import configure_utf8_stdio
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare'); p.add_argument('project'); p.add_argument('--pages', required=True)
    p = sub.add_parser('record'); p.add_argument('project'); p.add_argument('--version', type=int, required=True)
    p.add_argument('--pages', nargs='+', required=True)
    p.add_argument('--decision', choices=['approved', 'delegated', 'changes_requested'], required=True)
    p.add_argument('--message', required=True); p.add_argument('--message-id', required=True)
    p = sub.add_parser('check'); p.add_argument('project'); p.add_argument('--source', default='svg_output')
    p.add_argument('--before-authoring', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare':
            result = prepare(args.project, args.pages)
            result = {'status': 'prepared_not_approved', 'version': result['version'],
                      'pages': [p['id'] for p in result['pages']]}
        elif args.command == 'record':
            result = record_decision(args.project, version=args.version, page_ids=args.pages,
                                     decision=args.decision, message=args.message, message_id=args.message_id)
        else:
            result = check(args.project, args.source, require_svgs=not args.before_authoring)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ReviewError, OSError, ValueError, KeyError, ET.ParseError) as exc:
        print(f'REFERENCE REVIEW BLOCKED: {exc}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
