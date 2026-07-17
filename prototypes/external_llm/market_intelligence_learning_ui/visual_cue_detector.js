/* Market Intelligence — Visual Cue Detector v1.0 */
/* Detecta trechos que precisam de evidencia visual. */
const VisualCueDetector = (function() {
  var VERSION = 'visual-cue-detector-v1.0';
  var VISUAL_TRIGGERS = [
    { pattern: 'olha aqui', classification: 'demonstracao', priority: 5 },
    { pattern: 'olha na tela', classification: 'demonstracao', priority: 5 },
    { pattern: 'vou mostrar', classification: 'demonstracao', priority: 4 },
    { pattern: 'esse grafico', classification: 'grafico', priority: 5 },
    { pattern: 'esse painel', classification: 'ferramenta', priority: 4 },
    { pattern: 'essa ferramenta', classification: 'ferramenta', priority: 5 },
    { pattern: 'essa pagina', classification: 'visual_essencial', priority: 4 },
    { pattern: 'como voces podem ver', classification: 'demonstracao', priority: 3 },
    { pattern: 'esta aparecendo ai', classification: 'demonstracao', priority: 3 },
    { pattern: 'vou abrir aqui', classification: 'demonstracao', priority: 4 },
    { pattern: 'nessa planilha', classification: 'ferramenta', priority: 4 },
    { pattern: 'nesse dashboard', classification: 'ferramenta', priority: 5 },
    { pattern: 'vou abrir', classification: 'demonstracao', priority: 3 },
    { pattern: 'mostrar na tela', classification: 'demonstracao', priority: 4 },
    { pattern: 'olha so', classification: 'demonstracao', priority: 3 },
    { pattern: 'dá uma olhada', classification: 'demonstracao', priority: 3 },
    { pattern: 'veja aqui', classification: 'visual_complementar', priority: 3 },
    { pattern: 'notem que', classification: 'visual_complementar', priority: 2 },
    { pattern: 'repara que', classification: 'visual_complementar', priority: 2 }
  ];
  function detect(segments) {
    if (!segments) return [];
    var cues = [];
    segments.forEach(function(seg) {
      var t = seg.text.toLowerCase();
      VISUAL_TRIGGERS.forEach(function(trigger) {
        if (t.includes(trigger.pattern)) {
          cues.push({
            source_id: seg.source_id || '',
            segment_id: seg.segment_id,
            timestamp: seg.start_time,
            text: seg.text,
            trigger: trigger.pattern,
            classification: trigger.classification,
            priority: trigger.priority,
            status: 'pending',
            suggested_before: Math.max(0, seg.start_time - 3),
            suggested_exact: seg.start_time,
            suggested_after: seg.start_time + 3,
            screenshot_id: null
          });
        }
      });
    });
    return cues;
  }
  function classifyByText(text) {
    var t = text.toLowerCase();
    for (var i = 0; i < VISUAL_TRIGGERS.length; i++) {
      if (t.includes(VISUAL_TRIGGERS[i].pattern)) {
        return VISUAL_TRIGGERS[i];
      }
    }
    return null;
  }
  return { detect: detect, classifyByText: classifyByText, VERSION: VERSION, TRIGGERS: VISUAL_TRIGGERS };
})();
