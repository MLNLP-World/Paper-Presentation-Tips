"""Install the real PPT Master bundle and use it outside this repository."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'skills/ppt-master'
INSTALLER = ROOT / 'skills/ppt-master/scripts/install_skill.py'


class PptMasterPackaging(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        runtime = ROOT / '.local/test-runtime'
        runtime.mkdir(parents=True, exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(prefix='ppt-master-portable-', dir=runtime)
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name).resolve()
        cls.target = cls.work / 'independent project' / '.claude/skills/ppt-master'
        result = cls.command(INSTALLER, '--skill', 'ppt-master', '--agent', 'claude',
                             '--project', cls.work / 'independent project')
        if result.returncode:
            raise AssertionError(result.stderr)

    @classmethod
    def command(cls, *args):
        return subprocess.run([sys.executable, *map(str, args)], cwd=cls.work,
                              env=dict(os.environ, PYTHONUTF8='1'),
                              capture_output=True, text=True, encoding='utf-8')

    def test_native_tools_and_resources_resolve_without_source_repository(self):
        result = self.command(self.target / 'scripts/attribution_guard.py')
        self.assertEqual(0, result.returncode, result.stderr)
        script = ('import sys,json;sys.path.insert(0,sys.argv[1]);'
                  'from project_management.paths import SKILL_DIR,CHARTS_DIR,SCHEMA_DIR;'
                  'print(json.dumps([str(SKILL_DIR),CHARTS_DIR.is_dir(),SCHEMA_DIR.is_dir()]))')
        result = self.command('-c', script, self.target / 'scripts')
        self.assertEqual(0, result.returncode, result.stderr)
        values = json.loads(result.stdout)
        self.assertEqual(self.target, Path(values[0]))
        self.assertEqual([True, True], values[1:])
        for tool in ('svg_to_pptx.py', 'reviewed_export.py', 'project_manager.py'):
            result = self.command(self.target / 'scripts' / tool, '--help')
            self.assertEqual(0, result.returncode, result.stderr)

    def test_full_bundle_is_byte_identical_and_has_no_repository_dependency(self):
        def paths(root):
            return {p.relative_to(root).as_posix() for p in root.rglob('*')
                    if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc', '.pyo')
                    and p.relative_to(root).parts[:2] != ('scripts', 'tests')
                    and p.relative_to(root).parts[0] != 'tests'}
        source_paths = paths(SOURCE)
        self.assertEqual(source_paths, paths(self.target) - {'local-marker.txt'})
        for relative in ['SKILL.md', 'LICENSE', 'scripts/reviewed_export.py',
                         'scripts/svg_to_pptx.py', 'references/academic-chat-design.md',
                         'assets/templates/charts/column_chart.svg']:
            source, target = SOURCE / relative, self.target / relative
            self.assertEqual(hashlib.sha256(source.read_bytes()).digest(),
                             hashlib.sha256(target.read_bytes()).digest(), str(source))
        self.assertGreater(len(source_paths), 12000)
        self.assertFalse((ROOT / 'tools/PPT-Master-local/skill').exists())
        self.assertFalse((self.target / 'scripts/tests').exists())
        self.assertFalse((self.target / 'tests').exists())
        self.assertFalse((self.target / 'SPONSORS.md').exists())

    def test_existing_install_is_not_silently_replaced(self):
        marker = self.target / 'local-marker.txt'
        marker.write_text('keep', encoding='utf-8')
        result = self.command(INSTALLER, '--skill', 'ppt-master', '--destination', self.target)
        self.assertNotEqual(0, result.returncode)
        self.assertIn('already exists', result.stderr)
        self.assertEqual('keep', marker.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
