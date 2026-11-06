// 현재 HTML 배치와 글꼴을 보존하는 독립 SVG를 만든다.
() => {
  const source = document.querySelector('.figure');
  const clone = source.cloneNode(true);
  const originals = [source, ...source.querySelectorAll('*')];
  const copies = [clone, ...clone.querySelectorAll('*')];
  originals.forEach((original, i) => {
    const style = getComputedStyle(original);
    copies[i].removeAttribute('style');
    Array.from(style).forEach(key => copies[i].style.setProperty(key, style.getPropertyValue(key)));
  });
  clone.querySelectorAll('.arch-motion-overlay').forEach(el => el.remove());
  clone.style.margin = '0';
  const bounds = source.getBoundingClientRect();
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('width', Math.ceil(bounds.width));
  svg.setAttribute('height', Math.ceil(bounds.height));
  svg.setAttribute('viewBox', `0 0 ${Math.ceil(bounds.width)} ${Math.ceil(bounds.height)}`);
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', document.querySelector('.canvas').getAttribute('aria-label'));
  const foreign = document.createElementNS(ns, 'foreignObject');
  foreign.setAttribute('width', '100%'); foreign.setAttribute('height', '100%');
  const wrapper = document.createElement('div');
  wrapper.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml');
  const fonts = document.createElement('style');
  fonts.textContent = [...document.querySelectorAll('style')].map(s =>
    (s.textContent.match(/@font-face\s*\{[^}]*\}/g) || []).join('\n')).join('\n');
  wrapper.append(fonts, clone); foreign.append(wrapper); svg.append(foreign);
  return new XMLSerializer().serializeToString(svg);
}
