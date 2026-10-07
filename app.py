import os, random, time, math, importlib.util
from datetime import datetime
import streamlit as st

# Load the user's ORIGINAL V5.6 source only for its knowledge/content constants.
# The terminal input() UI is not executed in the browser.
SOURCE_PATH = os.path.join(os.path.dirname(__file__), "PROJECT_ARYABHUTT_V5.6_FINAL_COMPLETE_GEMINI_VOICE_FIXED-1.py")
legacy = None
try:
    spec = importlib.util.spec_from_file_location("aryabhutt_v56", SOURCE_PATH)
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
except Exception:
    legacy = None

APP_NAME = "PROJECT ARYABHUTT: DIGITAL LEARNING ECOSYSTEM"
TAGLINE = "Learn • Visualize • Practice • Explore • Track"

st.set_page_config(page_title="PROJECT ARYABHUTT", page_icon="🌼", layout="wide")

if "language" not in st.session_state: st.session_state.language = "hi"
if "scores" not in st.session_state: st.session_state.scores = {}
if "chat" not in st.session_state: st.session_state.chat = []
if "feedback" not in st.session_state: st.session_state.feedback = ""


def ui(hi, en):
    return hi if st.session_state.language == "hi" else en


def metric(name, value=1):
    st.session_state.scores[name] = st.session_state.scores.get(name, 0) + value


def offline_answer(question):
    if legacy:
        try:
            ok, ans = legacy._v56_offline_lookup(question)
            if ok: return ans
        except Exception:
            pass
    return "इस प्रश्न का उत्तर अभी Offline Knowledge Book में उपलब्ध नहीं है।"


def gemini_answer(question):
    key = None
    try:
        key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        pass
    key = key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        return None, "offline"
    model = "gemini-3.8-flash"
    try:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        prompt = ("You are Acharya Aryabhatta, a friendly Class 8 educational assistant. "
                  "Answer in simple Hindi/Hinglish unless the student asks in English. "
                  "Be accurate, child-friendly and concise. Never invent historical facts.\n\n"
                  f"Student question: {question}")
        r = requests.post(url, json={"contents":[{"parts":[{"text":prompt}]}]}, timeout=15)
        r.raise_for_status()
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return text, "online"
    except Exception:
        return None, "error"


def ask_ai(question):
    answer, mode = gemini_answer(question)
    if answer: return answer, mode
    return offline_answer(question), "offline"


def header():
    st.title("🌼 PROJECT ARYABHUTT")
    st.caption(f"{APP_NAME}  |  {TAGLINE}")


def chat_page():
    st.header("🤖 Aryabhutt AI Chatbot")
    st.info(ui("Gemini उपलब्ध होने पर AI उत्तर देगा; अन्यथा V5.6 की Offline Knowledge Book से उत्तर मिलेगा।", "Gemini is used when available; otherwise answers come from the V5.6 Offline Knowledge Book."))
    q = st.text_area(ui("अपना प्रश्न लिखें", "Ask your question"), placeholder="आर्यभट्ट कौन थे? / What is photosynthesis? / 25 का वर्ग क्या है?")
    if st.button(ui("पूछें", "Ask"), type="primary") and q.strip():
        ans, mode = ask_ai(q.strip())
        st.session_state.chat.append((q.strip(), ans, mode))
        metric("questions")
    for q0, a0, mode in reversed(st.session_state.chat[-10:]):
        with st.chat_message("user"): st.write(q0)
        with st.chat_message("assistant"):
            st.write(a0)
            st.caption("🟢 Online AI" if mode == "online" else "📚 Offline Knowledge")


def daily_quiz():
    st.header("📚 Daily Quiz — 20 Questions")
    qs = legacy.DAILY_QUIZ if legacy else []
    if not qs: return
    if "quiz_order" not in st.session_state: st.session_state.quiz_order = random.sample(qs, len(qs))
    score = 0; answered = 0
    with st.form("daily_quiz"):
        for i,(q,opts,c) in enumerate(st.session_state.quiz_order,1):
            ans = st.radio(f"Q{i}. {q}", opts, key=f"dq_{i}")
            if ans == opts[int(c)-1]: score += 1
            answered += 1
        submitted = st.form_submit_button("Submit Quiz")
    if submitted:
        st.success(f"Score: {score}/{answered}")
        metric("Daily Quiz", score)
        if score >= 16: st.balloons()


