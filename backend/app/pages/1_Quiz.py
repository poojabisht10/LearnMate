import streamlit as st
import sys
import os

# ── Path setup ────────────────────────────────────────────────────────────────
_HERE    = os.path.dirname(os.path.abspath(__file__))   # .../backend/pages
_BACKEND = os.path.dirname(_HERE)                        # .../backend
_APP     = os.path.join(_BACKEND, "app")                 # .../backend/app  ← quiz lives here
_ROOT    = os.path.dirname(_BACKEND)                     # project root
for _p in [_BACKEND, _APP, _ROOT]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Quiz · Learn Mate",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS (same design system as main.py) ───────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:        #0a0a0f;
    --surface:   #111118;
    --card:      #16161f;
    --border:    #2a2a3a;
    --accent:    #6c63ff;
    --accent2:   #00e5ff;
    --accent3:   #ff6b9d;
    --text:      #e8e8f0;
    --muted:     #6b6b80;
    --success:   #00c896;
    --warning:   #ffb347;
    --error:     #ff4d6d;
    --mono:      'Space Mono', monospace;
    --sans:      'DM Sans', sans-serif;
}

html, body, [class*="css"] {
    font-family: var(--sans);
    background-color: var(--bg);
    color: var(--text);
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 4rem; max-width: 1200px; }

[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .block-container { padding: 1.5rem 1rem; }

/* ── Hero ── */
.hero { text-align: center; padding: 2.5rem 0 2rem; }
.hero-badge {
    display: inline-block;
    font-family: var(--mono);
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--accent3);
    border: 1px solid var(--accent3);
    padding: 0.3rem 0.9rem;
    border-radius: 2px;
    margin-bottom: 1rem;
}
.hero h1 {
    font-family: var(--mono);
    font-size: 2.6rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--accent3) 0%, var(--accent) 60%, var(--accent2) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 0.5rem;
    line-height: 1.1;
}
.hero p { color: var(--muted); font-size: 0.95rem; font-weight: 300; margin: 0; }

.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 1.5rem 0;
}

/* ── Labels & Cards ── */
.section-label {
    font-family: var(--mono);
    font-size: 0.65rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--border); }

.info-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    font-size: 0.85rem;
}
.info-card .label {
    font-family: var(--mono);
    font-size: 0.6rem;
    letter-spacing: 0.15em;
    color: var(--muted);
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}

/* ── Pills ── */
.pill {
    display: inline-flex; align-items: center; gap: 0.35rem;
    font-size: 0.72rem; font-family: var(--mono);
    padding: 0.2rem 0.7rem; border-radius: 20px;
    font-weight: 700; letter-spacing: 0.05em;
}
.pill-green  { background: rgba(0,200,150,.12); color: var(--success); border: 1px solid rgba(0,200,150,.3); }
.pill-orange { background: rgba(255,179,71,.12); color: var(--warning); border: 1px solid rgba(255,179,71,.3); }
.pill-pink   { background: rgba(255,107,157,.12); color: var(--accent3); border: 1px solid rgba(255,107,157,.3); }
.pill-blue   { background: rgba(108,99,255,.12); color: var(--accent);  border: 1px solid rgba(108,99,255,.3); }

