import streamlit as st
import sys
import os
import time

# app.py lives inside backend/ — add backend/ to path so all submodules resolve
_HERE = os.path.dirname(os.path.abspath(__file__))   # .../backend
_ROOT = os.path.dirname(_HERE)                        # project root
for _p in [_HERE, _ROOT]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("TOP_K", "3")

# Load .env early so qa_pipeline module-level code finds GOOGLE_API_KEY on import
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Learn Mate",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session State ──────────────────────────────────────────────────────────────
for key, default in {
    "pipeline_ready":    False,
    "embedded_docs":     None,
    "doc_summary":       {},
    "available_sources": [],           # List of loaded source names (PDFs + YouTube URLs)
    "source_titles":     {},           # Map of source URL/filename to display title
    "selected_sources":  [],           # List of sources selected for quiz filtering
    "chat_history":      [],
    "processing":        False,
    "yt_inputs":         [""],
    "removed_pdf_ids":   [],
    "theme":             "dark",
    "theme_user_set":    False,
    # ── Quiz state ──────────────────────────────────────────────────────────
    "quiz_text":         "",
    "quiz_parsed":       [],
    "quiz_user_answers": {},
    "quiz_result":       None,
    "quiz_phase":        "config",   # config | answering | results
    "quiz_topic":        "",
    "quiz_num_q":        5,
    "quiz_difficulty":   "medium",
    "quiz_detail_qid":   None,         # selected question id in results modal
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Enforce dark on launch until the user explicitly toggles theme.
if not st.session_state.theme_user_set:
    st.session_state.theme = "dark"

# ── Theme toggle handler ───────────────────────────────────────────────────────
_is_dark = st.session_state.theme == "dark"

if st.button("☀ Light" if _is_dark else "🌙 Dark", key="theme_switch", help="Toggle theme"):
    st.session_state.theme = "light" if _is_dark else "dark"
    st.session_state.theme_user_set = True
    st.rerun()

theme_tokens = {
    "bg":        "#000000" if _is_dark else "#f7f9fc",
    "surface":   "#111111" if _is_dark else "#eef3f8",
    "card":      "#1a1a1a" if _is_dark else "#ffffff",
    "border":    "#2e2e2e" if _is_dark else "#d6dee8",
    "accent":    "#78b2ff" if _is_dark else "#2563eb",
    "accent2":   "#38d6c3" if _is_dark else "#0891b2",
    "accent3":   "#c4a7ff" if _is_dark else "#7c3aed",
    "text":      "#f5f5f5" if _is_dark else "#111827",
    "muted":     "#888888" if _is_dark else "#667085",
    "success":   "#4ade80" if _is_dark else "#059669",
    "warning":   "#fbbf24" if _is_dark else "#d97706",
    "shadow":    "0 1px 3px rgba(0,0,0,.8), 0 1px 2px rgba(0,0,0,.6)" if _is_dark else "0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.05)",
    "shadow_lg": "0 4px 16px rgba(0,0,0,.9), 0 2px 4px rgba(0,0,0,.7)" if _is_dark else "0 4px 16px rgba(0,0,0,.1), 0 2px 4px rgba(0,0,0,.06)",
    "pill_green_bg":      "rgba(74,222,128,.1)"   if _is_dark else "rgba(5,150,105,.08)",
    "pill_green_border":  "rgba(74,222,128,.3)"   if _is_dark else "rgba(5,150,105,.2)",
    "pill_blue_bg":       "rgba(120,178,255,.1)"  if _is_dark else "rgba(37,99,235,.08)",
    "pill_blue_border":   "rgba(120,178,255,.3)"  if _is_dark else "rgba(37,99,235,.2)",
    "pill_orange_bg":     "rgba(251,191,36,.1)"   if _is_dark else "rgba(217,119,6,.08)",
    "pill_orange_border": "rgba(251,191,36,.3)"   if _is_dark else "rgba(217,119,6,.2)",
    "pill_pink_bg":       "rgba(196,167,255,.1)"  if _is_dark else "rgba(124,58,237,.08)",
    "pill_pink_border":   "rgba(196,167,255,.3)"  if _is_dark else "rgba(124,58,237,.2)",
    "input_focus_shadow": "0 0 0 3px rgba(120,178,255,.25)" if _is_dark else "0 0 0 3px rgba(37,99,235,.12)",
    "link_hover_bg":      "rgba(56,214,195,.06)"  if _is_dark else "rgba(8,145,178,.06)",
    "btn_shadow":         "0 3px 12px rgba(0,0,0,.6)"  if _is_dark else "0 2px 8px rgba(37,99,235,.25)",
    "btn_shadow_hover":   "0 6px 18px rgba(0,0,0,.8)"  if _is_dark else "0 4px 14px rgba(37,99,235,.35)",
    "toggle_shadow":      "0 3px 12px rgba(0,0,0,.9)"  if _is_dark else "0 2px 10px rgba(0,0,0,.1)",
    "color_scheme":       "dark" if _is_dark else "light",
}

# ── Load fonts locally (fallback: try Google, then system fonts) ───────────────
import base64, pathlib

def _load_local_fonts() -> str:
    font_dir = pathlib.Path(__file__).parent.parent / "static" / "fonts"
    if not font_dir.exists():
        return ""
    faces = []
    specs = [
        ("poppins-300.woff2", "Poppins", "normal", 300),
        ("poppins-400.woff2", "Poppins", "normal", 400),
        ("poppins-500.woff2", "Poppins", "normal", 500),
        ("poppins-600.woff2", "Poppins", "normal", 600),
        ("poppins-700.woff2", "Poppins", "normal", 700),
    ]
    for fname, family, style, weight in specs:
        p = font_dir / fname
        if p.exists():
            b64 = base64.b64encode(p.read_bytes()).decode()
            faces.append(
                f"@font-face{{font-family:'{family}';font-style:{style};"
                f"font-weight:{weight};"
                f"src:url('data:font/woff2;base64,{b64}') format('woff2');}}"
            )
    return "\n".join(faces)

_local_fonts_css = _load_local_fonts()
_google_fonts_import = (
    ""
    if _local_fonts_css
    else "@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
""" + _google_fonts_import + """
""" + _local_fonts_css + """

:root {
    --serif-stack: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --mono-stack:  'Courier New', Courier, monospace;
}
:root {
    --bg:        #ffffff;
    --surface:   #f8f9fa;
    --card:      #f1f3f5;
    --border:    #dee2e6;
    --accent:    #2563eb;
    --accent2:   #0891b2;
    --accent3:   #7c3aed;
    --text:      #111827;
    --muted:     #6b7280;
    --success:   #059669;
    --warning:   #d97706;
    --mono:      'Courier New', Courier, monospace;
    --serif:     'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --shadow:    0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.05);
    --shadow-lg: 0 4px 16px rgba(0,0,0,.1), 0 2px 4px rgba(0,0,0,.06);
    --radius:    8px;
    --pill-green-bg: rgba(5,150,105,.08);
    --pill-green-border: rgba(5,150,105,.2);
    --pill-blue-bg: rgba(37,99,235,.08);
    --pill-blue-border: rgba(37,99,235,.2);
    --pill-orange-bg: rgba(217,119,6,.08);
    --pill-orange-border: rgba(217,119,6,.2);
    --pill-pink-bg: rgba(124,58,237,.08);
    --pill-pink-border: rgba(124,58,237,.2);
    --input-focus-shadow: 0 0 0 3px rgba(37,99,235,.12);
    --link-hover-bg: rgba(8,145,178,.06);
    --btn-shadow: 0 2px 8px rgba(37,99,235,.25);
    --btn-shadow-hover: 0 4px 14px rgba(37,99,235,.35);
    --toggle-shadow: 0 2px 10px rgba(0,0,0,.1);
}

html, body, [class*="css"] {
    font-family: var(--serif);
    background-color: var(--bg) !important;
    color: var(--text);
}

[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
section[data-testid="stSidebar"] > div,
.main, .main > div {
    background-color: var(--bg) !important;
}

[data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0.9rem 2.5rem 4rem; max-width: 1200px; }

.theme-toggle-wrapper {
    position: fixed;
    top: 14px;
    right: 18px;
    z-index: 9999;
}

[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child {
    display: none !important;
}

.hero {
    text-align: center;
    padding: 1.2rem 0 1.7rem;
}
.hero-badge {
    display: inline-block;
    font-family: var(--mono);
    font-size: 0.62rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--accent2);
    border: 1px solid var(--accent2);
    padding: 0.28rem 0.85rem;
    border-radius: 2px;
    margin-bottom: 1.1rem;
    opacity: 0.85;
}
.hero h1 {
    font-family: var(--serif);
    font-size: 3rem;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: var(--text);
    margin: 0 0 0.5rem;
    line-height: 1.05;
}
.hero h1 span {
    color: var(--accent);
    font-style: normal;
}
.hero p {
    color: var(--muted);
    font-family: var(--mono);
    font-size: 0.72rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin: 0;
}

.divider {
    height: 1px;
    background: var(--border);
    margin: 0.55rem 0 0.8rem;
    opacity: 0.7;
}

.section-label {
    font-family: var(--mono);
    font-size: 0.6rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

.info-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.5rem;
    font-size: 0.84rem;
    box-shadow: var(--shadow);
    color: var(--text);
    transition: border-color 0.2s, transform 0.12s;
}
.info-card:hover {
    border-color: var(--accent);
    transform: translateY(-1px);
}
.info-card .label {
    font-family: var(--mono);
    font-size: 0.58rem;
    letter-spacing: 0.16em;
    color: var(--muted);
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}

.pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.68rem;
    font-family: var(--mono);
    padding: 0.22rem 0.75rem;
    border-radius: 20px;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
}
.pill-green  { background: var(--pill-green-bg);  color: var(--success); border: 1px solid var(--pill-green-border); }
.pill-blue   { background: var(--pill-blue-bg);   color: var(--accent);  border: 1px solid var(--pill-blue-border); }
.pill-orange { background: var(--pill-orange-bg); color: var(--warning); border: 1px solid var(--pill-orange-border); }
.pill-pink   { background: var(--pill-pink-bg);   color: var(--accent3); border: 1px solid var(--pill-pink-border); }

.answer-box {
    background: var(--card);
    border: 1px solid var(--border);
    border-top: 3px solid var(--accent);
    border-radius: var(--radius);
    padding: 1.3rem 1.5rem;
    font-size: 0.95rem;
    line-height: 1.8;
    color: var(--text);
    margin-top: 0.8rem;
    box-shadow: var(--shadow);
}

.user-bubble {
    text-align: right;
    margin-bottom: 0.5rem;
}
.user-bubble span {
    background: var(--accent);
    color: #fff;
    border-radius: 16px 16px 4px 16px;
    padding: 0.48rem 1.05rem;
    display: inline-block;
    font-size: 0.88rem;
    max-width: 80%;
    font-family: var(--serif);
    font-weight: 300;
    line-height: 1.5;
}

.source-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.6rem 0.95rem;
    margin-bottom: 0.45rem;
    transition: border-color .2s, box-shadow .2s;
    box-shadow: var(--shadow);
}
.source-item:hover {
    border-color: var(--accent2);
    box-shadow: var(--shadow-lg);
}
.source-icon {
    font-size: 0.95rem;
    width: 26px;
    text-align: center;
    flex-shrink: 0;
}
.source-link {
    font-family: var(--mono);
    font-size: 0.72rem;
    color: var(--accent2);
    text-decoration: none;
    word-break: break-all;
}

.pipeline-step {
    display: flex;
    align-items: flex-start;
    gap: 0.9rem;
    padding: 0.65rem 0;
    border-bottom: 1px solid var(--border);
}
.pipeline-step:last-child { border-bottom: none; }
.step-num {
    font-family: var(--mono);
    font-size: 0.6rem;
    color: var(--accent);
    width: 20px;
    flex-shrink: 0;
    padding-top: 2px;
    font-weight: 600;
}
.step-text {
    font-size: 0.84rem;
    color: var(--text);
    font-family: var(--serif);
    font-weight: 500;
}
.step-sub  { font-family: var(--mono); font-size: 0.68rem; color: var(--muted); margin-top: 0.12rem; }

.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--text) !important;
    font-family: var(--serif) !important;
    font-size: 0.9rem !important;
    box-shadow: var(--shadow) !important;
    transition: border-color .2s, box-shadow .2s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: var(--input-focus-shadow) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: var(--muted) !important;
    opacity: 0.92 !important;
}

