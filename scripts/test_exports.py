# 실제 미디어 내보내기의 프레임과 글꼴 및 테마를 검증한다.
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/arch-diagram/scripts'))
from presentation import present
from export_media import export, save_gif


class EncoderTests(unittest.TestCase):
    def test_frame_encoding(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'frames.gif'
            save_gif([Image.new('RGB', (40, 30), color) for color in ('red', 'blue', 'red')], path, 10)
            with Image.open(path) as result:
                self.assertGreaterEqual(result.n_frames, 2)
                self.assertEqual(result.info['loop'], 0)
                self.assertEqual(result.size, (40, 30))


class BrowserExportTests(unittest.TestCase):
    def test_actual_media(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = (ROOT / 'skills/arch-diagram/assets/examples/order-service.html').read_text()
            html = root / 'diagram.html'
            html.write_text(present(source, style='full-sketch', animate=True))
            svg, gif, png = root / 'diagram.svg', root / 'diagram.gif', root / 'diagram.png'
            export(html, svg, 'svg')
            document = ET.parse(svg)
            self.assertEqual(len(document.findall('.//{http://www.w3.org/2000/svg}foreignObject')), 1)
            self.assertIn('@font-face', svg.read_text())
            self.assertIn('data:image/', svg.read_text())
            self.assertIn('저장소', svg.read_text())
            from playwright.sync_api import sync_playwright
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page()
                page.goto(svg.as_uri())
                page.evaluate('document.fonts.ready')
                centered = page.locator('.tile').first.evaluate('''tile => {
                    const a = tile.getBoundingClientRect();
                    const b = tile.querySelector('img').getBoundingClientRect();
                    return Math.abs((a.left+a.right-b.left-b.right)/2) < 1;
                }''')
                self.assertTrue(centered)
                self.assertEqual(page.locator('.sw').first.evaluate('e => getComputedStyle(e).borderTopStyle'), 'solid')
                browser.close()
            export(html, gif, 'gif', fps=4, width=640, seconds=1)
            with Image.open(gif) as result:
                self.assertGreater(result.n_frames, 1)
                result.seek(0)
                first = result.convert('RGB')
                result.seek(1)
                self.assertIsNotNone(ImageChops.difference(first, result.convert('RGB')).getbbox())
            subprocess.run([sys.executable, str(ROOT / 'skills/arch-diagram/scripts/render_png.py'),
                            str(html), str(png), '--scale', '1'], check=True, capture_output=True)
            light = Image.open(png).convert('RGB')
            dark = Image.open(root / 'diagram-dark.png').convert('RGB')
            self.assertEqual(light.size, dark.size)
            self.assertIsNotNone(ImageChops.difference(light, dark).getbbox())


if __name__ == '__main__':
    unittest.main()
