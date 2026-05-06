"""
quiz_page.py
────────────────────────────────────────────────────────────────────────────────
Drop-in quiz page for Learn Mate.

Usage – add to app.py after the existing tab definitions:

    tab_ingest, tab_qa, tab_quiz = st.tabs([
        "⬆  Sources & Ingest",
        "💬  Ask Questions",
        "📝  Quiz",
    ])

    # ... existing tab_ingest and tab_qa code ...

    with tab_quiz:
        from quiz_page import render_quiz_tab
        render_quiz_tab()

Requires the quiz/ package already present in your project:
    quiz/quiz_generator.py  → QuizGenerator
    quiz/scoring.py         → QuizScorer, hide_answers
────────────────────────────────────────────────────────────────────────────────
"""

import streamlit as st


# ── helpers ───────────────────────────────────────────────────────────────────

def _pill(text: str, variant: str = "blue") -> str:
    """Return a status-pill HTML string matching app.py style."""
    return f'<span class="pill pill-{variant}">{text}</span>'


def _section(label: str) -> None:
    st.markdown(f'<div class="section-label">{label}</div>', unsafe_allow_html=True)


def _divider() -> None:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


def _card(body: str, label: str = "") -> str:
    lbl = f'<div class="label">{label}</div>' if label else ""
    return f'<div class="info-card">{lbl}{body}</div>'


def _notice(text: str) -> None:
    st.markdown(f'<div class="notice">{text}</div>', unsafe_allow_html=True)


def _status_line(text: str, ok: bool = False) -> None:
    cls = "status-line status-line-ok" if ok else "status-line"
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)


# ── session-state initialisation ─────────────────────────────────────────────