.stButton > button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: var(--mono) !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 0.55rem 1.4rem !important;
    transition: opacity .15s, transform .12s, box-shadow .15s !important;
    box-shadow: var(--btn-shadow) !important;
    font-weight: 600 !important;
}
.stButton > button:hover {
    opacity: .88 !important;
    transform: translateY(-1px) !important;
    box-shadow: var(--btn-shadow-hover) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
    opacity: 1 !important;
}

button[kind="secondary"],
.stButton > button[data-testid*="clear"],
.stButton > button[data-testid*="reset"] {
    background: var(--card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow) !important;
}
.stButton > button[data-testid*="del"] {
    background: transparent !important;
    color: var(--muted) !important;
    border: 1px solid var(--border) !important;
    box-shadow: none !important;
    padding: 0.3rem 0.6rem !important;
    font-size: 0.8rem !important;
}
.stButton > button[data-testid*="del"]:hover {
    color: var(--accent3) !important;
    border-color: var(--accent3) !important;
    box-shadow: none !important;
}

[data-testid="stFileUploader"] {
    background: var(--card);
    border: 1.5px dashed var(--border);
    border-radius: var(--radius);
    padding: 0.6rem;
    transition: border-color .2s;
    box-shadow: var(--shadow);
}
[data-testid="stFileUploader"]:hover { border-color: var(--accent2); }
[data-testid="stFileUploaderFile"] { display: none !important; }
[data-testid="stFileUploaderDropzone"] {
    background: var(--card) !important;
    border: 1px dashed var(--border) !important;
}
[data-testid="stFileUploaderDropzone"] * { color: var(--text) !important; }
[data-testid="stFileUploaderDropzoneInstructions"] { color: var(--muted) !important; }
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
}

