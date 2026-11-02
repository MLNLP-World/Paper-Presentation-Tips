"""Portable image generation, attribution and local preview behavior."""
import base64
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / 'skills/ppt-master'
SCRIPTS = SKILL / 'scripts'
sys.path.insert(0, str(SCRIPTS))
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aD1sAAAAASUVORK5CYII=')


class PptMasterRelease(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ppt-master-release-')
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def run_python(self, *args, env=None):
        return subprocess.run([sys.executable, *map(str, args)], cwd=self.root,
                              capture_output=True, text=True, encoding='utf-8',
                              env=dict(os.environ, PYTHONUTF8='1', **(env or {})), timeout=30)

    def guard_fixture(self):
        from attribution_guard import _REQUIRED_GATE_FILES
        files = ['SKILL.md', 'LICENSE', 'scripts/attribution_guard.py', *_REQUIRED_GATE_FILES]
        for name in files:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SKILL / name, target)
        entry = self.root / 'SKILL.md'
        text = entry.read_text(encoding='utf-8')
        text = text.replace('  sponsors:\n    - "SPONSORS.md"\n    - "SPONSORS_CN.md"\n', '')
        entry.write_text(text, encoding='utf-8')
        return self.root / 'scripts/attribution_guard.py'

    def test_sponsor_free_package_preserves_attribution_guard(self):
        script = self.guard_fixture()
        result = self.run_python(script)
        self.assertEqual(0, result.returncode, result.stderr)
        license_file = self.root / 'LICENSE'
        license_file.write_text('removed copyright', encoding='utf-8')
        self.assertNotEqual(0, self.run_python(script).returncode)

    def test_external_api_requires_explicit_selection(self):
        result = self.run_python(SCRIPTS / 'image_gen.py', 'OFFLINE TEST')
        self.assertEqual(2, result.returncode)
        self.assertIn('--allow-api', result.stderr)

    def test_selected_api_uses_reference_image_and_saves_real_output(self):
        calls = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers['Content-Length']))
                calls.append((self.path, body))
                payload = json.dumps({'data': [{'b64_json': base64.b64encode(PNG).decode()}]}).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        background = self.root / 'background.png'
        background.write_bytes(PNG)
        env = {'OPENAI_API_KEY': 'offline-fixture-not-a-real-key',
               'OPENAI_BASE_URL': f'http://127.0.0.1:{server.server_port}/v1',
               'OPENAI_MODEL': 'fixture-image', 'OPENAI_SIZE_PRESET': 'legacy',
               'IMAGE_BACKEND': 'openai'}
        result = self.run_python(SCRIPTS / 'image_gen.py', 'OFFLINE TEST exact slide',
                                 '--allow-api', '--reference-image', background,
                                 '--output', self.root / 'images', '--filename', 'reference', env=env)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        self.assertEqual(1, len(calls))
        self.assertTrue(calls[0][0].endswith('/images/edits'))
        self.assertIn(b'OFFLINE TEST exact slide', calls[0][1])
        self.assertIn(PNG, calls[0][1])
        self.assertTrue(list((self.root / 'images').glob('reference.*')))

    def test_api_reference_evidence_is_not_labelled_host_native(self):
        from reference_review import generation_snapshot, ReviewError
        (self.root / 'prompt.md').write_text('OFFLINE TEST full slide prompt', encoding='utf-8')
        generation = {'method': 'external_image_api', 'tool': 'image_gen.py',
                      'invocation_ref': 'offline-test-command', 'prompt': 'prompt.md',
                      'provider': 'fixture', 'model': 'fixture-image',
                      'authorization': {'message': 'TEST FIXTURE: use configured API',
                                        'message_id': 'offline-fixture'}}
        result = generation_snapshot(self.root, {'generation': generation}, 'external_image_api')
        self.assertEqual('external_image_api', result['method'])
        self.assertEqual('fixture', result['provider'])
        del generation['authorization']
        with self.assertRaises(ReviewError):
            generation_snapshot(self.root, {'generation': generation}, 'external_image_api')

    def test_local_preview_resolves_picture_and_icon_without_web_service(self):
        module = importlib.import_module('visual_review')
        prepare_content = getattr(module, 'prepare_slide_content')
        (self.root / 'svg_output').mkdir()
        (self.root / 'images').mkdir()
        (self.root / 'icons/imported').mkdir(parents=True)
        (self.root / 'images/picture.png').write_bytes(PNG)
        (self.root / 'icons/imported/marker.svg').write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M0 0h24v24H0z"/></svg>', encoding='utf-8')
        source = self.root / 'svg_output/page.svg'
        source.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 90">'
                          '<image href="../images/picture.png" width="40" height="40"/>'
                          '<use data-icon="imported/marker" x="60" y="0" width="24" height="24"/>'
                          '<text x="10" y="70">中文 preview</text></svg>', encoding='utf-8')
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        content = prepare_content(self.root, source)
        self.assertIn('data:image/png;base64,', content)
        self.assertNotIn('<use ', content)
        self.assertIn('中文 preview', content)
        self.assertEqual(before, hashlib.sha256(source.read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
