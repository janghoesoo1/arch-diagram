# 예제 다이어그램의 시각 결함(흰 타일 위 흰 로고, 한글 고정폭 라벨, 범례 잘림)을 실제 브라우저로 검증한다.
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "skills/arch-diagram/assets/examples"

with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    for name in ("order-service", "rag-chatbot"):
        page = browser.new_page()
        page.goto((EXAMPLES / f"{name}.html").as_uri())
        page.evaluate("document.fonts.ready")
        page.evaluate("document.documentElement.setAttribute('data-theme','dark')")

        # a white tile stays white in dark theme, so it must never show the white (dk) logo variant
        bad = page.evaluate("""() => [...document.querySelectorAll('.tile:not(.bare):not(.dark) img.dk')]
            .filter(i => getComputedStyle(i).display !== 'none').map(i => i.closest('.node').dataset.id)""")
        assert not bad, f"{name}: white logo on white tile in dark theme: {bad}"

        # Korean labels: a monospace space is ~2x a Korean word gap, so labels must not use the mono stack
        mono = page.evaluate("""() => [...document.querySelectorAll('svg text.el, .node .role, .legend')]
            .filter(e => /[\\uac00-\\ud7a3]/.test(e.textContent))
            .filter(e => getComputedStyle(e).fontFamily.includes('Mono')).length""")
        assert mono == 0, f"{name}: {mono} Korean labels still in the monospace stack"

        # the legend's first swatch must not sit flush on the captured figure's left edge
        inset = page.evaluate("""() => document.querySelector('.legend .sw').getBoundingClientRect().left
            - document.querySelector('.figure').getBoundingClientRect().left""")
        assert inset >= 8, f"{name}: legend swatch only {inset}px from the figure edge"
        page.close()
    browser.close()
print("visual browser checks: ok")
