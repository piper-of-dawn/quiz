(function () {
  function renderMath(el) {
    try {
      if (window.renderMathInElement) {
        window.renderMathInElement(el || document.body, {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '\\[', right: '\\]', display: true },
            { left: '$', right: '$', display: false },
            { left: '\\(', right: '\\)', display: false }
          ],
          throwOnError: false,
          strict: 'ignore',
          trust: false,
          ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
        });
      }
    } catch (err) {
      console.error('[mcq-math] render failed', err);
    }
  }

  function initQuiz() {
    const form = document.getElementById('quizForm');
    const questions = Array.from(document.querySelectorAll('section.question'));
    if (!form || !questions.length) return;

    const outcomeStatus = document.getElementById('outcomeStatus');
    const outcomePill = document.getElementById('outcomePill');
    const outcomeBody = document.getElementById('outcomeBody');
    const outcomeBox = document.getElementById('outcomeBox');
    const seeExplanationBtn = document.getElementById('seeExplanationBtn');
    const scoreEl = document.getElementById('scoreValue');
    const streakEl = document.getElementById('streakValue');
    const longestEl = document.getElementById('longestPill');
    const timerEl = document.getElementById('timerValue');
    const timeChartCanvas = document.getElementById('timeChartCanvas');
    const timeChartEmpty = document.getElementById('timeChartEmpty');
    const timeChartLatest = document.getElementById('timeChartLatest');
    const timeChartDelta = document.getElementById('timeChartDelta');
    const inlineBodies = new Map();
    const inlineStems = new Map();
    let activeExplanationHtml = '';
    let activeStemHtml = '';
    let chart = null;
    const firstAnswered = new Set();
    const avgSeries = [];
    const startTs = Date.now();
    const totalSecs = parseInt(document.body.dataset.timerSeconds || '0', 10) || 0;

    function setText(node, text) {
      if (node) node.textContent = text;
    }

    function recomputeTotals() {
      const answers = questions.map((question) => {
        const checked = question.querySelector('input[type="radio"]:checked');
        return checked && parseInt(checked.value, 10) === parseInt(question.dataset.correct, 10);
      });
      const score = answers.filter(Boolean).length;
      let streak = 0;
      for (let i = answers.length - 1; i >= 0; i--) {
        if (answers[i]) streak += 1;
        else break;
      }
      let longest = 0;
      let current = 0;
      answers.forEach((ok) => {
        current = ok ? current + 1 : 0;
        longest = Math.max(longest, current);
      });
      setText(scoreEl, `${score} / ${questions.length}`);
      setText(streakEl, String(streak));
      setText(longestEl, `Longest: ${longest}`);
    }

    function setOutcome(title, ok, body) {
      setText(outcomeStatus, title);
      if (outcomePill) {
        outcomePill.className = 'pill ' + (ok ? 'pill-success' : 'pill-danger');
        outcomePill.textContent = ok ? 'Right Answer' : 'Incorrect';
      }
      if (outcomeBody) {
        outcomeBody.innerHTML = body;
        renderMath(outcomeBody);
      }
      if (outcomeBox) outcomeBox.hidden = false;
      if (seeExplanationBtn) {
        seeExplanationBtn.hidden = false;
        seeExplanationBtn.classList.toggle('attention', !ok);
      }
    }

    function showExplanationPopup(html, stemHtml) {
      let modal = document.getElementById('explainModal');
      if (!modal) {
        modal = document.createElement('div');
        modal.id = 'explainModal';
        modal.className = 'katas-modal';
        modal.innerHTML = '<div class="katas-backdrop" data-close></div><div class="katas-dialog" role="dialog" aria-modal="true"><div class="katas-head"><h2 class="katas-title">Explanation</h2><button class="katas-close" type="button" data-close>&times;</button></div><div class="katas-body" id="explainBody"></div></div>';
        document.body.appendChild(modal);
        modal.addEventListener('click', (event) => {
          if (event.target && event.target.hasAttribute('data-close')) modal.classList.remove('show');
        });
        window.addEventListener('keydown', (event) => {
          if (event.key === 'Escape') modal.classList.remove('show');
        });
      }
      const body = modal.querySelector('#explainBody');
      body.innerHTML = `${stemHtml ? `<div class="katas-stem">${stemHtml}</div>` : ''}<div class="katas-richtext">${html}</div>`;
      renderMath(body);
      modal.classList.add('show');
    }

    function checkQuestion(question) {
      const qname = question.dataset.qname;
      const selected = question.querySelector('input[type="radio"]:checked');
      if (!selected) return;
      const correct = parseInt(question.dataset.correct, 10);
      const chosenIdx = parseInt(selected.value, 10);
      const ok = chosenIdx === correct;
      const data = JSON.parse(question.dataset.json || '{}');
      const choices = data.choices || [];
      const chosenText = choices[chosenIdx] || `Option ${chosenIdx + 1}`;
      const correctText = choices[correct] || `Option ${correct + 1}`;
      const explanation = data.explanation_html || data.explanation || '';
      const body = ok
        ? `<div><strong>${chosenText}</strong> is correct.</div>${explanation ? `<div>${explanation}</div>` : ''}`
        : `<div>Your answer: <strong>${chosenText}</strong><br>Correct answer: <strong>${correctText}</strong></div>${explanation ? `<div>${explanation}</div>` : ''}`;
      activeExplanationHtml = body;
      activeStemHtml = (question.querySelector('.stem') || {}).innerHTML || '';
      inlineBodies.set(qname, body);
      inlineStems.set(qname, activeStemHtml);
      const inlineBtn = question.querySelector('.inline-explain-btn');
      if (inlineBtn) {
        inlineBtn.hidden = false;
        inlineBtn.classList.toggle('attention', !ok);
      }
      question.classList.toggle('correct', ok);
      question.classList.toggle('incorrect', !ok);
      question.classList.remove('glow-correct', 'glow-incorrect');
      void question.offsetWidth;
      question.classList.add(ok ? 'glow-correct' : 'glow-incorrect');
      window.setTimeout(() => {
        question.classList.remove('glow-correct', 'glow-incorrect');
      }, 4100);
      question.querySelectorAll('.choice').forEach((choice) => choice.classList.remove('is-correct', 'is-incorrect'));
      const selectedLi = selected.closest('.choice');
      if (selectedLi) selectedLi.classList.add(ok ? 'is-correct' : 'is-incorrect');
      setOutcome(`Question ${Number(qname.replace('q', '')) + 1}`, ok, body);
      recomputeTotals();
    }

    function fmtMMSS(value) {
      const sign = value < 0 ? '-' : '';
      const abs = Math.abs(Math.floor(value));
      return `${sign}${String(Math.floor(abs / 60)).padStart(2, '0')}:${String(abs % 60).padStart(2, '0')}`;
    }

    function updateTimer() {
      if (!timerEl || totalSecs <= 0) return;
      const remaining = Math.round(totalSecs - ((Date.now() - startTs) / 1000));
      timerEl.textContent = fmtMMSS(remaining);
      if (remaining <= 0) document.body.classList.add('time-expired');
    }

    function renderChart() {
      if (!timeChartCanvas || !window.Chart) return;
      if (!avgSeries.length) {
        if (timeChartEmpty) timeChartEmpty.hidden = false;
        return;
      }
      if (timeChartEmpty) timeChartEmpty.hidden = true;
      const latest = avgSeries[avgSeries.length - 1];
      if (timeChartLatest) timeChartLatest.textContent = latest < 100 ? `${latest.toFixed(1)}s` : `${Math.round(latest)}s`;
      const expected = totalSecs > 0 ? totalSecs / questions.length : 60;
      if (timeChartDelta) {
        const pct = Math.abs(((latest - expected) / expected) * 100);
        timeChartDelta.textContent = latest <= expected ? `YOU ARE ${pct.toFixed(1)}% FASTER THAN EXPECTED.` : `YOU ARE ${pct.toFixed(1)}% SLOWER THAN EXPECTED.`;
        timeChartDelta.style.color = latest <= expected ? 'var(--success)' : 'var(--danger)';
      }
      if (chart) chart.destroy();
      const styles = getComputedStyle(document.documentElement);
      const color = styles.getPropertyValue('--secondary').trim() || '#1244ff';
      const labels = avgSeries.map((_, index) => String(index + 1));
      chart = new Chart(timeChartCanvas.getContext('2d'), {
        type: 'line',
        data: { labels, datasets: [{ label: 'AVG TIME (SECONDS)', data: avgSeries, stepped: 'before', borderColor: color, pointRadius: 2 }] },
        options: { responsive: true, maintainAspectRatio: false, animation: false }
      });
    }

    form.addEventListener('change', function (event) {
      const target = event.target;
      if (!target || target.type !== 'radio') return;
      if (!firstAnswered.has(target.name)) {
        firstAnswered.add(target.name);
        avgSeries.push(((Date.now() - startTs) / 1000) / firstAnswered.size);
        renderChart();
      }
      const question = target.closest('section.question');
      if (question) checkQuestion(question);
    });

    document.querySelectorAll('.inline-explain-btn').forEach((btn) => {
      btn.addEventListener('click', function () {
        const question = btn.closest('section.question');
        if (!question) return;
        showExplanationPopup(inlineBodies.get(question.dataset.qname), inlineStems.get(question.dataset.qname));
        btn.classList.remove('attention');
      });
    });
    if (seeExplanationBtn) {
      seeExplanationBtn.addEventListener('click', function () {
        showExplanationPopup(activeExplanationHtml, activeStemHtml);
        seeExplanationBtn.classList.remove('attention');
      });
    }

    renderMath(document.body);
    recomputeTotals();
    updateTimer();
    setInterval(updateTimer, 1000);
    window.addEventListener('themechange', renderChart);
  }

  window.addEventListener('load', initQuiz);
})();
