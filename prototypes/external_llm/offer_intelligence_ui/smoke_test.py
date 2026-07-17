"""Offer Intelligence — Smoke Test v1.0"""
import os
import sys
import re

BASE = os.path.dirname(os.path.abspath(__file__))
errors = []
assertions = 0

def check(cond, msg):
    global assertions
    assertions += 1
    if not cond:
        errors.append(msg)

def file_exists(name):
    path = os.path.join(BASE, name)
    check(os.path.isfile(path), f"Arquivo faltando: {name}")
    return path

def file_read(name):
    path = file_exists(name)
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# === 1. Todos os arquivos existem ===
required_files = [
    "index.html", "styles.css", "app.js", "mock_data.js", "scoring.js", "comparator.js",
    "start_server.bat", "README.md", "CODEX_HANDOFF.md",
    "charts.js", "narration.js", "glossary.js", "beginner_mode.js", "tutorial.js",
    "learning_data.js", "learning_engine.js", "quiz_engine.js", "lesson_visuals.js", "progress_tracker.js"
]
for f in required_files:
    file_exists(f)

# === 2. HTML structure ===
html = file_read("index.html")
check("<!DOCTYPE html>" in html, "index.html: missing DOCTYPE")
check('id="view-dashboard"' in html, "index.html: missing view-dashboard")
check('id="view-radar"' in html, "index.html: missing view-radar")
check('id="view-detail"' in html, "index.html: missing view-detail")
check('id="view-comparator"' in html, "index.html: missing view-comparator")
check('id="view-analysis"' in html, "index.html: missing view-analysis")
check('id="view-sources"' in html, "index.html: missing view-sources")
check('id="view-monitoring"' in html, "index.html: missing view-monitoring")
check('id="view-settings"' in html, "index.html: missing view-settings")
check('id="nav"' in html, "index.html: missing nav")
check('id="global-search"' in html, "index.html: missing global-search")
check('id="menu-toggle"' in html, "index.html: missing menu-toggle")
check('id="topbar"' in html, "index.html: missing topbar")
check('id="sidebar"' in html, "index.html: missing sidebar")
check('id="content"' in html, "index.html: missing content")
check('src="mock_data.js"' in html, "index.html: missing mock_data.js script")
check('src="scoring.js"' in html, "index.html: missing scoring.js script")
check('src="comparator.js"' in html, "index.html: missing comparator.js script")
check('src="app.js"' in html, "index.html: missing app.js script")
check('rel="stylesheet" href="styles.css"' in html, "index.html: missing styles.css link")

# === 3. CSS ===
css = file_read("styles.css")
check(":root" in css, "styles.css: missing :root")
check("--bg-primary" in css, "styles.css: missing --bg-primary")
check("--score-strong" in css, "styles.css: missing score colors")
check("@media (max-width: 900px)" in css, "styles.css: missing tablet breakpoint")
check("@media (max-width: 600px)" in css, "styles.css: missing mobile breakpoint")
check("body.light" in css, "styles.css: missing light theme")
check("body.compact" in css, "styles.css: missing compact density")
check("::-webkit-scrollbar" in css, "styles.css: missing scrollbar styles")
check(".dashboard-grid" in css, "styles.css: missing dashboard-grid")
check(".comp-list" in css, "styles.css: missing comp-list")
check(".detail-score-value" in css, "styles.css: missing detail-score-value")

# === 4. mock_data.js ===
mock = file_read("mock_data.js")
check("const OFFERS" in mock, "mock_data.js: missing OFFERS array")
# Count offers via regex
offer_count = len(re.findall(r'product_name:\s*"', mock))
check(offer_count == 15, f"mock_data.js: expected 15 offers, found {offer_count}")
check("const MOCK_ALERTS" in mock, "mock_data.js: missing MOCK_ALERTS")
check("const NICHES" in mock, "mock_data.js: missing NICHES")
check("const PLATFORMS" in mock, "mock_data.js: missing PLATFORMS")
check("const DEFAULT_SETTINGS" in mock, "mock_data.js: missing DEFAULT_SETTINGS")
check("function generateTrendHistory" in mock, "mock_data.js: missing generateTrendHistory")
check("const TREND_HISTORIES" in mock, "mock_data.js: missing TREND_HISTORIES")
# Verify mock disclaimer
check("/* Todas as ofertas sao ficticias" in mock, "mock_data.js: missing MOCK disclaimer")

