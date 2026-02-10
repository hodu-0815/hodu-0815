import streamlit as st
import requests
import re
import json
import google.generativeai as genai
import time
import random

# Page Config
st.set_page_config(page_title="일본어 복습 (Japanese Review)", page_icon="🇯🇵", layout="wide")

# --- Configuration: Documents ---
DOCS = {
    "2025년 3월": "1fRVKctT-AugOBh6cnBxs3xQZot8A7Xl1eEHrZdVCs_M",
    "2025년 4월": "1bmIMVBstBX-nQjwONtR3Sgixh_fLc4ERPHOzcFgmV04",
    "2025년 5월": "1vYm0woPy59Jwh1zvM57fCkMnqpZSS7vZAmqaqIlKxt4",
    "2025년 6월": "1p7tMZQWtEovCw-eZFzGMtsAmIQa0IZA7QFcRwaiSDA8",
    "2025년 7월": "1IFWsUU3XLQYfwuQ-uEjiTnVyBfovE8NoB7JqfNuFDMM",
    "2025년 8월": "1ftFaVRGxNI8ODx2Nq2huPcstpkCEyza-tmN8TcfjWus",
    "2025년 9월": "15qLaEi2Zt2TkQSCYazdu81hI4jSL6v7mYp5YvNtEKH0",
    "2025년 10월": "1dj6sNkMlEUN61eQMbe475yW7vyFcsXhr_N2kr4VLrzQ",
    "2025년 11월": "1G0tRrvYgTnwZ7nbitJ-8QheBpdc0TmIvJEjHYlNXoLE",
    "2025년 12월": "1cyfAuQ2X87WOVLwr_8SZQbvK27ZrsRyAmxGR5Rf8NoY",
    "2026년 1월": "1At-w6SNXvaQczO5sr4Hofuq8IV3q-ujBRGE7uXSa3gE",
    "2026년 2월": "1o3hJwHd0Le2rlYEk9g1ojqARiadDgDfnJvwXkosGThc"
}

# --- Logic: Parser ---
def parse_doc(text):
    lines = text.split('\n')
    lessons = {}
    current_date = None
    current_content = []
    
    date_pattern = re.compile(r'^@\s*(\d{1,2}-\d{1,2})')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = date_pattern.match(line)
        if match:
            if current_date:
                month = current_date.split('-')[0].zfill(2)
                if month not in lessons:
                    lessons[month] = []
                lessons[month].append({
                    'date': current_date,
                    'content': '\n'.join(current_content).strip()
                })
            
            current_date = match.group(1)
            current_content = []
        else:
            if current_date:
                current_content.append(line)

    if current_date:
        month = current_date.split('-')[0].zfill(2)
        if month not in lessons:
            lessons[month] = []
        lessons[month].append({
            'date': current_date,
            'content': '\n'.join(current_content).strip()
        })

    return lessons

@st.cache_data(ttl=3600)
def fetch_and_parse(doc_id):
    url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return parse_doc(response.text)
    except Exception as e:
        return None

