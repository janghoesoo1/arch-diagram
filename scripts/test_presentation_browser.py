# 실제 브라우저에서 오프라인 재생과 접근성 및 뷰어 호환성을 검증한다.
import sys
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/arch-diagram/scripts"))
from presentation import present, MODES

source = (ROOT / "skills/arch-diagram/assets/examples/order-service.html").read_text()
with tempfile.TemporaryDirectory() as directory, sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    for mode in MODES:
        path = Path(directory) / (mode + ".html")
        path.write_text(present(source, animate=True, mode=mode))
        context = browser.new_context(offline=True)
        page = context.new_page()
        errors, requests = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: requests.append(request.url) if request.url.startswith("http") else None)
        page.goto(path.as_uri())
        page.evaluate("document.fonts.ready")
        assert page.evaluate("!!window.ArchDiagramMotion"), mode
        page.evaluate("ArchDiagramMotion.pause()")
        before = page.evaluate("ArchDiagramMotion.state.time")
        page.wait_for_timeout(60)
        assert page.evaluate("ArchDiagramMotion.state.time") == before
        page.evaluate("ArchDiagramMotion.seek(1000)")
        assert page.evaluate("ArchDiagramMotion.state.time") == 1000
        page.locator('.arch-motion-controls input').uncheck()
        page.evaluate("ArchDiagramMotion.seek(ArchDiagramMotion.duration-30); ArchDiagramMotion.play()")
        page.wait_for_timeout(150)
        assert not page.evaluate("ArchDiagramMotion.state.running")
        assert page.evaluate("ArchDiagramMotion.state.time === ArchDiagramMotion.duration")
        page.locator('.arch-motion-controls input').check()
        page.evaluate("ArchDiagramMotion.seek(ArchDiagramMotion.duration-30); ArchDiagramMotion.play()")
        page.wait_for_timeout(150)
        assert page.evaluate("ArchDiagramMotion.state.running && ArchDiagramMotion.state.time < ArchDiagramMotion.duration")
        page.locator('.arch-motion-controls select').select_option('2')
        assert page.evaluate("ArchDiagramMotion.state.speed") == 2
        page.evaluate("ArchDiagramMotion.restart()")
        page.wait_for_timeout(80)
        assert page.evaluate("ArchDiagramMotion.state.running")
        page.locator('.node[data-id]').first.click()
        assert page.locator('.canvas').evaluate("e => e.classList.contains('has-focus')")
        page.evaluate("ArchDiagramMotion.pause()")
        light = page.evaluate("getComputedStyle(document.querySelector('.canvas')).backgroundColor")
        page.evaluate("document.documentElement.dataset.theme = 'dark'")
        assert page.evaluate("getComputedStyle(document.querySelector('.canvas')).backgroundColor") != light
        page.emulate_media(reduced_motion='reduce')
        page.wait_for_timeout(60)
        assert not page.evaluate("ArchDiagramMotion.state.running")
        assert page.locator('.arch-motion-controls button').first.is_disabled()
        assert page.locator('.arch-motion-overlay').evaluate("e => getComputedStyle(e).display") == 'none'
        assert not errors, errors
        assert not requests, requests
        context.close()
        print('passed offline controls, focus, dark, reduced motion:', mode)
    browser.close()