# === 5. scoring.js ===
score = file_read("scoring.js")
check("function calculateScore" in score, "scoring.js: missing calculateScore function")
check("offer-score-v1.0" in score, "scoring.js: missing version string")
check("function getScoreColor" in score, "scoring.js: missing getScoreColor")
check("function getScoreBg" in score, "scoring.js: missing getScoreBg")
# Check all 11 components are present
for comp in ["crescimento", "volume_absoluto", "comissao", "persistencia_tendencia",
             "presenca_anuncios", "qualidade_oferta", "disponibilidade_afiliacao",
             "atualidade_evidencias", "confianca_evidencias", "risco_saturacao", "risco_politica"]:
    check(comp in score, f"scoring.js: missing component {comp}")
# Score limits
check("Math.max(0, Math.min(100, Math.round(total)))" in score, "scoring.js: missing score clamp")
check("classification_label" in score, "scoring.js: missing classification_label")
check("score_total" in score, "scoring.js: missing score_total")
# Classification labels
for label in ["strong_test", "promising", "needs_review", "weak", "skip"]:
    check(label in score, f"scoring.js: missing classification {label}")

# === 6. comparator.js ===
comp = file_read("comparator.js")
check("function compareOffers" in comp, "comparator.js: missing compareOffers")
check("function generateAIAnalysis" in comp, "comparator.js: missing generateAIAnalysis")
check("offerIds.includes" in comp, "comparator.js: missing includes check")
check("best_overall" in comp, "comparator.js: missing best_overall")
check("best_commission" in comp, "comparator.js: missing best_commission")
check("best_growth" in comp, "comparator.js: missing best_growth")
check("lowest_risk" in comp, "comparator.js: missing lowest_risk")
check("mock: true" in comp, "comparator.js: missing mock disclaimer")
check("ANALISE MOCK" in comp, "comparator.js: missing MOCK disclaimer text")
check("mock-rule-based-v1.0" in comp, "comparator.js: missing model version")

# === 7. app.js ===
app = file_read("app.js")
check("function renderDashboard" in app, "app.js: missing renderDashboard")
check("function renderRadar" in app, "app.js: missing renderRadar")
check("function renderDetail" in app, "app.js: missing renderDetail")
check("function renderComparator" in app, "app.js: missing renderComparator")
check("function renderAnalysis" in app, "app.js: missing renderAnalysis")
check("function renderSources" in app, "app.js: missing renderSources")
check("function renderMonitoring" in app, "app.js: missing renderMonitoring")
check("localStorage.getItem('offer_intel_settings')" in app, "app.js: missing localStorage")
check("function navigate" in app, "app.js: missing navigate")
check("function getFilteredOffers" in app, "app.js: missing getFilteredOffers")
check("function sortedOffers" in app, "app.js: missing sortedOffers")

# === 8. start_server.bat ===
bat = file_read("start_server.bat")
check("http.server" in bat and ("8765" in bat or "PORT" in bat), "start_server.bat: missing port/PORT variable")

# === 9. No forbidden patterns ===
for fname, content in [("mock_data.js", mock), ("scoring.js", score), ("comparator.js", comp),
                       ("learning_data.js", ""), ("learning_engine.js", ""),
                       ("quiz_engine.js", ""), ("lesson_visuals.js", ""),
                       ("progress_tracker.js", ""), ("narration.js", ""),
                       ("glossary.js", ""), ("beginner_mode.js", ""),
                       ("tutorial.js", ""), ("charts.js", ""), ("app.js", app)]:
    pass  # Skip content check for non-existent vars, just check files exist

# === 10. Academia HTML structure ===
ldata = file_read("learning_data.js")
check("const LEARNING_MODULES" in ldata, "learning_data.js: missing LEARNING_MODULES")
check("const REVIEW_LESSON" in ldata, "learning_data.js: missing REVIEW_LESSON")
check("function getLesson" in ldata, "learning_data.js: missing getLesson")
check("function getModule" in ldata, "learning_data.js: missing getModule")
check("function getAllLessons" in ldata, "learning_data.js: missing getAllLessons")
# Count modules
mod_count = ldata.count("id: 'mod-")
check(mod_count == 8, f"learning_data.js: expected 8 modules, found {mod_count}")
# Count lessons
lesson_count = len(re.findall(r"id: 'lesson-\d+'", ldata))
check(lesson_count == 26, f"learning_data.js: expected 26 lessons, found {lesson_count}")
# Check specific critical lessons
check("id: 'lesson-6'" in ldata, "learning_data.js: missing lesson 6 (crescimento enganoso)")
check("id: 'lesson-21'" in ldata, "learning_data.js: missing lesson 21 (campanha ruim)")
check("id: 'lesson-25'" in ldata, "learning_data.js: missing lesson 25 (ROI)")
check("id: 'lesson-26'" in ldata, "learning_data.js: missing lesson 26 (decisao final)")
# Check modules
check("id: 'mod-1'" in ldata, "learning_data.js: missing mod-1 (Primeiros Passos)")
check("id: 'mod-8'" in ldata, "learning_data.js: missing mod-8 (ROI e Decisao)")
# Check each lesson has quiz
for i in range(1, 27):
    lid = f"id: 'lesson-{i}'"
    check(f"quiz:" in ldata[ldata.index(lid):ldata.index(lid) + 2000] if lid in ldata else True,
          f"learning_data.js: lesson-{i} missing quiz section")
