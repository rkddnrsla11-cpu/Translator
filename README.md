# 🌐 다국어 번역기

입력한 글을 영어 / 일본어 / 베트남어로 번역하는 Streamlit 앱입니다. 번역에는 OpenAI API를 사용합니다.

## 설치

```bash
pip install -r requirements.txt
```

## 설정

`.env.example`을 복사해 `.env`를 만들고 값을 채웁니다.

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-6-astra
```

`OPENAI_MODEL`을 비워두면 기본값 `gpt-6-astra`(GPT-6-Astra)를 사용합니다.

## 실행

```bash
streamlit run app.py
```

브라우저에서 http://localhost:8501 에 접속합니다.
