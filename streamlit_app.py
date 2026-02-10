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
    "3월": "1fRVKctT-AugOBh6cnBxs3xQZot8A7Xl1eEHrZdVCs_M",
    "4월": "1bmIMVBstBX-nQjwONtR3Sgixh_fLc4ERPHOzcFgmV04",
    "5월": "1vYm0woPy59Jwh1zvM57fCkMnqpZSS7vZAmqaqIlKxt4",
    "6월": "1p7tMZQWtEovCw-eZFzGMtsAmIQa0IZA7QFcRwaiSDA8",
    "7월": "1IFWsUU3XLQYfwuQ-uEjiTnVyBfovE8NoB7JqfNuFDMM",
    "8, 9월": "1ftFaVRGxNI8ODx2Nq2huPcstpkCEyza-tmN8TcfjWus",
    "10, 11, 12, 1월": "1dj6sNkMlEUN61eQMbe475yW7vyFcsXhr_N2kr4VLrzQ"
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
    
    difficulty_instruction = ""
    language_rules = "질문과 보기는 모두 **한국어**로 작성하세요. (일본어 단어는 한글 발음으로 표기, 예: 타베루)"

    if difficulty == "Easy":
        difficulty_instruction = "기본적인 단어와 간단한 문장 위주로 출제하세요."
    elif difficulty == "Normal":
        difficulty_instruction = "배운 내용을 충실히 복습할 수 있도록 적절한 난이도로 출제하세요."
    elif difficulty == "Hard":
        difficulty_instruction = "복잡한 문법, 반말/존댓말 구분, 미묘한 뉘앙스 차이를 물어보세요."
        language_rules = """
        1. **질문**: 한국어로 작성하세요.
        2. **보기**: 반드시 **일본어(한자, 히라가나, 가타가나)**로 작성하세요. 
           **주의**: 절대 한글 발음(예: 타베루)을 적지 마세요. 실제 일본어 텍스트(예: 食べる)를 사용하세요.
        """
    elif difficulty == "Very Hard":
        difficulty_instruction = "고급 어휘와 자연스러운 일본어 표현을 다루세요. (너무 어렵지 않게, N2~N3 수준)"
        language_rules = """
        1. **질문**: 반드시 **일본어**로 작성하세요.
        2. **보기**: 반드시 **일본어(한자, 히라가나, 가타가나)**로 작성하세요.
           **주의**: 절대 한글 발음(예: 타베루)을 적지 마세요. 실제 일본어 텍스트(예: 食べる)를 사용하세요.
        """

    prompt = f"""
    당신은 엄격하고 전문적인 일본어 학원 선생님입니다.
    아래의 [수업 노트]를 바탕으로 복습용 5지 선다형 퀴즈를 {count}문제 만들어주세요.

    난이도: {difficulty}
    {difficulty_instruction}

    **언어 규칙 (Language Rules) - 중요!:**
    {language_rules}
    
    * **해설(Explanation)**: 난이도와 상관없이 무조건 **한국어**로 설명하세요. 
      단, 일본어 단어나 문장이 나올 경우 반드시 괄호 안에 한국어 발음과 뜻을 적어주세요. 
      예: "食べる(타베루, 먹다)는..."

    **기본 규칙:**
    1. 문제는 5지 선다형(객관식)이어야 합니다.
    2. 정답은 1개입니다.
    3. 문제 유형을 다양하게 섞으세요 (한자 읽기, 한국어 뜻 맞추기, 문법 채우기, 뉘앙스 차이 등).

    **중요한 출제 지침 (Critical):**
    * **단순 암기 금지**: "어제 몇 시까지 근무했습니까?"와 같이 문서 내의 **구체적인 사실(Fact)**을 묻지 마세요.
    * **응용 능력 평가**: 문서에 나온 **단어(Vocabulary)**와 **문법(Grammar)**을 활용하여, 새로운 문맥이나 일반적인 일본어 실력을 테스트하는 문제를 만드세요.
      * 나쁜 예: "수업 노트에서 선생님은 무엇을 먹었나요?"
      * 좋은 예: "다음 중 '먹다(食べる)'의 정중한 과거형으로 올바른 것은?" 또는 "문맥상 괄호 안에 들어갈 조사로 적절한 것은?"

    **출력 형식 (JSON Array Only, No Markdown):**
    [
      {{
        "question": "다음 중 '먹다'의 정중한 표현은?",
        "options": ["타베루", "타베마스", "논데", "이쿠", "쿠루"],
        "answer_index": 1, 
        "explanation": "'타베마스'가 정중한 표현입니다.",
        "type": "문법"
      }}
    ]

    **주의사항 (Critical JSON Rules):**
    1. 반드시 **유효한 JSON** 형식이어야 합니다.
    2. 문자열 내부에서 큰따옴표(")를 사용할 경우 반드시 **이스케이프(\")** 처리하세요.
    3. Trailing Comma (마지막 항목 뒤 쉼표)를 남기지 마세요.

    [수업 노트]:
    {content}
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
    
    if st.button("캐시 삭제 (새로고침)"):
        st.cache_data.clear()
        st.rerun()

# --- UI: Main Content ---
st.title("🇯🇵 일본어 완벽 복습")

if "GOOGLE_API_KEY" not in st.secrets:
    st.warning("⚠️ `.streamlit/secrets.toml` 파일에 `GOOGLE_API_KEY`를 설정해주세요.")
    st.stop()

# State Management
if 'quiz_state' not in st.session_state:
    st.session_state.quiz_state = {
        'active': False,
        'questions': [],
        'current_index': 0,
        'score': 0,
        'selected_option': None,
        'checked': False,
        'completed': False
    }

def start_quiz(questions):
    st.session_state.quiz_state = {
        'active': True,
        'questions': questions,
        'current_index': 0,
        'score': 0,
        'selected_option': None,
        'checked': False,
        'completed': False
    }

def submit_answer():
    st.session_state.quiz_state['checked'] = True
    qs = st.session_state.quiz_state
    q = qs['questions'][qs['current_index']]
    
    # Check answer
    if qs['selected_option'] == q['options'][q['answer_index']]:
        qs['score'] += 1

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


# QUIZ VIEW
if st.session_state.quiz_state['active']:
    qs = st.session_state.quiz_state
    
    if qs['completed']:
        if qs['score'] == len(qs['questions']):
            st.balloons()
        
        st.success(f"🎉 퀴즈 종료! 점수: {qs['score']} / {len(qs['questions'])}")
        
        if st.button("홈으로 돌아가기"):
            reset_quiz()
            st.rerun()
    else:
        q = qs['questions'][qs['current_index']]
        total = len(qs['questions'])
        
        # Progress
        progress = (qs['current_index']) / total
        st.progress(progress)
        st.caption(f"문제 {qs['current_index'] + 1} / {total} • {q.get('type', '일반')}")
        
        # Question Styling
        st.markdown(f"### Q. {q['question']}")
        
        # Options
        # Use radio for selection. If checked, disable it.
        # We need a key that changes per question to reset selection
        selection = st.radio(
            "정답을 선택하세요:",
            q['options'],
            index=None,
            key=f"q_{qs['current_index']}",
            disabled=qs['checked']
        )
        
        if selection:
            qs['selected_option'] = selection

        # Action Buttons
        if not qs['checked']:
            if st.button("정답 확인", type="primary", disabled=not selection):
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

            if st.button("다음 문제 ➡", type="primary"):
                next_question()
                st.rerun()
                
        # Exit
        if st.button("퀴즈 그만두기", type="secondary"):
            reset_quiz()
            st.rerun()

else:
    # DASHBOARD VIEW
    
    # 1. Current Document Review
    st.subheader(f"📖 선택된 교재: {selected_doc_name}")
    
    # Load Data
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
                        
                    questions = generate_quiz(full_text, difficulty, count=10)
                    if questions:
                        start_quiz(questions)
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
                
                questions = generate_quiz(sample_text, difficulty, count=10)
                if questions:
                    start_quiz(questions)
                    st.rerun()
            else:
                st.error("데이터가 없습니다.")
