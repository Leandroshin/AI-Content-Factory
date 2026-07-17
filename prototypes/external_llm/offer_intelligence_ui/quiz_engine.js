/* Offer Intelligence — Quiz Engine v1.0 */
/* Multipla escolha, verdadeiro/falso, identificacao visual, feedback. */

const QuizEngine = (function() {
  'use strict';

  let currentLessonId = null;
  let attempts = 0;
  let answeredCorrectly = false;
  let onCompleteCallback = null;

  function startQuiz(lessonId, onComplete) {
    const lesson = getLesson(lessonId);
    if (!lesson || !lesson.quiz) return false;

    currentLessonId = lessonId;
    attempts = 0;
    answeredCorrectly = false;
    onCompleteCallback = onComplete || null;

    renderQuiz(lesson.quiz);
    return true;
  }

  function renderQuiz(quiz) {
    var container = document.getElementById('academia-lesson-content');
    if (!container) return;

    var html = '<div class="quiz-container">';
    html += '<div class="quiz-header"><span class="quiz-badge">Exercicio</span></div>';
    html += '<p class="quiz-question">' + quiz.question + '</p>';
    html += '<div class="quiz-options">';

    quiz.options.forEach(function(opt, i) {
      html += '<button class="quiz-option" data-index="' + i + '">' + opt + '</button>';
    });

    html += '</div>';
    html += '<div id="quiz-feedback" class="quiz-feedback hidden"></div>';
    html += '<div class="quiz-actions hidden" id="quiz-actions">';
    html += '<button id="quiz-continue" class="btn quiz-continue-btn">Continuar</button>';
    html += '</div>';
    html += '</div>';

    container.innerHTML = html;

    /* Bind events */
    document.querySelectorAll('.quiz-option').forEach(function(btn) {
      btn.addEventListener('click', function() {
        handleAnswer(parseInt(this.dataset.index), quiz);
      });
    });
  }

  function handleAnswer(selectedIndex, quiz) {
    if (answeredCorrectly) return;

    var options = document.querySelectorAll('.quiz-option');
    var feedback = document.getElementById('quiz-feedback');
    var actions = document.getElementById('quiz-actions');

    attempts++;

    options.forEach(function(opt, i) {
      opt.disabled = true;
      if (i === quiz.correct) {
        opt.classList.add('quiz-correct');
      } else if (i === selectedIndex) {
        opt.classList.add('quiz-incorrect');
      }
    });

    if (selectedIndex === quiz.correct) {
      answeredCorrectly = true;
      feedback.className = 'quiz-feedback quiz-feedback-correct';
      feedback.innerHTML = '<span class="quiz-feedback-icon">✓</span> ' + quiz.explanation;
      feedback.classList.remove('hidden');
      ProgressTracker.recordAnswer(currentLessonId, true, attempts);

      if (actions) {
        actions.classList.remove('hidden');
        var continueBtn = document.getElementById('quiz-continue');
        if (continueBtn) {
          continueBtn.onclick = function() {
            if (onCompleteCallback) onCompleteCallback(currentLessonId, true);
          };
        }
      }
    } else {
      feedback.className = 'quiz-feedback quiz-feedback-incorrect';
      feedback.innerHTML = '<span class="quiz-feedback-icon">✗</span> ' + quiz.explanation;
      feedback.classList.remove('hidden');
      ProgressTracker.recordAnswer(currentLessonId, false, attempts);

      /* Allow second attempt */
      if (attempts < 2) {
        feedback.innerHTML += '<p class="quiz-retry-hint">Tente novamente.</p>';
        setTimeout(function() {
          options.forEach(function(opt) {
            opt.disabled = false;
            opt.classList.remove('quiz-correct', 'quiz-incorrect');
          });
          feedback.className = 'quiz-feedback hidden';
        }, 2000);
      } else {
        /* Show correct answer after 2nd failure */
        if (actions) {
          actions.classList.remove('hidden');
          var continueBtn = document.getElementById('quiz-continue');
          if (continueBtn) {
            continueBtn.onclick = function() {
              if (onCompleteCallback) onCompleteCallback(currentLessonId, false);
            };
          }
        }
      }
    }
  }

  function renderExercise(exercise) {
    if (!exercise) return '';
    if (exercise.type === 'identify') {
      return '<div class="quiz-exercise"><p class="quiz-exercise-instruction">' + exercise.instruction + '</p>' +
        (exercise.hint ? '<p class="quiz-exercise-hint">Dica: ' + exercise.hint + '</p>' : '') + '</div>';
    }
    return '';
  }

  function isAnsweredCorrectly() {
    return answeredCorrectly;
  }

  function getAttempts() {
    return attempts;
  }

  function reset() {
    currentLessonId = null;
    attempts = 0;
    answeredCorrectly = false;
    onCompleteCallback = null;
  }

  return {
    startQuiz,
    renderQuiz,
    renderExercise,
    isAnsweredCorrectly,
    getAttempts,
    reset
  };
})();
