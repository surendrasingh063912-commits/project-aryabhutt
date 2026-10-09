# PROJECT ARYABHUTT — V5.6 WEB

AI-assisted educational learning platform built with Streamlit.

## Files (four-file package)
- `app.py` — Streamlit app, Gemini chatbot, browser voice, quizzes, Treasure Hunt, AI Challenge, Study Center, visualizers, reports, feedback, settings and Teacher/Admin dashboard.
- `requirements.txt` — Python dependencies.
- `README.md` — setup and deployment instructions.
- `aryabhutt_v56_core.py` — original V5.6 core/master reference, preserved separately.

## Run locally
1. Install Python 3.10 or newer.
2. Run `pip install -r requirements.txt`.
3. Run `streamlit run app.py`.

## Gemini setup
Add `GEMINI_API_KEY` as a Streamlit secret. `GOOGLE_API_KEY` is also accepted. Do not commit API keys to GitHub. The app tries supported Gemini model IDs in sequence and shows a status/error when online generation fails. Actual availability still depends on the API key, project access, quota and network.

Example `.streamlit/secrets.toml` (keep this file private and out of Git):
```toml
GEMINI_API_KEY = "paste-your-key-here-locally-only"
```

## Quiz and challenge modes
Daily Quiz, AI Challenge, Riddle/Brain Challenge and Treasure Hunt offer 5, 10, 15, 20 or 50 questions. The question bank includes Hindi and English prompts, three-choice multiple-choice questions and short-answer questions. The sidebar language selection controls question language.

## Voice and data
Voice uses browser SpeechSynthesis where supported; availability depends on the browser/device. Some analytics/student data are session-based and are not a full cloud database. The original V5.6 core source remains a separate reference file.