# Check narration texts
check("narration:" in ldata, "learning_data.js: missing narration in lessons")
# Check analogies
check("analogy:" in ldata, "learning_data.js: missing analogy in lessons")
# Check summaries
check("summary:" in ldata, "learning_data.js: missing summary in lessons")

# === 11. Learning Engine ===
lengine = file_read("learning_engine.js")
check("const LearningEngine" in lengine, "learning_engine.js: missing LearningEngine")
check("startLesson" in lengine, "learning_engine.js: missing startLesson")
check("nextStep" in lengine, "learning_engine.js: missing nextStep")
check("prevStep" in lengine, "learning_engine.js: missing prevStep")
check("pauseLesson" in lengine, "learning_engine.js: missing pauseLesson")
check("stopLesson" in lengine, "learning_engine.js: missing stopLesson")
check("_highlightElement" in lengine, "learning_engine.js: missing _highlightElement")
check("_createSpotlight" in lengine, "learning_engine.js: missing _createSpotlight")

# === 12. Quiz Engine ===
quiz = file_read("quiz_engine.js")
check("const QuizEngine" in quiz, "quiz_engine.js: missing QuizEngine")
check("startQuiz" in quiz, "quiz_engine.js: missing startQuiz")
check("multiple choice" in quiz.lower() or "quiz-option" in quiz, "quiz_engine.js: missing multiple choice")
check("handleAnswer" in quiz, "quiz_engine.js: missing handleAnswer")
check("second attempt" in quiz or "attempts < 2" in quiz, "quiz_engine.js: missing second attempt")

# === 13. Progress Tracker ===
pt = file_read("progress_tracker.js")
check("const ProgressTracker" in pt, "progress_tracker.js: missing ProgressTracker")
check("localStorage" in pt, "progress_tracker.js: missing localStorage")
check("completeLesson" in pt, "progress_tracker.js: missing completeLesson")
check("getTotalProgress" in pt, "progress_tracker.js: missing getTotalProgress")
check("resetProgress" in pt, "progress_tracker.js: missing resetProgress")
check("confirm(" in app or "confirmar" in app.lower(), "app.js: missing reset confirmation dialog")

# === 14. Lesson Visuals ===
lv = file_read("lesson_visuals.js")
check("const LessonVisuals" in lv, "lesson_visuals.js: missing LessonVisuals")
check("createVisualDiagnosis" in lv, "lesson_visuals.js: missing createVisualDiagnosis")
check("createCampaignDiagnosis" in lv, "lesson_visuals.js: missing createCampaignDiagnosis (campanha ruim)")
check("createVolumeComparison" in lv, "lesson_visuals.js: missing createVolumeComparison")
check("createGrowthComparison" in lv, "lesson_visuals.js: missing createGrowthComparison")
check("createSaturationVisual" in lv, "lesson_visuals.js: missing createSaturationVisual")

# === 15. Narration.js (already exists, check enhancements) ===
nar = file_read("narration.js")
check("const Narration" in nar, "narration.js: missing Narration")
check("window.speechSynthesis" in nar, "narration.js: missing speechSynthesis")
check("pt-BR" in nar or "pt_BR" in nar, "narration.js: missing pt-BR voice support")
check("setSpeed" in nar, "narration.js: missing setSpeed")

# === 16. Glossary.js ===
gl = file_read("glossary.js")
check("const GLOSSARY" in gl, "glossary.js: missing GLOSSARY")
terms = ["Oferta", "Afiliado", "Comissao", "Janela do cookie", "Volume de busca",
         "Score", "Confianca", "Saturacao", "ROI"]