# --- Logic: AI (Gemini) ---
def generate_quiz(content, difficulty, count=10):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except KeyError:
        st.error("GOOGLE_API_KEY가 설정되지 않았습니다 (.streamlit/secrets.toml).")
        return []

    genai.configure(api_key=api_key)
    
    # Using latest Flash-Lite as requested
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    # Define distinct rules and examples per difficulty
    if difficulty == "Easy":
        difficulty_instruction = "기본적인 단어와 간단한 문장 위주로 출제하세요."
        language_rules = """
        1. **질문**: 한국어로 작성하세요.
        2. **보기**: 일본어 단어와 한국어 발음을 함께 적거나, 한국어로만 적으세요. (예: 食べる (타베루) 또는 타베루)
        """
        example_options = '["타베루 (먹다)", "노무 (마시다)", "이쿠 (가다)", "쿠루 (오다)", "네루 (자다)"]'
        
    elif difficulty == "Normal":
        difficulty_instruction = "배운 내용을 충실히 복습할 수 있도록 적절한 난이도로 출제하세요."
        language_rules = """
        1. **질문**: 한국어로 작성하세요.
        2. **보기**: **일본어(한자/히라가나)**와 **한국어 발음**을 함께 표기하세요. 
           예: 食べる (타베루)
        """
        example_options = '["食べる (타베루)", "飲む (노무)", "行く (이쿠)", "来る (쿠루)", "寝る (네루)"]'

    elif difficulty == "Hard":
        difficulty_instruction = "복잡한 문법, 반말/존댓말 구분, 미묘한 뉘앙스 차이를 물어보세요."
        language_rules = """
        1. **질문**: 한국어로 작성하세요.
        2. **보기**: 반드시 **일본어(한자, 히라가나, 가타가나)**로만 작성하세요. 
           **주의**: 절대 한글 발음(예: 타베루)을 적지 마세요. 오직 일본어 텍스트만 보여주세요.
           예: 食べる (O), 食べる (타베루) (X)
        """
        example_options = '["食べる", "飲みます", "行った", "来る", "寝ない"]'

    elif difficulty == "Very Hard":
        difficulty_instruction = "고급 어휘와 자연스러운 일본어 표현을 다루세요. (N2~N3 수준)"
        language_rules = """
        1. **질문**: **일본어**로 작성하세요.
        2. **보기**: 반드시 **일본어(한자, 히라가나, 가타가나)**로만 작성하세요.
           **주의**: 절대 한글 발음이나 한국어 뜻을 적지 마세요.
        """
        example_options = '["召し上がる", "参る", "伺う", "存じる", "申す"]'

    prompt = f"""
    당신은 엄격하고 전문적인 일본어 학원 선생님입니다.
    아래의 [수업 노트]를 바탕으로 복습용 5지 선다형 퀴즈를 {{count}}문제 만들어주세요.

    난이도: {{difficulty}}
    {{difficulty_instruction}}

    **언어 규칙 (Language Rules) - 중요!:**
    {{language_rules}}
    
    * **해설(Explanation)**: 난이도와 상관없이 무조건 **한국어**로 설명하세요. 
      단, 일본어 단어나 문장이 나올 경우 반드시 괄호 안에 한국어 발음과 뜻을 적어주세요. 

    **기본 규칙:**
    1. 문제는 5지 선다형(객관식)이어야 합니다.
    2. 정답은 1개입니다.
    3. 문제 유형을 다양하게 섞으세요 (한자 읽기, 한국어 뜻 맞추기, 문법 채우기, 뉘앙스 차이 등).

    **중요한 출제 지침 (Critical):**
    * **단순 암기 금지**: "어제 몇 시까지 근무했습니까?"와 같이 문서 내의 **구체적인 사실(Fact)**을 묻지 마세요.
    * **응용 능력 평가**: 문서에 나온 **단어(Vocabulary)**와 **문법(Grammar)**을 활용하여, 새로운 문맥이나 일반적인 일본어 실력을 테스트하는 문제를 만드세요.
    * **문맥 포함 필수**: "다음 문장의 괄호에 들어갈 말은?" 같은 질문을 낼 때는, **반드시 그 '문장'을 질문 내용에 포함해야 합니다.**
      * 나쁜 예: "다음 괄호에 들어갈 조사는?" (문장이 없음)
      * 좋은 예: "다음 문장의 괄호에 들어갈 조사는? 「私は学校(  )行きます。」"

    **출력 형식 (JSON Array Only, No Markdown):**
    [
      {{
        "question": "다음 중 올바른 표현은?",
        "options": {{example_options}},
        "answer_index": 0, 
        "explanation": "'...'(설명)가 정답입니다.",
        "type": "문법"
      }}
    ]

    **주의사항 (Critical JSON Rules):**
    1. 반드시 **유효한 JSON** 형식이어야 합니다.
    2. 문자열 내부에서 큰따옴표(")를 사용할 경우 반드시 **이스케이프(\")** 처리하세요.
    3. Trailing Comma (마지막 항목 뒤 쉼표)를 남기지 마세요.

    [수업 노트]:
    {{content}}
    """

    try:
        response = model.generate_content(prompt)
        text = response.text
        # Clean markdown if present
        cleaned = text.replace("```json", "").replace("```", "").strip()
        
        # Additional cleanup for common JSON errors
        # Remove trailing commas in arrays/objects (simple regex approach)
        cleaned = re.sub(r',\s*([\]}])', r'\1', cleaned)
        
        return json.loads(cleaned)
    except Exception as e:
        st.error(f"문제 생성 실패 (JSON 오류): {e}")
        # Show raw output for debugging if needed (hidden in expander)
        with st.expander("AI 원본 응답 보기 (디버깅용)"):
            st.code(text if 'text' in locals() else "No response")
        return []