[data-testid="stExpander"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    box-shadow: var(--shadow) !important;
}
[data-testid="stExpander"] summary {
    font-family: var(--mono);
    font-size: 0.75rem;
    color: var(--muted);
    letter-spacing: 0.05em;
}

.stProgress > div > div > div { background: var(--accent) !important; }
.stProgress > div > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 999px !important;
    padding: 1px !important;
}
[data-testid="stProgress"] [data-testid="stMarkdownContainer"],
[data-testid="stProgress"] p,
[data-testid="stProgress"] span {
    color: var(--text) !important;
    opacity: 1 !important;
    font-family: var(--mono) !important;
}

[data-testid="stMetric"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 0.8rem 1rem !important;
    box-shadow: var(--shadow) !important;
}
[data-testid="stMetricLabel"] {
    font-family: var(--mono) !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--serif) !important;
    font-size: 1.8rem !important;
    color: var(--text) !important;
    font-weight: 500 !important;
}

[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid var(--border);
    gap: 0;
}
[data-testid="stTabs"] button[role="tab"] {
    font-family: var(--mono) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
    padding: 0.7rem 1.2rem !important;
    border-bottom: none !important;
    transition: color .2s !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--accent) !important;
}
[data-testid="stTabs"] button[role="tab"]:hover { color: var(--text) !important; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background: var(--accent) !important;
    height: 3px !important;
}

[data-testid="stLinkButton"] > a {
    background: var(--card) !important;
    color: var(--accent2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 5px !important;
    font-family: var(--mono) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.04em !important;
    padding: 0.42rem 0.9rem !important;
    text-align: left !important;
    justify-content: flex-start !important;
    transition: border-color .2s, background .2s !important;
    box-shadow: var(--shadow) !important;
}
[data-testid="stLinkButton"] > a:hover {
    border-color: var(--accent2) !important;
    background: var(--link-hover-bg) !important;
}

[data-testid="stStatusWidget"] {
    background: linear-gradient(180deg, var(--card), var(--surface)) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    box-shadow: var(--shadow-lg) !important;
}
[data-testid="stStatusWidget"],
[data-testid="stStatusWidget"] * {
    color: var(--text) !important;
    opacity: 1 !important;
}
[data-testid="stStatusWidget"] [data-testid="stStatusWidgetLabel"] {
    font-family: var(--mono) !important;
    letter-spacing: 0.05em !important;
}
[data-testid="stStatusWidget"] [data-testid="stMarkdownContainer"],
[data-testid="stStatusWidget"] [data-testid="stMarkdownContainer"] p,
[data-testid="stStatusWidget"] [data-testid="stMarkdownContainer"] li,
[data-testid="stStatusWidget"] [data-testid="stMarkdownContainer"] span,
[data-testid="stStatusWidget"] [data-testid="stMarkdownContainer"] div {
    color: var(--text) !important;
    opacity: 1 !important;
}

[data-testid="stAlert"] {
    border-radius: var(--radius) !important;
    font-family: var(--mono) !important;
    font-size: 0.8rem !important;
}

.notice {
    font-family: var(--mono);
    font-size: 0.7rem;
    color: var(--muted);
    letter-spacing: 0.05em;
    padding: 0.5rem 0;
    line-height: 1.7;
}

.status-line {
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: 0.8rem !important;
    line-height: 1.7 !important;
    letter-spacing: 0.01em;
    opacity: 1 !important;
}
.status-line-ok {
    color: var(--accent2) !important;
    font-weight: 600;
}

[data-testid="stProgress"] p,
[data-testid="stProgress"] span,
[data-testid="stProgress"] div,
.stProgress p,
.stProgress span,
.stProgress div {
    color: var(--text) !important;
    opacity: 1 !important;
    font-family: var(--mono) !important;
    font-size: 0.78rem !important;
}

[data-testid="stStatusWidget"] p,
[data-testid="stStatusWidget"] span,
[data-testid="stStatusWidget"] li,
[data-testid="stStatusWidget"] div,
[data-testid="stStatusWidget"] label,
[data-testid="stStatusWidget"] small,
[data-testid="stStatusWidget"] [style*="opacity"],
[data-testid="stStatusWidget"] [style*="color"] {
    color: var(--text) !important;
    opacity: 1 !important;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--surface); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }

.st-key-theme_switch { display: inline-block; float: right; margin: 0 !important; }
.st-key-theme_switch > div { margin: 0 !important; }
.st-key-theme_switch button {
    background: var(--card);
    border: 1.5px solid var(--border);
    border-radius: 50px;
    padding: 6px 14px 6px 10px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    box-shadow: var(--toggle-shadow);
    transition: border-color 0.2s, color 0.2s, box-shadow 0.2s;
    text-decoration: none;
    user-select: none;
}
.st-key-theme_switch button:hover {
    border-color: var(--accent);
    color: var(--accent);
    box-shadow: 0 3px 14px rgba(37,99,235,0.18);
}

/* ── Number input (quiz question count) ── */
[data-testid="stNumberInput"] input {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--text) !important;
    font-family: var(--serif) !important;
    box-shadow: var(--shadow) !important;
}
[data-testid="stNumberInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: var(--input-focus-shadow) !important;
}

/* ── Radio buttons (quiz answer options) ── */
[data-testid="stRadio"] label {
    font-family: var(--mono) !important;
    font-size: 0.78rem !important;
    color: var(--text) !important;
}
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    font-family: var(--mono) !important;
    font-size: 0.78rem !important;
    color: var(--text) !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<style>
