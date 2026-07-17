/* Market Intelligence — Narration v2.0 — INTERACTION-UNDERSTAND */
/* speechSynthesis local. Nenhuma chamada externa. Velocidade 0.75x, 1x, 1.25x. */
const Narration = (function() {
  let voice = null, speed = 1, isPlaying = false, isPaused = false, utterance = null;
  let pendingCallback = null;
  var SPEEDS = [0.75, 1, 1.25];
  function init() {
    if (!window.speechSynthesis) return false;
    const v = window.speechSynthesis.getVoices();
    voice = v.find(x => x.lang.startsWith('pt') && x.lang.includes('BR')) || v.find(x => x.lang.startsWith('pt')) || null;
    window.speechSynthesis.onvoiceschanged = function() {
      const a = window.speechSynthesis.getVoices();
      voice = a.find(x => x.lang.startsWith('pt') && x.lang.includes('BR')) || a.find(x => x.lang.startsWith('pt')) || null;
    };
    return !!window.speechSynthesis;
  }
  function speak(text, cb) {
    if (!window.speechSynthesis) { if (cb) cb(); return; }
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = 'pt-BR'; u.rate = speed;
    if (voice) u.voice = voice;
    utterance = u; isPlaying = true; isPaused = false; pendingCallback = cb || null;
    u.onend = function() { isPlaying = false; utterance = null; var c = pendingCallback; pendingCallback = null; if (c) c(); };
    u.onerror = function() { isPlaying = false; utterance = null; var c = pendingCallback; pendingCallback = null; if (c) c(); };
    window.speechSynthesis.speak(u);
  }
  function pause() { if (window.speechSynthesis && isPlaying) { window.speechSynthesis.pause(); isPaused = true; } }
  function resume() { if (window.speechSynthesis && isPaused) { window.speechSynthesis.resume(); isPaused = false; } }
  function stop() { if (window.speechSynthesis) { window.speechSynthesis.cancel(); } isPlaying = false; isPaused = false; utterance = null; pendingCallback = null; }
  function setSpeed(s) { speed = Math.max(0.5, Math.min(2, s)); }
  function getSpeed() { return speed; }
  function isSupported() { return !!window.speechSynthesis; }
  function hasVoice() { return voice !== null; }
  function getSpeeds() { return SPEEDS; }
  return {
    init: init, speak: speak, pause: pause, resume: resume, stop: stop,
    setSpeed: setSpeed, getSpeed: getSpeed,
    isSupported: isSupported, hasVoice: hasVoice, getSpeeds: getSpeeds,
    get isPlaying() { return isPlaying; }
  };
})();
