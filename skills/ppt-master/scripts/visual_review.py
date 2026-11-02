#!/usr/bin/env python3
"""Render project SVGs to PNG with local Chromium; no web service is required.

Usage: python visual_review.py PROJECT [--pages 02 03]
Outputs: PROJECT/.preview/*.png and a JSON rendering summary.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET

from console_encoding import configure_utf8_stdio
from resource_paths import icon_dir_for_project
from svg_finalize.embed_icons import parse_use_element, resolve_icon_path, extract_paths_from_icon, generate_icon_group
from svg_finalize.embed_images import get_mime_type
from svg_to_pptx.geometry_properties import materialize_inline_geometry_properties
from slide_roster import discover_slide_svgs
from svg_to_pptx.canvas_contract import parse_project_svg_root

configure_utf8_stdio()


# Histogram threshold: PNG counts as "all background" if a single quantized
# color bucket holds >= ALL_BG_THRESHOLD of pixels. Guards against blank
# renders without false-firing on legitimate sparse dark layouts.
ALL_BG_THRESHOLD = 0.99


def _safe_print(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


@contextmanager
def file_lock(lock_path: Path, timeout: float = 30.0):
    """POSIX advisory lock via fcntl. Falls back to lockless on Windows."""
    try:
        import fcntl
    except ImportError:
        yield
        return

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fp = open(lock_path, 'w')
    deadline = time.monotonic() + timeout
    while True:
        try:
            fcntl.flock(fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                fp.close()
                raise TimeoutError(f"render lock contended for {timeout}s at {lock_path}")
            time.sleep(0.1)
    try:
        fp.write(str(os.getpid()))
        fp.flush()
        yield
    finally:
        fcntl.flock(fp.fileno(), fcntl.LOCK_UN)
        fp.close()
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def is_all_background(png_bytes: bytes) -> bool:
    """Histogram check: quantize each channel to 4 bits, count dominant bucket.
    Returns True only when the PNG is essentially monochrome (blank render)."""
    try:
        from PIL import Image
    except ImportError:
        # PIL not installed — skip this check, the rubric subagent will
        # re-validate visually.
        return False

    img = Image.open(io.BytesIO(png_bytes)).convert('RGB')
    pixels = img.getdata()
    total = img.width * img.height
    if total == 0:
        return True
    counts: dict[tuple[int, int, int], int] = {}
    for r, g, b in pixels:
        key = (r >> 4, g >> 4, b >> 4)
        counts[key] = counts.get(key, 0) + 1
    dominant = max(counts.values())
    return dominant / total >= ALL_BG_THRESHOLD


def _json_number(value: Decimal) -> int | float:
    """Keep integral canvas values compact while preserving fractional input."""
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def parse_slide_canvas(svg_content: str, page_name: str) -> dict:
    """Read the authoritative canvas from one inlined SVG root viewBox."""
    try:
        root = ET.fromstring(svg_content)
    except ET.ParseError as exc:
        raise ValueError(f'{page_name}: unable to parse root SVG: {exc}') from exc

    viewbox = parse_project_svg_root(root, context=page_name)
    width = _json_number(viewbox.width)
    height = _json_number(viewbox.height)
    return {
        'view_box': [_json_number(value) for value in viewbox.values],
        'width': width,
        'height': height,
        'png_width': math.ceil(float(viewbox.width)),
        'png_height': math.ceil(float(viewbox.height)),
    }


def prepare_slide_content(project_path: Path, svg_path: Path) -> str:
    """Resolve project assets in memory without changing the authored SVG."""
    project_path = project_path.resolve()
    svg_path = svg_path.resolve()
    if not svg_path.is_relative_to(project_path):
        raise ValueError('Preview SVG must be inside the project')
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    root = ET.fromstring(svg_path.read_text(encoding='utf-8-sig'))
    materialize_inline_geometry_properties(root)
    for parent in list(root.iter()):
        for index, node in enumerate(list(parent)):
            if node.tag.rsplit('}', 1)[-1] != 'use' or not node.get('data-icon'):
                continue
            attrs = parse_use_element(ET.tostring(node, encoding='unicode'))
            icon, _ = resolve_icon_path(str(attrs['icon']), icon_dir_for_project(project_path))
            elements, style, size = extract_paths_from_icon(icon, str(attrs.get('fill', '#000000')), target_dir=svg_path.parent)
            if not elements:
                raise ValueError(f'Icon has no visible geometry: {node.get("data-icon")}')
            replacement = ET.fromstring(generate_icon_group(attrs, elements, style, size))
            parent.remove(node)
            parent.insert(index, replacement)
    xlink = '{http://www.w3.org/1999/xlink}href'
    for node in root.iter():
        if node.tag.rsplit('}', 1)[-1] != 'image':
            continue
        href = node.get('href') or node.get(xlink) or ''
        if href.startswith('data:'):
            continue
        parts = urllib.parse.urlsplit(href)
        if not href or parts.scheme or parts.netloc:
            raise ValueError('Preview images must be local project assets or data URIs')
        image = (svg_path.parent / urllib.parse.unquote(parts.path)).resolve()
        if not image.is_relative_to(project_path):
            raise ValueError('Preview image leaves the project')
        payload = image.read_bytes()
        node.set('href', f'data:{get_mime_type(image.name, payload)};base64,' + base64.b64encode(payload).decode('ascii'))
        node.attrib.pop(xlink, None)
    return ET.tostring(root, encoding='unicode')


def render_pages(project_path: Path, pages: list[str], preview_dir: Path) -> list[dict]:
    """Render self-contained slides in one headless browser session."""
    from playwright.sync_api import sync_playwright

    preview_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []

    inject_js = """
