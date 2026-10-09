PROJECT ARYABHUTT — V5.6 WEB
AI-Assisted Educational Learning Platform

FILES
- app.py: Streamlit web app, study tools, chatbot, Game Zone, AI Challenge, Riddle Challenge, and Treasure Hunt.
- aryabhutt_v56_core.py: original V5.6 Python/Pydroid core/master reference, preserved separately.
- requirements.txt: dependencies for the web adaptation.
- README.md: full setup and deployment instructions.

CHALLENGE QUESTION COUNTS
Daily Quiz, AI Challenge, Riddle Challenge, and Treasure Hunt let users choose 5, 10, 15, 20, or 50 questions. The curated local bank contains 50 challenge questions and 50 riddles, so these activities can still run without Gemini. AI Challenge uses this offline question bank; it does not claim every question is generated live by AI.

RUN
1. Install Python 3.10+.
2. Run: pip install -r requirements.txt
3. Optional Gemini setup: add GEMINI_API_KEY in Streamlit Secrets. Never place API keys in app.py or commit them to GitHub.
4. Run: streamlit run app.py

DEPLOYMENT
For Streamlit Community Cloud, use app.py as the entry point and add GEMINI_API_KEY under app Settings > Secrets. Do not commit secrets.

VOICE
The browser adaptation uses browser SpeechSynthesis where supported. Android/Pydroid-specific voice routes remain in the original V5.6 core source.

NOTE
The original V5.6 Python project is preserved separately as the core/master reference. The web version is an adaptation for browser access. Live Gemini behavior requires a valid configured key and has not been verified by a syntax check.
