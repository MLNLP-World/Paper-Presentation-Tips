"""Behavior tests for reference approval; every message below is a test fixture."""
import json
import shutil
import subprocess
import sys
import unittest
import uuid
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[3] / 'skills' / 'paper-presentation-skill' / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from reference_review import ReviewError, prepare, record_decision, check


class ReferenceReviewTests(unittest.TestCase):
    def setUp(self):
        self.runtime = Path(__file__).resolve().parents[3] / '.local' / 'test-runtime'
        self.root = self.runtime / ('case-' + uuid.uuid4().hex)
        self.root.mkdir(parents=True)
        (self.root / 'reference_review').mkdir()
        (self.root / 'svg_output').mkdir()
        (self.root / 'source.md').write_text('Fixture: A=71%, B=79%', encoding='utf-8')
        from PIL import Image
        self.pages = []
        for i in (1, 2):
            Image.new('RGB', (160, 90), 'white').save(self.root / f'reference_review/P0{i}.png')
            (self.root / f'reference_review/P0{i}.json').write_text(
                json.dumps({'core_task': f'Fixture page {i}', 'components': ['native_text']}), encoding='utf-8')
            (self.root / f'svg_output/slide_0{i}.svg').write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 90"><text x="8" y="20">Fixture</text></svg>', encoding='utf-8')
            self.pages.append({'id': f'P0{i}', 'svg': f'slide_0{i}.svg',
                               'reference': f'reference_review/P0{i}.png',
                               'blueprint': f'reference_review/P0{i}.json'})
        self.roster = self.root / 'reference_review/pages.json'
        self.write_roster()

    def tearDown(self):
        assert self.root.resolve().is_relative_to(self.runtime.resolve())
        assert self.root.name.startswith('case-')
        shutil.rmtree(self.root)

    def write_roster(self):
        self.roster.write_text(json.dumps({'bindings': ['source.md'], 'pages': self.pages}), encoding='utf-8')

    def approve(self, ids=('P01', 'P02'), version=1):
        return record_decision(self.root, version=version, page_ids=list(ids),
                               decision='approved', message='TEST FIXTURE: these pages are approved',
                               message_id='unit-test-fixture')

    def test_no_approval_blocks_and_approval_allows(self):
        prepare(self.root, self.roster)
        with self.assertRaises(ReviewError):
            check(self.root)
        self.approve()
        self.assertEqual(check(self.root)['page_count'], 2)

    def test_changed_reference_requires_new_confirmation(self):
        prepare(self.root, self.roster)
        self.approve()
        from PIL import Image
        Image.new('RGB', (160, 90), 'blue').save(self.root / 'reference_review/P01.png')
        with self.assertRaises(ReviewError):
            check(self.root)
        prepare(self.root, self.roster)
        with self.assertRaises(ReviewError):
            check(self.root)
        self.approve(('P01',), 2)
        self.assertEqual(check(self.root)['page_count'], 2)

    def test_changed_page_brief_invalidates_only_that_page(self):
        prepare(self.root, self.roster)
        self.approve()
        (self.root / 'reference_review/P01.json').write_text('{"core_task":"changed"}', encoding='utf-8')
        prepare(self.root, self.roster)
        self.approve(('P01',), 2)
        self.assertEqual(check(self.root)['page_count'], 2)

    def test_stale_version_and_blank_receipt_are_rejected(self):
        prepare(self.root, self.roster)
        with self.assertRaises(ReviewError):
            self.approve(version=0)
        with self.assertRaises(ReviewError):
            record_decision(self.root, version=1, page_ids=['P01'], decision='approved', message='', message_id='test')

    def test_source_snapshot_drift_blocks(self):
        prepare(self.root, self.roster)
        self.approve()
        (self.root / 'source.md').write_text('A=71%, B=80%', encoding='utf-8')
        with self.assertRaises(ReviewError):
            check(self.root)

    def test_declining_previously_approved_page_revokes_it(self):
        prepare(self.root, self.roster)
        self.approve()
        record_decision(self.root, version=1, page_ids=['P01'], decision='changes_requested',
                        message='TEST FIXTURE: revise page one', message_id='unit-test-fixture-2')
        with self.assertRaises(ReviewError):
            check(self.root)

    def test_coverage_and_order_cannot_silently_change(self):
        prepare(self.root, self.roster)
        self.approve()
        (self.root / 'svg_output/slide_03.svg').write_text('<svg/>', encoding='utf-8')
        with self.assertRaises(ReviewError):
            check(self.root)
        (self.root / 'svg_output/slide_03.svg').unlink()
        self.pages.reverse()
        self.write_roster()
        with self.assertRaises(ReviewError):
            prepare(self.root, self.roster)

    def test_reference_bitmap_cannot_be_embedded_as_slide(self):
        prepare(self.root, self.roster)
        self.approve()
        (self.root / 'svg_output/slide_01.svg').write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"><image href="../reference_review/P01.png" width="160" height="90"/></svg>', encoding='utf-8')
        with self.assertRaises(ReviewError):
            check(self.root)

    def test_paths_must_stay_inside_project(self):
        self.pages[0]['reference'] = '../outside.png'
        self.write_roster()
        with self.assertRaises(ReviewError):
            prepare(self.root, self.roster)

    def test_explicit_delegation_is_not_mislabelled_as_visual_approval(self):
        prepare(self.root, self.roster)
        receipt = record_decision(self.root, version=1, page_ids=['P01', 'P02'],
                                  decision='delegated', message='TEST FIXTURE: proceed without waiting',
                                  message_id='delegation-test-fixture')
        self.assertEqual(receipt['decision'], 'delegated')
        self.assertEqual(check(self.root)['page_count'], 2)

    def test_export_cli_blocks_before_producing_unapproved_pptx(self):
        result = subprocess.run([sys.executable, str(SCRIPTS / 'reviewed_export.py'),
                                 str(self.root), '--no-notes'], capture_output=True, text=True,
                                encoding='utf-8', errors='replace')
        self.assertEqual(result.returncode, 2)
        self.assertFalse(list(self.root.rglob('*.pptx')))

    def test_legacy_image_api_cli_is_disabled(self):
        result = subprocess.run([sys.executable, str(SCRIPTS / 'image_gen.py'), 'TEST FIXTURE'],
                                capture_output=True, text=True, encoding='utf-8', errors='replace')
        self.assertEqual(result.returncode, 2)
        self.assertIn('External image API generation is disabled', result.stderr)

    def ai_roster(self):
        prompt = self.root / 'reference_review/P01-prompt.md'
        prompt.write_text('Make a complete slide: exact title, labels, A=71%, B=79%, two short takeaways.', encoding='utf-8')
        shutil.copy2(self.root / 'reference_review/P01.png', self.root / 'style.png')
        generations = []
        for page in self.pages:
            generation = {'method': 'host_native_image', 'tool': 'TEST FIXTURE native image tool',
                          'invocation_ref': 'synthetic-test-call', 'prompt': 'reference_review/P01-prompt.md',
                          'references': [{'path': 'style.png', 'role': 'style'}]}
            generations.append(generation)
            page['generation'] = generation
        spec = {'bindings': ['source.md'], 'reference_generation': 'host_native_image',
                'image_usage': ['none'], 'pages': self.pages}
        self.roster.write_text(json.dumps(spec), encoding='utf-8')
        return spec

    def test_full_slide_ai_is_allowed_when_final_assets_have_no_ai_images(self):
        self.ai_roster()
        manifest = prepare(self.root, self.roster)
        self.assertEqual(manifest['pages'][0]['generation']['method'], 'host_native_image')

    def test_ai_mode_requires_actual_prompt_and_tool_receipt_fields(self):
        spec = self.ai_roster()
        del spec['pages'][0]['generation']['invocation_ref']
        self.roster.write_text(json.dumps(spec), encoding='utf-8')
        with self.assertRaises(ReviewError):
            prepare(self.root, self.roster)

    def test_prompt_change_invalidates_the_approved_reference(self):
        self.ai_roster()
        prepare(self.root, self.roster)
        self.approve()
        (self.root / 'reference_review/P01-prompt.md').write_text('Different visual emphasis', encoding='utf-8')
        with self.assertRaises(ReviewError):
            check(self.root)

    def test_native_fallback_cannot_silently_replace_requested_ai_generation(self):
        spec = self.ai_roster()
        spec['pages'][0]['generation'] = {'method': 'native_design'}
        self.roster.write_text(json.dumps(spec), encoding='utf-8')
        with self.assertRaises(ReviewError):
            prepare(self.root, self.roster)

    def test_explicit_native_fallback_choice_is_supported(self):
        spec = self.ai_roster()
        spec['pages'][0]['generation'] = {'method': 'native_design',
            'authorization': {'message': 'TEST FIXTURE: choose native preview for P01', 'message_id': 'test-choice'}}
        self.roster.write_text(json.dumps(spec), encoding='utf-8')
        self.assertEqual(prepare(self.root, self.roster)['pages'][0]['generation']['method'], 'native_design')

    def test_changed_style_reference_invalidates_approval(self):
        self.ai_roster()
        prepare(self.root, self.roster)
        self.approve()
        from PIL import Image
        Image.new('RGB', (160, 90), 'orange').save(self.root / 'style.png')
        with self.assertRaises(ReviewError):
            check(self.root)


if __name__ == '__main__':
    unittest.main()