/* ── Question card ── */
.question-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 6px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 0.8rem;
}
.question-num {
    font-family: var(--mono);
    font-size: 0.62rem;
    letter-spacing: 0.18em;
    color: var(--accent);
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.question-text { font-size: 1rem; font-weight: 500; color: var(--text); line-height: 1.6; }

/* ── Result feedback ── */
.result-correct {
    background: rgba(0,200,150,.08); border: 1px solid rgba(0,200,150,.3);
    border-radius: 6px; padding: 0.9rem 1.2rem;
    font-size: 0.88rem; color: var(--success); margin-top: 0.5rem;
}
.result-wrong {
    background: rgba(255,77,109,.08); border: 1px solid rgba(255,77,109,.3);
    border-radius: 6px; padding: 0.9rem 1.2rem;
    font-size: 0.88rem; color: var(--error); margin-top: 0.5rem;
}
.explanation-box {
    background: linear-gradient(135deg, rgba(108,99,255,.06), rgba(0,229,255,.04));
    border: 1px solid rgba(108,99,255,.2); border-radius: 6px;
    padding: 0.9rem 1.2rem; font-size: 0.85rem;
    color: var(--muted); margin-top: 0.5rem; line-height: 1.65;
}

/* ── Score card ── */
.score-card {
    text-align: center; background: var(--card);
    border: 1px solid var(--border); border-radius: 8px;
    padding: 2.5rem 2rem; margin: 1rem 0;
}
.score-number {
    font-family: var(--mono); font-size: 4rem; font-weight: 700;
    background: linear-gradient(135deg, var(--accent3), var(--accent), var(--accent2));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; line-height: 1;
}
.score-label {
    font-family: var(--mono); font-size: 0.7rem;
    letter-spacing: 0.15em; color: var(--muted);
    text-transform: uppercase; margin-top: 0.5rem;
}
.score-message { font-size: 1rem; color: var(--text); margin-top: 1rem; font-weight: 500; }

/* ── Inputs / buttons ── */
.stProgress > div > div > div { background: var(--accent) !important; }

.stButton > button {
    background: var(--accent) !important; color: #fff !important;
    border: none !important; border-radius: 5px !important;
    font-family: var(--mono) !important; font-size: 0.78rem !important;
    letter-spacing: 0.08em !important; text-transform: uppercase !important;
    padding: 0.55rem 1.4rem !important; transition: opacity .2s, transform .1s !important;
}
.stButton > button:hover { opacity: .85 !important; transform: translateY(-1px) !important; }

.stRadio > div > label {
    background: var(--card) !important; border: 1px solid var(--border) !important;
    border-radius: 5px !important; padding: 0.6rem 1rem !important;
    transition: border-color .2s !important; font-size: 0.88rem !important;
}
.stRadio > div > label:hover { border-color: var(--accent) !important; }

.stTextInput > div > div > input {
    background: var(--card) !important; border: 1px solid var(--border) !important;
    border-radius: 5px !important; color: var(--text) !important;
    font-family: var(--sans) !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(108,99,255,.15) !important;
}

[data-testid="stMetric"] {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 6px; padding: 0.8rem 1rem;
}

.notice {
    font-family: var(--mono); font-size: 0.72rem;
    color: var(--muted); letter-spacing: 0.05em; padding: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)


# ── Lazy-load quiz modules once ────────────────────────────────────────────────
@st.cache_resource
def load_quiz_modules():
    from quiz.quiz_generator import QuizGenerator
    from quiz.scoring import QuizScorer, hide_answers
    return QuizGenerator(), QuizScorer(), hide_answers


# ── Session state ──────────────────────────────────────────────────────────────
for key, default in {
    "quiz_raw":       None,   # raw quiz_text string from QuizGenerator
    "quiz_questions": None,   # parsed list of dicts
    "quiz_answers":   {},     # {q_index: chosen_letter}  e.g. {0: "A"}
    "quiz_submitted": False,
    "quiz_score":     None,   # result dict from QuizScorer
    # settings
    "quiz_topic":      "",
    "quiz_num_q":      5,
    "quiz_difficulty": "medium",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Helpers ────────────────────────────────────────────────────────────────────
def score_message(pct: float) -> str:
    if pct == 100:  return "🏆 Perfect score! Outstanding!"
    if pct >= 80:   return "🎉 Excellent work!"
    if pct >= 60:   return "👍 Good effort — review the explanations below."
    if pct >= 40:   return "📖 Keep studying — you're getting there."
    return "💪 Don't give up — try again after reviewing the material."


def parse_quiz_text(quiz_text: str, num_q: int) -> list:
    """
    Parse the raw string from QuizGenerator into a list of dicts.

    Handles formats like:
        Q1. Question?          or    1. Question?
        A) option              or    A. option
        B) option
        C) option
        D) option
        Answer: A
        Explanation: ...
    """
    import re
    questions = []

    # Split on question boundaries
    blocks = re.split(r'\n(?=Q?\d+[\.\)])', quiz_text.strip())

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.splitlines()

        # Question text: strip leading "Q1." / "1." / "Q1)"
        q_line = re.sub(r'^Q?\d+[\.\)]\s*', '', lines[0]).strip()
        if not q_line:
            continue

        # Options A–D
        options = {}
        for line in lines[1:]:
            m = re.match(r'^([A-D])[\.\)]\s*(.+)', line.strip())
            if m:
                options[m.group(1)] = m.group(2).strip()

        if len(options) < 2:
            continue

        # Answer letter
        ans_match = re.search(r'Answer[:\s]+([A-D])', block, re.IGNORECASE)
        answer_letter = ans_match.group(1).upper() if ans_match else ""

        # Explanation
        exp_match = re.search(r'Explanation[:\s]+(.+)', block, re.IGNORECASE | re.DOTALL)
        explanation = exp_match.group(1).strip() if exp_match else ""
        explanation = re.split(r'\nQ?\d+[\.\)]', explanation)[0].strip()

        questions.append({
            "question":      q_line,
            "options":       options,          # {"A": "text", "B": "text", ...}
            "answer_letter": answer_letter,
            "explanation":   explanation,
        })

    return questions[:num_q]


def reset_quiz():
    st.session_state.quiz_raw       = None
    st.session_state.quiz_questions = None
    st.session_state.quiz_answers   = {}
    st.session_state.quiz_submitted = False
    st.session_state.quiz_score     = None


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-label">System</div>', unsafe_allow_html=True)

    if st.session_state.get("pipeline_ready"):
        st.markdown('<span class="pill pill-green">● PIPELINE READY</span>', unsafe_allow_html=True)
        s = st.session_state.get("doc_summary", {})
        st.markdown("<br>", unsafe_allow_html=True)
        cols = st.columns(2)
        with cols[0]:
            st.metric("PDFs", s.get("pdf_count", "—"))
        with cols[1]:
            st.metric("Videos", s.get("youtube_count", "—"))
        st.markdown(
            f'<div class="info-card" style="margin-top:.8rem">'
            f'<div class="label">Chunks</div>{s.get("total_chunks","—")}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<span class="pill pill-orange">○ NOT READY</span>', unsafe_allow_html=True)
        st.markdown(
            '<div class="notice" style="margin-top:.8rem">'
            'Go to the main page, add sources, and run the pipeline first.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Quiz Settings</div>', unsafe_allow_html=True)

    st.session_state.quiz_topic = st.text_input(
        "Topic / focus",
        value=st.session_state.quiz_topic,
        placeholder="e.g. neural networks, chapter 3…",
    )
    st.session_state.quiz_num_q = st.select_slider(
        "Number of questions",
        options=[3, 5, 7, 10],
        value=st.session_state.quiz_num_q,
    )
    st.session_state.quiz_difficulty = st.selectbox(
        "Difficulty",
        ["easy", "medium", "hard", "mix"],
        index=["easy", "medium", "hard", "mix"].index(st.session_state.quiz_difficulty),
        format_func=str.capitalize,
    )

    if st.session_state.quiz_questions:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("↺  New Quiz", use_container_width=True):
            reset_quiz()
            st.rerun()


# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-badge">Test Your Knowledge</div>
  <h1>Quiz Mode</h1>
  <p>AI-generated questions · From your own sources · Instant feedback</p>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)

# ── Guard ──────────────────────────────────────────────────────────────────────
if not st.session_state.get("pipeline_ready"):
    st.markdown("""
    <div style="text-align:center;padding:3rem 1rem">
      <div style="font-size:3rem;margin-bottom:1rem">🔒</div>
      <div style="font-family:var(--mono);font-size:0.8rem;color:var(--muted);
                  letter-spacing:0.1em;text-transform:uppercase">Pipeline not ready</div>
      <div style="color:var(--muted);font-size:0.9rem;margin-top:0.5rem">
        Go to the <strong>main page</strong>, upload your PDFs / YouTube links,
        and run the pipeline first.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

embedded_docs = st.session_state.get("embedded_docs", [])


# ══════════════════════════════════════════════════════════════════════════════
# STATE 1 — Generate
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.quiz_questions is None:

    col_cfg, col_btn = st.columns([3, 1], gap="large")
    with col_cfg:
        st.markdown('<div class="section-label">Ready to test yourself?</div>', unsafe_allow_html=True)
        topic_display = (
            f"Topic: <em>{st.session_state.quiz_topic}</em> &nbsp;·&nbsp;"
            if st.session_state.quiz_topic else ""
        )
        st.markdown(f"""
        <div class="info-card">
          <div class="label">Configuration</div>
          {topic_display}
          <strong>{st.session_state.quiz_num_q} questions</strong>
          &nbsp;·&nbsp; {st.session_state.quiz_difficulty.capitalize()} difficulty
        </div>
        <div class="notice">Questions are generated from your uploaded sources only.</div>
        """, unsafe_allow_html=True)

    with col_btn:
        st.markdown("<br><br>", unsafe_allow_html=True)
        gen_btn = st.button("⚡  Generate Quiz", use_container_width=True)

    if gen_btn:
        topic = st.session_state.quiz_topic.strip() or "general knowledge from the material"
        with st.spinner("🧠  Generating quiz from your knowledge base…"):
            try:
                quiz_gen, _, _ = load_quiz_modules()

                # ── Exact same call as test_quiz.py ──
                raw_quiz = quiz_gen.generate_quiz(
                    query=topic,
                    embedded_docs=embedded_docs,
                    num_questions=st.session_state.quiz_num_q,
                    difficulty=st.session_state.quiz_difficulty,
                    sources=None,
                )

                parsed = parse_quiz_text(raw_quiz, st.session_state.quiz_num_q)
                if not parsed:
                    st.error("❌ Could not parse quiz questions. Check the raw output below and try again.")
                    with st.expander("Raw LLM output"):
                        st.text(raw_quiz)
                else:
                    st.session_state.quiz_raw       = raw_quiz
                    st.session_state.quiz_questions = parsed
                    st.session_state.quiz_answers   = {}
                    st.session_state.quiz_submitted = False
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Failed to generate quiz: {e}")
                st.exception(e)


# ══════════════════════════════════════════════════════════════════════════════
# STATE 2 — Take the quiz
# ══════════════════════════════════════════════════════════════════════════════
elif not st.session_state.quiz_submitted:

    questions = st.session_state.quiz_questions
    total     = len(questions)
    answered  = len(st.session_state.quiz_answers)

    # Progress bar
    col_prog, col_pill = st.columns([4, 1])
    with col_prog:
        st.progress(answered / total, text=f"Progress: {answered} / {total} answered")
    with col_pill:
        st.markdown(
            f'<div style="text-align:right;padding-top:.35rem">'
            f'<span class="pill pill-pink">{st.session_state.quiz_difficulty.upper()}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Render questions
    for i, q in enumerate(questions):
        st.markdown(
            f'<div class="question-card">'
            f'  <div class="question-num">Question {i+1} of {total}</div>'
            f'  <div class="question-text">{q["question"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Build "A.  option text" labels for the radio
        option_labels  = [f"{k}.  {v}" for k, v in sorted(q["options"].items())]
        current_letter = st.session_state.quiz_answers.get(i)
        current_label  = (
            f"{current_letter}.  {q['options'][current_letter]}"
            if current_letter and current_letter in q["options"] else None
        )

        choice = st.radio(
            f"q_{i}",
            options=option_labels,
            index=option_labels.index(current_label) if current_label in option_labels else None,
            key=f"radio_{i}",
            label_visibility="collapsed",
        )

        if choice:
            # Store only the letter
            st.session_state.quiz_answers[i] = choice.split(".")[0].strip()

        st.markdown("<br>", unsafe_allow_html=True)

    # Submit button — disabled until all answered
    all_answered = len(st.session_state.quiz_answers) == total
    col_sub, col_hint = st.columns([2, 4])
    with col_sub:
        submit = st.button("✔  Submit Quiz", use_container_width=True, disabled=not all_answered)
    with col_hint:
        if not all_answered:
            st.markdown(
                f'<div class="notice" style="padding-top:.9rem">'
                f'Answer {total - answered} more question(s) to submit.</div>',
                unsafe_allow_html=True,
            )

    if submit and all_answered:
        # QuizScorer expects 1-indexed dict: {1: "A", 2: "B", ...}
        user_answers_indexed = {i + 1: st.session_state.quiz_answers[i] for i in range(total)}
        try:
            _, quiz_scorer, _ = load_quiz_modules()
            result = quiz_scorer.evaluate(st.session_state.quiz_raw, user_answers_indexed)
            st.session_state.quiz_score     = result
            st.session_state.quiz_submitted = True
            st.rerun()
        except Exception as e:
            st.error(f"❌ Scoring error: {e}")
            st.exception(e)


# ══════════════════════════════════════════════════════════════════════════════
# STATE 3 — Results
# ══════════════════════════════════════════════════════════════════════════════
else:
    result    = st.session_state.quiz_score
    questions = st.session_state.quiz_questions
    total     = result.get("total",      len(questions))
    correct   = result.get("score",      0)
    pct       = result.get("percentage", round(correct / total * 100, 1) if total else 0)

    # Score card
    st.markdown(f"""
    <div class="score-card">
      <div class="score-number">{correct}/{total}</div>
      <div class="score-label">Final Score · {pct:.0f}%</div>
      <div class="score-message">{score_message(pct)}</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("✅ Correct", correct)
    with col2: st.metric("❌ Wrong",   total - correct)
    with col3: st.metric("Score",      f"{pct:.0f}%")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Question Review</div>', unsafe_allow_html=True)

    # Per-question breakdown using QuizScorer's detail list
    details = result.get("details", [])

    for i, q in enumerate(questions):
        # QuizScorer returns 1-indexed details
        detail = next((d for d in details if d.get("id") == i + 1), None)

        user_letter    = detail["user"]      if detail else st.session_state.quiz_answers.get(i, "—")
        correct_letter = detail["correct"]   if detail else q["answer_letter"]
        is_correct     = detail["is_correct"] if detail else (user_letter == correct_letter)

        user_text    = f"{user_letter}. {q['options'].get(user_letter, '—')}"
        correct_text = f"{correct_letter}. {q['options'].get(correct_letter, '—')}"
        accent       = "var(--success)" if is_correct else "var(--error)"
        label        = "✅ Correct" if is_correct else "❌ Wrong"

        st.markdown(
            f'<div class="question-card" style="border-left-color:{accent}">'
            f'  <div class="question-num">Question {i+1} · {label}</div>'
            f'  <div class="question-text">{q["question"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if is_correct:
            st.markdown(
                f'<div class="result-correct">✅ Your answer: <strong>{user_text}</strong></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="result-wrong">'
                f'❌ Your answer: <strong>{user_text}</strong><br>'
                f'✅ Correct answer: <strong>{correct_text}</strong>'
                f'</div>',
                unsafe_allow_html=True,
            )

        if q.get("explanation"):
            st.markdown(
                f'<div class="explanation-box">💡 {q["explanation"]}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

    # Action buttons
    col_retry, col_new, _ = st.columns([1, 1, 2])
    with col_retry:
        if st.button("↺  Retry Same Quiz", use_container_width=True):
            st.session_state.quiz_answers   = {}
            st.session_state.quiz_submitted = False
            st.session_state.quiz_score     = None
            st.rerun()
    with col_new:
        if st.button("⚡  New Quiz", use_container_width=True):
            reset_quiz()
            st.rerun()