def game_zone():
    st.header("🎮 Game Zone — 10 Games + Daily Quiz")
    game = st.selectbox("Choose a game", ["Guess the Number","Flip a Coin","Rock-Paper-Scissors","Color Matcher","Roll the Dice","Math Quiz","Magic Ball 8","Word Scramble","Animal Guessing","Click Speed Test","Daily Quiz"])
    rounds = st.slider("Rounds", 1, 30, 5)
    if game == "Daily Quiz":
        daily_quiz(); return
    if game == "Guess the Number":
        if "gn" not in st.session_state: st.session_state.gn = random.randint(1,100)
        g = st.number_input("Guess 1–100", 1, 100, 50)
        if st.button("Check Guess"):
            if g == st.session_state.gn: st.success("🎉 Correct!"); metric(game)
            elif g < st.session_state.gn: st.info("Try a higher number")
            else: st.info("Try a lower number")
        if st.button("New Number"): st.session_state.gn = random.randint(1,100); st.rerun()
    elif game == "Flip a Coin":
        if st.button("Flip"):
            st.write("🪙", random.choice(["Heads","Tails"])); metric(game)
    elif game == "Rock-Paper-Scissors":
        p = st.selectbox("Your choice", ["stone","paper","scissors"])
        if st.button("Play"):
            c = random.choice(["stone","paper","scissors"]); st.write("Computer:", c)
            win = (p,c) in {("stone","scissors"),("scissors","paper"),("paper","stone")}
            st.success("You win!") if win else st.info("Draw") if p==c else st.warning("Computer wins")
            if win: metric(game)
    elif game == "Color Matcher":
        color = random.choice(["लाल","नीला","हरा","पीला","नारंगी","बैंगनी"])
        st.write("Match this color name:", color)
        a = st.text_input("Your answer")
        if st.button("Check"):
            st.success("Correct!") if a.strip()==color else st.error(f"Correct answer: {color}")
            if a.strip()==color: metric(game)
    elif game == "Roll the Dice":
        if st.button("Roll"):
            d=random.randint(1,6); st.metric("🎲 Dice",d); metric(game) if d==6 else None
    elif game == "Math Quiz":
        a,b=random.randint(1,100),random.randint(1,100); op=random.choice(["+","-","×"])
        correct=a+b if op=="+" else a-b if op=="-" else a*b
        st.write(f"{a} {op} {b} = ?")
        x=st.number_input("Answer", step=1)
        if st.button("Check"):
            st.success("Correct!") if x==correct else st.error(f"Answer: {correct}")
            if x==correct: metric(game)
    elif game == "Magic Ball 8":
        if st.button("Ask the Magic Ball"):
            st.write(random.choice(["हाँ! अभ्यास जारी रखो।","शायद—सोचकर निर्णय लो।","जिज्ञासा रखो!","एक और प्रश्न पूछो।"])); metric(game)
    elif game == "Word Scramble":
        word=random.choice(["moon","star","earth","sun","math","space","planet","school","python","science","number","circle","square","triangle","rocket","galaxy","coding","orbit","zero","prime"])
        scrambled=''.join(random.sample(word,len(word)))
        st.write("Unscramble:", scrambled); x=st.text_input("Word")
        if st.button("Check Word"):
            st.success("Correct!") if x.strip().lower()==word else st.error(f"Answer: {word}")
            if x.strip().lower()==word: metric(game)
    elif game == "Animal Guessing":
        animals=[("शेर","जंगल का प्रसिद्ध शिकारी"),("हाथी","बहुत बड़ा स्थल-जीव, सूँड होती है"),("बाघ","शरीर पर धारियाँ"),("खरगोश","तेज़ दौड़ने वाला छोटा स्तनपायी"),("ऊँट","रेगिस्तान के लिए अनुकूलित"),("मोर","भारत का राष्ट्रीय पक्षी")]
        name,h=random.choice(animals); st.write("Hint:",h); x=st.text_input("Animal")
        if st.button("Check Animal"):
            st.success("Correct!") if x.strip()==name else st.error(f"Answer: {name}")
            if x.strip()==name: metric(game)
    else:
        st.write("Click-speed is adapted for browser interaction. Use the button repeatedly to practice reaction speed.")
        if st.button("🚀 CLICK NOW"):
            metric(game); st.success("Click registered!")


