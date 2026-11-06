// 기존 연결 경로를 재사용하고 뷰어와 독립적인 재생 상태를 관리한다.
(function () {
  'use strict';
  const canvas = document.querySelector('.canvas[data-motion]');
  if (!canvas) return;
  const mode = canvas.dataset.motion;
  const edges = Array.from(canvas.querySelectorAll('svg.edges path[data-from][data-to]'));
  const nodes = Array.from(canvas.querySelectorAll('.node[data-id]'));
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const ko = document.documentElement.lang.startsWith('ko');
  const words = ko ? ['재생', '일시정지', '재시작', '반복', '속도', '동작 줄이기 설정 적용'] : ['Play', 'Pause', 'Restart', 'Loop', 'Speed', 'Reduced motion enabled'];
  const controls = document.createElement('div');
  controls.className = 'arch-motion-controls';
  const play = document.createElement('button');
  const restart = document.createElement('button');
  play.type = restart.type = 'button';
  restart.textContent = words[2];
  const speedLabel = document.createElement('label');
  speedLabel.textContent = words[4] + ' ';
  const speed = document.createElement('select');
  speed.setAttribute('aria-label', words[4]);
  [0.5, 1, 1.5, 2].forEach(value => {
    const option = document.createElement('option');
    option.value = String(value); option.textContent = value + '×'; option.selected = value === 1;
    speed.append(option);
  });
  speedLabel.append(speed);
  const loopLabel = document.createElement('label');
  const loop = document.createElement('input');
  loop.type = 'checkbox'; loop.checked = true;
  loopLabel.append(loop, ' ' + words[3]);
  const status = document.createElement('span');
  status.setAttribute('role', 'status');
  controls.append(play, restart, speedLabel, loopLabel, status);
  document.querySelector('.figure').after(controls);
  const ns = 'http://www.w3.org/2000/svg';
  const overlay = document.createElementNS(ns, 'svg');
  overlay.setAttribute('class', 'arch-motion-overlay');
  overlay.setAttribute('aria-hidden', 'true');
  overlay.setAttribute('viewBox', canvas.querySelector('svg.edges').getAttribute('viewBox'));
  canvas.querySelector('svg.edges').after(overlay);
  const tracks = edges.map(edge => {
    const dot = document.createElementNS(ns, 'circle');
    dot.setAttribute('r', '2');
    const trace = document.createElementNS(ns, 'path');
    trace.setAttribute('d', edge.getAttribute('d'));
    const length = edge.getTotalLength();
    trace.style.strokeDasharray = String(length);
    overlay.append(trace, dot);
    return { edge, dot, trace, length };
  });
  const canvasBox = canvas.getBoundingClientRect();
  const nodeFrames = nodes.map(node => {
    const tile = node.querySelector('.tile').getBoundingClientRect();
    const rect = document.createElementNS(ns, 'rect');
    rect.setAttribute('x', tile.left - canvasBox.left + 2);
    rect.setAttribute('y', tile.top - canvasBox.top + 2);
    rect.setAttribute('width', tile.width - 4);
    rect.setAttribute('height', tile.height - 4);
    rect.setAttribute('rx', '10');
    overlay.append(rect);
    const length = rect.getTotalLength();
    rect.style.strokeDasharray = String(length);
    return { node, rect, length };
  });
  const intro = Math.max(1, nodes.length + edges.length) * 500;
  const duration = mode === 'flow' ? 3000 : mode === 'combined' ? intro + 3000 : intro;
  let time = 0, running = false, previous = null, frame = null, rate = 1;
  function paint() {
    nodes.forEach(node => node.classList.remove('arch-step'));
    const focusing = canvas.classList.contains('has-focus');
    const phase = mode === 'combined' ? time - intro : time;
    nodeFrames.forEach((track, index) => {
      const progress = Math.max(0, Math.min(1, (time - index * 500) / 500));
      const drawing = (mode === 'draw' || mode === 'combined') && time < intro && !reduced.matches && !track.node.querySelector('.tile').classList.contains('bare');
      track.rect.style.display = drawing && progress > 0 && (!focusing || track.node.classList.contains('is-on')) ? '' : 'none';
      track.rect.style.strokeDashoffset = String(track.length * (1 - progress));
    });
    tracks.forEach((track, index) => {
      const visible = !focusing || track.edge.classList.contains('is-on');
      const flow = (mode === 'flow' || mode === 'combined') && phase >= 0 && !reduced.matches;
      track.dot.style.display = visible && flow ? '' : 'none';
      const fraction = ((Math.max(0, phase) % 3000) / 3000);
      const point = track.edge.getPointAtLength(fraction * track.length);
      track.dot.setAttribute('cx', point.x); track.dot.setAttribute('cy', point.y);
      track.dot.style.opacity = String(Math.min(1, fraction * 12, (1 - fraction) * 12));
      const drawing = (mode === 'draw' || mode === 'combined') && time < intro && !reduced.matches;
      const progress = Math.max(0, Math.min(1, (time - (nodes.length + index) * 500) / 500));
      track.trace.style.display = visible && drawing && progress > 0 ? '' : 'none';
      track.trace.style.strokeDashoffset = String(track.length * (1 - progress));
    });
    if (!reduced.matches && (mode === 'steps' || ((mode === 'draw' || mode === 'combined') && time < intro))) {
      const step = Math.min(nodes.length + edges.length - 1, Math.floor(time / 500));
      const selected = step < nodes.length ? [nodes[step]] : nodes.filter(n => {
        const e = edges[step - nodes.length];
        return e && (e.dataset.from === n.dataset.id || e.dataset.to === n.dataset.id);
      });
      selected.filter(n => !focusing || n.classList.contains('is-on')).forEach(n => n.classList.add('arch-step'));
      const description = selected.map(n => n.querySelector('.name').textContent.trim() + (n.dataset.note ? ': ' + n.dataset.note : '')).join(' → ');
      if (status.textContent !== description) status.textContent = description;
    } else status.textContent = reduced.matches ? words[5] : '';
    play.textContent = running ? words[1] : words[0];
    play.setAttribute('aria-pressed', String(running));
    play.disabled = restart.disabled = reduced.matches;
  }
  function tick(now) {
    frame = null;
    if (reduced.matches) { pause(); return; }
    if (!running) return;
    if (previous !== null) time += (now - previous) * rate;
    previous = now;
    if (time >= duration) {
      if (loop.checked) time %= duration;
      else { time = duration; running = false; }
    }
    paint();
    if (running) frame = requestAnimationFrame(tick);
  }
  function pause() {
    running = false; previous = null;
    if (frame !== null) cancelAnimationFrame(frame);
    frame = null; paint();
  }
  function start() {
    if (reduced.matches || running) return;
    if (time >= duration) time = 0;
    overlay.style.display = '';
    running = true; previous = null; paint(); frame = requestAnimationFrame(tick);
  }
  function seek(ms) {
    if (!Number.isFinite(ms) || ms < 0) throw new Error('invalid animation time');
    pause(); overlay.style.display = ''; time = Math.min(ms, duration); paint();
  }
  function reset() { pause(); time = 0; start(); }
  function settle() { pause(); overlay.style.display = 'none'; nodes.forEach(n => n.classList.remove('arch-step')); }
  play.addEventListener('click', () => { overlay.style.display = ''; running ? pause() : start(); });
  restart.addEventListener('click', () => { overlay.style.display = ''; reset(); });
  speed.addEventListener('change', () => { rate = Number(speed.value); });
  reduced.addEventListener('change', () => { pause(); paint(); });
  new MutationObserver(paint).observe(canvas, { attributes:true, attributeFilter:['class'] });
  window.ArchDiagramMotion = { pause, play:start, restart:reset, seek, settle, duration,
    get state() { return { time, running, speed:rate, loop:loop.checked, mode }; } };
  paint(); start();
})();
