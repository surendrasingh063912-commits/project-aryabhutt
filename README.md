# PROJECT ARYABHUTT V5.6 WEB — merged recovery package

Hindi-first educational Streamlit app. This recovery build combines the Gemini fallback improvement with the bilingual 50-question challenge bank and keeps the separate 50-riddle bank, Treasure Hunt, Study Center, Offline Knowledge Library, QR Scanner, visualizers, reports, feedback, settings, and Teacher/Admin screens.

## Four files
- `app.py` — Streamlit app, Gemini chatbot + offline fallback, student check-in, activity tracking, quizzes and admin screens.
- `requirements.txt` — Python dependencies.
- `README.md` — setup notes.
- `aryabhutt_v56_core.py` — preserved original core/reference file.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Secrets
In the same Streamlit app's Settings/Secrets, keep the existing API key if already saved. Never paste API keys into `app.py`, commit them to GitHub, or show them in screenshots.

```toml
GEMINI_API_KEY = "your-existing-key"
GEMINI_MODEL = "gemini-3.8-flash"
ADMIN_PASSWORD = "choose-a-strong-private-password"
```

`GEMINI_MODEL` is optional. The app tries the configured model followed by fallback model IDs. Settings includes a small live Gemini connection test. A saved key does not guarantee success: access, quota, API service status, model availability, or network timeouts can still cause the offline fallback to appear.

## Student check-in and Teacher/Admin
- On opening the app, a learner enters their first name and may choose a school and class/section.
- Teacher/Admin can add schools and student records.
- The dashboard lists session start date, weekday, time-in, last activity, approximate active minutes, school/class and recent activities; it also provides a CSV attendance export.
- Questions and answers are not stored in the activity log; only event types and small summary details (such as quiz score) are stored.
- Student first names are personal information. Use school/guardian approval and limit who can access the Admin password.

## Important storage limitation
Activity data uses a local SQLite file (`aryabhutt_activity.db`) on the running host. It persists across reruns while that file remains, but Streamlit-hosted deployments may lose local files during restart/redeploy and multiple app instances may not share the same file. This is not yet permanent school-wide attendance storage. For official long-term records, connect a hosted database such as PostgreSQL/Supabase and configure its credentials securely.

## Admin safety
Set `ADMIN_PASSWORD` in Streamlit Secrets before publishing. If it is missing, the legacy demo password `aryabhutt` remains available and the app displays a warning. Do not publish with the demo password.

## Tests and limitations
The release package is checked for ZIP integrity, Python syntax, question-bank counts, and required feature markers. A real Gemini call must still be tested in the deployed Streamlit app because this build environment has no Streamlit/Gemini runtime or access to the user's secret key.
