// Centralized chart fetching + rendering helper
// Expose as window.fetchAndRenderAnswerData(aid, cid, wrapper)
window.fetchAndRenderAnswerData = async function(aid, cid, wrapper, userOptions = {}) {
  // aid: answer id (string), cid: canvas id, wrapper: DOM element where canvas resides
  console.debug('fetchAndRenderAnswerData start', aid, cid);
  // visible started marker
  const startedId = `${cid}-started`;
  let startedEl = document.createElement('div');
  startedEl.id = startedId;
  startedEl.className = 'text-xs text-gray-400 dark:text-gray-500 mt-1';
  startedEl.textContent = 'fetch démarré...';
  try { wrapper.appendChild(startedEl); } catch(e){}
  try { document.getElementById('debug-log').textContent = `Chargement graphique id ${aid}...`; } catch(e){}
  try {
    const resp = await fetch(`/api/answer-data/${aid}`);
    if (!resp.ok) {
      const errEl = document.createElement('div');
      errEl.className = 'text-sm text-red-500';
      const text = await resp.text().catch(()=>'');
      errEl.textContent = `Impossible de charger le graphique (status ${resp.status}) ${text}`;
      wrapper.appendChild(errEl);
      return;
    }
    const data = await resp.json();
    console.debug('Chart data for', aid, data);
    try { document.getElementById('debug-log').textContent = `Données reçues pour id ${aid}`; } catch(e){}

    // ensure canvas is present
    let canvasEl = document.getElementById(cid);
    let attempts = 0;
    while (!canvasEl && attempts < 10) {
      await new Promise(r => setTimeout(r, 40));
      canvasEl = document.getElementById(cid);
      attempts++;
    }
    if (!canvasEl) {
      const errEl = document.createElement('div');
      errEl.className = 'text-sm text-red-500';
      errEl.textContent = 'Canvas introuvable pour le graphique';
      wrapper.appendChild(errEl);
      return;
    }

    await new Promise(r => requestAnimationFrame(r));

    // prepare ctx and gradient
    canvasEl.style.width = '100%';
    canvasEl.style.height = '260px';
    const ctx = canvasEl.getContext('2d');
    const displayHeight = 260;
    const gradient = ctx.createLinearGradient(0, 0, 0, displayHeight);
    gradient.addColorStop(0, 'rgba(99,102,241,0.35)');
    gradient.addColorStop(1, 'rgba(99,102,241,0.05)');

    if (typeof Chart === 'undefined') {
      const errEl = document.createElement('div');
      errEl.className = 'text-sm text-red-500';
      errEl.textContent = 'Chart.js non chargé';
      wrapper.appendChild(errEl);
      console.error('Chart.js not loaded');
      return;
    }

    // destroy previous instance if any
    if (canvasEl._chartInstance) {
      try { canvasEl._chartInstance.destroy(); } catch(e) { /* ignore */ }
      canvasEl._chartInstance = null;
    }

    // create chart
    const isDarkMode = document.documentElement.classList.contains('dark');
    const axisColor = isDarkMode ? '#9CA3AF' : '#6B7280';
    try {
      const chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: (data.x || []).map(String),
          datasets: [{
            label: 'Valeurs',
            data: data.y || [],
            borderColor: '#6366f1',
            backgroundColor: gradient,
            tension: 0.35,
            pointRadius: 4,
            pointBackgroundColor: '#6366f1'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
          scales: {
            x: {
              ticks: { color: axisColor },
              grid: { color: 'transparent' },
              title: {
                display: true,
                text: (userOptions && userOptions.xLabel) ? userOptions.xLabel : 'Nombre d\'itérations / quantité de travail' ,
                color: axisColor,
                font: { size: 13, weight: '600' },
                padding: { top: 10 }
              }
            },
            y: {
              ticks: { color: axisColor },
              grid: { color: 'rgba(0,0,0,0.04)' },
              title: {
                display: true,
                text: (userOptions && userOptions.yLabel) ? userOptions.yLabel : 'Qualité du résultat' ,
                color: axisColor,
                font: { size: 13, weight: '600' },
                padding: { bottom: 8 }
              }
            }
          }
        }
      });
      canvasEl._chartInstance = chart;
      try { document.getElementById('debug-log').textContent = `Données reçues pour id ${aid}`; } catch(e){}
    } catch (chartErr) {
      console.error('Chart render error', chartErr);
      const errEl = document.createElement('div');
      errEl.className = 'text-sm text-red-500 mt-2';
      errEl.textContent = 'Erreur lors du rendu du graphique: ' + (chartErr && chartErr.message ? chartErr.message : '');
      wrapper.appendChild(errEl);
    }
  } catch (err) {
    console.error('fetchAndRenderAnswerData error', err);
    const errEl = document.createElement('div');
    errEl.className = 'text-sm text-red-500';
    errEl.textContent = 'Erreur lors du chargement du graphique: ' + (err && err.message ? err.message : '');
    wrapper.appendChild(errEl);
  } finally {
    // remove started marker
    try { const se = document.getElementById(`${cid}-started`); if (se) se.remove(); } catch(e){}
  }
};