# ... (Imports are unchanged at the top, just replacing from line 173 onwards ideally, but I will do a larger chunk to restructure)

# --- Logic: Persistence & Stats ---
def get_current_stats():
    if 'history' not in st.session_state:
        st.session_state.history = {
            'mastery': {},  # "question_text": correct_count (int)
            'wrong_notes': []  # List of {question, options, answer_index, explanation, your_answer}
        }
    return st.session_state.history

def save_progress():
    history = get_current_stats()
    return json.dumps(history, ensure_ascii=False, indent=2)

def load_progress(uploaded_file):
    try:
        data = json.load(uploaded_file)
        # Validation could be added here
        st.session_state.history = data
        st.toast("데이터를 성공적으로 불러왔습니다!", icon="✅")
    except Exception as e:
        st.error(f"파일 불러오기 실패: {e}")

# --- UI: Sidebar ---
with st.sidebar:
    st.title("설정 (Settings)")
    
    selected_doc_name = st.selectbox("교재 선택 (Document)", list(DOCS.keys()))
    
    st.divider()
    
    difficulty = st.select_slider(
        "난이도 (Difficulty)",
        options=["Easy", "Normal", "Hard", "Very Hard"],
        value="Normal"
    )
    
    st.divider()
    
    st.subheader("데이터 관리 (Data)")
    
    # Init stats
    stats = get_current_stats()
    mastered_count = sum(1 for v in stats['mastery'].values() if v >= 3)
    wrong_count = len(stats['wrong_notes'])
    
    st.caption(f"🏆 마스터한 문제: {mastered_count}개")
    st.caption(f"📝 오답 노트: {wrong_count}개")

    # Download
    json_str = save_progress()
    st.download_button(
        label="내 기록 저장하기 (Download)",
        data=json_str,
        file_name="japanese_quiz_progress.json",
        mime="application/json"
    )
    
    # Upload
    uploaded_file = st.file_uploader("기록 불러오기 (Upload)", type=["json"])
    if uploaded_file is not None:
        if st.button("파일 적용하기"):
            load_progress(uploaded_file)
            st.rerun()

    st.divider()
    
    if st.button("캐시 삭제 (새로고침)"):
        st.cache_data.clear()
        st.rerun()

# --- UI: Main Content ---
st.title("🇯🇵 일본어 완벽 복습")

if "GOOGLE_API_KEY" not in st.secrets:
    st.warning("⚠️ `.streamlit/secrets.toml` 파일에 `GOOGLE_API_KEY`를 설정해주세요.")
    st.stop()

# State Management (Quiz Session)
if 'quiz_state' not in st.session_state:
    st.session_state.quiz_state = {
        'active': False,
        'questions': [],
        'current_index': 0,
        'score': 0,
        'selected_option': None,
        'checked': False,
        'completed': False,
        'mode': 'quiz' # 'quiz' or 'wrong_note'
    }

def start_quiz(questions, mode='quiz'):
    # Filter mastered questions if in normal quiz mode
    if mode == 'quiz':
        history = get_current_stats()
        filtered_questions = []
        for q in questions:
            q_text = q['question']
            # If mastered (>= 3 correct), skip
            if history['mastery'].get(q_text, 0) < 3:
                filtered_questions.append(q)
        
        if len(filtered_questions) < len(questions):
            st.toast(f"마스터한 {len(questions) - len(filtered_questions)}문제를 건너뛰었습니다! 😎")
            
        questions = filtered_questions

    if not questions:
        st.warning("출제할 문제가 없습니다! (모두 마스터했거나 데이터가 부족합니다)")
        return

    st.session_state.quiz_state = {
        'active': True,
        'questions': questions,
        'current_index': 0,
        'score': 0,
        'selected_option': None,
        'checked': False,
        'completed': False,
        'mode': mode
    }