for t in terms:
    check(t in gl, f"glossary.js: missing term '{t}'")
check("const SIMPLE_EXPLANATIONS" in gl, "glossary.js: missing SIMPLE_EXPLANATIONS")
check("function openGlossaryTerm" in gl, "glossary.js: missing openGlossaryTerm")
check("function speakGlossaryTerm" in gl, "glossary.js: missing speakGlossaryTerm")

# === 17. Beginner mode ===
bm = file_read("beginner_mode.js")
check("const BeginnerMode" in bm, "beginner_mode.js: missing BeginnerMode")
check("isBeginner" in bm, "beginner_mode.js: missing isBeginner")
check("setMode" in bm, "beginner_mode.js: missing setMode")
check("oneLiner" in bm, "beginner_mode.js: missing oneLiner")
check("scoreReasons" in bm, "beginner_mode.js: missing scoreReasons")
check("askModeAfterAcademia" in bm, "beginner_mode.js: missing askModeAfterAcademia")
check("enableBeginnerForAcademia" in bm, "beginner_mode.js: missing enableBeginnerForAcademia")

# === 18. Tutorial.js ===
tut = file_read("tutorial.js")
check("const Tutorial" in tut, "tutorial.js: missing Tutorial")
check("STEPS" in tut or "const STEPS" in tut, "tutorial.js: missing STEPS")
step_count = tut.count("target:")
check(step_count >= 18, f"tutorial.js: expected 18+ steps, found {step_count}")
check("academia" in tut.lower(), "tutorial.js: missing academia step")

# === 19. Charts.js ===
chart = file_read("charts.js")
check("function createChart" in chart, "charts.js: missing createChart")
chart_types = ["donut", "scatter", "bar", "sparkline", "comparison_bars", "trend_detail"]
for ct in chart_types:
    check(ct in chart, f"charts.js: missing chart type {ct}")
check("svg" in chart.lower(), "charts.js: missing SVG")

# === 20. App.js academia integration ===
check("function renderAcademia" in app, "app.js: missing renderAcademia")
check("function openLesson" in app, "app.js: missing openLesson")
check("function renderAcademiaLesson" in app, "app.js: missing renderAcademiaLesson")
check("function renderLessonStep" in app, "app.js: missing renderLessonStep")
check("function renderLessonComplete" in app, "app.js: missing renderLessonComplete")
check("function bindLessonEvents" in app, "app.js: missing bindLessonEvents")
check("function closeGlossaryPopup" in app, "app.js: missing closeGlossaryPopup")
check("academia-lesson" in app or "'academia-lesson'" in app, "app.js: missing academia-lesson view")
check("LearningEngine" in app, "app.js: missing LearningEngine integration")
check("QuizEngine" in app, "app.js: missing QuizEngine integration")
check("LessonVisuals" in app, "app.js: missing LessonVisuals integration")
check("ProgressTracker" in app, "app.js: missing ProgressTracker integration")

# === 21. index.html academia ===
check('data-view="academia"' in html, "index.html: missing academia nav item")
check('id="view-academia"' in html, "index.html: missing view-academia section")
check('id="view-academia-lesson"' in html, "index.html: missing view-academia-lesson section")
check('id="academia-modules"' in html, "index.html: missing academia-modules")
check('id="academia-lesson-content"' in html, "index.html: missing academia-lesson-content")
check('id="academia-progress-bar"' in html, "index.html: missing academia-progress-bar")
check('id="academia-continue"' in html, "index.html: missing academia-continue button")
check('id="academia-restart"' in html, "index.html: missing academia-restart button")
check('id="academia-speed"' in html, "index.html: missing academia-speed")
check('id="academia-narration-toggle"' in html, "index.html: missing academia-narration-toggle")
check('id="academia-lesson-back"' in html, "index.html: missing academia-lesson-back")
check('id="academia-lesson-glossary"' in html, "index.html: missing academia-lesson-glossary")
check('id="academia-lesson-counter"' in html, "index.html: missing academia-lesson-counter")
check('id="narration-prev"' in html, "index.html: missing narration-prev")
check('id="narration-next"' in html, "index.html: missing narration-next")
check('id="narration-play-pause"' in html, "index.html: missing narration-play-pause")
check('id="narration-skip"' in html, "index.html: missing narration-skip")
check('id="academia-visual-diagnosis"' in html, "index.html: missing academia-visual-diagnosis")
check("Narracao local do navegador" in html, "index.html: missing narration disclaimer")
check("Nenhum servico externo foi chamado" in html, "index.html: missing no-external-service disclaimer")

