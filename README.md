# PROJECT ARYABHUTT — V5.6 WEB

AI-assisted educational learning platform built with Streamlit. This browser adaptation keeps the original V5.6 Python/Pydroid source separately as the core/master reference.

## Files

- `app.py` — Streamlit web application, study tools, astronomy/visualizers, analytics, admin/session reports, offline library, QR scanner, chatbot, Game Zone, AI Challenge, Riddle Challenge, and Treasure Hunt.
- `aryabhutt_v56_core.py` — original V5.6 core/master source preserved separately; the web app is an adaptation and does not replace the original platform.
- `requirements.txt` — Python dependencies.
- `README_ARYABHUTT.txt` — concise project notes.

## Quiz and challenge lengths

Daily Quiz, AI Challenge, Riddle Challenge, and Treasure Hunt include question-count options of **5, 10, 15, 20, or 50**. The local challenge banks contain 50 questions and the riddle bank contains 50 riddles. These curated banks work offline; the label “AI Challenge” describes the mixed challenge theme and does not mean every question is generated live by Gemini.

## Run locally

1. Install Python 3.10 or newer.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Optional: configure a Gemini key using Streamlit secrets. Create `.streamlit/secrets.toml` locally (do not commit it):
   ```toml
   GEMINI_API_KEY = "your-key-here"
   ```
   `GOOGLE_API_KEY` is also accepted by the app if configured in the supported environment/secrets path.
4. Start the app:
   ```bash
   streamlit run app.py
   ```

## Streamlit Community Cloud

Push the app files to the repository root, select `app.py` as the app entry point, and add `GEMINI_API_KEY` in the app's **Settings → Secrets**. Never put an API key in source code, README files, screenshots, or Git commits.

## Notes

- Browser voice uses SpeechSynthesis where supported. Android/Pydroid-specific voice paths remain in the original core source.
- Session activity and reports are for the current web session unless persistent storage is separately configured.
- A Python syntax check can confirm parseability, but a live Gemini request requires a valid key and was not verified as part of this package.
