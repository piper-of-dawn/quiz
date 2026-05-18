(function () {
  function initGrid() {
    const canvas = document.getElementById('gridCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const gridSize = 28;
    const hoverRadius = 150;
    let mouseX = -1e9;
    let mouseY = -1e9;

    function resize() {
      const dpr = window.devicePixelRatio || 1;
      const w = window.innerWidth;
      const h = window.innerHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);
    }

    function draw() {
      const w = window.innerWidth;
      const h = window.innerHeight;
      const styles = getComputedStyle(document.body);
      const rgb = styles.getPropertyValue('--secondary-rgb').trim() || '134, 182, 255';
      const baseOpacity = parseFloat(styles.getPropertyValue('--grid-base-opacity')) || 0.06;
      const hoverBoost = parseFloat(styles.getPropertyValue('--grid-hover-opacity-boost')) || 0.12;
      const baseSize = parseFloat(styles.getPropertyValue('--grid-base-size')) || 1;
      const sizeBoost = parseFloat(styles.getPropertyValue('--grid-hover-size-boost')) || 0.45;
      ctx.clearRect(0, 0, w, h);
      const offsetY = -(window.scrollY % gridSize);
      for (let y = offsetY; y < h + gridSize; y += gridSize) {
        for (let x = 0; x < w + gridSize; x += gridSize) {
          const dist = Math.hypot(x - mouseX, y - mouseY);
          let opacity = baseOpacity;
          let size = baseSize;
          if (dist < hoverRadius) {
            const intensity = 1 - dist / hoverRadius;
            opacity += intensity * hoverBoost;
            size += intensity * sizeBoost;
          }
          ctx.beginPath();
          ctx.arc(x, y, size, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(${rgb}, ${opacity})`;
          ctx.fill();
        }
      }
      requestAnimationFrame(draw);
    }

    document.addEventListener('mousemove', function (event) {
      mouseX = event.clientX;
      mouseY = event.clientY;
    });
    window.addEventListener('resize', resize);
    resize();
    requestAnimationFrame(draw);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGrid, { once: true });
  } else {
    initGrid();
  }
})();