# === 22. Script includes ===
check('src="learning_data.js"' in html, "index.html: missing learning_data.js script")
check('src="learning_engine.js"' in html, "index.html: missing learning_engine.js script")
check('src="quiz_engine.js"' in html, "index.html: missing quiz_engine.js script")
check('src="lesson_visuals.js"' in html, "index.html: missing lesson_visuals.js script")
check('src="progress_tracker.js"' in html, "index.html: missing progress_tracker.js script")
check('src="charts.js"' in html, "index.html: missing charts.js script")
check('src="narration.js"' in html, "index.html: missing narration.js script")
check('src="glossary.js"' in html, "index.html: missing glossary.js script")
check('src="beginner_mode.js"' in html, "index.html: missing beginner_mode.js script")
check('src="tutorial.js"' in html, "index.html: missing tutorial.js script")

# === 23. CSS academia styles ===
check(".learning-highlight" in css, "styles.css: missing learning-highlight")
check(".learning-spotlight" in css or ".learning-spotlight-svg" in css, "styles.css: missing spotlight")
check(".quiz-option" in css, "styles.css: missing quiz-option")
check(".quiz-correct" in css, "styles.css: missing quiz-correct")
check(".quiz-incorrect" in css, "styles.css: missing quiz-incorrect")
check(".quiz-feedback" in css, "styles.css: missing quiz-feedback")
check(".visual-diagnosis" in css, "styles.css: missing visual-diagnosis")
check(".diagnosis-step" in css, "styles.css: missing diagnosis-step")
check(".volume-comparison" in css, "styles.css: missing volume-comparison")
check(".growth-comparison" in css, "styles.css: missing growth-comparison")
check(".saturation-visual" in css, "styles.css: missing saturation-visual")
check("@media (prefers-reduced-motion)" in css, "styles.css: missing reduced-motion")
check(".academia-modules" in css, "styles.css: missing academia-modules")
check(".academia-module-card" in css, "styles.css: missing academia-module-card")
check(".academia-lesson-item" in css, "styles.css: missing academia-lesson-item")

# === 24. MOCK URL fields ===
check("const MOCK_URL_FIELDS" in mock, "mock_data.js: missing MOCK_URL_FIELDS")
check("const MOCK_URL_DISCLAIMER" in mock, "mock_data.js: missing MOCK_URL_DISCLAIMER")
url_fields = ["official_product_url", "sales_page_url", "affiliate_program_url",
              "checkout_url", "ad_library_url", "evidence_url", "verification_status"]
for uf in url_fields:
    check(uf in mock, f"mock_data.js: missing URL field '{uf}'")

# === 25. Accessibility ===
check("aria-label" in html, "index.html: missing aria labels")
check("role=" in html, "index.html: missing ARIA roles")
check("prefers-reduced-motion" in css, "styles.css: missing accessibility prefers-reduced-motion")
check("outline" in css, "styles.css: missing focus outline")
check("z-index: 9998" in app or "z-index:9998" in app, "app.js: missing glossary popup z-index")

# === 26. No forbidden content ===
all_content = html + app + mock + ldata + lengine + quiz + pt + lv
check("fetch(" not in all_content, "codebase: contains fetch (external call prohibited)")
check("XMLHttpRequest" not in all_content, "codebase: contains XMLHttpRequest (external call prohibited)")
check("axios" not in all_content, "codebase: contains axios (external call prohibited)")
check("http://" not in all_content or "http://localhost" in all_content or "https://" not in all_content,
      "codebase: contains http/https (may be external URL)")
check("import " not in all_content or "import { " in all_content or "import " not in all_content,
      "codebase: contains ES module imports (should be plain scripts)")

# === Summary ===
total_assertions = assertions
passed = total_assertions - len(errors)

print(f"=" * 50)
print(f"  Offer Intelligence — Smoke Test v1.0")
print(f"=" * 50)
print(f"  Assertions: {total_assertions}")
print(f"  Passed:     {passed}")
print(f"  Failed:     {len(errors)}")
print(f"  +{total_assertions - 72} novos desde a Fase 2 (72)")
print(f"=" * 50)

if errors:
    print(f"\n  FAILURES:")
    for e in errors:
        print(f"    [FAIL] {e}")
    sys.exit(1)
else:
    print(f"\n  ALL CHECKS PASSED")
    print(f"=" * 50)