def study_center():
    st.header("📘 Study Center")
    tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8=st.tabs(["Maths Visualizer","Formula Bank","Definitions","Sia Story","Astronomy","Kusumpura","Technology","Timetable"])
    with tab1:
        st.subheader("📐 Maths Shape Visualizer")
        shape=st.selectbox("Shape",["Square","Rectangle","Circle","Triangle"])
        if shape=="Square":
            a=st.number_input("Side",1.0,1000.0,5.0); st.write(f"Area = {a*a:g}"); st.write(f"Perimeter = {4*a:g}")
        elif shape=="Rectangle":
            a=st.number_input("Length",1.0,1000.0,6.0); b=st.number_input("Width",1.0,1000.0,4.0); st.write(f"Area = {a*b:g}"); st.write(f"Perimeter = {2*(a+b):g}")
        elif shape=="Circle":
            r=st.number_input("Radius",1.0,1000.0,3.0); st.write(f"Area ≈ {math.pi*r*r:.3f}"); st.write(f"Circumference ≈ {2*math.pi*r:.3f}")
        else:
            b=st.number_input("Base",1.0,1000.0,6.0); h=st.number_input("Height",1.0,1000.0,4.0); st.write(f"Area = {0.5*b*h:g}")
    with tab2:
        st.subheader("➗ Important Maths Formula Bank")
        formulas = legacy.FORMULA_BANK if legacy and hasattr(legacy,'FORMULA_BANK') else None
        if isinstance(formulas, dict):
            for k,v in formulas.items(): st.markdown(f"**{k}**\n\n{v}")
        else:
            st.markdown("""**Square area:** a²  
**Rectangle area:** l × b  
**Triangle area:** ½ × b × h  
**Circle area:** πr²  
**Simple Interest:** PRT/100""")
    with tab3:
        st.subheader("📖 Maths Definitions — हिन्दी + English")
        defs=legacy.DEFINITIONS if legacy and hasattr(legacy,'DEFINITIONS') else None
        if isinstance(defs, dict):
            for k,v in defs.items(): st.markdown(f"**{k}** — {v}")
        else: st.write("Point, line, angle, triangle, square, prime number and other school-level definitions are available in the original V5.6 project.")
    with tab4:
        st.subheader("📚 Sia & Aryabhatta Story")
        if legacy:
            for title,text in legacy.STORY_BOOK: st.markdown(f"### {title}\n{text}")
    with tab5:
        st.subheader("🔭 Space & Astronomy Gallery")
        if legacy:
            name=st.selectbox("Topic", list(legacy.SOLAR_ART.keys()) + ["Solar System","Solar Eclipse","Lunar Eclipse","Earth Rotation"])
            if name in legacy.SOLAR_ART:
                title, art, fact=legacy.SOLAR_ART[name]; st.markdown(f"### {title}"); st.code(art); st.info(fact)
            else: st.write("Visual astronomy concept from the V5.6 gallery.")
    with tab6:
        st.subheader("🏛️ Kusumpura Ancient Astronomy Gallery")
        if legacy and hasattr(legacy,'KUSUMPURA_GALLERY'):
            for item in legacy.KUSUMPURA_GALLERY:
                st.markdown(str(item))
        else: st.write("Kusumpura learning material is included in the original V5.6 Study Center.")
    with tab7:
        st.subheader("💻 Technology / Coding Visualizer")
        st.code("INPUT → PROCESS → OUTPUT\n        ↓\n   DATA + LOGIC\n        ↓\n   LEARNING RESULT", language="text")
        st.write("Python concepts, coding flow and technology learning are presented as an educational visualizer.")
    with tab8:
        st.subheader("🗓️ 4-Week Timetable")
        for week in range(1,5):
            with st.expander(f"Week {week}"):
                st.dataframe([[d,"",""] for d in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]], column_config={0:"Day",1:"Time",2:"Subject"}, hide_index=True)


