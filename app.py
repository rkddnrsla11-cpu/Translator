"""다국어 번역기 - Streamlit 앱"""

import os

import openai
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MODEL = os.getenv("OPENAI_MODEL", "").strip() or "gpt-6-astra"
MAX_CHARS = 5000
WARN_CHARS = 4500  # 이 글자 수를 넘으면 글자 수 표시 색이 바뀐다.

# 언어를 추가하려면 이 딕셔너리에 한 줄만 추가하면 된다.
LANGUAGES = {
    # 국기 이모지는 Windows에서 "US/JP" 같은 글자로 보이므로 텍스트 라벨을 쓴다.
    "english":    {"label": "영어 · English",       "name": "English"},
    "japanese":   {"label": "일본어 · 日本語",       "name": "Japanese"},
    "vietnamese": {"label": "베트남어 · Tiếng Việt", "name": "Vietnamese"},
}

API_TIMEOUT_SECONDS = 30
API_MAX_RETRIES = 2

SYSTEM_PROMPT = (
    "You are a professional translator. Translate the user's text into {target_language}. "
    "Preserve the original meaning, tone, and line breaks. "
    "Output only the translated text without any explanation."
)

CSS = """
<style>
.block-container { max-width: 760px; padding-top: 2.5rem; padding-bottom: 3rem; }
h1 { word-break: keep-all; }
.app-subtitle { opacity: 0.7; margin-top: -0.75rem; margin-bottom: 1.25rem; }
.char-count { text-align: right; font-size: 0.85rem; opacity: 0.6; margin-top: -0.5rem; }
.char-count.near { color: #e8590c; opacity: 1; }
.char-count.over { color: #e03131; opacity: 1; font-weight: 600; }
.stTextArea textarea { font-size: 1rem; line-height: 1.6; border-radius: 10px; }
.stButton button { border-radius: 10px; font-weight: 600; padding: 0.6rem 0; }
.result-label { font-weight: 600; font-size: 1.05rem; margin-bottom: 0.25rem; }
.empty-state { text-align: center; opacity: 0.55; padding: 1.5rem 0; }
[data-testid="stCode"] pre { font-size: 1rem; line-height: 1.6; }
/* 번역문은 코드가 아니므로 복사 버튼만 살리고 글꼴은 본문 글꼴을 쓴다. */
[data-testid="stCode"] pre, [data-testid="stCode"] code {
  font-family: "Source Sans", "Source Sans Pro", "Malgun Gothic", "Apple SD Gothic Neo", sans-serif;
}
@media (max-width: 640px) {
  .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 1.5rem; }
}
</style>
"""


class TranslationError(Exception):
    """사용자에게 그대로 보여줘도 되는 번역 오류 메시지."""


@st.cache_resource
def get_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key, timeout=API_TIMEOUT_SECONDS, max_retries=API_MAX_RETRIES)


def translate(text: str, target_language: str) -> str:
    """OpenAI 모델로 text를 target_language로 번역해 반환한다."""
    client = get_client(API_KEY)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.format(target_language=target_language)},
                {"role": "user", "content": text},
            ],
        )
    # 오류 원문에는 API 키 일부가 포함될 수 있으므로 메시지를 직접 노출하지 않는다.
    except openai.AuthenticationError:
        raise TranslationError("API 키 인증에 실패했습니다. .env의 OPENAI_API_KEY를 확인해주세요.")
    except openai.PermissionDeniedError:
        raise TranslationError("이 API 키로는 해당 모델을 사용할 권한이 없습니다.")
    except openai.NotFoundError:
        raise TranslationError(f"모델 '{MODEL}'을(를) 찾을 수 없습니다. .env의 OPENAI_MODEL을 확인해주세요.")
    except openai.RateLimitError:
        raise TranslationError("요청 한도를 초과했거나 크레딧이 부족합니다. 잠시 후 다시 시도해주세요.")
    except openai.APITimeoutError:
        raise TranslationError("응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.")
    except openai.APIConnectionError:
        raise TranslationError("OpenAI 서버에 연결할 수 없습니다. 네트워크 연결을 확인해주세요.")
    except openai.APIStatusError as e:
        raise TranslationError(f"번역 요청 중 오류가 발생했습니다. (HTTP {e.status_code})")

    content = response.choices[0].message.content or ""
    result = content.strip()
    if not result:
        raise TranslationError("번역 결과가 비어 있습니다. 다시 시도해주세요.")
    return result


def request_translation(code: str) -> None:
    """버튼 콜백: 어떤 언어 버튼이 눌렸는지 기록한다."""
    st.session_state["pending"] = code


# ---------- 화면 ----------
st.set_page_config(page_title="다국어 번역기", page_icon="🌐", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)

st.title("🌐 다국어 번역기")
st.markdown('<p class="app-subtitle">글을 입력하고 번역할 언어 버튼을 눌러주세요.</p>', unsafe_allow_html=True)

if not API_KEY:
    st.error("OPENAI_API_KEY가 설정되지 않았습니다. 프로젝트 폴더의 .env 파일에 API 키를 입력한 뒤 앱을 다시 실행해주세요.")

text = st.text_area(
    "번역할 내용",
    key="source_text",
    placeholder="번역할 내용을 입력하세요...",
    height=200,
    label_visibility="collapsed",
)
count_class = "over" if len(text) > MAX_CHARS else "near" if len(text) >= WARN_CHARS else ""
st.markdown(
    f'<div class="char-count {count_class}">{len(text):,} / {MAX_CHARS:,}</div>',
    unsafe_allow_html=True,
)

# 버튼은 번역 처리 뒤에 그려야 방금 번역한 언어를 강조할 수 있으므로 자리만 먼저 잡아둔다.
button_row = st.container()
message_area = st.container()
result_area = st.container(border=True)

pending = st.session_state.pop("pending", None)
if pending:
    if not text.strip():
        message_area.warning("번역할 내용을 입력해주세요.")
    elif len(text) > MAX_CHARS:
        message_area.warning(f"입력은 최대 {MAX_CHARS:,}자까지 가능합니다. (현재 {len(text):,}자)")
    else:
        try:
            with result_area, st.spinner("번역 중..."):
                translated = translate(text, LANGUAGES[pending]["name"])
            st.session_state["result"] = {"lang": pending, "text": translated}
        except TranslationError as e:
            message_area.error(str(e))

result = st.session_state.get("result")

with button_row:
    cols = st.columns(len(LANGUAGES))
    for col, (code, lang) in zip(cols, LANGUAGES.items()):
        col.button(
            lang["label"],
            key=f"btn_{code}",
            type="primary" if result and result["lang"] == code else "secondary",
            disabled=not API_KEY,
            width="stretch",
            on_click=request_translation,
            args=(code,),
        )

with result_area:
    if result:
        st.markdown(
            f'<div class="result-label">{LANGUAGES[result["lang"]]["label"]} 번역 결과</div>',
            unsafe_allow_html=True,
        )
        st.code(result["text"], language=None, wrap_lines=True)
    else:
        st.markdown('<div class="empty-state">번역 결과가 여기에 표시됩니다.</div>', unsafe_allow_html=True)
