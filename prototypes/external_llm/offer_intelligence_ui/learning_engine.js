/* Offer Intelligence — Learning Engine v1.0 */
/* Controla fluxo de aulas: iniciar, pausar, continuar, navegar, destacar. */

const LearningEngine = (function() {
  'use strict';

  let currentLessonId = null;
  let currentStepIndex = 0;
  let isActive = false;
  let isPaused = false;
  let lessonStarted = false;
  let onFinishCallback = null;
  let onStepChangeCallback = null;

  /* Spotlight overlay for visual diagnosis */
  let spotlightOverlay = null;
  let spotlightLabel = null;

  function startLesson(lessonId, onFinish) {
    const lesson = getLesson(lessonId);
    if (!lesson) return false;

    currentLessonId = lessonId;
    currentStepIndex = 0;
    isActive = true;
    isPaused = false;
    lessonStarted = true;
    onFinishCallback = onFinish || null;

    ProgressTracker.startLesson(lessonId);

    _executeStep();
    return true;
  }

  function resumeLesson(lessonId) {
    const data = ProgressTracker.getLessonProgress(lessonId);
    if (!data || !data.started) return false;

    currentLessonId = lessonId;
    currentStepIndex = data.stepIndex || 0;
    isActive = true;
    isPaused = false;
    lessonStarted = true;

    const lesson = getLesson(lessonId);
    if (!lesson) return false;

    _executeStep();
    return true;
  }

  function getCurrentLesson() {
    if (!currentLessonId) return null;
    return getLesson(currentLessonId);
  }

  function getCurrentStepIndex() {
    return currentStepIndex;
  }

  function getCurrentStep() {
    const lesson = getCurrentLesson();
    if (!lesson || !lesson.steps || !lesson.steps[currentStepIndex]) return null;
    return lesson.steps[currentStepIndex];
  }

  function isLessonActive() {
    return isActive;
  }

  function nextStep() {
    if (!isActive || isPaused) return;
    const lesson = getCurrentLesson();
    if (!lesson || !lesson.steps) return;

    if (currentStepIndex < lesson.steps.length - 1) {
      currentStepIndex++;
      _executeStep();
    } else {
      _finishLesson();
    }
  }

  function prevStep() {
    if (!isActive || isPaused) return;
    if (currentStepIndex > 0) {
      currentStepIndex--;
      _executeStep();
    }
  }

  function pauseLesson() {
    isPaused = true;
    Narration.pause();
  }

  function resumeLessonAction() {
    isPaused = false;
    Narration.resume();
  }

  function stopLesson() {
    isActive = false;
    isPaused = false;
    lessonStarted = false;
    Narration.stop();
    _clearSpotlight();
    currentLessonId = null;
    currentStepIndex = 0;
  }

  function finishLesson() {
    _finishLesson();
  }

  function setOnStepChange(fn) {
    onStepChangeCallback = fn;
  }

  function _executeStep() {
    if (!isActive) return;

    const lesson = getCurrentLesson();
    if (!lesson || !lesson.steps) return;

    _clearSpotlight();

    const step = lesson.steps[currentStepIndex];
    if (!step) return;

    ProgressTracker.saveProgress(currentLessonId, currentStepIndex);

    /* Navigate to correct view if lesson has highlight/view */
    if (lesson.highlight && lesson.highlight.view && typeof navigate === 'function') {
      navigate(lesson.highlight.view);
    }

    /* Highlight element if specified */
    if (step.highlight) {
      setTimeout(function() {
        _highlightElement(step.highlight, step.label || '');
      }, 300);
    }

    /* Create spotlight with circle and label if label is provided */
    if (step.label && step.highlight) {
      setTimeout(function() {
        _createSpotlight(step.highlight, step.label);
      }, 400);
    }

    /* Speak narration */
    const text = step.text || '';
    if (text) {
      Narration.stop();
      Narration.speak(text, function() {
        /* Narration finished - do nothing, wait for user action */
      });
    }

    /* Notify step change */
    if (onStepChangeCallback) {
      onStepChangeCallback(currentLessonId, currentStepIndex);
    }
  }

  function _highlightElement(selector, label) {
    /* Remove previous highlights */
    document.querySelectorAll('.learning-highlight').forEach(function(el) {
      el.classList.remove('learning-highlight');
    });
    document.querySelectorAll('.learning-highlight-label').forEach(function(el) {
      el.remove();
    });

    if (!selector) return;
    var el = document.querySelector(selector);
    if (!el) return;

    el.classList.add('learning-highlight');
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });

    /* Add label */
    if (label) {
      var labelEl = document.createElement('div');
      labelEl.className = 'learning-highlight-label';
      labelEl.textContent = label;
      el.style.position = 'relative';
      el.appendChild(labelEl);
    }
  }

  function _createSpotlight(selector, label) {
    _clearSpotlight();

    var el = document.querySelector(selector);
    if (!el) return;

    var rect = el.getBoundingClientRect();
    if (!rect || rect.width === 0) return;

    /* SVG overlay for circle/arrow */
    spotlightOverlay = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    spotlightOverlay.setAttribute('class', 'learning-spotlight-svg');
    spotlightOverlay.setAttribute('style', 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9998;');
    document.body.appendChild(spotlightOverlay);

    /* Circle around element */
    var cx = rect.left + rect.width / 2;
    var cy = rect.top + rect.height / 2;
    var r = Math.max(rect.width, rect.height) / 2 + 12;

    var circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', String(cx));
    circle.setAttribute('cy', String(cy));
    circle.setAttribute('r', String(r));
    circle.setAttribute('fill', 'none');
    circle.setAttribute('stroke', 'var(--accent-blue)');
    circle.setAttribute('stroke-width', '2.5');
    circle.setAttribute('stroke-dasharray', '6,3');
    circle.setAttribute('class', 'learning-spotlight-circle');
    spotlightOverlay.appendChild(circle);

    /* Arrow pointing to element */
    var arrowY = Math.max(10, cy - r - 30);
    var line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', String(cx));
    line.setAttribute('y1', String(arrowY));
    line.setAttribute('x2', String(cx));
    line.setAttribute('y2', String(arrowY + 20));
    line.setAttribute('stroke', 'var(--accent-blue)');
    line.setAttribute('stroke-width', '2');
    line.setAttribute('marker-end', 'url(#arrowhead)');
    spotlightOverlay.appendChild(line);

    /* Arrowhead marker */
    var defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    var marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
    marker.setAttribute('id', 'arrowhead');
    marker.setAttribute('markerWidth', '10');
    marker.setAttribute('markerHeight', '7');
    marker.setAttribute('refX', '10');
    marker.setAttribute('refY', '3.5');
    marker.setAttribute('orient', 'auto');
    var polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    polygon.setAttribute('points', '0 0, 10 3.5, 0 7');
    polygon.setAttribute('fill', 'var(--accent-blue)');
    marker.appendChild(polygon);
    defs.appendChild(marker);
    spotlightOverlay.appendChild(defs);

    /* Label above arrow */
    if (label) {
      spotlightLabel = document.createElement('div');
      spotlightLabel.className = 'learning-spotlight-label';
      spotlightLabel.textContent = label;
      spotlightLabel.style.cssText =
        'position:fixed;left:' + (cx - 40) + 'px;top:' + (arrowY - 22) + 'px;' +
        'background:var(--accent-blue);color:#fff;padding:3px 10px;border-radius:4px;' +
        'font-size:12px;font-weight:600;z-index:9999;pointer-events:none;' +
        'white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,0.3);';
      document.body.appendChild(spotlightLabel);
    }
  }

  function _clearSpotlight() {
    if (spotlightOverlay) {
      spotlightOverlay.remove();
      spotlightOverlay = null;
    }
    if (spotlightLabel) {
      spotlightLabel.remove();
      spotlightLabel = null;
    }
    document.querySelectorAll('.learning-highlight').forEach(function(el) {
      el.classList.remove('learning-highlight');
    });
    document.querySelectorAll('.learning-highlight-label').forEach(function(el) {
      el.remove();
    });
  }

  function _finishLesson() {
    if (!currentLessonId) return;
    ProgressTracker.completeLesson(currentLessonId);
    Narration.stop();
    _clearSpotlight();
    isActive = false;
    lessonStarted = false;

    if (onFinishCallback) onFinishCallback(currentLessonId);
  }

  function getActiveStepText() {
    const step = getCurrentStep();
    return step ? step.text : '';
  }

  return {
    startLesson,
    resumeLesson,
    getCurrentLesson,
    getCurrentStepIndex,
    getCurrentStep,
    isLessonActive,
    nextStep,
    prevStep,
    pauseLesson,
    resumeLessonAction,
    stopLesson,
    finishLesson,
    setOnStepChange,
    getActiveStepText,
    _highlightElement,
    _createSpotlight,
    _clearSpotlight
  };
})();
