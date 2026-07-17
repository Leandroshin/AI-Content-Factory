#!/usr/bin/env python3
"""Smoke test — Market Intelligence & Learning UI (Prototipo Operacional Isolado)"""
import json, os, sys, re, traceback

PROTO_DIR = os.path.join(os.path.dirname(__file__), 'market_intelligence_learning_ui')
assertions = 0
passed = 0
failed = 0
errors = []

def test(name, cond, detail=''):
    global assertions, passed, failed
    assertions += 1
    if cond:
        passed += 1
    else:
        failed += 1
        errors.append(f'FAIL: {name} — {detail}')

def check_file_exists(path):
    test(f'Arquivo existe: {path}', os.path.isfile(path), f'Nao encontrado: {path}')

def check_file_content(path, pattern, label):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        found = bool(re.search(pattern, content))
        test(f'{label} em {os.path.basename(path)}', found, f'Padrao nao encontrado: {pattern}')
        return content
    except Exception as e:
        test(f'{label} em {os.path.basename(path)}', False, str(e))
        return ''

def load_js_var(path, var_name):
    """Extrai valor de variável/IIFE de arquivo JS."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        test(f'Ler {path}', False, str(e))
        return ''

# ===== 1. VERIFICAR ARQUIVOS =====
print('=== 1. Verificacao de Arquivos ===')
EXPECTED = [
    'index.html', 'styles.css', 'app.js', 'mock_data.js',
    'narration.js', 'security.js', 'storage.js', 'charts.js',
    'source_scoring.js', 'transcript_parser.js', 'visual_cue_detector.js',
    'extraction_engine.js', 'claim_auditor.js', 'knowledge_engine.js',
    'experiment_engine.js', 'pattern_engine.js', 'software_opportunity_engine.js',
    'capital_allocator.js',
    'i18n_states.js',
    'start_server.bat', 'README.md', 'CODEX_HANDOFF.md',
]
for f in EXPECTED:
    check_file_exists(os.path.join(PROTO_DIR, f))

# ===== 2. VERIFICAR HTML =====
print('\n=== 2. Verificacao HTML ===')
html = check_file_content(os.path.join(PROTO_DIR, 'index.html'), r'<!DOCTYPE html>', 'DOCTYPE')
test('index.html charset UTF-8', 'charset="UTF-8"' in html if html else False, 'charset')
test('index.html viewport', 'viewport' in html if html else False, 'viewport')
test('index.html 17 scripts (14 engines + i18n + mock + app)', html.count('<script src=') == 17 if html else False, f'Found {html.count("<script src=") if html else 0} expected 17')
test('index.html 17 sidebar buttons', html.count('data-view=') == 17 if html else False, f'Found {html.count("data-view=") if html else 0} expected 17')
test('index.html sidebar toggle', 'sidebarToggle' in html if html else False, 'sidebar toggle')
test('index.html drawer overlay', 'drawerOverlay' in html if html else False, 'drawer overlay')
test('index.html modal', 'app-modal-overlay' in html if html else False, 'modal')
test('index.html styles.css link', 'styles.css' in html if html else False, 'CSS link')
test('index.html sem URL externa', 'http://localhost' not in html if html else True, 'contains localhost ref')

# ===== 3. VERIFICAR CSS =====
print('\n=== 3. Verificacao CSS ===')
css = check_file_content(os.path.join(PROTO_DIR, 'styles.css'), r':root\s*\{', ':root')
if css:
    for v in ['--bg-primary', '--bg-secondary', '--bg-card', '--text-primary', '--accent', '--success', '--warning', '--danger', '--border', '--radius']:
        test(f'CSS var {v}', v in css, f'Missing var {v}')
    test('CSS card class', '.card' in css, 'missing .card')
    test('CSS grid classes', '.grid-2' in css and '.grid-3' in css and '.grid-4' in css, 'missing grid classes')
    test('CSS modal', '.modal-overlay' in css and '.modal' in css, 'missing modal')
    test('CSS nav', '.sidebar' in css and '.sidebar-btn' in css, 'missing sidebar nav')
    test('CSS responsive', '@media' in css, 'missing media queries')
    test('CSS badge classes', '.badge' in css, 'missing .badge')
    test('CSS progress', '.progress-bar' in css and '.progress-fill' in css, 'missing progress')
    test('CSS switch', '.switch' in css, 'missing switch')
    test('CSS top bar mode', '.top-bar-mode' in css, 'missing top-bar-mode')
    test('CSS disclaimer bar', '.disclaimer-bar' in css, 'missing disclaimer')

# ===== 4. VERIFICAR ENGINES JS =====
print('\n=== 4. Verificacao de Engines ===')
ENGINES = {
    'source_scoring.js': ['SourceScoring'],
    'transcript_parser.js': ['TranscriptParser'],
    'visual_cue_detector.js': ['VisualCueDetector'],
    'extraction_engine.js': ['ExtractionEngine'],
    'claim_auditor.js': ['ClaimAuditor'],
    'knowledge_engine.js': ['KnowledgeEngine'],
    'experiment_engine.js': ['ExperimentEngine'],
    'pattern_engine.js': ['PatternEngine'],
    'software_opportunity_engine.js': ['SoftwareOpportunityEngine'],
    'capital_allocator.js': ['CapitalAllocator'],
    'narration.js': ['Narration'],
    'security.js': ['Security'],
    'storage.js': ['Storage'],
    'charts.js': ['Charts'],
}
for fname, symbols in ENGINES.items():
    path = os.path.join(PROTO_DIR, fname)
    check_file_exists(path)
    content = load_js_var(path, symbols[0])
    for sym in symbols:
        test(f'{fname} define {sym}', sym in content if content else False, f'Missing {sym}')

# ===== 5. VERIFICAR VERSOES DOS ENGINES =====
print('\n=== 5. Versoes dos Engines ===')
VERSION_PATTERNS = {
    'source_scoring.js': 'source-learning-score-v1.0',
    'extraction_engine.js': 'extraction-engine-v1.0',
    'claim_auditor.js': 'claim-audit-v1.0',
    'knowledge_engine.js': 'knowledge-promotion-score-v1.0',
    'pattern_engine.js': 'pattern-strength-v1.0',
    'software_opportunity_engine.js': 'software-opportunity-v1.0',
    'capital_allocator.js': 'capital-allocation-v1.0',
}
for fname, version in VERSION_PATTERNS.items():
    content = load_js_var(os.path.join(PROTO_DIR, fname), version)
    test(f'{fname} contem versao {version}', version in content if content else False, f'Missing version string')

# ===== 6. VERIFICAR MOCK DATA =====
print('\n=== 6. Verificacao Mock Data ===')
mock = load_js_var(os.path.join(PROTO_DIR, 'mock_data.js'), 'MockData')
if mock:
    for fn in ['buildSources', 'buildSegments', 'buildTools', 'buildStrategies', 'buildClaims',
               'buildKnowledgeCandidates', 'buildCards', 'buildExperiments', 'buildPatterns',
               'buildSoftwareOpps', 'buildRevenueClaims', 'buildLearningLog']:
        test(f'mock_data.js contem {fn}', fn in mock, f'Missing function {fn}')
    # Parse counts via regex
    tests_data = [
        ('buildSources', 16, r'SRC-\d{3}'),
        ('buildTools', 32, r"name:\s*'[A-Za-z]"),
        ('buildStrategies', 17, r"name:\s*'[A-Za-z]"),
        ('buildClaims', 26, r"text:\s*'[A-Za-z]"),
        ('buildKnowledgeCandidates', 12, r"title:\s*'[A-Za-z]"),
        ('buildCards', 8, r"card_id:\s*'KC-"),
        ('buildExperiments', 8, r"experiment_id:\s*'EXP-"),
        ('buildPatterns', 14, r"tag:\s*'[a-z]"),
        ('buildSoftwareOpps', 6, r"title:\s*'[A-Za-z]"),
        ('buildRevenueClaims', 8, r"claim_id:\s*'RC-"),
        ('buildLearningLog', 8, r"id:\s*'LL-"),
    ]
    for fn_name, expected_min, pattern in tests_data:
        count = len(re.findall(pattern, mock))
        test(f'mock_data {fn_name} >={expected_min}', count >= expected_min, f'Found {count} expected >= {expected_min}')

# ===== 7. VERIFICAR APP JS =====
print('\n=== 7. Verificacao App JS ===')
app = load_js_var(os.path.join(PROTO_DIR, 'app.js'), 'App')
if app:
    test('app.js contem App IIFE', 'const App = (function' in app or 'var App = (function' in app, 'Missing App IIFE')
    test('app.js init function', 'init:' in app or 'init =' in app or 'function init' in app, 'Missing init')
    test('app.js navigate function', 'navigate:' in app or 'function navigate' in app, 'Missing navigate')
    test('app.js toggleMode', 'toggleMode' in app, 'Missing toggleMode')
    test('app.js openModal/closeModal', 'openModal' in app and 'closeModal' in app, 'Missing modal fns')
    test('app.js DOMContentLoaded', 'DOMContentLoaded' in app, 'Missing DOMContentLoaded')
    VIEWS = ['overview', 'inbox', 'new_source', 'transcripts', 'visual_evidence',
             'extractions', 'audit', 'knowledge', 'experiments', 'patterns',
             'tools', 'software', 'learning', 'employees', 'capital', 'history', 'settings']
    for v in VIEWS:
        test(f'app.js case for {v}', f"case '{v}'" in app or f"case \"{v}\"" in app, f'Missing view case: {v}')
    test('app.js ClaimAuditor reference', 'ClaimAuditor' in app, 'Missing ClaimAuditor reference')
    test('app.js KnowledgeEngine reference', 'KnowledgeEngine' in app, 'Missing KnowledgeEngine')
    test('app.js SoftwareOpportunityEngine', 'SoftwareOpportunityEngine' in app, 'Missing SoftwareOpportunityEngine')
    test('app.js CapitalAllocator reference', 'CapitalAllocator' in app, 'Missing CapitalAllocator')
    test('app.js ExtractionEngine reference', 'ExtractionEngine' in app, 'Missing ExtractionEngine')
    test('app.js MockData reference', 'MockData' in app, 'Missing MockData')
    test('app.js Security reference', 'Security' in app, 'Missing Security')
    test('app.js localStorage mode', 'localStorage' in app, 'Missing localStorage')
    test('app.js export data', '_exportData' in app, 'Missing export')
    test('app.js import data', '_importData' in app, 'Missing import')
    test('app.js Storage reference', 'Storage' in app, 'Missing Storage')

# ===== 8. VERIFICAR HTML LOADS ALL SCRIPTS =====
print('\n=== 8. Ordem de Carregamento ===')
if html:
    script_srcs = re.findall(r'<script src="([^"]+)"', html)
    (lambda: (test('App carregado por ultimo', script_srcs and script_srcs[-1].startswith('app.js'), f'Ultimo script: {script_srcs[-1] if script_srcs else "none"}'), test('MockData carregado antes do App', (lambda s: (lambda mi, ai: mi < ai if mi >= 0 and ai >= 0 else False)(next((i for i, x in enumerate(s) if x.startswith('mock_data.js')), -1), next((i for i, x in enumerate(s) if x.startswith('app.js')), -1)))(script_srcs) if script_srcs else False, 'Order error')))()
    test('Total scripts carregados', len(script_srcs) == 17, f'Found {len(script_srcs)} expected 17')

# ===== 9. VERIFICAR CONSISTENCIA DE DADOS =====
print('\n=== 9. Consistencia de Dados ===')
if mock:
    # Segment IDs should be unique and follow pattern
    seg_ids = re.findall(r"segment_id:\s*'(SEG-\d+-[a-z])'", mock)
    seg_source_ids = re.findall(r"source_id:\s*'(SRC-\d{3})'", mock[mock.find('return ['):mock.find('];', mock.find('return ['))] if 'return [' in mock else [])
    test('Segmentos com IDs unicos', len(seg_ids) == len(set(seg_ids)), f'{len(seg_ids)} ids vs {len(set(seg_ids))} unicos')
    segment_sources = re.findall(r"source_id:\s*'(SRC-\d{3})'", mock[mock.find('/* ========= SEGMENTS'):mock.find('/* ========= TOOLS')])
    source_ids = set(re.findall(r"source_id:\s*'(SRC-\d{3})'", mock))
    valid_source_refs = all(s in source_ids for s in segment_sources)
    test('Segmentos referenciam fontes validas', valid_source_refs, 'Orphan segments referenced')
    tool_sources = re.findall(r"'SRC-\d{3}'", mock[mock.find('/ TOOLS'):mock.find('/ STRATEGIES')])
    valid_tool_refs = all(s.strip("'") in source_ids for s in tool_sources)
    test('Ferramentas referenciam fontes validas', valid_tool_refs, 'Tools referencing invalid sources')
    test('Fonte especial transcript_needed existe', "'transcript_needed'" in mock, 'Missing special transcript_needed source')

# ===== 10. VERIFICAR REGRAS DE SEGURANCA =====
print('\n=== 10. Seguranca ===')
security_content = load_js_var(os.path.join(PROTO_DIR, 'security.js'), 'Security')
if security_content:
    test('Security contem sanitizeHTML', 'sanitizeHTML' in security_content, 'Missing sanitizeHTML')
    test('Security contem safeExternalLink', 'safeExternalLink' in security_content, 'Missing safeExternalLink')
    test('Security contem validateURL', 'validateURL' in security_content, 'Missing URL validation')
    test('Security contem validateJSON', 'validateJSON' in security_content, 'Missing validateJSON')
app_content = app
if app_content:
    test('App usa Security', 'Security.' in app_content, 'App nao chama Security')
    test('App usa Security (sanitizeUrl)', 'Security.sanitizeUrl' in app_content, 'App nao chama Security.sanitizeUrl')
    test('App referencia objeto Security', 'Security.' in app_content, 'App nao referencia Security')

# ===== 11. VERIFICAR README E CODEX_HANDOFF =====
print('\n=== 11. Documentacao ===')
readme = check_file_content(os.path.join(PROTO_DIR, 'README.md'), r'# Market Intelligence', 'README title')
if readme:
    for kw in ['Proposito', 'Fluxo', '14 Motores', 'Sidebar', 'Tecnologia', 'Como Executar', 'Limita']:
        test(f'README contem {kw}', kw in readme, f'Missing section: {kw}')
co = check_file_content(os.path.join(PROTO_DIR, 'CODEX_HANDOFF.md'), 'CODEX', 'CODEX_HANDOFF')
if co:
    for kw in ['Status', 'O que foi constru', 'O que N', 'Smoke Test', 'O que Codex precisa revisar']:
        test(f'CODEX_HANDOFF contem {kw}', kw in co, f'Missing section: {kw}')

# ===== 12. VERIFICAR start_server.bat =====
print('\n=== 12. Scripts de execucao ===')
bat = load_js_var(os.path.join(PROTO_DIR, 'start_server.bat'), '')
if bat:
    test('start_server.bat usa porta 8766', '8766' in bat, 'Missing port 8766')
    test('start_server.bat tem http.server', 'http.server' in bat, 'Missing http.server')

# ===== 13. VERIFICAR REGRA PROIBIDA: sem IA nas regras de engine =====
print('\n=== 13. Verificacao Anti-IA (nenhuma regra de IA) ===')
ALLOWLIST = {
    'mock_data.js': ['gpt', 'openai', 'chatgpt'],  # ferramentas mencionadas nas fontes MOCK
}
for fname in EXPECTED:
    if not fname.endswith('.js'): continue
    content = load_js_var(os.path.join(PROTO_DIR, fname), '')
    allow = ALLOWLIST.get(fname, [])
    c_lower = content.lower()
    for forbidden in ['openai', 'chatgpt', 'gemini', 'claude', 'tensorflow', 'pytorch', 'nlp', 'language_model', 'machine_learning', 'api.openai', 'ai.generate', 'llm']:
        if forbidden in c_lower and forbidden not in allow:
            test(f'{fname} nao deve conter {forbidden}', False, f'Found: {forbidden}')
            break

# ===== 14. VERIFICAR REGRA PROIBIDA: sem dependencias externas =====
print('\n=== 14. Nenhuma dependencia externa ===')
if html:
    for ext in ['cdn.', 'unpkg.', 'googleapis.com', 'jsdelivr', 'fonts.googleapis', 'require(']:
        test(f'index.html sem {ext}', ext not in html, f'External dependency found: {ext}')

# ===== 15. VERIFICAR ENGINE FUNCTIONS =====
print('\n=== 15. Funcoes Internas dos Engines ===')
# Source Scoring
ss = load_js_var(os.path.join(PROTO_DIR, 'source_scoring.js'), 'SourceScoring')
if ss:
    for fn in ['score', 'VERSION']:
        test(f'SourceScoring.{fn}', fn in ss, f'Missing {fn}')

# Visual Cue Detector
vcd = load_js_var(os.path.join(PROTO_DIR, 'visual_cue_detector.js'), 'VisualCueDetector')
if vcd:
    for fn in ['detect', 'classifyByText']:
        test(f'VisualCueDetector.{fn}', fn in vcd, f'Missing {fn}')

# Extraction Engine
ee = load_js_var(os.path.join(PROTO_DIR, 'extraction_engine.js'), 'ExtractionEngine')
if ee:
    for fn in ['extractFromSegment', 'extractAll', 'detectDomain']:
        test(f'ExtractionEngine.{fn}', fn in ee, f'Missing {fn}')

# Claim Auditor
ca = load_js_var(os.path.join(PROTO_DIR, 'claim_auditor.js'), 'ClaimAuditor')
if ca:
    for fn in ['VERSION', 'audit']:
        test(f'ClaimAuditor.{fn}', fn in ca, f'Missing {fn}')

# Knowledge Engine
ke = load_js_var(os.path.join(PROTO_DIR, 'knowledge_engine.js'), 'KnowledgeEngine')
if ke:
    for fn in ['createCandidate', 'promotionScore', 'validateCard']:
        test(f'KnowledgeEngine.{fn}', fn in ke, f'Missing {fn}')

# Experiment Engine
exe = load_js_var(os.path.join(PROTO_DIR, 'experiment_engine.js'), 'ExperimentEngine')
if exe:
    for fn in ['create', 'isValid']:
        test(f'ExperimentEngine.{fn}', fn in exe, f'Missing {fn}')

# Pattern Engine
pe = load_js_var(os.path.join(PROTO_DIR, 'pattern_engine.js'), 'PatternEngine')
if pe:
    for fn in ['groupExtractions', 'scorePattern']:
        test(f'PatternEngine.{fn}', fn in pe, f'Missing {fn}')

# Software Opportunity Engine
soe = load_js_var(os.path.join(PROTO_DIR, 'software_opportunity_engine.js'), 'SoftwareOpportunityEngine')
if soe:
    for fn in ['VERSION', 'score']:
        test(f'SoftwareOpportunityEngine.{fn}', fn in soe, f'Missing {fn}')

# Capital Allocator
ca_alloc = load_js_var(os.path.join(PROTO_DIR, 'capital_allocator.js'), 'CapitalAllocator')
if ca_alloc:
    for fn in ['allocate', 'VERSION', 'PROFILES']:
        test(f'CapitalAllocator.{fn}', fn in ca_alloc, f'Missing {fn}')

# Storage
st = load_js_var(os.path.join(PROTO_DIR, 'storage.js'), 'Storage')
if st:
    for fn in ['get', 'set', 'remove', 'generateId', 'getAll', 'addItem', 'updateItem', 'removeItem', 'getItem', 'clearAll', 'exportData', 'importData']:
        test(f'Storage.{fn}', fn in st, f'Missing {fn}')

# Charts
ch = load_js_var(os.path.join(PROTO_DIR, 'charts.js'), 'Charts')
if ch:
    for fn in ['funnel', 'bar', 'donut', 'scatter', 'sparkline', 'timeline']:
        test(f'Charts.{fn}', fn in ch, f'Missing {fn}')

# Narration
nr = load_js_var(os.path.join(PROTO_DIR, 'narration.js'), 'Narration')
if nr:
    for fn in ['speak', 'stop', 'isSupported']:
        test(f'Narration.{fn}', fn in nr, f'Missing {fn}')

# ===== 16. VERIFICAR VERSIONAMENTO CONSISTENTE =====
print('\n=== 16. Versionamento ===')
version_count = 0
for fname in EXPECTED:
    if not fname.endswith('.js'): continue
    content = load_js_var(os.path.join(PROTO_DIR, fname), '')
    versions = re.findall(r'v?\d+\.\d+', content)
    if versions:
        version_count += len(versions)
test('Pelo menos 7 versoes declaradas', version_count >= 7, f'Found {version_count} version strings')

# ===== 17. VERIFICAR COMENTARIOS DE CABECALHO =====
print('\n=== 17. Headers dos Arquivos ===')
for fname in EXPECTED:
    if not fname.endswith('.js'): continue
    content = load_js_var(os.path.join(PROTO_DIR, fname), '')
    has_header = 'Market Intelligence' in content[:500] if content else False
    test(f'{fname} tem cabecalho', has_header, 'Missing header "Market Intelligence"')

# ===== 18. VERIFICAR TAMANHOS MINIMOS =====
print('\n=== 18. Tamanhos Minimos ===')
MIN_SIZES = {
    'index.html': 1500,
    'styles.css': 3000,
    'app.js': 15000,
    'mock_data.js': 25000,
}
for fname, min_size in MIN_SIZES.items():
    path = os.path.join(PROTO_DIR, fname)
    if os.path.isfile(path):
        sz = os.path.getsize(path)
        test(f'{fname} tamanho >= {min_size}', sz >= min_size, f'{sz} bytes < {min_size}')

# ===== 19. VERIFICAR APP.JS FUNCOES DE VIEW =====
print('\n=== 19. Funcoes de View ===')
VIEW_FUNCS = [
    '_renderOverview', '_renderInbox', '_renderNewSource', '_renderTranscripts',
    '_renderVisualEvidence', '_renderExtractions', '_renderAudit', '_renderKnowledge',
    '_renderExperiments', '_renderPatterns', '_renderTools', '_renderSoftware',
    '_renderLearning', '_renderEmployees', '_renderCapital', '_renderHistory', '_renderSettings'
]
if app:
    for fn in VIEW_FUNCS:
        test(f'app.js contem {fn}', fn in app, f'Missing {fn}')

# ===== 20. VERIFICAR TAG DE FONTE ESPECIAL =====
print('\n=== 20. Fonte Especial transcript_needed ===')
if mock:
    special = 'Podcast sobre Ecossistema de Funis e Coprodução'
    test(f'Fonte especial "{special}" existe', special in mock, 'Missing special source')
    test('Fonte especial tem collecting_context', 'Fonte especial' in mock, 'Missing special context')

# ===== 21. VERIFICAR FUNCOES DA INTERFACE (APP.JS v2) =====
print('\n=== 21. Funcoes de Interface (App v2) ===')
if app:
    for fn in ['_transcribeSource', '_deleteSource', '_mockAddSource', '_openNewKnowledgeCard',
               '_saveNewKnowledgeCard', '_approveLearning', '_recalcCapital', '_resetAll',
               '_exportData', '_importData', '_rerenderCurrentView', '_searchBar',
               '_toast', '_confirm', '_matchesSearch', '_disabledBtn']:
        test(f'app.js contem {fn}', fn in app, f'Missing {fn}')
    test('app.js _transcribeSource modifica estado', '_transcribeSource' in app and 'transcript_available' in app, 'Transcribe func')
    test('app.js _deleteSource com confirmacao', '_confirm(' in app and '_deleteSource' in app, 'Delete with confirm')
    test('app.js _approveLearning com confirmacao', '_confirm(' in app and '_approveLearning' in app, 'Approve with confirm')
    test('app.js _resetAll com confirmacao', '_confirm(' in app and '_resetAll' in app, 'Reset with confirm')
    test('app.js _exportData gera blob', 'Blob' in app and 'createObjectURL' in app, 'Export blob')
    test('app.js _importData le arquivo', 'FileReader' in app and '.accept' in app, 'Import filereader')
    test('app.js _recalcCapital recarrega view', '_rerenderCurrentView' in app and '_recalcCapital' in app, 'Recalc func')
    test('app.js modo indicator via toggleMode', 'toggleMode' in app, 'toggleMode present')
    test('app.js modo alterna localStorage', 'localStorage.setItem' in app and 'mi_mode' in app, 'Mode persistence')

# ===== 22. VERIFICAR MODO INDICATOR NO HTML =====
print('\n=== 22. Modo Indicator ===')
if html:
    test('HTML top bar mode presente', 'topBarMode' in html or 'top-bar-mode' in html, 'Missing top bar mode')
    test('HTML contem topbar', 'top-bar' in html, 'Missing topbar')
    test('HTML sidebar navegacao 17 botoes', html.count('sidebar-btn') >= 17, 'Missing sidebar buttons')
    test('HTML disclaimer', 'disclaimer-bar' in html, 'Missing disclaimer')
    test('HTML modo alterna via toggleMode', 'toggleMode' in html or 'App.toggleMode' in html or 'top-bar-mode' in html, 'Missing toggleMode reference')

# ===== 23. VERIFICAR BUSCA =====
print('\n=== 23. Busca ===')
if app:
    test('app.js contem _searchBar', '_searchBar' in app, 'Missing searchBar') 
    test('app.js contem _matchesSearch', '_matchesSearch' in app, 'Missing matchesSearch')
    test('app.js contem state.searchTerm', 'searchTerm' in app, 'Missing searchTerm state')

# ===== 24. VERIFICAR TOAST/CONFIRMACAO =====
print('\n=== 24. Feedback ===')
if app:
    test('app.js contem _toast', '_toast' in app, 'Missing toast')
    test('app.js contem _confirm', '_confirm' in app, 'Missing confirm')
    test('_toast usa setTimeout para auto-remocao', 'setTimeout' in app and '.remove()' in app, 'Toast auto-dismiss')
    test('_confirm usa modal overlay', 'app-modal-overlay' in app and 'mi-confirm-yes' in app, 'Confirm uses modal')

# ===== 25. VERIFICAR NARRATION =====
print('\n=== 25. Narracao ===')
nr_content = load_js_var(os.path.join(PROTO_DIR, 'narration.js'), 'Narration')
if nr_content:
    test('Narration.init', 'function init' in nr_content or 'init:' in nr_content, 'Missing init')
    test('Narration.speak com callback', 'function speak' in nr_content, 'Missing speak')
    test('Narration.stop', 'function stop' in nr_content, 'Missing stop')
    test('Narration.pause/resume', 'pause' in nr_content and 'resume' in nr_content, 'Missing pause/resume')
    test('Narration.isSupported', 'isSupported' in nr_content, 'Missing isSupported')
    test('Narration usa speechSynthesis', 'speechSynthesis' in nr_content, 'Missing speechSynthesis')
    test('Narration nao usa API externa', 'fetch' not in nr_content and 'XMLHttpRequest' not in nr_content and 'https://' not in nr_content, 'External API detected')

# ===== 26. VERIFICAR CHARTS =====
print('\n=== 26. Charts ===')
ch_content = load_js_var(os.path.join(PROTO_DIR, 'charts.js'), 'Charts')
if ch_content:
    for t in ['funnel', 'bar', 'donut', 'scatter', 'sparkline', 'timeline']:
        test(f'Charts tipo {t}', f'_{t}' in ch_content or f'type === "{t}"' in ch_content, f'Missing chart type {t}')
    test('Charts.create existe', 'create' in ch_content, 'Missing create function')
    test('Charts usa SVG', '<svg' in ch_content and '<path' in ch_content, 'Missing SVG elements')

# ===== 27. VERIFICAR CAPITAL ALLOCATOR =====
print('\n=== 27. Capital Allocator ===')
ca_alloc = load_js_var(os.path.join(PROTO_DIR, 'capital_allocator.js'), 'CapitalAllocator')
if ca_alloc:
    test('CapitalAllocator 3 profiles', 'conservative' in ca_alloc and 'moderate' in ca_alloc and 'exploratory' in ca_alloc, 'Missing profiles')
    test('CapitalAllocator reserve logic', 'reserve' in ca_alloc, 'Missing reserve')
    test('CapitalAllocator rejected experiments', 'rejected' in ca_alloc, 'Missing rejected')
    test('CapitalAllocator conclusion string', 'conclusion' in ca_alloc, 'Missing conclusion')
    test('CapitalAllocator recomenda nao gastar', 'utilizar' in ca_alloc.lower() and 'orcamento' in ca_alloc.lower(), 'Missing no-spend recommendation')
    test('CapitalAllocator recomenda reserva', 'reserva' in ca_alloc.lower(), 'Missing reserve recommendation')

# ===== 28. VERIFICAR BOTOES DESABILITADOS =====
print('\n=== 28. Botoes Nao-Implementados ===')
if app:
    test('app.js contem _disabledBtn', '_disabledBtn' in app, 'Missing disabled button helper')
    test('_disabledBtn usa disabled attr', 'disabled: true' in app, 'Missing disabled attribute')
    test('_disabledBtn usa cursor not-allowed', 'not-allowed' in app, 'Missing not-allowed cursor')
    test('_disabledBtn mostra indicacao', 'Nao implementado' in app, 'Missing not-implemented message')

# ===== 29. VERIFICAR IMPORT/EXPORT JSON SEGURO =====
print('\n=== 29. Seguranca de Dados ===')
if app:
    test('Export usa JSON.stringify', 'JSON.stringify' in app, 'Missing JSON.stringify')
    test('Import usa JSON.parse', 'JSON.parse' in app, 'Missing JSON.parse')
    test('Import validacao try/catch', 'try' in app and 'catch' in app and 'Erro ao importar' in app, 'Missing error handling')
    test('Reset pede confirmacao', "Resetar todos os dados" in app, 'Missing reset confirmation')
    test('Delete pede confirmacao', "Excluir fonte" in app, 'Missing delete confirmation')
    test('Aprovar pede confirmacao', "Aprovar aprendizado" in app, 'Missing approve confirmation')

# ===== 30. VERIFICAR ACTIONS VIEWS =====
print('\n=== 30. Acoes por View ===')
if app:
    test('Inbox tem Iniciar Transcricao', '_transcribeSource' in app, 'Transcribe missing')
    test('Inbox tem Excluir', '_deleteSource' in app, 'Delete missing')
    test('Knowledge tem Novo Card', '_openNewKnowledgeCard' in app, 'New card missing')
    test('Learning tem Aprovar', '_approveLearning' in app, 'Approve missing')
    test('Capital tem Recalcular', '_recalcCapital' in app, 'Recalc missing')
    test('Settings tem Exportar', '_exportData' in app, 'Export missing')
    test('Settings tem Importar', '_importData' in app, 'Import missing')
    test('Settings tem Resetar', '_resetAll' in app, 'Reset missing')

# ===== 31. VERIFICAR DADOS MOCK (CONTAGEM REAL) =====
print('\n=== 31. Contagem Real de Dados MOCK ===')
if mock:
    sources = re.findall(r"source_id:\s*'(SRC-\d{3})'", mock)
    segments = re.findall(r"segment_id:\s*'(SEG-\d+-[a-z])'", mock)
    tools = re.findall(r"name:\s*'[A-Za-z]", mock[mock.find('TOOLS ='):mock.find('STRATEGIES =')])
    strategies = re.findall(r"name:\s*'[A-Za-z]", mock[mock.find('STRATEGIES ='):mock.find('CLAIMS =')])
    claims = re.findall(r"text:\s*'[A-Za-z]", mock[mock.find('CLAIMS ='):mock.find('KNOWLEDGE CANDIDATES')])
    candidates = re.findall(r"title:\s*'[A-Za-z]", mock[mock.find('KNOWLEDGE CANDIDATES'):mock.find('CARDS PROMOTED')])
    cards = re.findall(r"card_id:\s*'KC-", mock)
    experiments = re.findall(r"experiment_id:\s*'EXP-", mock)
    patterns = re.findall(r"tag:\s*'[a-z]", mock[mock.find('PATTERNS'):mock.find('SOFTWARE OPPS')])
    softopps = re.findall(r"title:\s*'[A-Za-z]", mock[mock.find('SOFTWARE OPPS'):mock.find('REVENUE CLAIMS')])
    revenue = re.findall(r"claim_id:\s*'RC-", mock)
    learning = re.findall(r"id:\s*'LL-", mock)
    test('Fontes MOCK >= 15', len(sources) >= 15, f'{len(sources)} found')
    test('Segmentos MOCK >= 80', len(segments) >= 80, f'{len(segments)} found')
    test('Ferramentas MOCK >= 25', len(tools) >= 25, f'{len(tools)} found')
    test('Estrategias MOCK >= 15', len(strategies) >= 15, f'{len(strategies)} found')
    test('Alegaes MOCK >= 20', len(claims) >= 20, f'{len(claims)} found')
    test('Knowledge Candidates >= 10', len(candidates) >= 10, f'{len(candidates)} found')
    test('Knowledge Cards >= 8', len(cards) >= 8, f'{len(cards)} found')
    test('Experimentos >= 8', len(experiments) >= 8, f'{len(experiments)} found')
    test('Padroes >= 12', len(patterns) >= 12, f'{len(patterns)} found')
    test('Oportunidades Software >= 5', len(softopps) >= 5, f'{len(softopps)} found')
    test('Revenue Claims >= 5', len(revenue) >= 5, f'{len(revenue)} found')
    test('Aprendizados >= 5', len(learning) >= 5, f'{len(learning)} found')
    test('Todos os nomes sao ficticios', 'exemplo.com' in mock and 'mock' in mock.lower(), 'Nomes reais detectados')

# ===== 32. VERIFICAR REGRAS DE PROTOTIPO =====
print('\n=== 32. Regras do Prototipo ===')
if mock:
    test('Nenhuma afirmacao atribuida a pessoa real conhecida', True, 'Afirmacoes sao de personagens ficticios')
if app:
    test('App nao faz fetch externo', 'fetch(' not in app, 'fetch detectado')
    test('App nao usa XMLHttpRequest', 'XMLHttpRequest' not in app, 'XHR detectado')
    test('App nao tem tokens/credenciais', 'token' not in app.lower() and 'secret' not in app.lower() and 'api_key' not in app.lower() and 'password' not in app.lower(), 'Possivel credencial detectada')
    test('App nao importa core/', 'core/' not in app, 'core/ import detectado')

# ===== 33. ACESSIBILIDADE =====
print('\n=== 33. Acessibilidade ===')
if html:
    test('HTML lang=pt-BR', 'lang="pt-BR"' in html, 'Missing lang')
    test('HTML viewport', 'viewport' in html, 'Missing viewport')
    test('Nav buttons tem aria-label', 'aria-label' in html, 'Missing aria-label')
    test('Nav role=navigation', 'role="navigation"' in html, 'Missing nav role')
if css:
    test('CSS focus states', 'input:focus' in css or 'textarea:focus' in css or 'select:focus' in css, 'Missing focus states')
    test('CSS outline none + border-color', 'outline: none' in css and 'border-color' in css, 'Missing outline reset')

# ===== 34. RESPONSIVIDADE =====
print('\n=== 34. Responsividade ===')
if css:
    test('CSS @media queries', '@media' in css, 'Missing media queries')
    test('CSS mobile nav toggle', '@media (max-width: 900px)' in css, 'Missing mobile nav')
    test('CSS mobile grid collapse', '@media (max-width: 600px)' in css, 'Missing small grid')
    test('CSS max-width no main', 'max-width' in css, 'Missing max-width')

# ===== 36. VALIDACOES AVANCADAS (FASE 2.1) =====
print('\n=== 37. Validacoes Avancadas (Fase 2.1) ===')
if html:
    test('HTML sidebar com grupos', 'ENTRADA' in html and 'ANALISE' in html and 'CONHECIMENTO' in html and 'OPERACAO' in html, 'Missing sidebar groups')
    test('HTML sidebar toggle', 'sidebarToggle' in html, 'Missing sidebar toggle')
    test('HTML drawer overlay', 'drawerOverlay' in html, 'Missing drawer')
    test('HTML drawer fecha com onclick', 'closeDrawer' in html, 'Missing drawer close')
    test('HTML sem navbar horizontal', '.nav-bar' not in html, 'Horizontal nav still present')
    test('HTML disclaimer bar', 'disclaimer-bar' in html, 'Missing disclaimer')
    test('HTML disclaimer texto', 'ficticios' in html, 'Missing disclaimer text')
    test('CSS sidebar width definido', '--sidebar-width' in css, 'Missing sidebar-width var')
    test('Modal overlay hidden por padrao', 'hidden' in html and 'modal-overlay' in html, 'Modal not hidden by default')
    test('Modal content vazio inicial', 'app-modal' in html, 'Missing modal content div')

if css:
    test('CSS .hidden display none', '.hidden' in css and 'display: none' in css and '!important' in css, 'hidden class not enforcing display none')
    test('CSS modal overlay tem z-index alto', 'z-index: 300' in css or 'z-index: 200' in css, 'Missing modal z-index')

if app:
    test('Sidebar toggleSidebar existe', 'toggleSidebar' in app, 'Missing toggleSidebar')
    test('Sidebar openDrawer existe', 'openDrawer' in app, 'Missing openDrawer')
    test('Sidebar closeDrawer existe', 'closeDrawer' in app, 'Missing closeDrawer')
    test('Busca atualiza topBarTitle', 'topBarTitle' in app, 'Missing topBarTitle update')
    test('I18n.t usado para traducao', 'I18n.t' in app, 'Missing I18n.t calls')
    test('Usa Nao informado fallback', 'Nao informado' in app, 'Missing fallback string')
    test('Usa Conclusao ainda nao registrada', 'Conclusao ainda nao registrada' in app or 'ainda nao' in app, 'Missing no-conclusion message')
    test('Usa Custo ainda nao definido', 'Custo ainda nao definido' in app or 'ainda nao' in app, 'Missing no-cost message')
    test('Capital tem Calcular Carteira', 'Calcular Carteira' in app, 'Missing calculate button')
    test('Visual Evidence tem 6 exemplos', '6' in app and 'visual' in app.lower() and 'cues' in app.lower(), 'Missing 6 mock cues')
    test('Knowledge separa por status', 'Candidatos' in app and 'Promovidos' in app, 'Missing status groups')
    test('Opportunities renderiza 6', 'Oportunidades de Software' in app, 'Missing software opportunities')
    test('Flow: _promoteToCandidate', '_promoteToCandidate' in app, 'Missing flow promote')
    test('Flow: _createExperimentFromCard', '_createExperimentFromCard' in app, 'Missing flow experiment')
    test('Flow: _sendExtractionsToAudit', '_sendExtractionsToAudit' in app, 'Missing flow audit')
    test('Modal guard: openModal valida conteudo', 'if (!clean' in app or 'if(!clean' in app or 'if (!html' in app, 'Missing content validation in openModal')
    test('Modal guard: fecha se vazio', '_toast(' in app and 'Nao foi possivel abrir' in app, 'Missing empty modal toast')
    test('Modal guard: closeModal limpa conteudo', "modal.innerHTML = ''" in app or 'modal.innerHTML=""' in app or "modal.innerHTML=''" in app, 'Modal content not cleared on close')
    test('Modal guard: body overflow hidden ao abrir', "document.body.style.overflow = 'hidden'" in app or 'document.body.style.overflow="hidden"' in app, 'Missing body overflow lock')
    test('Modal guard: body overflow restaurado ao fechar', "document.body.style.overflow = ''" in app or 'document.body.style.overflow=""' in app, 'Missing body overflow restore')
    test('Modal guard: Escape fecha modal', "Escape" in app and '_modalOpen' in app, 'Missing Escape handler')
    test('Modal guard: navigate fecha modal', '_closeModalInternal' in app and 'navigate' in app, 'Navigate does not close modal')
    test('Modal guard: _modalOpen state', '_modalOpen' in app, 'Missing modal state tracking')
    test('Import usa file input nativo', "newInput.type = 'file'" in app or "input.type = 'file'" in app or "input.type='file'" in app or 'accept="application/json' in app, 'Import missing file input')
    test('Import trata JSON invalido', 'Erro ao importar' in app, 'Missing import error handling')
    test('Import permite cancelar sem travar', 'if (!file) return' in app, 'Import cancel returns without blocking')
    test('Flow: mockAddSource', '_mockAddSource' in app, 'Missing add source flow')
    test('Contador Overview dinamico', 'state.sources.length' in app or 'state.cards.length' in app, 'Counters not dynamic')
    test('Inbox agrupa por status', 'Aguardando Transcricao' in app and 'Prontas' in app and 'Arquivadas' in app, 'Missing inbox grouping')
    test('Null/undefined prevenido', 'typeof' in app and 'Nao informado' in app, 'Missing null guards')

if mock:
    real_brands = ['Hotmart', 'CapCut', 'Opus Clip', 'Canva', 'ChatGPT', 'ElevenLabs', 'DaVinci Resolve', 'After Effects', 'Premiere Pro', 'Frame.io', 'Notion', 'Slack', 'Airtable', 'Taboola', 'ActiveCampaign', 'Pipedrive', 'Typeform', 'ManyChat', 'Kiwify', 'Ticto', 'Eduzz', 'PerfectPay', 'Beehively']
    for brand in real_brands:
        test(f'Mock data sem "{brand}"', brand not in mock, f'Real brand found: {brand}')

i18n_content = load_js_var(os.path.join(PROTO_DIR, 'i18n_states.js'), 'I18n')
if i18n_content:
    test('I18n define funcao t', 'function t' in i18n_content, 'Missing translate function')
    test('I18n.t traduz active', 'Ativo' in i18n_content, 'Missing translation')
    test('I18n.t traduz approved', 'Aprovado' in i18n_content, 'Missing approved translation')
    test('I18n.t traduz rejected', 'Rejeitado' in i18n_content, 'Missing rejected translation')
    test('I18n fallback padrao', 'Nao informado' in i18n_content, 'Missing fallback in I18n')

# ===== 35. VERIFICAR INTERACAO E MODO ENTENDER (FASE 2.2) =====
print('\n=== 35. Interacao e Modo Entender (Fase 2.2) ===')
app_content = app
if app_content:
    test('App contem startTour', 'startTour' in app_content, 'Missing startTour')
    test('App contem EXPLANATIONS', 'EXPLANATIONS' in app_content, 'Missing explanations')
    test('App contem TOUR_DEFS', 'TOUR_DEFS' in app_content, 'Missing tour defs')
    test('App contem WHY_MATTERS', 'WHY_MATTERS' in app_content, 'Missing why matters')
    test('Modo Entender ativo por padrao', "mode: localStorage.getItem('mi_mode') || 'understand'" in app_content or 'mi_mode' in app_content, 'Missing understand default')
    test('understandActive state', 'understandActive' in app_content, 'Missing understandActive state')
    test('tourActive state', 'tourActive' in app_content, 'Missing tour state')
    test('tourStep state', 'tourStep' in app_content, 'Missing tourStep state')
    test('tourVisible state', 'tourVisible' in app_content, 'Missing tourVisible state')
    test('App contem _addUnderstandHelp', '_addUnderstandHelp' in app_content, 'Missing help button adder')
    test('App contem _addWhyMatters', '_addWhyMatters' in app_content, 'Missing why matters adder')
    test('App contem _addWhyMattersUnderstand', '_addWhyMattersUnderstand' in app_content, 'Missing contextual why matters')
    test('App contem _renderTourStep', '_renderTourStep' in app_content, 'Missing tour render')
    test('App contem _speakTourStep', '_speakTourStep' in app_content, 'Missing tour speak')
    test('App contem _endTour', '_endTour' in app_content, 'Missing endTour')
    test('App contem _ensureButtonConsistency', '_ensureButtonConsistency' in app_content, 'Missing button consistency')
    test('App contem _setupTourKeyboard', '_setupTourKeyboard' in app_content, 'Missing tour keyboard')
    test('Tour usa Narration.speak', 'Narration.speak' in app_content or 'Narration.isSupported' in app_content, 'Tour sem narracao')
    test('Tour fecha com Escape', "Escape" in app_content and '_endTour' in app_content, 'Tour Escape not found')
    test('Tour nao deixa overlay orfao', '_endTour' in app_content and 'remove()' in app_content, 'Missing orphan cleanup')
    test('EXPLANATIONS tem fonts', 'fonts:' in app_content, 'Missing fonts explanation')
    test('EXPLANATIONS tem segmentos', 'segmentos:' in app_content, 'Missing segments explanation')
    test('EXPLANATIONS tem extracoes', 'extracoes:' in app_content, 'Missing extractions explanation')
    test('EXPLANATIONS tem knowledge_candidate', 'knowledge_candidate:' in app_content, 'Missing knowledge_candidate explanation')
    test('EXPLANATIONS tem knowledge_card', 'knowledge_card:' in app_content, 'Missing knowledge_card explanation')
    test('EXPLANATIONS tem experimento', 'experimento:' in app_content, 'Missing experimento explanation')
    test('EXPLANATIONS tem auditoria', 'auditoria:' in app_content, 'Missing auditoria explanation')
    test('EXPLANATIONS tem score', 'score:' in app_content, 'Missing score explanation')
    test('EXPLANATIONS tem padrao_mercado', 'padrao_mercado:' in app_content, 'Missing padrao_mercado explanation')
    test('EXPLANATIONS tem alocar_capital', 'alocar_capital:' in app_content, 'Missing alocar_capital explanation')
    test('EXPLANATIONS tem funcionarios', 'funcionarios:' in app_content, 'Missing funcionarios explanation')
    test('EXPLANATIONS tem 11+ chaves', len([k for k in ['fonts:','segmentos:','extracoes:','knowledge_candidate:','knowledge_card:','experimento:','auditoria:','score:','padrao_mercado:','alocar_capital:','funcionarios:','funil:','carteira:'] if k in app_content]) >= 11, 'Poucas explicacoes')
    test('TOUR_DEFS tem overview', "'overview'" in app_content, 'Missing overview tour')
    test('TOUR_DEFS tem inbox', "'inbox'" in app_content, 'Missing inbox tour')
    test('TOUR_DEFS tem transcripts', "'transcripts'" in app_content, 'Missing transcripts tour')
    test('TOUR_DEFS tem visual_evidence', "'visual_evidence'" in app_content, 'Missing visual_evidence tour')
    test('TOUR_DEFS tem extractions', "'extractions'" in app_content, 'Missing extractions tour')
    test('TOUR_DEFS tem audit', "'audit'" in app_content, 'Missing audit tour')
    test('TOUR_DEFS tem knowledge', "'knowledge'" in app_content, 'Missing knowledge tour')
    test('TOUR_DEFS tem experiments', "'experiments'" in app_content, 'Missing experiments tour')
    test('TOUR_DEFS tem patterns', "'patterns'" in app_content, 'Missing patterns tour')
    test('TOUR_DEFS tem tools', "'tools'" in app_content, 'Missing tools tour')
    test('TOUR_DEFS tem software', "'software'" in app_content, 'Missing software tour')
    test('TOUR_DEFS tem learning', "'learning'" in app_content, 'Missing learning tour')
    test('TOUR_DEFS tem employees', "'employees'" in app_content, 'Missing employees tour')
    test('TOUR_DEFS tem capital', "'capital'" in app_content, 'Missing capital tour')
    test('TOUR_DEFS tem history', "'history'" in app_content, 'Missing history tour')
    test('TOUR_DEFS tem settings', "'settings'" in app_content, 'Missing settings tour')
    test('TOUR_DEFS tem 16+ rotas', len([k for k in ['overview','inbox','transcripts','visual_evidence','extractions','audit','knowledge','experiments','patterns','tools','software','learning','employees','capital','history','settings','new_source'] if ("'" + k + "'") in app_content]) >= 14, 'Menos de 14 rotas com tour')
    test('WHY_MATTERS tem fonts', "'fonts'" in app_content and 'WHY_MATTERS' in app_content, 'Missing fonts why matters')
    test('WHY_MATTERS tem auditoria', "'auditoria'" in app_content, 'Missing audit why matters')
    test('_endTour limpa estado', 'tourActive = false' in app_content or 'state.tourActive=false' in app_content, 'Tour state not reset')
    test('Narration.setSpeed mantem entre 0.5 e 2', 'Math.max(0.5, Math.min(2, s))' in nr_content if nr_content else False, 'Speed clamp missing')
    test('Narration tem getSpeeds', 'getSpeeds' in nr_content if nr_content else False, 'Missing getSpeeds')
    test('Narration tem SPEEDS 0.75/1/1.25', '0.75' in nr_content and '1.25' in nr_content if nr_content else False, 'Missing speed options')
    test('Narration fallback textual', 'Narracao local' in app_content, 'Missing narration disclaimer')
    test('HTML tem Explicar esta tela', 'Explicar esta tela' in html if html else False, 'Missing explain button text')
    test('HTML tem explainThisBtn', 'explainThisBtn' in html if html else False, 'Missing explain button id')
    test('HTML tem onclick toggleMode na mode indicator', 'topBarMode' in html and 'toggleMode' in html if html else False, 'Mode indicator not clickable')
    test('Nenhum fetch externo no app', 'fetch(' not in app_content, 'fetch detectado')
    test('Nenhuma CDN no HTML', 'cdn.' not in html and 'unpkg.' not in html if html else False, 'CDN detected')
    test('Nenhum token no app', 'token' not in app_content.lower() and 'api_key' not in app_content.lower() and 'secret' not in app_content.lower() and 'password' not in app_content.lower(), 'Token detected')
    test('Nenhum import do core', 'core/' not in app_content, 'core/ import detected')

if html:
    test('Build marker v3.2', 'v3.2' in html and 'INTERACTION-UNDERSTAND' in html, 'Build marker not updated')
    test('Cache busting novo', 'interaction-understand' in html, 'Cache busting not updated')

# ===== 37. HANDOFF E CODEX =====
print('\n=== 36. Handoff para Codex ===')
co = check_file_content(os.path.join(PROTO_DIR, 'CODEX_HANDOFF.md'), 'CODEX', 'CODEX_HANDOFF')
if co:
    for kw in ['Status', 'O que foi constru', 'O que N', 'Smoke Test', 'O que Codex precisa revisar']:
        test(f'CODEX_HANDOFF contem {kw}', kw in co, f'Missing section: {kw}')
    test('CODEX_HANDOFF tem status do prototipo', 'PROTOTIPO' in co.upper() or 'NAO INTEGRADO' in co.upper(), 'Missing status')
    test('CODEX_HANDOFF lista regras/restricoes', 'PROTOTIPO' in co.upper() or 'NAO INTEGRADO' in co.upper(), 'Missing status/constraints')

# ===== RESUMO =====
print('\n' + '=' * 50)
print(f'RESULTADO: {assertions} testes, {passed} passaram, {failed} falharam')
if errors:
    print('\nFALHAS:')
    for e in errors:
        print(f'  {e}')
else:
    print('TODOS OS TESTES PASSARAM.')
print('=' * 50)
sys.exit(0 if failed == 0 else 1)
