# 표현 계층의 기본 출력과 구조 보존을 검증한다.
import sys
import tempfile
import unittest
import json
import subprocess
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/arch-diagram/scripts"))
import check
from presentation import present, MODES, STYLES, sketch_points, validate_points
import render
import layout
import build


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / "skills/arch-diagram/assets/examples/order-service.html").read_text()

    def test_default_bytes(self):
        self.assertEqual(self.source, present(self.source))

    def test_motion_preserves_scene(self):
        original = check.Diagram()
        original.feed(self.source)
        for mode in MODES:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                result = present(self.source, animate=True, mode=mode)
                parsed = check.Diagram()
                parsed.feed(result)
                for name in ("nodes", "groups", "svg", "img_srcs", "canvas"):
                    self.assertEqual(getattr(original, name), getattr(parsed, name), name)
                self.assertEqual(result.count('<script'), 1)
                self.assertEqual(result, present(self.source, animate=True, mode=mode))
                path = Path(directory) / "test.html"
                path.write_text(result)
                failures = [item for item in check.run(path).items if item[0] == "FAIL"]
                self.assertEqual(failures, [])

    def test_invalid_options(self):
        for options in ({"style": "other"}, {"mode": "other"}):
            with self.assertRaises(ValueError):
                present(self.source, **options)

    def test_dynamic_korean_controls_are_subset_input(self):
        text = build.page_text(present(self.source, animate=True))
        for label in ('재생', '일시정지', '재시작', '반복', '속도', '동작 줄이기 설정 적용'):
            self.assertIn(label, text)

    def test_sketch_geometry_icons_and_gate(self):
        original = check.Diagram()
        original.feed(self.source)
        for style in STYLES:
            with self.subTest(style=style), tempfile.TemporaryDirectory() as directory:
                result = present(self.source, style=style)
                parsed = check.Diagram()
                parsed.feed(result)
                for name in ("nodes", "groups", "svg", "img_srcs", "canvas"):
                    self.assertEqual(getattr(original, name), getattr(parsed, name), name)
                self.assertEqual(result, present(self.source, style=style))
                if style != "professional":
                    self.assertIn('class="arch-sketch"', result)
                path = Path(directory) / "sketch.html"
                path.write_text(result)
                self.assertEqual([x for x in check.run(path).items if x[0] == "FAIL"], [])

    def test_decoration_bounds(self):
        for width, height in ((60, 60), (300, 210), (1000, 800), (24, 24)):
            points = sketch_points(width, height, "same-id")
            validate_points(points, width, height)
            self.assertEqual(points, sketch_points(width, height, "same-id"))
        for points in ([(0, 4)], [(30, 30)], [(float('nan'), 4)]):
            with self.assertRaises(ValueError):
                validate_points(points, 60, 60)
        with self.assertRaises(ValueError):
            sketch_points(10, 60, "small")

    def test_cloud_boundary_preserved(self):
        for kind in ("aws", "gcp", "azure", "boundary", "ga-nested"):
            source = f'<head></head><div class="group {kind}" style="width:200px;height:200px"></div>'
            self.assertNotIn('<svg', present(source, style="hybrid-sketch"))

    def test_full_decorates_tiles_not_bare_logos(self):
        source = '<head></head><div class="tile"><img src="original"></div><div class="tile bare"><img src="vendor"></div>'
        self.assertNotIn('<svg', present(source, style="hybrid-sketch"))
        full = present(source, style="full-sketch")
        self.assertEqual(full.count('<svg'), 1)
        self.assertIn('<div class="tile bare"><img src="vendor"></div>', full)

    def test_cli_default_equivalence_and_export_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = root / 'spec.json'
            spec.write_text(json.dumps({'title':'Test', 'description':'A client.', 'lang':'en',
                'nodes':[{'id':'client','name':'Client','icon':'client','row':0,'col':0}]}))
            (root / 'client.svg').write_bytes((ROOT / 'skills/arch-diagram/assets/generic/browser.svg').read_bytes())
            draft = root / 'draft.html'
            draft.write_text(layout.build_draft(spec, root)[0])
            baseline = root / 'baseline.html'
            subprocess.run([sys.executable, str(render.HERE / 'build.py'), str(draft), str(root), str(baseline)], check=True, capture_output=True)
            out = root / 'result.html'
            args = ['render.py', str(spec), str(out), '--icons', str(root)]
            with patch.object(sys, 'argv', args):
                self.assertEqual(render.main(), 0)
            self.assertEqual(out.read_bytes(), baseline.read_bytes())
            previous = out.read_bytes()
            receipt = out.with_suffix('.receipt.json').read_bytes()
            png = out.with_suffix('.png')
            png.write_bytes(b'previous png')
            real_run = render.run
            def fail_export(cmd, **kwargs):
                if any(str(value).endswith(('render_png.py', 'export_media.py')) for value in cmd):
                    return subprocess.CompletedProcess(cmd, 1, '', 'intentional export failure')
                return real_run(cmd, **kwargs)
            for option in ('--png', '--svg'):
                with patch.object(sys, 'argv', args + [option]), patch.object(render, 'run', fail_export):
                    self.assertEqual(render.main(), 5)
                self.assertEqual(out.read_bytes(), previous)
                self.assertEqual(out.with_suffix('.receipt.json').read_bytes(), receipt)
                self.assertEqual(png.read_bytes(), b'previous png')
            with patch.object(sys, 'argv', args + ['--gif']), self.assertRaises(SystemExit) as error:
                render.main()
            self.assertEqual(error.exception.code, 2)
            for style in STYLES:
                for mode in MODES:
                    with patch.object(sys, 'argv', args + ['--style', style, '--animate', '--animation-mode', mode]):
                        self.assertEqual(render.main(), 0)
                    text = out.read_text()
                    self.assertIn(f'data-motion="{mode}"', text)
                    self.assertEqual([x for x in check.run(out).items if x[0] == 'FAIL'], [])


if __name__ == "__main__":
    unittest.main()
