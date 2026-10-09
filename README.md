# PROJECT ARYABHUTT V5.6 WEB

Hindi-first educational Streamlit app with Gemini chat and an offline knowledge fallback.

## Files
- `app.py` — Streamlit web application
- `requirements.txt` — Python dependencies
- `README.md` — setup notes
- `aryabhutt_v56_core.py` — preserved original core/reference file

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Secrets
In the Streamlit app's Settings/Secrets, keep the existing API key if it is already saved for this same app. Do not paste the key into source code or share it in screenshots.

```toml
GEMINI_API_KEY = "your-key"
GEMINI_MODEL = "gemini-3.8-flash"
ADMIN_PASSWORD = "choose-a-strong-private-password"
```

`GEMINI_MODEL` is optional; the app defaults to `gemini-3.8-flash`. A saved key does not guarantee a successful API request: timeouts, quota, network access, or account/model availability can still cause the app to use its clearly labelled offline fallback.

## Activity records
The app now records anonymous app sessions in a local SQLite database and shows those records in Teacher/Admin and Data & Analytics. These are **sessions, not verified unique students**: one child can use multiple devices and multiple children can share one device. The SQLite file is local to the running app and may be lost on restart/redeployment or may not be shared across multiple app instances. For permanent school-wide records, connect a hosted database before relying on the dashboard for official statistics. No student name is collected automatically.

## Admin safety
Set `ADMIN_PASSWORD` in Streamlit Secrets before publishing. The legacy demo fallback remains `aryabhutt` if the secret is missing, so do not publish the app until a private password is configured.
