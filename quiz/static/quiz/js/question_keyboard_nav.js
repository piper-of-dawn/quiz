(function () {
  function isTypingTarget(el) {
    if (!el) return false;
    const tag = String(el.tagName || '').toLowerCase();
    if (tag === 'input') {
      const type = String(el.type || '').toLowerCase();
      return type !== 'radio' && type !== 'checkbox';
    }
    return tag === 'textarea' || tag === 'select' || el.isContentEditable;
  }

  function isModalOpen() {
    return !!document.querySelector('.katas-modal.show');
  }

  function optionNumberFromKey(event) {
    const code = String(event.code || '');
    if (code === 'KeyA' || code === 'KeyQ') return 1;
    if (code === 'KeyW') return 2;
    if (code === 'KeyC' || code === 'KeyE') return 3;
    return null;
  }

  function initQuestionKeyboardNav() {
    const questions = Array.from(document.querySelectorAll('section.question'));
    if (!questions.length) return;
    let selectedIndex = 0;

    function setSelectedQuestion(index, shouldScroll) {
      selectedIndex = Math.max(0, Math.min(questions.length - 1, index));
      questions.forEach((question, i) => question.classList.toggle('is-selected', i === selectedIndex));
      if (shouldScroll) questions[selectedIndex].scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function selectOption(number) {
      const question = questions[selectedIndex];
      if (!question) return;
      const input = question.querySelectorAll('input[type="radio"]')[number - 1];
      if (input) input.click();
    }

    questions.forEach((question, index) => {
      question.addEventListener('click', () => setSelectedQuestion(index, false));
      question.addEventListener('focusin', () => setSelectedQuestion(index, false));
    });

    window.addEventListener('keydown', function (event) {
      if (event.defaultPrevented || isTypingTarget(event.target) || isModalOpen()) return;
      if (event.key === 'ArrowDown' || event.key === 'ArrowRight') {
        event.preventDefault();
        setSelectedQuestion(selectedIndex + 1, true);
        return;
      }
      if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {
        event.preventDefault();
        setSelectedQuestion(selectedIndex - 1, true);
        return;
      }
      const number = optionNumberFromKey(event);
      if (number) {
        event.preventDefault();
        selectOption(number);
      }
    }, { capture: true });

    setSelectedQuestion(0, false);
  }

  window.initQuestionKeyboardNav = initQuestionKeyboardNav;
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initQuestionKeyboardNav, { once: true });
  } else {
    initQuestionKeyboardNav();
  }
})();