({svgContent, width, height}) => {
    document.documentElement.innerHTML =
        '<head><style>html,body{margin:0;padding:0;background:#0E1116;overflow:hidden}'
        + ' svg{display:block;width:' + width + 'px;height:' + height + 'px}</style></head>'
        + '<body>' + svgContent + '</body>';
    return { len: svgContent.length };
}
"""

    with sync_playwright() as p:
        launch = {}
        if os.environ.get('PPT_MASTER_BROWSER_CHANNEL'):
            launch['channel'] = os.environ['PPT_MASTER_BROWSER_CHANNEL']
        browser = p.chromium.launch(**launch)
        try:
            context = browser.new_context()
            context.route('**/*', lambda route: route.abort())
            for page_name in pages:
                rec: dict = {'page': page_name, 'ok': False}
                try:
                    svg_content = prepare_slide_content(project_path, project_path / 'svg_output' / page_name)
                    canvas = parse_slide_canvas(svg_content, page_name)
                    rec['canvas'] = canvas
                except urllib.error.URLError as e:
                    rec['error'] = f'server_unreachable: {e!r}'
                    records.append(rec)
                    continue
                except Exception as e:  # noqa: BLE001
                    rec['error'] = f'{type(e).__name__}: {e}'
                    records.append(rec)
                    continue

                stem = page_name[:-4] if page_name.endswith('.svg') else page_name
                out_path = preview_dir / f'{stem}.png'

                pg = None
                try:
                    pg = context.new_page()
                    pg.set_viewport_size({
                        'width': canvas['png_width'],
                        'height': canvas['png_height'],
                    })
                    pg.goto('about:blank')
                    pg.evaluate(inject_js, {
                        'svgContent': svg_content,
                        'width': canvas['width'],
                        'height': canvas['height'],
                    })
                    pg.evaluate('() => document.fonts.ready')
                    pg.evaluate('''() => Promise.all(Array.from(document.querySelectorAll('image')).map(
                        node => new Promise((resolve, reject) => {
                            const image = new Image(); image.onload = resolve;
                            image.onerror = () => reject(new Error('Preview image failed to load'));
                            image.src = node.getAttribute('href');
                        })))''')
                    png_bytes = pg.screenshot(type='png', full_page=False)

                    out_path.write_bytes(png_bytes)
                    rec['path'] = str(out_path)
                    rec['bytes'] = len(png_bytes)
                    rec['all_background'] = is_all_background(png_bytes)
                    rec['ok'] = True
                except Exception as e:  # noqa: BLE001 — best-effort per-page
                    rec['error'] = f'{type(e).__name__}: {e}'
                finally:
                    if pg is not None:
                        try:
                            pg.close()
                        except Exception:  # noqa: BLE001 — cleanup is best-effort
                            pass
                records.append(rec)
        finally:
            browser.close()

    return records


def discover_pages(project_path: Path, requested: list[str] | None) -> list[str]:
    svg_dir = project_path / 'svg_output'
    if not svg_dir.is_dir():
        raise FileNotFoundError(f'no svg_output/ in {project_path}')
    all_svgs = [path.name for path in discover_slide_svgs(svg_dir)]
    if not requested:
        return all_svgs
    selected: list[str] = []
    tokens = [part for item in requested for part in item.split(',') if part]
    for token in tokens:
        match = next((n for n in all_svgs if n.startswith(token) or n == token), None)
        if match is None:
            raise ValueError(f'no SVG matches token {token!r} in {svg_dir}')
        selected.append(match)
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Render project SVGs to PNGs for visual review.',
    )
    parser.add_argument('project_path', help='Path to project directory (contains svg_output/)')
    parser.add_argument(
        '--pages', nargs='+', default=None,
        help='Page tokens to render (default: all SVGs in svg_output/). '
             "Accepts '02', '02_three_steps', or '02_three_steps.svg'; several "
             "pages are space- or comma-separated (--pages 02 04 or --pages 02,04).",
    )
    parser.add_argument(
        '--lock-timeout', type=float, default=30.0,
        help='Seconds to wait for render lock (default: 30)',
    )
    args = parser.parse_args()

    project_path = Path(args.project_path).resolve()
    if not project_path.is_dir():
        _safe_print(f'project path not found: {project_path}')
        return 2

    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        _safe_print(
            'playwright not installed. Install with:\n'
            '    pip install playwright\n'
            '    python3 -m playwright install chromium\n'
            '(see skills/ppt-master/requirements.txt)'
        )
        return 3

    try:
        pages = discover_pages(project_path, args.pages)
    except (FileNotFoundError, ValueError) as e:
        _safe_print(str(e))
        return 2

    preview_dir = project_path / '.preview'
    lock_path = preview_dir / '.render.lock'

    with file_lock(lock_path, timeout=args.lock_timeout):
        try:
            records = render_pages(project_path, pages, preview_dir)
        except Exception as e:  # noqa: BLE001 — browser launch failure
            _safe_print(f'browser session failed: {type(e).__name__}: {e}')
            _safe_print(
                'try:  python3 -m playwright install chromium'
            )
            return 3

    for rec in records:
        if not rec['ok']:
            _safe_print(f"[FAIL] {rec['page']}: {rec.get('error')}")
        elif rec.get('all_background'):
            _safe_print(f"[WARN] {rec['page']}: PNG rendered but is all-background")

    summary = {
        'project': str(project_path),
        'renderer': 'chromium-local',
        'rendered': sum(1 for r in records if r['ok']),
        'failed': sum(1 for r in records if not r['ok']),
        'all_background': sum(1 for r in records if r.get('all_background')),
        'pages': records,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if summary['failed']:
        return 4
    return 0


if __name__ == '__main__':
    sys.exit(main())