:root {{
    color-scheme: {theme_tokens['color_scheme']};
    --bg: {theme_tokens['bg']};
    --surface: {theme_tokens['surface']};
    --card: {theme_tokens['card']};
    --border: {theme_tokens['border']};
    --accent: {theme_tokens['accent']};
    --accent2: {theme_tokens['accent2']};
    --accent3: {theme_tokens['accent3']};
    --text: {theme_tokens['text']};
    --muted: {theme_tokens['muted']};
    --success: {theme_tokens['success']};
    --warning: {theme_tokens['warning']};
    --shadow: {theme_tokens['shadow']};
    --shadow-lg: {theme_tokens['shadow_lg']};
    --pill-green-bg: {theme_tokens['pill_green_bg']};
    --pill-green-border: {theme_tokens['pill_green_border']};
    --pill-blue-bg: {theme_tokens['pill_blue_bg']};
    --pill-blue-border: {theme_tokens['pill_blue_border']};
    --pill-orange-bg: {theme_tokens['pill_orange_bg']};
    --pill-orange-border: {theme_tokens['pill_orange_border']};
    --pill-pink-bg: {theme_tokens['pill_pink_bg']};
    --pill-pink-border: {theme_tokens['pill_pink_border']};
    --input-focus-shadow: {theme_tokens['input_focus_shadow']};
    --link-hover-bg: {theme_tokens['link_hover_bg']};
    --btn-shadow: {theme_tokens['btn_shadow']};
    --btn-shadow-hover: {theme_tokens['btn_shadow_hover']};
    --toggle-shadow: {theme_tokens['toggle_shadow']};
}}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def extract_link_from_source(citation) -> str:
    if isinstance(citation, dict):
        ctype = citation.get("type", "")
        if ctype == "YouTube":
            return citation.get("link", "")
        elif ctype == "PDF":
            return citation.get("file", "") or citation.get("filename", "")
        return citation.get("link", citation.get("display", str(citation)))
    return str(citation)

def is_youtube(link: str) -> bool:
    return "youtube.com" in link or "youtu.be" in link

def source_icon(link: str) -> str:
    if is_youtube(link):
        return "▶"
    if link.lower().endswith(".pdf") or "pdf" in link.lower():
        return "📄"
    return "🔗"


@st.cache_resource
def load_qa_modules():
    from rag.qa_pipeline import qa_pipeline
    from rag.citation_handler import format_citations
    return qa_pipeline, format_citations


# ── Quiz helpers (inline — no separate file needed) ───────────────────────────
def _pill(text: str, variant: str = "blue") -> str:
    return f'<span class="pill pill-{variant}">{text}</span>'

def _section(label: str) -> None:
    st.markdown(f'<div class="section-label">{label}</div>', unsafe_allow_html=True)

def _divider() -> None:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

def _card_html(body: str, label: str = "") -> str:
    lbl = f'<div class="label">{label}</div>' if label else ""
    return f'<div class="info-card">{lbl}{body}</div>'

def _notice(text: str) -> None:
    st.markdown(f'<div class="notice">{text}</div>', unsafe_allow_html=True)

def _status_line(text: str, ok: bool = False) -> None:
    cls = "status-line status-line-ok" if ok else "status-line"
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-label">System</div>', unsafe_allow_html=True)

    if st.session_state.pipeline_ready:
        st.markdown(
            '<span class="pill pill-green">● Pipeline Ready</span>',
            unsafe_allow_html=True,
        )
        s = st.session_state.doc_summary
        st.markdown("<br>", unsafe_allow_html=True)

        cols = st.columns(2)
        with cols[0]:
            st.metric("PDFs", s.get("pdf_count", "—"))
        with cols[1]:
            st.metric("Videos", s.get("youtube_count", "—"))

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f'<div class="info-card"><div class="label">Total chunks</div>{s.get("total_chunks","—")}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="info-card"><div class="label">Embedded docs</div>{s.get("embedded_count","—")}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("↺  Reset pipeline"):
            for k in ("pipeline_ready", "embedded_docs", "doc_summary", "chat_history", "processing", "available_sources", "source_titles", "selected_sources"):
                st.session_state[k] = False if isinstance(st.session_state[k], bool) else (
                    [] if isinstance(st.session_state[k], list) else
                    ({} if isinstance(st.session_state[k], dict) else None)
                )
            # Also reset quiz state when pipeline is reset
            for k in ("quiz_text", "quiz_parsed", "quiz_user_answers", "quiz_result"):
                st.session_state[k] = "" if k == "quiz_text" else ([] if k == "quiz_parsed" else ({} if k == "quiz_user_answers" else None))
            st.session_state.quiz_phase = "config"
            st.rerun()
    else:
        st.markdown(
            '<span class="pill pill-blue">○ Not Ready</span>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div class="notice">Add sources in the main panel and run the pipeline to enable Q&amp;A and Quizzes.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Pipeline Steps</div>', unsafe_allow_html=True)
    steps = [
        ("01", "Load Sources",  "PDFs + YouTube transcripts"),
        ("02", "Clean",         "Normalise & de-noise text"),
        ("03", "Chunk",         "Split into semantic windows"),
        ("04", "Embed",         "Vector representations"),
        ("05", "QA / Quiz",     "Retrieve & generate answers"),
    ]
    for num, title, sub in steps:
        st.markdown(
            f"""<div class="pipeline-step">
                  <span class="step-num">{num}</span>
                  <div><div class="step-text">{title}</div>
                  <div class="step-sub">{sub}</div></div>
                </div>""",
            unsafe_allow_html=True,
        )


