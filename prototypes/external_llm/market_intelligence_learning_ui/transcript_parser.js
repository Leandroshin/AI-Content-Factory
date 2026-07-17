/* Market Intelligence — Transcript Parser v1.0 */
/* Parser deterministico de transcricao. Sem modelo de linguagem externo. */
const TranscriptParser = (function() {
  var VERSION = 'transcript-parser-v1.0';
  var TIMESTAMP_RE = /(?:\[)?(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\.(\d+))?(?:\])?/g;
  var SPEAKER_RE = /^([A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇa-záéíóúâêîôûãõç]+(?:\s[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇa-záéíóúâêîôûãõç]+)?:)\s*/;
  function parse(rawText) {
    if (!rawText) return { segments: [], speakers: [], chapters: [], version: VERSION };
    var lines = rawText.split('\n');
    var segments = [];
    var speakers = {};
    var chapters = [];
    var currentChapter = '';
    var currentSpeaker = '';
    var currentText = '';
    var currentStart = 0;
    function flushSegment() {
      if (currentText.trim()) {
        segments.push({
          segment_id: 'seg-' + segments.length,
          start_time: currentStart,
          end_time: null,
          speaker: currentSpeaker,
          text: currentText.trim(),
          chapter: currentChapter,
          tags: [],
          visual_cue: false,
          tool_mentions: [],
          claims: [],
          notes: ''
        });
      }
    }
    lines.forEach(function(line) {
      line = line.trim();
      if (!line) return;
      /* Check for chapter markers */
      if (line.match(/^#{1,3}\s/) || line.match(/^\[(.*?)\]$/) || line.match(/^--+$/)) {
        flushSegment();
        currentChapter = line.replace(/^#{1,3}\s/, '').replace(/^\[(.*)\]$/, '$1').replace(/^--+$/, '').trim();
        if (currentChapter) chapters.push(currentChapter);
        return;
      }
      /* Check for timestamp */
      var tsMatch = line.match(TIMESTAMP_RE);
      if (tsMatch) {
        flushSegment();
        var m = line.match(TIMESTAMP_RE);
        if (m) {
          var parts = m[0].replace(/[\[\]]/g, '').split(':');
          var sec = parseInt(parts[0]) * 60 + parseInt(parts[1]);
          currentStart = sec;
          line = line.replace(TIMESTAMP_RE, '').trim();
        }
      }
      /* Check for speaker */
      var spMatch = line.match(SPEAKER_RE);
      if (spMatch) {
        flushSegment();
        currentSpeaker = spMatch[1].replace(':', '').trim();
        speakers[currentSpeaker] = true;
        line = line.replace(SPEAKER_RE, '').trim();
      }
      if (line) currentText += (currentText ? ' ' : '') + line;
    });
    flushSegment();
    /* Post-process: detect visual cues, tool mentions, claims */
    segments.forEach(function(seg) {
      var t = seg.text.toLowerCase();
      var visualWords = ['olha aqui', 'olha na tela', 'vou mostrar', 'esse grafico', 'esse painel', 'essa ferramenta', 'essa pagina', 'como voces podem ver', 'esta aparecendo ai', 'vou abrir aqui', 'nessa planilha', 'nesse dashboard', 'vou abrir', 'mostrar na tela', 'olha so'];
      visualWords.forEach(function(w) { if (t.includes(w)) seg.visual_cue = true; });
      var toolWords = ['usamos', 'ferramenta', 'plataforma', 'software', 'crm', 'checkout', 'dashboard', 'app', 'analytics', 'builder'];
      toolWords.forEach(function(w) { if (t.includes(w)) seg.tool_mentions.push(w); });
      var claimWords = ['r$', 'us$', 'faturamento', 'lucro', 'vendas', 'milhao', 'milhoes', 'roi', 'retorno', 'margem', 'comissao', 'sete digitos', 'oito digitos'];
      claimWords.forEach(function(w) { if (t.includes(w)) seg.claims.push(w); });
    });
    return { segments: segments, speakers: Object.keys(speakers), chapters: chapters, version: VERSION };
  }
  function formatTime(seconds) {
    var m = Math.floor(seconds / 60);
    var s = Math.floor(seconds % 60);
    return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
  }
  return { parse: parse, formatTime: formatTime, VERSION: VERSION };
})();