def submit_answer():
    st.session_state.quiz_state['checked'] = True
    qs = st.session_state.quiz_state
    q = qs['questions'][qs['current_index']]
    history = get_current_stats()
    
    # Check answer
    correct_option = q['options'][q['answer_index']]
    is_correct = (qs['selected_option'] == correct_option)
    
    if is_correct:
        qs['score'] += 1
        # Update Mastery (Only in normal quiz mode)
        if qs['mode'] == 'quiz':
            current_mastery = history['mastery'].get(q['question'], 0)
            history['mastery'][q['question']] = current_mastery + 1
            if history['mastery'][q['question']] == 3:
                 st.toast("🎉 축하합니다! 이 문제를 마스터했습니다! (3번 연속 정답)", icon="🏆")
        
        # If answering correctly in wrong note mode, maybe remove it?
        # User requested "view wrong notes", not necessarily "remove logic".
        # Let's keep it simple: Wrong notes are a collection.
        # Optional: Remove from wrong notes if answered correctly? 
        # For now, let's keep them until manually cleared or just append.
        # Actually better UX: If I get it right in Wrong Note mode, I probably explicitly want to clear it?
        # Let's add a "Delete from note" button instead of auto-delete.
        
    else:
        # Incorrect behavior
        # Reset Mastery streak? Or decrement?
        # Usually stricter is reset to 0.
        if qs['mode'] == 'quiz':
            history['mastery'][q['question']] = 0
            
            # Add to Wrong Notes if not already present
            # distinct by question text
            exists = any(wn['question'] == q['question'] for wn in history['wrong_notes'])
            if not exists:
                # Store full question object + my wrong answer (optional)
                note_entry = q.copy()
                # note_entry['failed_at'] = ...
                history['wrong_notes'].append(note_entry)

def next_question():
    qs = st.session_state.quiz_state
    if qs['current_index'] < len(qs['questions']) - 1:
        qs['current_index'] += 1
        qs['selected_option'] = None
        qs['checked'] = False
    else:
        qs['completed'] = True

def reset_quiz():
    st.session_state.quiz_state['active'] = False


# --- Logic: Vocabulary ---
@st.cache_data(ttl=3600, show_spinner=False)
def extract_vocabulary(text):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        prompt = f"""
        당신은 일본어 선생님입니다. 
        아래 텍스트에서 학습에 필요한 **주요 단어와 숙어**를 추출해서 정리해주세요.
        
        [지침]
        1. 전체 문장이 아니라 **단어(Word)**나 **숙어(Idiom)** 위주로 뽑아주세요.
        2. 너무 쉬운 기초 단어는 제외하고, 학습 가치가 있는 단어 위주로 20~30개 정도 추출하세요.
        3. 문맥상 중요한 단어를 우선하세요.
        
        [출력 형식 (JSON Array Only)]
        [
          {{
            "word": "食べる",
            "meaning": "먹다",
            "pronunciation": "타베루"
          }},
          {{
            "word": "学生",
            "meaning": "학생",
            "pronunciation": "가쿠세이"
          }}
        ]
        
        [텍스트]:
        {text[:10000]} 
        """
        # Limit text length to avoid token limits for vocabulary extraction context
        
        response = model.generate_content(prompt)
        text_resp = response.text
        cleaned = text_resp.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except Exception as e:
        st.error(f"단어 추출 실패: {e}")
        return []