# ── Main Layout ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-badge">Your AI Study Companion</div>
  <h1><span>Learn</span> Mate</h1>
  <p>Multi-source · PDF &amp; Video · Semantic Q&amp;A · Quiz</p>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_ingest, tab_qa, tab_quiz = st.tabs([
    "⬆  Sources & Ingest",
    "💬  Ask Questions",
    "📝  Quiz",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — INGEST
# ═══════════════════════════════════════════════════════════════════════════════
with tab_ingest:
    col_pdf, col_yt = st.columns(2, gap="large")

    # ── PDF column ────────────────────────────────────────────────────────────
    with col_pdf:
        st.markdown('<div class="section-label">PDF Documents</div>', unsafe_allow_html=True)
        uploaded_pdfs = st.file_uploader(
            "Drop PDFs here",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload one or more PDF files to include in the knowledge base.",
            label_visibility="collapsed",
        )

        uploaded_pdfs = uploaded_pdfs or []
        all_pdf_ids = [f"{f.name}:{f.size}" for f in uploaded_pdfs]
        st.session_state.removed_pdf_ids = [
            pid for pid in st.session_state.removed_pdf_ids if pid in all_pdf_ids
        ]

        active_uploaded_pdfs = []
        for f in uploaded_pdfs:
            pdf_id = f"{f.name}:{f.size}"
            if pdf_id not in st.session_state.removed_pdf_ids:
                active_uploaded_pdfs.append((pdf_id, f))

        if active_uploaded_pdfs:
            for idx, (pdf_id, f) in enumerate(active_uploaded_pdfs):
                card_col, del_col = st.columns([12, 1], vertical_alignment="center")
                with card_col:
                    st.markdown(
                        f'<div class="info-card">📄 <strong>{f.name}</strong>'
                        f'<span style="float:right;color:var(--muted);font-family:var(--mono);font-size:.72rem">'
                        f'{f.size/1024:.1f} KB</span></div>',
                        unsafe_allow_html=True,
                    )
                with del_col:
                    if st.button("✕", key=f"rm_pdf_{idx}"):
                        st.session_state.removed_pdf_ids.append(pdf_id)
                        st.rerun()

    # ── YouTube column ────────────────────────────────────────────────────────
    with col_yt:
        st.markdown('<div class="section-label">YouTube Videos</div>', unsafe_allow_html=True)

        def render_yt_inputs():
            for i, url in enumerate(st.session_state.yt_inputs):
                cols = st.columns([10, 1])
                with cols[0]:
                    new_val = st.text_input(
                        f"URL {i+1}",
                        value=url,
                        key=f"yt_{i}",
                        placeholder="https://www.youtube.com/watch?v=...",
                        label_visibility="collapsed",
                    )
                    st.session_state.yt_inputs[i] = new_val
                with cols[1]:
                    if len(st.session_state.yt_inputs) > 1:
                        if st.button("✕", key=f"del_{i}"):
                            st.session_state.yt_inputs.pop(i)
                            st.rerun()

        render_yt_inputs()

        if st.button("+ Add another URL"):
            st.session_state.yt_inputs.append("")
            st.rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Run pipeline ──────────────────────────────────────────────────────────
    col_btn, col_hint = st.columns([3, 7])
    with col_btn:
        run_btn = st.button("▶  Run Pipeline", use_container_width=True)
    with col_hint:
        st.markdown(
            '<div class="notice" style="padding-top:.9rem">Loads, cleans, chunks, and embeds all sources.</div>',
            unsafe_allow_html=True,
        )

    if run_btn:
        yt_urls   = [u.strip() for u in st.session_state.yt_inputs if u.strip()]
        pdf_paths = []

        if active_uploaded_pdfs:
            import tempfile
            tmp_dir = tempfile.mkdtemp()
            for _, f in active_uploaded_pdfs:
                tmp_path = os.path.join(tmp_dir, f.name)
                with open(tmp_path, "wb") as out:
                    out.write(f.read())
                pdf_paths.append(tmp_path)

        if not pdf_paths and not yt_urls:
            st.error("Please add at least one PDF or YouTube URL before running.")
        else:
            try:
                from ingestion.document_manager import DocumentManager
                from processing.transcript_cleaner import clean_documents
                from processing.chunking import chunk_documents
                from embeddings.embedding_model import EmbeddingModel

                progress_bar = st.progress(0, text="Starting pipeline…")

                with st.status("Running pipeline…", expanded=True) as status:

                    st.markdown('<div class="status-line">📥 Loading sources - may take a moment for YouTube videos...</div>', unsafe_allow_html=True)
                    progress_bar.progress(5, text="📥  Loading sources…")
                    manager   = DocumentManager()
                    documents = manager.load_all_sources(
                        pdf_paths=pdf_paths,
                        youtube_urls=yt_urls,
                    )
                    progress_bar.progress(20, text="📥  Sources loaded!")
                    st.markdown(
                        f'<div class="status-line status-line-ok">✅ Loaded {len(documents)} document(s)</div>',
                        unsafe_allow_html=True,
                    )

                    if not documents:
                        status.update(label="❌ No documents loaded", state="error")
                        progress_bar.empty()
                        st.stop()

                    raw_summary = manager.summarize(documents)

                    st.markdown('<div class="status-line">🧹 Cleaning and normalising text...</div>', unsafe_allow_html=True)
                    progress_bar.progress(30, text="🧹  Cleaning text…")
                    clean_docs = clean_documents(documents)
                    progress_bar.progress(45, text="🧹  Text cleaned!")
                    st.markdown('<div class="status-line status-line-ok">✅ Text cleaned</div>', unsafe_allow_html=True)

                    st.markdown('<div class="status-line">✂️ Chunking documents...</div>', unsafe_allow_html=True)
                    progress_bar.progress(50, text="✂️  Chunking…")
                    chunks = chunk_documents(clean_docs)
                    progress_bar.progress(62, text=f"✂️  {len(chunks)} chunks created!")
                    st.markdown(
                        f'<div class="status-line status-line-ok">✅ Created {len(chunks)} chunks</div>',
                        unsafe_allow_html=True,
                    )

                    st.markdown('<div class="status-line">🧠 Generating embeddings - this is the slow step...</div>', unsafe_allow_html=True)
                    progress_bar.progress(65, text="🧠  Embedding…")
                    embedding_model = EmbeddingModel()
                    embedded_docs   = embedding_model.embed_documents(chunks)
                    progress_bar.progress(95, text="🧠  Embeddings ready!")
                    st.markdown(
                        f'<div class="status-line status-line-ok">✅ Embedded {len(embedded_docs)} documents</div>',
                        unsafe_allow_html=True,
                    )

                    progress_bar.progress(100, text="✅  Pipeline complete!")
                    status.update(
                        label="✅ Pipeline complete — go to Ask Questions or Quiz tab!",
                        state="complete",
                        expanded=False,
                    )

                st.session_state.embedded_docs  = embedded_docs
                st.session_state.pipeline_ready = True
                # Deduplicate sources (set removes duplicates, then convert to sorted list for consistency)
                unique_sources = sorted(list(set(raw_summary.get("sources", []))))
                st.session_state.available_sources = unique_sources
                st.session_state.source_titles = raw_summary.get("source_titles", {})
                st.session_state.selected_sources = unique_sources  # Default: all sources selected
                st.session_state.doc_summary    = {
                    "pdf_count":      len(pdf_paths),
                    "youtube_count":  len(yt_urls),
                    "total_chunks":   len(chunks),
                    "embedded_count": len(embedded_docs),
                }

                time.sleep(1.2)
                st.rerun()

            except Exception as e:
                progress_bar.empty()
                st.error(f"❌ Pipeline error: {e}")
                st.exception(e)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Q&A
# ═══════════════════════════════════════════════════════════════════════════════
with tab_qa:
    if not st.session_state.pipeline_ready:
        st.markdown(
            '<div class="answer-box" style="border-top-color:var(--accent2);text-align:center;color:var(--muted)">'
            'Pipeline not ready. Add sources and run ingest first.'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        if st.session_state.chat_history:
            st.markdown('<div class="section-label">Conversation</div>', unsafe_allow_html=True)
            for entry in st.session_state.chat_history:
                st.markdown(
                    f'<div class="user-bubble"><span>{entry["question"]}</span></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="answer-box">{entry["answer"]}</div>',
                    unsafe_allow_html=True,
                )
                if entry.get("sources"):
                    with st.expander(f"📎  {len(entry['sources'])} source(s)  — click to expand"):
                        for src in entry["sources"]:
                            stype   = src.get("type", "")
                            display = src.get("display", "")
                            link    = src.get("link", "")
                            fname   = src.get("file", "")

                            if stype == "YouTube" and link:
                                label = f"▶  {display}" if display else link
                                label = label if len(label) <= 70 else label[:67] + "..."
                                st.link_button(label, link, use_container_width=True)
                            elif stype == "PDF":
                                pdf_label = fname or src.get("filename", "") or src.get("display", "Document")
                                page = src.get("page", "N/A")
                                st.markdown(
                                    f'<div class="source-item">'
                                    f'<span class="source-icon">📄</span>'
                                    f'<span style="font-family:var(--mono);font-size:.72rem;color:var(--text)">'
                                    f'{pdf_label} — Page {page}</span>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(
                                    f'<div class="source-item">'
                                    f'<span class="source-icon">🔗</span>'
                                    f'<span style="font-family:var(--mono);font-size:.72rem;color:var(--muted)">{display}</span>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )
                st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="section-label">Ask</div>', unsafe_allow_html=True)
        question = st.text_area(
            "Question",
            placeholder="What would you like to know from your documents and videos?",
            height=90,
            label_visibility="collapsed",
        )

        col_ask, col_clear = st.columns([3, 1])
        with col_ask:
            ask_btn = st.button("Ask →", use_container_width=True)
        with col_clear:
            if st.button("Clear history", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

        if ask_btn and question.strip():
            with st.spinner("🔍  Searching knowledge base & generating answer…"):
                try:
                    qa_pipeline, format_citations = load_qa_modules()

                    answer, sources = qa_pipeline(
                        question.strip(),
                        st.session_state.embedded_docs,
                    )
                    citations = format_citations(sources)

                    links = []
                    for doc in sources:
                        meta     = doc.get("metadata", {})
                        src_type = meta.get("source", "unknown")
                        if src_type == "youtube":
                            links.append({
                                "type":      "YouTube",
                                "title":     meta.get("title", "YouTube Video"),
                                "timestamp": meta.get("timestamp", "N/A"),
                                "link":      meta.get("link", meta.get("video_url", "")),
                                "display":   f"{meta.get('title','YouTube Video')} ({meta.get('timestamp','N/A')})"
                            })
                        elif src_type == "pdf":
                            fname = (meta.get("filename")
                                     or meta.get("file_name")
                                     or meta.get("file")
                                     or "Document")
                            page = meta.get("page", "N/A")
                            links.append({
                                "type":    "PDF",
                                "file":    fname,
                                "page":    page,
                                "display": f"{fname} — Page {page}"
                            })
                        else:
                            links.append({
                                "type":    src_type,
                                "display": meta.get("title", str(meta))
                            })
                    links = links[:3]

                    cant_answer = "i don't have enough information" in answer.lower()
                    st.session_state.chat_history.append({
                        "question": question.strip(),
                        "answer":   answer.strip(),
                        "sources":  [] if cant_answer else links,
                    })
                    st.rerun()

                except Exception as e:
                    st.error(f"QA error: {e}")

        elif ask_btn:
            st.warning("Please enter a question.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — QUIZ
# ═══════════════════════════════════════════════════════════════════════════════
with tab_quiz:

    # ── Gate ─────────────────────────────────────────────────────────────────
    if not st.session_state.pipeline_ready:
        st.markdown(
            '<div class="answer-box" style="border-top-color:var(--accent2);'
            'text-align:center;color:var(--muted)">'
            'Pipeline not ready. Add sources and run ingest first.'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── Phase breadcrumb ─────────────────────────────────────────────────────
    else:
        phase      = st.session_state.quiz_phase
        active_idx = {"config": 0, "answering": 1, "results": 2}.get(phase, 0)
        crumb_labels = ("01 Configure", "02 Answer", "03 Results")

        crumb_html = '<div style="display:flex;gap:1.2rem;margin-bottom:1rem;align-items:center">'
        for i, label in enumerate(crumb_labels):
            if i == active_idx:
                crumb_html += f'<span class="pill pill-blue">{label}</span>'
            elif i < active_idx:
                crumb_html += f'<span class="pill pill-green">{label}</span>'
            else:
                crumb_html += (
                    f'<span style="font-family:var(--mono);font-size:.65rem;'
                    f'letter-spacing:.1em;text-transform:uppercase;color:var(--muted)">'
                    f'{label}</span>'
                )
            if i < 2:
                crumb_html += '<span style="color:var(--border);font-size:.8rem">→</span>'
        crumb_html += '</div>'
        st.markdown(crumb_html, unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════
        # PHASE 1 — CONFIG
        # ══════════════════════════════════════════════════════════════════════
        if phase == "config":

            _section("Quiz Configuration")

            col_topic, col_right = st.columns([5, 3], gap="large")

            with col_topic:
                quiz_topic = st.text_input(
                    "Topic",
                    value=st.session_state.quiz_topic,
                    placeholder="e.g. Gradient Descent, Transformers, Neural Networks…",
                    label_visibility="collapsed",
                    key="quiz_topic_input",
                )
                _notice("Enter the subject you want to be tested on.")

            with col_right:
                quiz_num_q = st.number_input(
                    "Number of questions",
                    min_value=1,
                    max_value=20,
                    value=st.session_state.quiz_num_q,
                    step=1,
                    key="quiz_num_q_input",
                )

            _section("Difficulty")
            diff_cols   = st.columns(4)
            diff_labels = ["Easy",  "Medium", "Hard",  "Dynamic"]
            diff_vals   = ["easy",  "medium", "hard",  "dynamic"]

            if st.session_state.quiz_difficulty == "mix":
                st.session_state.quiz_difficulty = "dynamic"

            for col, label, val in zip(diff_cols, diff_labels, diff_vals):
                with col:
                    is_sel = st.session_state.quiz_difficulty == val
                    if st.button(
                        label,
                        key=f"diff_{val}",
                        use_container_width=True,
                        type="primary" if is_sel else "secondary",
                    ):
                        st.session_state.quiz_difficulty = val
                        st.rerun()

            _divider()
            _section("Source Filter  (optional)")
            
            available_sources = st.session_state.available_sources
            source_titles = st.session_state.source_titles
            
            if available_sources:
                _notice(f"Select sources ({len(available_sources)} available):")
                
                # Create columns for checkbox layout
                cols = st.columns(2)
                selected = []
                
                for idx, source in enumerate(available_sources):
                    col_idx = idx % 2
                    with cols[col_idx]:
                        # Get display title from mapping, with icon
                        if source.startswith("http"):
                            # YouTube URL
                            title = source_titles.get(source, "YouTube Video")
                            display_name = f"📺 {title}"
                        else:
                            # PDF filename
                            title = source_titles.get(source, source)
                            display_name = f"📄 {title}"
                        
                        if st.checkbox(display_name, value=True, key=f"source_check_{idx}"):
                            selected.append(source)
                
                st.session_state.selected_sources = selected if selected else available_sources
            else:
                _notice("No sources loaded yet. Go to Ingest tab to add PDFs or YouTube videos.")
                st.session_state.selected_sources = []

            _divider()

            col_btn, col_hint = st.columns([3, 7])
            with col_btn:
                gen_btn = st.button("▶  Generate Quiz", use_container_width=True)
            with col_hint:
                _notice("Retrieves relevant content and generates multiple-choice questions.")

            if gen_btn:
                topic_val   = quiz_topic.strip()
                sources_val = st.session_state.selected_sources or None

                if not topic_val:
                    st.error("Please enter a topic before generating.")
                else:
                    st.session_state.quiz_topic = topic_val
                    st.session_state.quiz_num_q = int(quiz_num_q)

                    try:
                        from quiz.quiz_generator import QuizGenerator
                        from quiz.scoring import QuizScorer

                        progress_bar = st.progress(0, text="Starting quiz generation…")

                        with st.status("Generating quiz…", expanded=True) as status:

                            _status_line("🔍  Retrieving relevant chunks from the knowledge base…")
                            progress_bar.progress(15, text="🔍  Retrieving context…")

                            generator = QuizGenerator()
                            progress_bar.progress(35, text="🧠  Calling language model…")
                            _status_line("🧠  Generating questions with the language model…")

                            quiz_text = generator.generate_quiz(
                                query         = topic_val,
                                embedded_docs = st.session_state.embedded_docs,
                                num_questions = int(quiz_num_q),
                                difficulty    = st.session_state.quiz_difficulty,
                                sources       = sources_val,
                            )

                            progress_bar.progress(75, text="✂️  Parsing questions…")
                            _status_line("✂️  Parsing and validating questions…")

                            scorer = QuizScorer()
                            parsed = scorer.parse_quiz(quiz_text)

                            if not parsed:
                                status.update(label="❌ Could not parse quiz output", state="error")
                                progress_bar.empty()
                                st.error("The model returned an unexpected format. Try a different topic or retry.")
                            else:
                                progress_bar.progress(100, text="✅  Quiz ready!")
                                _status_line(f"✅  Generated {len(parsed)} question(s)", ok=True)
                                status.update(
                                    label=f"✅  Quiz ready — {len(parsed)} questions!",
                                    state="complete",
                                    expanded=False,
                                )

                                st.session_state.quiz_text         = quiz_text
                                st.session_state.quiz_parsed       = parsed
                                st.session_state.quiz_user_answers = {}
                                st.session_state.quiz_result       = None
                                st.session_state.quiz_detail_qid   = None
                                st.session_state.quiz_phase        = "answering"
                                st.rerun()

                    except Exception as e:
                        st.error(f"❌ Quiz generation error: {e}")
                        st.exception(e)

        # ══════════════════════════════════════════════════════════════════════
        # PHASE 2 — ANSWERING
        # ══════════════════════════════════════════════════════════════════════
        elif phase == "answering":

            parsed   = st.session_state.quiz_parsed
            num_q    = len(parsed)
            diff     = st.session_state.quiz_difficulty.capitalize()
            topic    = st.session_state.quiz_topic

            header_col, reset_col = st.columns([7, 2])
            with header_col:
                _section(f"Quiz · {topic}")
                st.markdown(
                    _pill(f"{num_q} Questions", "blue") + "&nbsp;&nbsp;" +
                    _pill(diff, {"Easy":"green","Medium":"blue","Hard":"pink","Dynamic":"orange","Mix":"orange"}.get(diff,"blue")),
                    unsafe_allow_html=True,
                )
                st.markdown("<br>", unsafe_allow_html=True)
            with reset_col:
                if st.button("↺  New Quiz", use_container_width=True):
                    st.session_state.quiz_phase = "config"
                    st.rerun()

            user_answers = st.session_state.quiz_user_answers

            for q in parsed:
                qid   = q["id"]
                raw   = q["question"]
                lines = raw.strip().split("\n")

                # Parse question text and options
                q_text  = ""
                options = []

                def _is_option_line(text: str) -> bool:
                    return bool(text and len(text) > 1 and text[0] in "ABCDabcd" and text[1] in ".):")

                for line in lines:
                    stripped = line.strip()
                    if stripped.lower().startswith("question"):
                        parts = stripped.split(":", 1)
                        if len(parts) > 1:
                            q_text = parts[1].strip()
                    elif _is_option_line(stripped):
                        options.append(stripped)
                    # Answer: lines intentionally skipped (hidden from user)

                # Handle formats where the question header is on one line and
                # the actual question text is on the next non-option line.
                if not q_text:
                    for i, line in enumerate(lines):
                        stripped = line.strip()
                        if stripped.lower().startswith("question"):
                            for candidate in lines[i + 1:]:
                                candidate = candidate.strip()
                                if not candidate:
                                    continue
                                if candidate.lower().startswith("answer"):
                                    continue
                                if _is_option_line(candidate):
                                    continue
                                q_text = candidate
                                break
                            if q_text:
                                break

                if not q_text:
                    for candidate in lines:
                        candidate = candidate.strip()
                        if not candidate:
                            continue
                        if candidate.lower().startswith("answer"):
                            continue
                        if _is_option_line(candidate):
                            continue
                        if candidate.lower().startswith("question"):
                            continue
                        q_text = candidate
                        break

                if not q_text:
                    q_text = f"Question {qid}"

                answered      = qid in user_answers
                border_accent = "var(--accent2)" if answered else "var(--border)"

                st.markdown(
                    f'<div class="info-card" style="border-left:3px solid {border_accent};margin-bottom:.3rem">'
                    f'<div class="label">Question {qid}</div>'
                    f'<span style="font-size:.92rem;line-height:1.7">{q_text}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                if options:
                    radio_options = options
                    current_idx   = None
                    if qid in user_answers:
                        letter = user_answers[qid]
                        for idx, opt in enumerate(options):
                            if opt[0].upper() == letter:
                                current_idx = idx
                                break

                    choice = st.radio(
                        f"q{qid}_radio",
                        options=radio_options,
                        index=current_idx,
                        label_visibility="collapsed",
                        key=f"radio_{qid}",
                    )

                    if choice is not None:
                        user_answers[qid] = choice[0].upper()
                    elif qid in user_answers:
                        del user_answers[qid]
                else:
                    prev = user_answers.get(qid, "")
                    ans  = st.text_input(
                        "Your answer (A/B/C/D)",
                        value=prev,
                        max_chars=1,
                        key=f"ans_text_{qid}",
                        placeholder="A, B, C or D",
                    )
                    if ans.strip():
                        user_answers[qid] = ans.strip().upper()[0]

                st.session_state.quiz_user_answers = user_answers

            _divider()

            answered_count = len(user_answers)
            pct_answered   = int((answered_count / num_q) * 100) if num_q else 0
            st.progress(pct_answered / 100, text=f"Answered {answered_count} / {num_q}")
            st.markdown("<br>", unsafe_allow_html=True)

            col_submit, col_regen = st.columns([3, 1])
            with col_submit:
                submit_btn = st.button(
                    "Submit Answers →",
                    use_container_width=True,
                    disabled=(answered_count < num_q),
                )
                if answered_count < num_q:
                    _notice(f"Answer all {num_q} questions to enable submission.")
            with col_regen:
                if st.button("↺  Regenerate", use_container_width=True):
                    st.session_state.quiz_phase = "config"
                    st.rerun()

            if submit_btn:
                from quiz.scoring import QuizScorer
                scorer = QuizScorer()
                result = scorer.evaluate(
                    st.session_state.quiz_text,
                    st.session_state.quiz_user_answers,
                )
                st.session_state.quiz_result = result
                st.session_state.quiz_phase  = "results"
                st.rerun()

        # ══════════════════════════════════════════════════════════════════════
        # PHASE 3 — RESULTS
        # ══════════════════════════════════════════════════════════════════════
        elif phase == "results":

            result = st.session_state.quiz_result
            topic  = st.session_state.quiz_topic
            diff   = st.session_state.quiz_difficulty.capitalize()

            if not result:
                st.warning("No results found. Please take the quiz first.")
            else:
                score   = result["score"]
                total   = result["total"]
                pct     = result["percentage"]
                details = result["details"]

                def _grade(p):
                    if p >= 90: return ("Outstanding",     "green")
                    if p >= 75: return ("Great Work",       "green")
                    if p >= 60: return ("Good Effort",      "blue")
                    if p >= 40: return ("Keep Practicing",  "orange")
                    return             ("Keep Studying",    "pink")

                grade_label, grade_variant = _grade(pct)

                _section(f"Results · {topic}")

                hero_col, meta_col = st.columns([3, 5], gap="large")

                with hero_col:
                    st.markdown(
                        f'<div class="info-card" style="text-align:center;padding:1.5rem 1rem;">'
                        f'<div class="label">Final Score</div>'
                        f'<div style="font-family:var(--serif);font-size:3.5rem;font-weight:600;'
                        f'color:var(--accent);line-height:1;margin:.4rem 0">{score}/{total}</div>'
                        f'<div style="font-family:var(--mono);font-size:.8rem;color:var(--muted)">'
                        f'{pct:.1f}%</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(_pill(grade_label, grade_variant), unsafe_allow_html=True)

                with meta_col:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.progress(pct / 100, text=f"{pct:.1f}% correct")
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(
                        _card_html(f"{total}",         "Total questions") +
                        _card_html(f"{score}",         "Correct") +
                        _card_html(f"{total - score}", "Incorrect"),
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        _pill(diff, {"Easy":"green","Medium":"blue","Hard":"pink","Dynamic":"orange","Mix":"orange"}.get(diff,"blue")),
                        unsafe_allow_html=True,
                    )

                _divider()
                _section("Question Breakdown")

                parsed     = st.session_state.quiz_parsed
                parsed_map = {q["id"]: q for q in parsed}

                for r in details:
                    qid      = r["id"]
                    correct  = r["correct"]
                    user_ans = r["user"] or "—"
                    is_ok    = r["is_correct"]

                    # Extract full question text and options
                    q_text  = ""
                    options = []
                    raw_q   = parsed_map.get(qid, {}).get("question", "")
                    q_lines = raw_q.split("\n")
                    
                    for line in q_lines:
                        stripped = line.strip()
                        if stripped.lower().startswith("question"):
                            parts = stripped.split(":", 1)
                            if len(parts) > 1 and parts[1].strip():
                                q_text = parts[1].strip()
                        elif len(stripped) > 1 and stripped[0] in "ABCDabcd" and stripped[1] in (".", ")", ":"):
                            options.append(stripped)
                    
                    if not q_text:
                        for line in q_lines:
                            stripped = line.strip()
                            if not stripped or stripped.lower().startswith(("question", "answer")):
                                continue
                            if len(stripped) > 1 and stripped[0] in "ABCDabcd" and stripped[1] in (".", ")", ":"):
                                continue
                            q_text = stripped
                            break
                    
                    if not q_text:
                        q_text = f"Question {qid}"

                    icon         = "✅" if is_ok else "❌"
                    border_color = "var(--success)" if is_ok else "var(--accent3)"
                    bg_color     = "rgba(74,222,128,.08)" if is_ok else "rgba(196,167,255,.08)"
                    ans_color    = "var(--success)" if is_ok else "var(--accent3)"
                    ans_bg_user  = "rgba(196,167,255,.15)" if not is_ok else "rgba(74,222,128,.15)"
                    ans_border_user = "rgba(196,167,255,.4)" if not is_ok else "rgba(74,222,128,.4)"

                    # Build options HTML
                    options_html = ""
                    if options:
                        options_html = '<div style="font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-bottom:.4rem">Options</div>'
                        for opt in options:
                            options_html += f'<div style="padding:.35rem 0;font-size:.85rem;line-height:1.4">{opt}</div>'

                    st.markdown(
                        f'<div class="info-card" style="background:{bg_color};border-left:4px solid {border_color};'
                        f'padding:1.2rem;border-radius:8px;margin-bottom:1rem">'
                        f'<div style="display:grid;grid-template-columns:1fr auto;gap:1.5rem;align-items:flex-start">'
                        f'<div style="display:flex;flex-direction:column;gap:.8rem">'
                        f'<div>'
                        f'<div style="font-size:.75rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.4rem">Question {qid}</div>'
                        f'<div style="max-height:80px;overflow-y:auto;padding-right:.5rem;font-size:.95rem;line-height:1.6;color:var(--text);margin-bottom:.6rem">'
                        f'{q_text}'
                        f'</div>'
                        f'</div>'
                        f'<div style="border-top:1px solid var(--border);padding-top:.6rem;max-height:100px;overflow-y:auto;padding-right:.5rem">'
                        f'{options_html}'
                        f'</div>'
                        f'</div>'
                        f'<div style="display:flex;flex-direction:column;gap:.6rem;min-width:160px">'
                        f'<div style="background:{ans_bg_user};border:1px solid {ans_border_user};padding:.7rem;border-radius:6px;text-align:center">'
                        f'<div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-bottom:.3rem">Your Answer</div>'
                        f'<div style="font-size:1.4rem;font-weight:700;color:{ans_color};font-family:var(--mono)">{user_ans} <span style="font-size:.9rem">{icon}</span></div>'
                        f'</div>'
                        f'<div style="background:rgba(74,222,128,.15);border:1px solid rgba(74,222,128,.4);padding:.7rem;border-radius:6px;text-align:center">'
                        f'<div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-bottom:.3rem">✅ Correct</div>'
                        f'<div style="font-size:1.4rem;font-weight:700;color:var(--success);font-family:var(--mono)">{correct or "?"}</div>'
                        f'</div>'
                        f'</div>'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                _divider()

                col_retry, col_new = st.columns(2, gap="large")
                with col_retry:
                    if st.button("↺  Retake This Quiz", use_container_width=True):
                        st.session_state.quiz_user_answers = {}
                        st.session_state.quiz_result       = None
                        st.session_state.quiz_phase        = "answering"
                        st.rerun()
                with col_new:
                    if st.button("＋  New Quiz", use_container_width=True):
                        st.session_state.quiz_phase = "config"
                        st.rerun()