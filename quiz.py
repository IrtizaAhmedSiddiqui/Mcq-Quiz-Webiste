import pandas as pd
import re
import os
import streamlit as st
from streamlit_option_menu import option_menu
import base64
import random
import difflib


def main():
    st.set_page_config(
        page_title="MCQ Quiz Application",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize session state
    if 'mcqs' not in st.session_state:
        st.session_state.mcqs = []
    if 'original_mcqs' not in st.session_state:
        st.session_state.original_mcqs = []
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'answered' not in st.session_state:
        st.session_state.answered = {}
    if 'marked_questions' not in st.session_state:
        st.session_state.marked_questions = set()
    if 'correct_answers' not in st.session_state:
        st.session_state.correct_answers = 0
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False
    if 'show_search' not in st.session_state:
        st.session_state.show_search = False
    if 'show_marked' not in st.session_state:
        st.session_state.show_marked = False
    if 'is_random_quiz' not in st.session_state:
        st.session_state.is_random_quiz = False
    if 'show_random_options' not in st.session_state:
        st.session_state.show_random_options = False

    with st.sidebar:
        st.title("📚 MCQ Quiz App")

        selected = option_menu(
            menu_title="Navigation",
            options=["Home", "Quiz", "Results"],
            icons=["house", "question-circle", "trophy"],
            menu_icon="cast",
            default_index=0 if not st.session_state.quiz_started else 1
        )

    if selected == "Home":
        show_home_page()
    elif selected == "Quiz":
        if st.session_state.mcqs:
            show_quiz_page()
        else:
            st.warning("Please load MCQs from the Home page first!")
            st.stop()
    elif selected == "Results":
        if st.session_state.show_results:
            show_results_page()
        else:
            st.info("Complete the quiz to see results!")
            st.stop()


def show_home_page():
    st.title("🎯 MCQ Quiz Application")
    st.markdown("---")

    # File upload section
    st.header("📁 Load Your MCQ Excel File")

    uploaded_file = st.file_uploader(
        "Choose an Excel file with MCQs",
        type=['xlsx', 'xls', 'xlsm'],
        help="Upload an Excel file containing your MCQ questions"
    )

    if uploaded_file is not None:
        try:
            with st.spinner("Loading MCQs..."):
                mcqs = extract_mcqs_from_excel(uploaded_file)

            if mcqs:
                st.session_state.original_mcqs = mcqs
                st.success(f"✅ Successfully loaded {len(mcqs)} MCQs!")

                # Quiz type selection
                st.header("🎲 Choose Quiz Type")
                st.info(
                    "💡 **Tip:** Mark important questions during the quiz using the ⭐ button, then create focused practice quizzes with just those questions!")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("📋 Full Quiz", use_container_width=True, type="primary"):
                        st.session_state.mcqs = mcqs
                        st.session_state.is_random_quiz = False
                        initialize_quiz()
                        st.rerun()

                with col2:
                    if st.button("🎲 Random Quiz", use_container_width=True, type="secondary"):
                        st.session_state.show_random_options = True
                        st.rerun()

                # Random quiz options
                if st.session_state.get('show_random_options', False):
                    st.subheader("🎲 Random Quiz Options")

                    # Calculate max questions (minimum of 50 or total available)
                    max_questions = min(50, len(mcqs))

                    num_questions = st.slider(
                        "Number of questions:",
                        min_value=5,
                        max_value=max_questions,
                        value=min(50, max_questions),
                        help=f"Choose between 5 and {max_questions} questions"
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("🎲 Start Random Quiz", use_container_width=True, type="primary"):
                            random_mcqs = generate_random_quiz(
                                mcqs, num_questions)
                            st.session_state.mcqs = random_mcqs
                            st.session_state.is_random_quiz = True
                            st.session_state.show_random_options = False
                            initialize_quiz()
                            st.rerun()

                    with col2:
                        if st.button("❌ Cancel", use_container_width=True):
                            st.session_state.show_random_options = False
                            st.rerun()

                # Keyword-based quiz creator
                st.header("🔎 Create Quiz by Keyword")
                kw_col1, kw_col2 = st.columns([3, 1])
                with kw_col1:
                    home_keywords = st.text_input(
                        "Enter keyword(s) (comma-separated)",
                        value="",
                        help="Example: helicopter, rotor, flight"
                    )
                with kw_col2:
                    home_fuzzy = st.checkbox(
                        "Fuzzy match", value=True, help="Catch typos like 'helicoptior'")

                kw_btn_col1, kw_btn_col2 = st.columns(2)
                with kw_btn_col1:
                    if st.button("🔎 Create Keyword Quiz", use_container_width=True):
                        keywords = [k.strip()
                                    for k in home_keywords.split(',') if k.strip()]
                        filtered = filter_mcqs_by_keywords(
                            st.session_state.original_mcqs, keywords, use_fuzzy=home_fuzzy, search_in_options=True)
                        if filtered:
                            st.session_state.mcqs = filtered
                            st.session_state.is_random_quiz = False
                            initialize_quiz()
                            st.rerun()
                        else:
                            st.warning(
                                "No questions matched the given keywords.")
                with kw_btn_col2:
                    st.caption(
                        "Searches in questions and options. Case-insensitive.")

                # Range-based quiz creator
                st.header("📏 Create Quiz by Question Range")
                st.caption(
                    "Drag to pick a range of questions (1-indexed, inclusive).")
                total = len(st.session_state.original_mcqs)

                # Responsive range slider
                default_range = (1, total if total <= 25 else 25)
                start_q, end_q = st.slider(
                    "Select range",
                    min_value=1,
                    max_value=total,
                    value=default_range,
                    step=1,
                    key="range_slider",
                )

                # Options for ordering and preview
                opt_col1, opt_col2, _ = st.columns([1, 1, 2])
                with opt_col1:
                    randomize_order = st.checkbox(
                        "Randomize order", value=False, key="range_randomize")
                with opt_col2:
                    show_preview = st.checkbox(
                        "Show preview", value=True, key="range_preview")

                # Live summary and optional preview
                start_idx = int(start_q) - 1
                end_idx = int(end_q)
                ranged = st.session_state.original_mcqs[start_idx:end_idx]
                st.info(
                    f"Selected Q{start_q}–Q{end_q} • {len(ranged)} questions")

                if show_preview and ranged:
                    st.caption("Preview of selected range:")
                    for i, mcq in enumerate(ranged[:3]):
                        title = mcq['question'] if isinstance(
                            mcq.get('question'), str) else str(mcq.get('question'))
                        st.write(
                            f"- Q{start_q + i}: {title[:100]}{'...' if len(title) > 100 else ''}")

                action_cols = st.columns([1, 1, 2])
                with action_cols[0]:
                    if st.button("📏 Create Range Quiz", use_container_width=True, key="btn_create_range"):
                        if not ranged:
                            st.warning("Selected range returned no questions.")
                        else:
                            final_mcqs = list(ranged)
                            if randomize_order:
                                random.shuffle(final_mcqs)
                            st.session_state.mcqs = final_mcqs
                            st.session_state.is_random_quiz = False
                            initialize_quiz()
                            st.rerun()
                with action_cols[1]:
                    if st.button("❌ Reset Range", use_container_width=True, key="btn_reset_range"):
                        st.session_state.range_slider = (1, min(25, total))
                        st.session_state.range_randomize = False
                        st.session_state.range_preview = True
                        st.rerun()

                # Preview section
                st.header("📋 Preview")
                preview_questions = min(3, len(mcqs))

                for i in range(preview_questions):
                    with st.expander(f"Question {i+1}"):
                        mcq = mcqs[i]
                        st.write(f"**Question:** {mcq['question']}")
                        st.write("**Options:**")
                        for opt, text in mcq['options'].items():
                            st.write(f"  {opt}. {text}")
                        st.write(f"**Answer:** {mcq['answer']}")

            else:
                st.error("❌ No MCQs found in the uploaded file!")

        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")


def generate_random_quiz(mcqs, num_questions):
    """Generate a random quiz with specified number of questions"""
    if len(mcqs) < num_questions:
        return mcqs

    # Randomly select questions without replacement
    selected_indices = random.sample(range(len(mcqs)), num_questions)
    random_mcqs = [mcqs[i] for i in selected_indices]

    return random_mcqs


def _normalize_text(text):
    """Normalize text for matching (casefold and strip extra spaces)."""
    if not isinstance(text, str):
        text = str(text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def _contains_keyword(text, keyword, use_fuzzy=False):
    """Check if text contains keyword (case-insensitive), with optional fuzzy matching."""
    norm_text = _normalize_text(text)
    norm_kw = _normalize_text(keyword)

    # Direct substring match first (fast path)
    if norm_kw in norm_text:
        return True

    if not use_fuzzy or not norm_kw:
        return False

    # Fuzzy check against words and sliding windows
    words = norm_text.split()
    # Compare with individual words
    for word in words:
        if difflib.SequenceMatcher(None, norm_kw, word).ratio() >= 0.8:
            return True
    # Compare with 2-3 word windows to catch short phrases
    for window_size in (2, 3):
        for i in range(len(words) - window_size + 1):
            window = " ".join(words[i:i + window_size])
            if difflib.SequenceMatcher(None, norm_kw, window).ratio() >= 0.8:
                return True
    return False


def filter_mcqs_by_keywords(mcqs, keywords, use_fuzzy=False, search_in_options=True):
    """Filter MCQs where question or options contain any of the keywords.

    Args:
        mcqs: List of MCQ dicts {question, options, answer}
        keywords: List[str] of keywords to match
        use_fuzzy: Allow fuzzy matching for typos
        search_in_options: Search in answer options as well
    Returns:
        List of MCQs matching any keyword
    """
    if not keywords:
        return []
    normalized_keywords = [k for k in (kw.strip() for kw in keywords) if k]
    if not normalized_keywords:
        return []

    filtered = []
    for mcq in mcqs:
        question_text = mcq.get("question", "")
        match_found = any(_contains_keyword(question_text, kw, use_fuzzy)
                          for kw in normalized_keywords)
        if not match_found and search_in_options:
            for _, opt_text in mcq.get("options", {}).items():
                if any(_contains_keyword(opt_text, kw, use_fuzzy) for kw in normalized_keywords):
                    match_found = True
                    break
        if match_found:
            filtered.append(mcq)
    return filtered


def initialize_quiz():
    """Initialize quiz state variables"""
    st.session_state.answered = {
        i: None for i in range(len(st.session_state.mcqs))}
    st.session_state.correct_answers = 0
    st.session_state.current_question = 0
    st.session_state.marked_questions = set()
    st.session_state.quiz_started = True
    st.session_state.show_results = False


def show_quiz_page():
    st.title("📝 MCQ Quiz")

    if not st.session_state.mcqs:
        st.error("No MCQs loaded!")
        return

    mcqs = st.session_state.mcqs

    # Show quiz type indicator
    if st.session_state.is_random_quiz:
        st.info(f"🎲 Random {len(mcqs)}-Question Quiz")
    elif len(mcqs) < len(st.session_state.original_mcqs):
        st.info(f"📌 Marked Questions Quiz ({len(mcqs)} questions)")
    else:
        st.info("📋 Full Quiz")

    # Show marking guidance
    if not st.session_state.is_random_quiz and len(mcqs) >= len(st.session_state.original_mcqs):
        st.info("💡 **Mark important questions using the ⭐ button below each question to create focused practice quizzes later!**")

    current_idx = st.session_state.current_question
    mcq = mcqs[current_idx]

    # Header with progress and navigation
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        progress = (current_idx + 1) / len(mcqs)
        st.progress(progress)
        st.write(f"**Question {current_idx + 1} of {len(mcqs)}**")

    with col2:
        correct_count = sum(1 for i, ans in st.session_state.answered.items()
                            if ans and ans == mcqs[i]["answer"])
        st.metric("Score", f"{correct_count}/{current_idx}")

    with col3:
        marked_count = len(st.session_state.marked_questions)
        st.metric("Marked", marked_count)

    # Search and navigation buttons
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("🔍 Search", use_container_width=True):
            st.session_state.show_search = True
            st.rerun()

    with col2:
        if st.button("📌 Show Marked", use_container_width=True):
            st.session_state.show_marked = True
            st.rerun()

    with col3:
        if st.button("⬅️ Previous", disabled=current_idx == 0, use_container_width=True):
            st.session_state.current_question = max(0, current_idx - 1)
            st.rerun()

    with col4:
        if st.button("➡️ Next", disabled=current_idx == len(mcqs) - 1, use_container_width=True):
            st.session_state.current_question = min(
                len(mcqs) - 1, current_idx + 1)
            st.rerun()

    with col5:
        if st.button("🏁 Finish Quiz", use_container_width=True):
            st.session_state.show_results = True
            st.rerun()

    # Show search dialog if needed
    if st.session_state.get('show_search', False):
        show_search_dialog()

    # Show marked dialog if needed
    if st.session_state.get('show_marked', False):
        show_marked_dialog()

    st.markdown("---")

    # Question display
    st.subheader(f"Question {current_idx + 1}")
    st.write(mcq['question'])

    # Mark/Unmark button
    if current_idx in st.session_state.marked_questions:
        if st.button("❌ Unmark Important", type="secondary", use_container_width=True):
            st.session_state.marked_questions.remove(current_idx)
            st.rerun()
    else:
        if st.button("⭐ Mark Important", type="secondary", use_container_width=True):
            st.session_state.marked_questions.add(current_idx)
            st.rerun()

    st.markdown("---")

    # Options
    st.subheader("Select your answer:")

    # Check if question was already answered
    previous_answer = st.session_state.answered.get(current_idx)

    if previous_answer:
        st.info(f"✅ You answered: **{previous_answer}**")
        if previous_answer == mcq['answer']:
            st.success("🎉 Correct!")
        else:
            st.error(f"❌ Wrong! Correct answer is: **{mcq['answer']}**")

    # Create options
    option_selected = st.radio(
        "Choose an option:",
        options=list(mcq['options'].keys()),
        format_func=lambda x: f"{x}. {mcq['options'][x]}",
        key=f"question_{current_idx}",
        index=list(mcq['options'].keys()).index(
            previous_answer) if previous_answer else None
    )

    # Submit answer button
    if not previous_answer:
        if st.button("✅ Submit Answer", type="primary", use_container_width=True):
            st.session_state.answered[current_idx] = option_selected
            if option_selected == mcq['answer']:
                st.session_state.correct_answers += 1
            st.rerun()


def show_search_dialog():
    """Show search dialog using sidebar"""
    with st.sidebar:
        st.subheader("🔍 Search / Create Quiz")
        mode = st.radio("Choose mode:", [
                        "By number", "By keyword"], key="search_mode")

        if mode == "By number":
            st.write("Enter question number to jump to:")
            qnum = st.number_input("Question #", min_value=1, max_value=len(
                st.session_state.mcqs), value=1, key="search_qnum")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Go", key="search_go"):
                    st.session_state.current_question = qnum - 1
                    st.session_state.show_search = False
                    st.rerun()
            with col2:
                if st.button("Cancel", key="search_cancel"):
                    st.session_state.show_search = False
                    st.rerun()
        else:
            st.write("Enter keywords to filter questions (comma-separated):")
            keyword_text = st.text_input(
                "Keywords", value="", key="search_keywords")
            fuzzy = st.checkbox(
                "Allow fuzzy matching (catch typos)", value=True, key="search_fuzzy")
            search_scope = st.radio("Search scope:", [
                                    "All loaded questions", "Current quiz only"], index=0, key="search_scope")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Create Quiz", key="keyword_create_quiz"):
                    base_set = st.session_state.original_mcqs if search_scope == "All loaded questions" else st.session_state.mcqs
                    keywords = [k.strip()
                                for k in keyword_text.split(",") if k.strip()]
                    filtered = filter_mcqs_by_keywords(
                        base_set, keywords, use_fuzzy=fuzzy, search_in_options=True)
                    if filtered:
                        st.session_state.mcqs = filtered
                        st.session_state.is_random_quiz = False
                        initialize_quiz()
                        st.session_state.show_search = False
                        st.rerun()
                    else:
                        st.warning("No questions matched the given keywords.")
            with col2:
                if st.button("Close", key="keyword_close"):
                    st.session_state.show_search = False
                    st.rerun()


def show_marked_dialog():
    """Show marked questions dialog using sidebar"""
    marked_list = sorted(st.session_state.marked_questions)

    with st.sidebar:
        st.subheader("📌 Marked Questions")

        if not marked_list:
            st.warning("You haven't marked any questions yet!")
            if st.button("Close", key="marked_close"):
                st.session_state.show_marked = False
                st.rerun()
            return

        st.write("Your marked important questions:")

        selected_question = st.selectbox(
            "Select a question to go to:",
            options=marked_list,
            format_func=lambda x: f"Q{x+1}: {st.session_state.mcqs[x]['question'][:50]}...",
            key="marked_select"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Go to Question", key="marked_go"):
                st.session_state.current_question = selected_question
                st.session_state.show_marked = False
                st.rerun()
        with col2:
            if st.button("Cancel", key="marked_cancel"):
                st.session_state.show_marked = False
                st.rerun()


def show_results_page():
    st.title("🏆 Quiz Results")

    mcqs = st.session_state.mcqs
    total_questions = len(mcqs)
    correct_answers = sum(1 for i, ans in st.session_state.answered.items()
                          if ans and ans == mcqs[i]["answer"])
    percentage = (correct_answers / total_questions) * 100

    # Calculate grade
    if percentage >= 90:
        grade = "A+"
        grade_color = "🟢"
    elif percentage >= 80:
        grade = "A"
        grade_color = "🟢"
    elif percentage >= 70:
        grade = "B"
        grade_color = "🟡"
    elif percentage >= 60:
        grade = "C"
        grade_color = "🟠"
    else:
        grade = "F"
        grade_color = "🔴"

    # Performance message
    if percentage >= 80:
        message = "🎉 Excellent Performance!"
    elif percentage >= 60:
        message = "👍 Good Performance!"
    else:
        message = "📚 Keep Practicing!"

    # Results display
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Correct Answers", f"{correct_answers}/{total_questions}")

    with col2:
        st.metric("Percentage", f"{percentage:.1f}%")

    with col3:
        st.metric("Grade", f"{grade_color} {grade}")

    st.markdown("---")

    # Performance message
    st.subheader(message)

    # Marked questions section
    marked_list = sorted(st.session_state.marked_questions)

    if marked_list:
        st.subheader("📌 Marked Questions for Review")

        for idx in marked_list:
            mcq = mcqs[idx]
            user_answer = st.session_state.answered.get(idx)

            with st.expander(f"Question {idx+1}"):
                st.write(f"**Question:** {mcq['question']}")
                st.write("**Options:**")
                for opt, text in mcq['options'].items():
                    if user_answer == opt:
                        if opt == mcq['answer']:
                            st.write(
                                f"  ✅ {opt}. {text} (Your answer - Correct!)")
                        else:
                            st.write(
                                f"  ❌ {opt}. {text} (Your answer - Wrong!)")
                    elif opt == mcq['answer']:
                        st.write(f"  ✅ {opt}. {text} (Correct answer)")
                    else:
                        st.write(f"  {opt}. {text}")

                if st.button(f"Review Question {idx+1}", key=f"review_{idx}"):
                    st.session_state.current_question = idx
                    st.session_state.quiz_started = True
                    st.rerun()

    # Marked questions summary
    if marked_list:
        st.markdown("---")
        st.subheader("📌 Marked Questions Summary")
        st.info(
            f"You marked **{len(marked_list)} questions** during this quiz. You can create a focused practice quiz with just these questions!")

        # Show a preview of marked questions
        preview_count = min(3, len(marked_list))
        for i in range(preview_count):
            idx = marked_list[i]
            mcq = mcqs[idx]
            with st.expander(f"Marked Question {idx+1}"):
                st.write(f"**{mcq['question'][:100]}...**")
                user_answer = st.session_state.answered.get(idx)
                if user_answer:
                    if user_answer == mcq['answer']:
                        st.success(f"✅ You answered correctly: {user_answer}")
                    else:
                        st.error(
                            f"❌ You answered: {user_answer}, Correct: {mcq['answer']}")
                else:
                    st.warning("⏭️ You didn't answer this question")

    # Action buttons
    if st.session_state.is_random_quiz:
        # For random quizzes, show 5 buttons
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            if st.button("🔄 Retake Quiz", use_container_width=True):
                st.session_state.answered = {i: None for i in range(len(mcqs))}
                st.session_state.correct_answers = 0
                st.session_state.current_question = 0
                st.session_state.quiz_started = True
                st.session_state.show_results = False
                st.rerun()

        with col2:
            if st.button("🎲 New Random Quiz", use_container_width=True):
                # Generate a new random quiz with the same number of questions as the current quiz
                current_quiz_size = len(st.session_state.mcqs)
                if len(st.session_state.original_mcqs) >= current_quiz_size:
                    random_mcqs = generate_random_quiz(
                        st.session_state.original_mcqs, current_quiz_size)
                    st.session_state.mcqs = random_mcqs
                    st.session_state.answered = {
                        i: None for i in range(len(random_mcqs))}
                    st.session_state.correct_answers = 0
                    st.session_state.current_question = 0
                    st.session_state.marked_questions = set()
                    st.session_state.quiz_started = True
                    st.session_state.show_results = False
                    st.rerun()
                else:
                    st.error(
                        f"❌ Not enough questions! You have {len(st.session_state.original_mcqs)} questions, but need at least {current_quiz_size} for a random quiz.")

        with col3:
            if st.button("📌 Marked Questions Quiz", use_container_width=True):
                # Create a quiz with only marked questions
                marked_list = sorted(st.session_state.marked_questions)
                if marked_list:
                    marked_mcqs = [st.session_state.mcqs[i]
                                   for i in marked_list]
                    st.session_state.mcqs = marked_mcqs
                    st.session_state.answered = {
                        i: None for i in range(len(marked_mcqs))}
                    st.session_state.correct_answers = 0
                    st.session_state.current_question = 0
                    st.session_state.marked_questions = set()
                    st.session_state.is_random_quiz = False  # This is now a focused quiz
                    st.session_state.quiz_started = True
                    st.session_state.show_results = False
                    st.rerun()
                else:
                    st.warning("⚠️ No marked questions to create a quiz from!")

        with col4:
            if st.button("📊 Detailed Analysis", use_container_width=True):
                show_detailed_analysis()

        with col5:
            if st.button("🏠 Back to Home", use_container_width=True):
                st.session_state.quiz_started = False
                st.session_state.show_results = False
                st.rerun()
    else:
        # For full quizzes, show 4 buttons
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("🔄 Retake Quiz", use_container_width=True):
                st.session_state.answered = {i: None for i in range(len(mcqs))}
                st.session_state.correct_answers = 0
                st.session_state.current_question = 0
                st.session_state.quiz_started = True
                st.session_state.show_results = False
                st.rerun()

        with col2:
            if st.button("📌 Marked Questions Quiz", use_container_width=True):
                # Create a quiz with only marked questions
                marked_list = sorted(st.session_state.marked_questions)
                if marked_list:
                    marked_mcqs = [st.session_state.mcqs[i]
                                   for i in marked_list]
                    st.session_state.mcqs = marked_mcqs
                    st.session_state.answered = {
                        i: None for i in range(len(marked_mcqs))}
                    st.session_state.correct_answers = 0
                    st.session_state.current_question = 0
                    st.session_state.marked_questions = set()
                    st.session_state.is_random_quiz = False  # This is now a focused quiz
                    st.session_state.quiz_started = True
                    st.session_state.show_results = False
                    st.rerun()
                else:
                    st.warning("⚠️ No marked questions to create a quiz from!")

        with col3:
            if st.button("📊 Detailed Analysis", use_container_width=True):
                show_detailed_analysis()

        with col4:
            if st.button("🏠 Back to Home", use_container_width=True):
                st.session_state.quiz_started = False
                st.session_state.show_results = False
                st.rerun()


def show_detailed_analysis():
    """Show detailed analysis of quiz performance"""
    st.subheader("📊 Detailed Analysis")

    mcqs = st.session_state.mcqs

    # Question-by-question analysis
    for i, mcq in enumerate(mcqs):
        user_answer = st.session_state.answered.get(i)
        correct_answer = mcq['answer']

        with st.expander(f"Question {i+1}"):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Question:**")
                st.write(mcq['question'])

                st.write("**Your Answer:**")
                if user_answer:
                    if user_answer == correct_answer:
                        st.success(
                            f"✅ {user_answer}. {mcq['options'][user_answer]}")
                    else:
                        st.error(
                            f"❌ {user_answer}. {mcq['options'][user_answer]}")
                else:
                    st.warning("⏭️ Skipped")

            with col2:
                st.write("**Correct Answer:**")
                st.success(
                    f"✅ {correct_answer}. {mcq['options'][correct_answer]}")

                st.write("**Status:**")
                if user_answer == correct_answer:
                    st.success("Correct")
                elif user_answer:
                    st.error("Wrong")
                else:
                    st.warning("Skipped")


def extract_mcqs_from_excel(uploaded_file):
    """Extract MCQs from uploaded Excel file"""
    try:
        # Read the Excel file
        df = pd.read_excel(uploaded_file)

        return parse_excel_to_mcqs(df)

    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        return []


def parse_excel_to_mcqs(df):
    """Parse Excel DataFrame to MCQ format"""
    mcqs = []

    # Check if this is a multi-table Excel file
    # Look for table names in the first column
    table_names = []
    for i, row in df.iterrows():
        first_val = str(row.iloc[0]).strip()
        if first_val.startswith('Table') and first_val[5:].isdigit():
            table_names.append((i, first_val))

    if table_names:
        return parse_multi_table_excel(df, table_names)
    else:
        return parse_single_table_excel(df)


def parse_multi_table_excel(df, table_names):
    """Parse Excel file with multiple tables"""
    mcqs = []

    for table_idx, (start_row, table_name) in enumerate(table_names):
        end_row = len(df)
        if table_idx + 1 < len(table_names):
            end_row = table_names[table_idx + 1][0]

        # Extract table data
        table_data = df.iloc[start_row:end_row]

        # Parse this table
        table_mcqs = parse_single_table_excel(table_data, table_name)
        mcqs.extend(table_mcqs)

    return mcqs


def parse_single_table_excel(df, table_name="Single Table"):
    """Parse a single table section of the Excel file"""
    mcqs = []

    # Process the table based on the actual structure
    current_question = None
    current_choices = {}
    current_answer = None

    for i, row in df.iterrows():
        row_values = [str(val).strip() if not pd.isna(val)
                      else '' for val in row.values]

        # Skip empty rows and table headers
        if not any(row_values) or row_values[0] in ['', 'nan']:
            continue

        # Check if this row starts a new question
        if row_values[0] == 'Question' and len(row_values) > 1:
            # Save previous question if exists
            if current_question and current_choices and current_answer:
                mcqs.append({
                    "question": current_question,
                    "options": current_choices.copy(),
                    "answer": current_answer
                })

            # Start new question
            current_question = row_values[1]
            current_choices = {}
            current_answer = None

        # Check if this row is a choice (A, B, C, D)
        elif row_values[0] in ['A', 'B', 'C', 'D'] and len(row_values) > 1:
            choice_letter = row_values[0]
            choice_text = row_values[1]
            if choice_text and choice_text != 'nan':
                current_choices[choice_letter] = choice_text

                # Check if this choice is the correct answer (look in column 3)
                if len(row_values) > 3 and row_values[3] == choice_letter:
                    current_answer = choice_letter

    # Add the last question
    if current_question and current_choices and current_answer:
        mcqs.append({
            "question": current_question,
            "options": current_choices,
            "answer": current_answer
        })

    return mcqs


if __name__ == "__main__":
    main()