# --- Render Logic ---
def render_quiz_ui():
    qs = st.session_state.quiz_state
    
    if qs['completed']:
        if qs['score'] == len(qs['questions']):
            st.balloons()
        
        st.success(f"🎉 퀴즈 종료! 점수: {qs['score']} / {len(qs['questions'])}")
        
        if st.button("홈으로 돌아가기", key="home_quiz"):
            reset_quiz()
            st.rerun()
    else:
        q = qs['questions'][qs['current_index']]
        total = len(qs['questions'])
        
        # Progress
        progress = (qs['current_index']) / total
        st.progress(progress)
        mode_label = "오답 노트" if qs['mode'] == 'wrong_note' else "일반 퀴즈"
        st.caption(f"[{mode_label}] 문제 {qs['current_index'] + 1} / {total} • {q.get('type', '일반')}")
        
        # Question Styling
        st.markdown(f"### Q. {q['question']}")
        
        # Options
        selection = st.radio(
            "정답을 선택하세요:",
            q['options'],
            index=None,
            key=f"q_{qs['mode']}_{qs['current_index']}",
            disabled=qs['checked']
        )
        
        if selection:
            qs['selected_option'] = selection

        # Action Buttons
        if not qs['checked']:
            if st.button("정답 확인", type="primary", disabled=not selection, key=f"check_{qs['mode']}"):
                submit_answer()
                st.rerun()
        else:
            # Result Display
            correct_option = q['options'][q['answer_index']]
            is_correct = (qs['selected_option'] == correct_option)
            
            if is_correct:
                st.success("✅ 정답입니다!")
            else:
                st.error(f"❌ 오답입니다. 정답: {correct_option}")
                
            st.info(f"💡 해설: {q.get('explanation', '해설 없음')}")

            if st.button("다음 문제 ➡", type="primary", key=f"next_{qs['mode']}"):
                next_question()
                st.rerun()
                
        # Exit
        if st.button("퀴즈 그만두기", type="secondary", key=f"stop_{qs['mode']}"):
            reset_quiz()
            st.rerun()


# --- Main Tabs ---
tab1, tab2, tab3 = st.tabs(["📝 퀴즈 (Quiz)", "📒 오답 노트 (Wrong Notes)", "📓 단어장 (Vocabulary)"])

with tab1:
    # If active and in quiz mode, show quiz. Otherwise show dashboard.
    if st.session_state.quiz_state['active'] and st.session_state.quiz_state['mode'] == 'quiz':
        render_quiz_ui()
    elif st.session_state.quiz_state['active'] and st.session_state.quiz_state['mode'] == 'wrong_note':
        st.info("현재 '오답 노트' 탭에서 복습을 진행 중입니다.")
    else:
        # DASHBOARD VIEW
        st.subheader(f"📖 선택된 교재: {selected_doc_name}")
        
        data = fetch_and_parse(DOCS[selected_doc_name])
        
        if data:
            # Calculate stats
            total_days = sum(len(lessons) for lessons in data.values())
            
            col1, col2 = st.columns([3, 1])
            with col1:
                 st.write(f"총 **{total_days}일치**의 수업 내용이 있습니다.")
            with col2:
                 if st.button(f"'{selected_doc_name}' 전체 복습하기", type="primary", use_container_width=True):
                     with st.spinner("AI가 문제를 출제하고 있습니다..."):
                        all_content = []
                        for m in data:
                            for l in data[m]:
                                all_content.append(l['content'])
                        
                        full_text = "\n\n".join(all_content)
                        if len(full_text) > 30000:
                            full_text = full_text[:30000]
                            
                        # Request slightly more questions to account for filtering
                        questions = generate_quiz(full_text, difficulty, count=15)
                        if questions:
                            start_quiz(questions, mode='quiz')
                            st.rerun()
        else:
            st.error("문서를 불러오지 못했습니다.")

        st.markdown("---")

        # 2. Grand Exam (Bottom section)
        st.subheader("🏆 전체 종합 평가 (Grand Exam)")
        st.write("3월부터 지금까지 배운 모든 내용을 종합해서 테스트합니다.")
        
        if st.button("종합 평가 시작하기", type="secondary"):
             with st.spinner("모든 교재를 분석 중입니다..."):
                all_content = []
                
                for name, doc_id in DOCS.items():
                    d = fetch_and_parse(doc_id)
                    if d:
                        for m in d:
                            for l in d[m]:
                                 all_content.append(l['content'])
                
                if all_content:
                    full_text = "\n\n".join(all_content)
                    chunks = full_text.split('\n\n')
                    random.shuffle(chunks)
                    sample_text = "\n\n".join(chunks)[:35000]
                    
                    questions = generate_quiz(sample_text, difficulty, count=15)
                    if questions:
                        start_quiz(questions, mode='quiz')
                        st.rerun()
                else:
                    st.error("데이터가 없습니다.")