def _init_state() -> None:
    defaults = {
        "quiz_text":        "",          # raw quiz text from generator (with answers)
        "quiz_parsed":      [],          # list of question dicts
        "quiz_user_answers": {},         # {q_id: letter}
        "quiz_result":      None,        # result dict from QuizScorer.evaluate()
        "quiz_phase":       "config",    # config | answering | results
        "quiz_topic":       "",
        "quiz_num_q":       5,
        "quiz_difficulty":  "medium",
        "quiz_detail_qid":  None,         # selected question id in results modal
        "available_sources": [],          # List of loaded source names (PDFs + YouTube URLs)
        "source_titles":     {},          # Map of source URL/filename to display title
        "selected_sources":  [],          # List of sources selected for quiz filtering
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── sub-renderers ─────────────────────────────────────────────────────────────

def _render_config_phase() -> None:
    """Step 1 – quiz configuration + generation."""

    if not st.session_state.get("pipeline_ready"):
        st.markdown(
            '<div class="answer-box" style="border-top-color:var(--accent2);'
            'text-align:center;color:var(--muted)">'
            'Pipeline not ready. Add sources and run ingest first.'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Config form ──────────────────────────────────────────────────────────
    _section("Quiz Configuration")

    col_topic, col_right = st.columns([5, 3], gap="large")

    with col_topic:
        topic = st.text_input(
            "Topic / Query",
            value=st.session_state.quiz_topic,
            placeholder="e.g. Gradient Descent, Transformers, Neural Networks…",
            label_visibility="collapsed",
            key="quiz_topic_input",
        )
        st.markdown(
            '<div class="notice" style="margin-top:-.5rem">Enter the subject you want to be tested on.</div>',
            unsafe_allow_html=True,
        )

    with col_right:
        num_q = st.number_input(
            "Number of questions",
            min_value=1,
            max_value=20,
            value=st.session_state.quiz_num_q,
            step=1,
            key="quiz_num_q_input",
        )

    _section("Difficulty")
    diff_cols = st.columns(4)
    diff_labels   = ["Easy", "Medium", "Hard", "Dynamic"]
    diff_vals     = ["easy", "medium", "hard", "dynamic"]
    diff_variants = ["green", "blue", "pink", "orange"]

    if st.session_state.quiz_difficulty == "mix":
        st.session_state.quiz_difficulty = "dynamic"

    selected_diff = st.session_state.quiz_difficulty

    for i, (col, label, val, variant) in enumerate(
        zip(diff_cols, diff_labels, diff_vals, diff_variants)
    ):
        with col:
            is_selected = selected_diff == val
            # Render a visual pill; a real button triggers the selection
            pill_style = (
                f"border:1.5px solid var(--accent);background:var(--pill-blue-bg)"
                if is_selected else ""
            )
            if val == "easy" and is_selected:
                pill_style = "border:1.5px solid var(--success);background:var(--pill-green-bg)"
            elif val == "hard" and is_selected:
                pill_style = "border:1.5px solid var(--accent3);background:var(--pill-pink-bg)"
            elif val == "dynamic" and is_selected:
                pill_style = "border:1.5px solid var(--warning);background:var(--pill-orange-bg)"

            if st.button(
                label,
                key=f"diff_{val}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
            ):
                st.session_state.quiz_difficulty = val
                st.rerun()

    _divider()

    # ── Sources filter (optional) ────────────────────────────────────────────
    _section("Source Filter (optional)")
    
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
        _notice("No sources loaded yet. Go back to main app and add PDFs or YouTube videos in Ingest tab.")
        st.session_state.selected_sources = []

    _divider()

    # ── Generate button ──────────────────────────────────────────────────────
    col_btn, col_hint = st.columns([3, 7])
    with col_btn:
        gen_btn = st.button("▶  Generate Quiz", use_container_width=True)
    with col_hint:
        _notice("Retrieves relevant content and generates multiple-choice questions.")

    # ── Error state ──────────────────────────────────────────────────────────
    if gen_btn:
        topic_val     = topic.strip()
        sources_val   = st.session_state.selected_sources or None

        if not topic_val:
            st.error("Please enter a topic before generating.")
            return

        st.session_state.quiz_topic    = topic_val
        st.session_state.quiz_num_q    = int(num_q)

        # ── Run generator ────────────────────────────────────────────────────
        try:
            from quiz.quiz_generator import QuizGenerator
            from quiz.scoring import QuizScorer, hide_answers

            progress_bar = st.progress(0, text="Starting quiz generation…")

            with st.status("Generating quiz…", expanded=True) as status:

                _status_line("🔍  Retrieving relevant chunks from the knowledge base…")
                progress_bar.progress(15, text="🔍  Retrieving context…")

                generator = QuizGenerator()
                progress_bar.progress(35, text="🧠  Calling language model…")
                _status_line("🧠  Generating questions with the language model…")

                quiz_text = generator.generate_quiz(
                    query        = topic_val,
                    embedded_docs= st.session_state.embedded_docs,
                    num_questions= int(num_q),
                    difficulty   = st.session_state.quiz_difficulty,
                    sources      = sources_val,
                )

                progress_bar.progress(75, text="✂️  Parsing questions…")
                _status_line("✂️  Parsing and validating questions…")

                scorer  = QuizScorer()
                parsed  = scorer.parse_quiz(quiz_text)

                if not parsed:
                    status.update(label="❌ Could not parse quiz output", state="error")
                    progress_bar.empty()
                    st.error("The model returned an unexpected format. Try a different topic or retry.")
                    return

                progress_bar.progress(100, text="✅  Quiz ready!")
                _status_line(f"✅  Generated {len(parsed)} question(s)", ok=True)
                status.update(
                    label=f"✅  Quiz ready — {len(parsed)} questions!",
                    state="complete",
                    expanded=False,
                )

            # Store & advance phase
            st.session_state.quiz_text        = quiz_text
            st.session_state.quiz_parsed      = parsed
            st.session_state.quiz_user_answers = {}
            st.session_state.quiz_result       = None
            st.session_state.quiz_phase        = "answering"
            st.rerun()

        except Exception as e:
            st.error(f"❌ Quiz generation error: {e}")
            st.exception(e)


def _render_answering_phase() -> None:
    """Step 2 – display questions and collect answers."""
    from quiz.scoring import hide_answers, QuizScorer

    parsed   = st.session_state.quiz_parsed
    num_q    = len(parsed)
    diff     = st.session_state.quiz_difficulty.capitalize()
    topic    = st.session_state.quiz_topic

    # ── Header row ───────────────────────────────────────────────────────────
    header_col, reset_col = st.columns([7, 2])
    with header_col:
        _section(f"Quiz · {topic}")
        st.markdown(
            _pill(f"{num_q} Questions", "blue") + "&nbsp;&nbsp;" +
            _pill(diff, {
                "Easy":   "green",
                "Medium": "blue",
                "Hard":   "pink",
                "Dynamic": "orange",
                "Mix":    "orange",
            }.get(diff, "blue")),
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
    with reset_col:
        if st.button("↺  New Quiz", use_container_width=True):
            st.session_state.quiz_phase = "config"
            st.rerun()

    # ── Questions ────────────────────────────────────────────────────────────
    user_answers = st.session_state.quiz_user_answers

    for q in parsed:
        qid   = q["id"]
        raw   = q["question"]
        lines = raw.strip().split("\n")

        # Extract question text (first non-empty line after "Question N:")
        q_text = ""
        options = []

        def _is_option_line(text: str) -> bool:
            return bool(text and len(text) > 1 and text[0] in "ABCDabcd" and text[1] in ".):")

        for line in lines:
            stripped = line.strip()
            if stripped.lower().startswith("question"):
                # Grab text after the colon
                parts = stripped.split(":", 1)
                if len(parts) > 1:
                    q_text = parts[1].strip()
            elif _is_option_line(stripped):
                options.append(stripped)
            # Ignore Answer: lines (hidden from user)

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

        # ── Question card ────────────────────────────────────────────────────
        answered = qid in user_answers
        border_accent = "var(--accent2)" if answered else "var(--border)"

        st.markdown(
            f'<div class="info-card" style="border-left:3px solid {border_accent};margin-bottom:.3rem">'
            f'<div class="label">Question {qid}</div>'
            f'<span style="font-size:.92rem;line-height:1.7">{q_text}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if options:
            # Radio via Streamlit (styled naturally)
            radio_options = options
            current_idx = None
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
                horizontal=False,
            )

            if choice is not None:
                user_answers[qid] = choice[0].upper()
            elif qid in user_answers:
                del user_answers[qid]

        else:
            # Fallback: plain text input
            prev = user_answers.get(qid, "")
            ans = st.text_input(
                f"Your answer (A/B/C/D)",
                value=prev,
                max_chars=1,
                key=f"ans_text_{qid}",
                placeholder="A, B, C or D",
                label_visibility="visible",
            )
            if ans.strip():
                user_answers[qid] = ans.strip().upper()[0]

        st.session_state.quiz_user_answers = user_answers

    _divider()

    # ── Progress indicator ───────────────────────────────────────────────────
    answered_count = len(user_answers)
    pct = int((answered_count / num_q) * 100) if num_q else 0
    st.progress(pct / 100, text=f"Answered {answered_count} / {num_q}")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Submit row ───────────────────────────────────────────────────────────
    col_submit, col_reset = st.columns([3, 1])
    with col_submit:
        submit_btn = st.button(
            "Submit Answers →",
            use_container_width=True,
            disabled=(answered_count < num_q),
        )
        if answered_count < num_q:
            _notice(f"Answer all {num_q} questions to enable submission.")
    with col_reset:
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


def _render_results_phase() -> None:
    """Step 3 – show scored results."""
    result  = st.session_state.quiz_result
    topic   = st.session_state.quiz_topic
    diff    = st.session_state.quiz_difficulty.capitalize()

    if not result:
        st.warning("No results found. Please take the quiz first.")
        return

    score   = result["score"]
    total   = result["total"]
    pct     = result["percentage"]
    details = result["details"]

    # ── Grade label ──────────────────────────────────────────────────────────
    def _grade(p):
        if p >= 90: return ("Outstanding", "green")
        if p >= 75: return ("Great Work", "green")
        if p >= 60: return ("Good Effort", "blue")
        if p >= 40: return ("Keep Practicing", "orange")
        return ("Keep Studying", "pink")

    grade_label, grade_variant = _grade(pct)

    # ── Score hero card ──────────────────────────────────────────────────────
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
        st.markdown(
            _pill(grade_label, grade_variant),
            unsafe_allow_html=True,
        )

    with meta_col:
        st.markdown("<br>", unsafe_allow_html=True)
        st.progress(pct / 100, text=f"{pct:.1f}% correct")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            _card(f"{total}", "Total questions") +
            _card(f"{score}", "Correct") +
            _card(f"{total - score}", "Incorrect"),
            unsafe_allow_html=True,
        )
        st.markdown(
            _pill(diff, {
                "Easy": "green", "Medium": "blue",
                "Hard": "pink", "Dynamic": "orange", "Mix": "orange",
            }.get(diff, "blue")),
            unsafe_allow_html=True,
        )

    _divider()

    # ── Per-question breakdown ───────────────────────────────────────────────
    _section("Question Breakdown")

    parsed = st.session_state.quiz_parsed
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

        icon          = "✅" if is_ok else "❌"
        border_color  = "var(--success)" if is_ok else "var(--accent3)"
        bg_color      = "rgba(74,222,128,.08)" if is_ok else "rgba(196,167,255,.08)"
        answer_color  = "var(--success)" if is_ok else "var(--accent3)"
        ans_bg_user   = "rgba(196,167,255,.15)" if not is_ok else "rgba(74,222,128,.15)"
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
            f'<div style="font-size:1.4rem;font-weight:700;color:{answer_color};font-family:var(--mono)">{user_ans} <span style="font-size:.9rem">{icon}</span></div>'
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

    # ── Action buttons ───────────────────────────────────────────────────────
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


# ── Public entry point ────────────────────────────────────────────────────────

def render_quiz_tab() -> None:
    """
    Main entry point. Call this inside a `with tab_quiz:` block in app.py.
    """
    _init_state()

    phase = st.session_state.quiz_phase

    # ── Phase breadcrumb ─────────────────────────────────────────────────────
    phase_map = {
        "config":    ("01 Configure", "02 Answer", "03 Results"),
        "answering": ("01 Configure", "02 Answer", "03 Results"),
        "results":   ("01 Configure", "02 Answer", "03 Results"),
    }
    active_idx = {"config": 0, "answering": 1, "results": 2}.get(phase, 0)

    crumb_html = '<div style="display:flex;gap:1.2rem;margin-bottom:1rem;align-items:center">'
    for i, label in enumerate(phase_map[phase]):
        if i == active_idx:
            crumb_html += (
                f'<span class="pill pill-blue">{label}</span>'
            )
        elif i < active_idx:
            crumb_html += (
                f'<span class="pill pill-green">{label}</span>'
            )
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

    # ── Dispatch ─────────────────────────────────────────────────────────────
    if phase == "config":
        _render_config_phase()
    elif phase == "answering":
        _render_answering_phase()
    elif phase == "results":
        _render_results_phase()