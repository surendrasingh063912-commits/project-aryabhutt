PROJECT ARYABHUTT — V5.6 WEB

Files:
- app.py: complete Streamlit web app with the existing study, astronomy, analytics, admin, offline library, QR scanner and Gemini chatbot sections.
- requirements.txt: Python dependencies.

New challenge features:
- Question count options: 5, 10, 15, 20, or 50.
- 50-question Daily Quiz / AI Challenge / Treasure Hunt bank.
- 50-riddle Riddle Challenge bank.
- Challenge banks are local and can be used when Gemini is temporarily unavailable.

Run locally:
1. Install Python 3.10+.
2. Run: pip install -r requirements.txt
3. Set GEMINI_API_KEY in Streamlit secrets (or environment/config appropriate for your deployment).
4. Run: streamlit run app.py

For Streamlit Community Cloud, upload app.py and requirements.txt to the repository root, then add GEMINI_API_KEY in App settings > Secrets. Do not place API keys in app.py or commit them to GitHub.

Note: syntax was checked; a live Gemini API request was not tested by this package build.