with tab2:
    st.subheader("📒 오답 노트 (Wrong Answer Notes)")
    
    # If active and in wrong_note mode, show quiz UI here
    if st.session_state.quiz_state['active'] and st.session_state.quiz_state['mode'] == 'wrong_note':
        render_quiz_ui()
    elif st.session_state.quiz_state['active'] and st.session_state.quiz_state['mode'] == 'quiz':
        st.info("현재 '퀴즈' 탭에서 학습을 진행 중입니다.")
    else:
        # Default Wrong Note List View
        history = get_current_stats()
        wrong_notes = history['wrong_notes']
        
        if not wrong_notes:
            st.info("아직 오답 노트가 비어있습니다. 문제를 틀리면 여기에 자동으로 추가됩니다.")
        else:
            st.write(f"총 **{len(wrong_notes)}개**의 틀린 문제가 있습니다.")
            
            if st.button("오답 노트 복습 시작하기 (Start Review)", type="primary"):
                review_qs = wrong_notes.copy()
                random.shuffle(review_qs)
                start_quiz(review_qs, mode='wrong_note')
                st.rerun()
                
            st.divider()
            
            for i, note in enumerate(reversed(wrong_notes)):
                # Store full question text for display
                q_text = note['question']
                # Correct Answer
                ans = note['options'][note['answer_index']]
                
                with st.expander(f"#{len(wrong_notes)-i}: {q_text}"):
                    st.write(f"**정답**: {ans}")
                    st.write(f"**해설**: {note.get('explanation', '')}")
                    
                    if st.button("이 문제 삭제", key=f"del_note_{i}"):
                        history['wrong_notes'].remove(note)
                        st.rerun()

with tab3:
    st.subheader("📓 AI 단어장 (Vocabulary List)")
    
    st.info("현재 선택된 강의 내용에서 중요 단어를 추출하여 단어장을 만듭니다.")
    
    col_v1, col_v2 = st.columns([3, 1])
    
    with col_v1:
        target_scope = st.radio("추출 대상", ["현재 선택된 교재", "모든 교재 (오래 걸림)"], horizontal=True)
    
    with col_v2: 
        if st.button("단어장 생성", type="primary"):
            with st.spinner("단어를 추출하고 있습니다..."):
                source_text = ""
                if target_scope == "현재 선택된 교재":
                    d = fetch_and_parse(DOCS[selected_doc_name])
                    if d:
                        all_c = []
                        for m in d:
                            for l in d[m]:
                                all_c.append(l['content'])
                        source_text = "\\n".join(all_c)
                else:
                    # All docs
                    all_c = []
                    for k, v in DOCS.items():
                        d = fetch_and_parse(v)
                        if d:
                             for m in d:
                                for l in d[m]:
                                    all_c.append(l['content'])
                    source_text = "\\n".join(all_c)
                
                if source_text:
                    vocab_list = extract_vocabulary(source_text)
                    st.session_state['vocab_list'] = vocab_list
                else:
                    st.error("데이터가 없습니다.")
    
    st.divider()
    
    if 'vocab_list' in st.session_state and st.session_state['vocab_list']:
        # Toggle options
        hide_korean = st.checkbox("뜻 & 발음 숨기기 (암기 테스트용)")
        
        vocab_data = st.session_state['vocab_list']
        
        # DataFrame Display
        # Create a display list based on toggle
        display_data = []
        for v in vocab_data:
            row = {"일본어 (Japanese)": v['word']}
            if not hide_korean:
                row["뜻 (Meaning)"] = v['meaning']
                row["발음 (Pronunciation)"] = v['pronunciation']
            display_data.append(row)
            
        st.table(display_data)
    else:
        st.caption("단어장을 생성해주세요.")

