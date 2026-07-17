/* Offer Intelligence — Narration v1.0 */
/* speechSynthesis local. Nenhuma chamada externa. */

const Narration = (function() {
  'use strict';

  let isPlaying = false;
  let isPaused = false;
  let currentUtterance = null;
  let queue = [];
  let queueIndex = 0;
  let speed = 1;
  let voice = null;
  let onStepCallback = null;

  function init() {
    if (!window.speechSynthesis) return false;
    const voices = window.speechSynthesis.getVoices();
    voice = voices.find(v => v.lang.startsWith('pt') && v.lang.includes('BR')) ||
            voices.find(v => v.lang.startsWith('pt')) || null;
    if (voice) return true;
    /* Try again when voices change */
    window.speechSynthesis.onvoiceschanged = function() {
      const all = window.speechSynthesis.getVoices();
      voice = all.find(v => v.lang.startsWith('pt') && v.lang.includes('BR')) ||
              all.find(v => v.lang.startsWith('pt')) || null;
    };
    return !!window.speechSynthesis;
  }

  function isSupported() {
    return !!window.speechSynthesis;
  }

  function hasPortugueseVoice() {
    return voice !== null;
  }

  function setSpeed(s) {
    speed = Math.max(0.5, Math.min(2, s));
  }

  function getSpeed() { return speed; }

  function setOnStep(fn) { onStepCallback = fn; }

  function speak(text, onEnd) {
    if (!window.speechSynthesis) {
      if (onEnd) onEnd();
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'pt-BR';
    utterance.rate = speed;
    if (voice) utterance.voice = voice;
    currentUtterance = utterance;
    isPlaying = true;
    isPaused = false;
    utterance.onend = function() {
      isPlaying = false;
      currentUtterance = null;
      if (onEnd) onEnd();
    };
    utterance.onerror = function() {
      isPlaying = false;
      currentUtterance = null;
      if (onEnd) onEnd();
    };
    window.speechSynthesis.speak(utterance);
  }

  function playQueue(steps, startIndex, onStep) {
    if (!window.speechSynthesis || !steps.length) return;
    queue = steps;
    queueIndex = Math.max(0, Math.min(startIndex, steps.length - 1));
    onStepCallback = onStep || null;
    _speakCurrent();
  }

  function _speakCurrent() {
    if (queueIndex >= queue.length) {
      isPlaying = false;
      return;
    }
    if (onStepCallback) onStepCallback(queueIndex);
    speak(queue[queueIndex].text || queue[queueIndex], function() {
      queueIndex++;
      _speakCurrent();
    });
  }

  function pause() {
    if (window.speechSynthesis && isPlaying) {
      window.speechSynthesis.pause();
      isPaused = true;
    }
  }

  function resume() {
    if (window.speechSynthesis && isPaused) {
      window.speechSynthesis.resume();
      isPaused = false;
    }
  }

  function stop() {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    isPlaying = false;
    isPaused = false;
    currentUtterance = null;
  }

  function skipForward() {
    stop();
    queueIndex = Math.min(queueIndex + 1, queue.length - 1);
    _speakCurrent();
  }

  function skipBackward() {
    stop();
    queueIndex = Math.max(0, queueIndex - 1);
    _speakCurrent();
  }

  function getStatus() {
    return { isPlaying, isPaused, current: queueIndex, total: queue.length, speed, hasVoice: !!voice };
  }

  return {
    init,
    isSupported,
    hasPortugueseVoice,
    setSpeed,
    getSpeed,
    speak,
    playQueue,
    pause,
    resume,
    stop,
    skipForward,
    skipBackward,
    setOnStep,
    getStatus
  };
})();
