/* Offer Intelligence — Progress Tracker v1.0 */
/* localStorage persistence for Academia progress. */

const ProgressTracker = (function() {
  'use strict';

  const STORAGE_KEY = 'offer_intel_academia_progress';

  function _load() {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      return data ? JSON.parse(data) : _default();
    } catch(e) {
      return _default();
    }
  }

  function _save(data) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch(e) {}
  }

  function _default() {
    return {
      completedLessons: {},
      inProgress: {},
      answers: {},
      quizAttempts: {},
      speed: 1,
      narrationActive: true,
      startedAt: null,
      lastActivity: null,
      completedModules: [],
      totalLessons: 26,
      currentLessonId: null
    };
  }

  function startLesson(lessonId) {
    const data = _load();
    if (!data.startedAt) data.startedAt = new Date().toISOString();
    data.lastActivity = new Date().toISOString();
    data.currentLessonId = lessonId;

    if (!data.inProgress[lessonId]) {
      data.inProgress[lessonId] = { stepIndex: 0, started: true, startedAt: new Date().toISOString() };
    }
    _save(data);
  }

  function saveProgress(lessonId, stepIndex) {
    const data = _load();
    data.lastActivity = new Date().toISOString();
    data.currentLessonId = lessonId;

    if (!data.inProgress[lessonId]) {
      data.inProgress[lessonId] = { stepIndex: stepIndex, started: true, startedAt: new Date().toISOString() };
    } else {
      data.inProgress[lessonId].stepIndex = stepIndex;
      data.inProgress[lessonId].started = true;
    }
    _save(data);
  }

  function completeLesson(lessonId) {
    const data = _load();
    data.completedLessons[lessonId] = true;
    data.lastActivity = new Date().toISOString();
    if (data.inProgress[lessonId]) {
      delete data.inProgress[lessonId];
    }

    /* Check if module is completed */
    for (const mod of LEARNING_MODULES) {
      const allCompleted = mod.lessons.every(function(l) {
        return data.completedLessons[l.id];
      });
      if (allCompleted && data.completedModules.indexOf(mod.id) === -1) {
        data.completedModules.push(mod.id);
      }
    }
    _save(data);
  }

  function recordAnswer(lessonId, correct, attempts) {
    const data = _load();
    if (!data.answers[lessonId]) {
      data.answers[lessonId] = { correct: 0, total: 0, attempts: 0 };
    }
    data.answers[lessonId].total++;
    if (correct) data.answers[lessonId].correct++;
    data.answers[lessonId].attempts += attempts;
    data.lastActivity = new Date().toISOString();
    _save(data);
  }

  function getProgress() {
    return _load();
  }

  function getLessonProgress(lessonId) {
    const data = _load();
    return data.inProgress[lessonId] || null;
  }

  function isLessonCompleted(lessonId) {
    const data = _load();
    return !!data.completedLessons[lessonId];
  }

  function getCompletedCount() {
    const data = _load();
    return Object.keys(data.completedLessons).length;
  }

  function getModuleProgress(modId) {
    const mod = getModule(modId);
    if (!mod) return { completed: 0, total: 0, percentage: 0 };

    const data = _load();
    const total = mod.lessons.length;
    const completed = mod.lessons.filter(function(l) { return data.completedLessons[l.id]; }).length;
    return {
      completed: completed,
      total: total,
      percentage: total > 0 ? Math.round((completed / total) * 100) : 0
    };
  }

  function getTotalProgress() {
    const data = _load();
    const total = 26;
    const completed = Object.keys(data.completedLessons).length;
    return {
      completed: completed,
      total: total,
      percentage: total > 0 ? Math.round((completed / total) * 100) : 0
    };
  }

  function setSpeed(speed) {
    const data = _load();
    data.speed = speed;
    Narration.setSpeed(speed);
    _save(data);
  }

  function getSpeed() {
    const data = _load();
    return data.speed || 1;
  }

  function setNarrationActive(active) {
    const data = _load();
    data.narrationActive = active;
    _save(data);
  }

  function isNarrationActive() {
    const data = _load();
    return data.narrationActive !== false;
  }

  function getLastLessonId() {
    const data = _load();
    return data.currentLessonId || null;
  }

  function getRecommendedReviewLessons() {
    const data = _load();
    const lessons = getAllLessons();
    const reviewIds = [];

    for (const lesson of lessons) {
      if (!data.completedLessons[lesson.id]) continue;
      const answer = data.answers[lesson.id];
      if (answer && answer.total > 0 && answer.correct / answer.total < 0.5) {
        reviewIds.push(lesson.id);
      }
    }
    return reviewIds;
  }

  function resetProgress() {
    _save(_default());
  }

  function isStarted() {
    const data = _load();
    return !!data.startedAt;
  }

  function getFirstIncompleteLesson() {
    const data = _load();
    for (const mod of LEARNING_MODULES) {
      for (const lesson of mod.lessons) {
        if (!data.completedLessons[lesson.id]) {
          return lesson.id;
        }
      }
    }
    return null;
  }

  return {
    startLesson,
    saveProgress,
    completeLesson,
    recordAnswer,
    getProgress,
    getLessonProgress,
    isLessonCompleted,
    getCompletedCount,
    getModuleProgress,
    getTotalProgress,
    setSpeed,
    getSpeed,
    setNarrationActive,
    isNarrationActive,
    getLastLessonId,
    getRecommendedReviewLessons,
    resetProgress,
    isStarted,
    getFirstIncompleteLesson
  };
})();