def treasure_hunt():
    st.header("🗺️ Treasure Hunt — Mission Save Sia")
    st.write("Solve the riddle and move through the mission.")
    riddles=[
        ("मैं 1 और खुद से ही पूरी तरह विभाजित होता हूँ। मैं कौन?", "prime"),
        ("मेरे बिना place value अधूरी लगती है। मैं कौन?", "zero"),
        ("सौरमंडल का सबसे बड़ा ग्रह?", "jupiter"),
        ("पृथ्वी का प्राकृतिक उपग्रह?", "moon"),
        ("3 × 4 = ?", "12"),
    ]
    n=st.slider("Mission rounds",1,30,5)
    for i in range(min(n,len(riddles))):
        q,ans=riddles[i]; x=st.text_input(f"Riddle {i+1}: {q}", key=f"r{i}")
        if x and x.strip().lower()==ans: st.success("🔓 Mission step unlocked!"); metric("Treasure Hunt")


def analytics():
    st.header("📊 Data & Analytics")
    total=sum(st.session_state.scores.values())
    st.metric("Activities / score events", total)
    if st.session_state.scores:
        st.bar_chart(st.session_state.scores)
    else: st.info("Activities शुरू करने पर analytics यहाँ दिखाई जाएगी।")


def reports():
    st.header("📄 Reports")
    st.write("### Student Activity Report")
    st.write(f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}")
    st.json(st.session_state.scores)
    st.download_button("Download report", "PROJECT ARYABHUTT\n" + repr(st.session_state.scores), "aryabhutt_report.txt")


def settings():
    st.header("⚙️ Settings & Extra Features")
    st.session_state.language = st.radio("Language", ["hi","en"], horizontal=True, format_func=lambda x: "हिन्दी" if x=="hi" else "English")
    st.checkbox("Focus Mode", key="focus")
    st.write("🔊 Browser voice support can be added using Web Speech API; Android-specific TTS/camera modules from Pydroid are not executed in Streamlit Cloud.")
    st.write("🔐 Gemini key should be stored in Streamlit Secrets, never in GitHub source code.")


def feedback():
    st.header("💬 Feedback")
    text=st.text_area("Your feedback")
    if st.button("Submit Feedback") and text.strip():
        st.session_state.feedback=text.strip(); st.success("Thank you for your feedback!")

header()
with st.sidebar:
    st.markdown("## 🌼 PROJECT ARYABHUTT")
    page=st.radio("Menu", ["Home","AI Chatbot","Treasure Hunt","Game Zone","Study Center","Analytics","Reports","Feedback","Settings"])
    st.caption("Web adaptation of the user's V5.6 project")

if page=="Home":
    st.subheader("An Interactive AI-Assisted Educational Learning Platform")
    st.write("PROJECT ARYABHUTT combines AI-assisted learning, offline knowledge, mathematics, astronomy, games, quizzes, story-based learning, technology visualization and activity tracking in one student-focused learning environment.")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("AI Learning","Online + Offline")
    c2.metric("Game Zone","10 Games")
    c3.metric("Daily Quiz","20 Questions")
    c4.metric("Study Center","8 Areas")
    st.markdown("### 🔁 Learning Cycle")
    st.info("ASK → UNDERSTAND → VISUALIZE → PRACTICE → PLAY → TRACK")
    st.markdown("### 🚀 Web Version")
    st.write("This browser version adapts the original Python/Pydroid V5.6 project for Streamlit. The original .py remains the source project; Android-only features are adapted or noted where browser APIs differ.")
elif page=="AI Chatbot": chat_page()
elif page=="Treasure Hunt": treasure_hunt()
elif page=="Game Zone": game_zone()
elif page=="Study Center": study_center()
elif page=="Analytics": analytics()
elif page=="Reports": reports()
elif page=="Feedback": feedback()
else: settings()
