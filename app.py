import os, json, random, time, math, html, re
from datetime import datetime
import streamlit as st

# V5.6 data/core is kept as a separate module so the web app is an adaptation,
# not a replacement of the original Pydroid project.
try:
    import aryabhutt_v56_core as core
except Exception as exc:
    core = None

APP_TITLE = "PROJECT ARYABHUTT"
VERSION = "V5.6 WEB"
MODEL_CANDIDATES = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]

st.set_page_config(page_title=f"{APP_TITLE} • {VERSION}", page_icon="🪷", layout="wide")

# ---------- persistent session state ----------
def init_state():
    defaults = {
        "page":"Home", "messages":[], "chat_online":None, "language":"hi",
        "focus":False, "sessions":0, "chat_questions":0, "games_played":0,
        "riddles_solved":0, "study_views":0, "formula_views":0,
        "story_points":0, "astronomy_views":0, "math_activity":0,
        "reports_generated":0, "feedback":[], "quiz_score":None,
        "game_result":None, "student_name":"", "selected_shape":None,
    }
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k]=v
    if not st.session_state.get("session_recorded"):
        st.session_state.sessions += 1
        st.session_state.session_recorded = True
init_state()

# ---------- visual theme ----------
st.markdown("""
<style>
:root{--ink:#172033;--muted:#667085;--accent:#7c3aed;--soft:#f6f3ff;--card:#ffffff;}
.block-container{padding-top:1.4rem;padding-bottom:3rem;max-width:1400px}
.hero{padding:1.4rem 1.6rem;border-radius:22px;background:linear-gradient(135deg,#faf7ff,#eef7ff);border:1px solid #e6e0f4;margin-bottom:1rem}
.hero h1{margin:0;color:var(--ink);font-size:2.15rem}.hero p{margin:.45rem 0 0;color:var(--muted);font-size:1rem}
.card{padding:1rem 1.1rem;border:1px solid #e7e7ee;border-radius:16px;background:white;margin-bottom:.8rem}
.small{color:var(--muted);font-size:.9rem}.acharya{border-left:5px solid #7c3aed;background:#faf8ff;padding:1rem 1.1rem;border-radius:12px;white-space:pre-wrap}
.metric{padding:.9rem;border:1px solid #ececf2;border-radius:14px;background:#fff}.metric b{font-size:1.35rem}
</style>
""", unsafe_allow_html=True)

# ---------- utilities ----------
def ui(hi, en): return hi if st.session_state.language == "hi" else en

def core_attr(name, fallback):
    return getattr(core, name, fallback) if core else fallback

SHAPES = core_attr("SHAPES", [
("Triangle","","तीन भुजाएँ"),("Square","","चार बराबर भुजाएँ"),("Rectangle","","विपरीत भुजाएँ बराबर"),
])
FORMULAS = core_attr("FORMULAS", {"Arithmetic":["a+b=b+a","a×b=b×a"]})
TECH_CARDS = core_attr("TECH_CARDS", [])
DAILY_QUIZ = core_attr("DAILY_QUIZ", [])
V56_QA = core_attr("_V56_MASTER_QA", [])
ASTRO_CARDS = [
("Solar Eclipse","☀️ 🌑 🌍","जब चंद्रमा सूर्य और पृथ्वी के बीच आता है तो सूर्य ग्रहण दिखाई दे सकता है।"),
("Lunar Eclipse","☀️ 🌍 🌕","जब पृथ्वी की छाया चंद्रमा पर पड़ती है तो चंद्र ग्रहण होता है।"),
("Earth Rotation","🌍 ↺","पृथ्वी का अपने अक्ष पर घूमना दिन-रात के चक्र से जुड़ा है।"),
("Earth Revolution","☀️ → 🌍","पृथ्वी सूर्य की परिक्रमा करती है; एक चक्कर लगभग एक वर्ष लेता है।"),
("Milky Way","🌌 ✨","Milky Way हमारी आकाशगंगा है जिसमें बहुत से तारे हैं।"),
("Earth–Moon","🌍 ↔ 🌙","पृथ्वी और चंद्रमा के बीच गुरुत्वाकर्षण महत्वपूर्ण है।"),
]
OBS_CARDS = [
("Kusumpura","🏛️","कुसुमपुर प्राचीन भारतीय गणित और खगोल अध्ययन से जुड़ा महत्वपूर्ण स्थान था।"),
("Gnomon","☀️ │","छाया की दिशा और लंबाई से समय तथा सूर्य की स्थिति का अध्ययन किया जा सकता था।"),
("Shadow Study","🌞 ↘","छाया प्रेक्षण खगोलीय गणनाओं का एक सरल तरीका था।"),
("Star Observation","🔭 ✨","रात्रि आकाश का नियमित प्रेक्षण तारों और ग्रहों की गति समझने में मदद करता है।"),
("Water Clock","💧 ⏱️","जल की नियंत्रित धारा से समय मापने के प्राचीन तरीके विकसित हुए।"),
("Calendar Study","🌙 📅","चंद्र कलाओं, ऋतुओं और खगोलीय चक्रों का अध्ययन कैलेंडर निर्माण में सहायक था।"),
]

# ---------- Gemini / offline knowledge ----------
def api_key():
    try:
        return st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

def acharya_persona(text):
    text = str(text).strip()
    if "आयुष्मान भव" not in text and "ज्ञानवान भव" not in text:
        text += "\n\n🌼 वत्स, ज्ञान की ज्योति जलाए रखो। आयुष्मान भव!"
    return text

def offline_answer(q):
    qn = q.lower().strip()
    # Preserve V5.6's master offline book when it is importable.
    if core:
        for fn in ("_v56_offline_lookup", "_v56_master_offline_lookup"):
            try:
                f = getattr(core, fn, None)
                if f:
                    found, ans = f(q)
                    if found:
                        return acharya_persona(ans), True
            except Exception:
                pass
    # A few essential web-demo fallbacks.
    fallback = {
        "abdul kalam":"डॉ. ए. पी. जे. अब्दुल कलाम भारत के प्रसिद्ध वैज्ञानिक और भारत के पूर्व राष्ट्रपति थे। उन्हें भारत के मिसाइल और अंतरिक्ष कार्यक्रमों में उनके योगदान तथा विद्यार्थियों को प्रेरित करने के लिए विशेष रूप से याद किया जाता है।",
        "aryabhata":"आर्यभट्ट प्राचीन भारत के महान गणितज्ञ और खगोलशास्त्री थे। उनकी कृति आर्यभटीय गणित और खगोल के इतिहास में महत्वपूर्ण है।",
        "आर्यभट्ट":"आर्यभट्ट प्राचीन भारत के महान गणितज्ञ और खगोलशास्त्री थे। उनकी कृति आर्यभटीय गणित और खगोल के इतिहास में महत्वपूर्ण है।",
        "python":"Python एक लोकप्रिय programming language है। इसका उपयोग शिक्षा, automation, data science और AI जैसे क्षेत्रों में किया जाता है।",
    }
    for k,v in fallback.items():
        if k in qn: return acharya_persona(v), True
    return "वत्स, यह प्रश्न मेरी Offline Knowledge Book में अभी नहीं मिला। यदि Gemini Online mode उपलब्ध है तो मैं वहीं से उत्तर दूँगा।", False

def gemini_call(messages):
    key = api_key()
    if not key:
        return None, "no_api_key"
    import requests
    system = ("तुम 'आचार्य आर्यभट्ट' नाम के स्नेही, बुद्धिमान भारतीय शिक्षक हो। "
              "विद्यार्थी से सीधे, सरल और स्वाभाविक हिंदी में बात करो। प्रश्न English में हो तो भी उत्तर हिंदी में दो, "
              "जब तक विद्यार्थी दूसरी भाषा न माँगे। 'वत्स', 'प्रिय विद्यार्थी' जैसे संबोधन स्वाभाविक रूप से कभी-कभी उपयोग करो। "
              "तथ्य मत गढ़ो। शिक्षा, गणित, विज्ञान, इतिहास, coding और astronomy में स्पष्ट उदाहरण दो। "
              "उत्तर के अंत में छोटा आशीर्वचन दे सकते हो।")
    contents=[]
    for m in messages[-12:]:
        role = "user" if m["role"]=="user" else "model"
        contents.append({"role":role,"parts":[{"text":m["content"]}]})
    for model in MODEL_CANDIDATES:
        try:
            url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            body={"system_instruction":{"parts":[{"text":system}]},"contents":contents,
                  "generationConfig":{"temperature":0.45,"maxOutputTokens":500}}
            r=requests.post(url,params={"key":key},json=body,timeout=20)
            if r.ok:
                data=r.json(); parts=data.get("candidates",[{}])[0].get("content",{}).get("parts",[])
                ans="".join(str(p.get("text","")) for p in parts if isinstance(p,dict)).strip()
                if ans: return acharya_persona(ans), "online"
        except Exception:
            continue
    return None, "online_error"

def speak_html(text, label="🔊 आचार्य आर्यभट्ट की आवाज़ सुनें"):
    safe=html.escape(text).replace("'","&#39;").replace("\n"," ")
    st.components.v1.html(f"""
    <div style='font-family:system-ui;padding:4px 0'>
      <button onclick=\"speakNow()\" style='padding:10px 15px;border-radius:10px;border:1px solid #ddd;background:#fafafa;cursor:pointer;font-size:15px\">{label}</button>
      <span id='status' style='margin-left:8px;color:#667085'></span>
    </div>
    <script>
    function speakNow(){{
      const s=window.speechSynthesis;
      if(!s){{document.getElementById('status').innerText='Browser TTS उपलब्ध नहीं है';return;}}
      s.cancel(); const u=new SpeechSynthesisUtterance('{safe}');
      u.lang='hi-IN'; u.rate=.92; u.pitch=1.0;
      u.onstart=()=>document.getElementById('status').innerText='🔊 बोल रहा हूँ…';
      u.onend=()=>document.getElementById('status').innerText='';
      s.speak(u);
    }}
    </script>
    """, height=55)

# ---------- navigation ----------
PAGES=["Home","AI Chatbot","Treasure Hunt","Game Zone","Study Center","Space & Visualizers","Analytics","Reports","Feedback","Settings"]
with st.sidebar:
    st.markdown("## 🪷 PROJECT ARYABHUTT")
    st.caption(f"{VERSION} • Learn • Visualize • Practice • Explore • Track")
    page=st.radio("Menu",PAGES,index=PAGES.index(st.session_state.page) if st.session_state.page in PAGES else 0)
    st.session_state.page=page
    st.divider()
    st.session_state.language=st.selectbox("🌐 Language",["hi","en"],format_func=lambda x:"हिन्दी" if x=="hi" else "English",index=0 if st.session_state.language=="hi" else 1)
    st.session_state.focus=st.toggle("🎯 Focus Mode",st.session_state.focus)
    st.caption("Web adaptation of the supplied V5.6 project. Android-only hardware routes are adapted for the browser.")

# ---------- pages ----------
def home():
    st.markdown(f"<div class='hero'><h1>🪷 {APP_TITLE}</h1><p>AI-Assisted Educational Learning Platform • {VERSION}</p><p>From Imagination to Innovation — From Aryabhata's Knowledge to AI-Assisted Learning.</p></div>",unsafe_allow_html=True)
    cols=st.columns(4)
    for c,val,label in zip(cols,["🤖 AI","🎮 10 Games","📚 8 Study Areas","🔊 Voice"],["AI Chatbot","Game Zone","Study Center","Browser Voice"]):
        with c: st.markdown(f"<div class='card'><b>{val}</b><br>{label}</div>",unsafe_allow_html=True)
    st.subheader("🧠 Learning Cycle")
    st.info("ASK → UNDERSTAND → VISUALIZE → PRACTICE → PLAY → TRACK")
    st.subheader("🌟 Sia: R-AI Adventure — Project Inspiration")
    st.write("Sia की science-fiction journey—प्राचीन भारत, आर्यभट्ट की ज्ञान-परंपरा और भविष्य के conversational AI की कल्पना—से PROJECT ARYABHUTT की real educational software journey प्रेरित हुई।")
    st.markdown("> “अगर एक कहानी की Sia अपनी imagination को R-AI में बदलने की कल्पना कर सकती है, तो आज का विद्यार्थी भी अपनी imagination और technology को मिलाकर कुछ नया बना सकता है।”")

def chatbot_page():
    st.title("🤖 आचार्य आर्यभट्ट — AI Knowledge Chat")
    st.caption("Continuous conversation • Gemini online • V5.6 Offline Knowledge Book • Browser voice")
    if not st.session_state.messages:
        st.info("वत्स, प्रश्न पूछो। मैं एक ही chat में आगे के प्रश्नों को भी context के साथ समझने की कोशिश करूँगा।")
    for m in st.session_state.messages:
        with st.chat_message("user" if m["role"]=="user" else "assistant"):
            if m["role"]=="assistant":
                st.markdown(f"<div class='acharya'>{html.escape(m['content'])}</div>",unsafe_allow_html=True)
                speak_html(m["content"])
            else: st.write(m["content"])
    q=st.chat_input("वत्स, अपना प्रश्न लिखो…")
    if q:
        st.session_state.messages.append({"role":"user","content":q})
        st.session_state.chat_questions += 1
        ans,mode=gemini_call(st.session_state.messages)
        if ans is None:
            ans,_=offline_answer(q); mode="offline"
        st.session_state.messages.append({"role":"assistant","content":ans})
        st.rerun()
    c1,c2=st.columns(2)
    with c1:
        if st.button("🗑️ New Conversation",use_container_width=True): st.session_state.messages=[]; st.rerun()
    with c2:
        if api_key(): st.success("🟢 Gemini key detected — Online mode ready")
        else: st.warning("🟡 Gemini key नहीं मिली — Offline mode चलेगा. Streamlit Secrets में GEMINI_API_KEY जोड़ें।")

def treasure_page():
    st.title("🧩 Treasure Hunt — Mission Save Sia")
    st.write("V5.6 के 20–30 round concept को web-friendly interactive form में adapt किया गया है।")
    riddles=[
        ("मैं बिना पैरों के चलता हूँ और समय बताता हूँ। मैं कौन हूँ?",["घड़ी","किताब","चंद्रमा"],0),
        ("जिस आकृति की तीन भुजाएँ होती हैं?",["त्रिभुज","वृत्त","षट्भुज"],0),
        ("पृथ्वी का प्राकृतिक उपग्रह?",["सूर्य","चंद्रमा","मंगल"],1),
        ("2, 4, 6, 8 के बाद?",["9","10","12"],1),
        ("पानी का रासायनिक सूत्र?",["CO₂","H₂O","O₂"],1),
    ]
    if "treasure_round" not in st.session_state: st.session_state.treasure_round=0; st.session_state.treasure_score=0
    if st.session_state.treasure_round < 20:
        i=st.session_state.treasure_round % len(riddles); q,opts,correct=riddles[i]
        st.progress(st.session_state.treasure_round/20)
        st.subheader(f"Round {st.session_state.treasure_round+1} / 20")
        ans=st.radio(q,opts,key=f"r{st.session_state.treasure_round}")
        if st.button("Check & Continue"):
            if opts.index(ans)==correct: st.session_state.treasure_score+=1; st.success("🎉 सही!")
            else: st.info(f"सही उत्तर: {opts[correct]}")
            st.session_state.riddles_solved+=1; st.session_state.treasure_round+=1; st.rerun()
    else:
        st.success(f"🏆 Mission Complete! Score: {st.session_state.treasure_score}/20")
        if st.button("Restart Mission"): st.session_state.treasure_round=0; st.session_state.treasure_score=0; st.rerun()

def game_page():
    st.title("🎮 Game Zone — 10 Games + Daily Quiz")
    game=st.selectbox("Choose a game",["Guess the Number","Flip a Coin","Rock-Paper-Scissors","Color Matcher","Roll the Dice","Math Quiz","Magic Ball 8","Word Scramble","Animal Guessing","Click Speed Test","Daily Quiz"])
    if game=="Guess the Number":
        if "target" not in st.session_state: st.session_state.target=random.randint(1,100)
        n=st.number_input("1–100 guess",1,100,50)
        if st.button("Check"):
            st.session_state.games_played+=1
            if n==st.session_state.target: st.success("🎉 Correct!"); del st.session_state.target
            elif n<st.session_state.target: st.info("थोड़ा बड़ा सोचो।")
            else: st.info("थोड़ा छोटा सोचो।")
    elif game=="Flip a Coin":
        if st.button("Flip"): st.session_state.games_played+=1; st.success(random.choice(["Heads 🪙","Tails 🪙"]))
    elif game=="Roll the Dice":
        if st.button("Roll"): st.session_state.games_played+=1; st.success(f"🎲 {random.randint(1,6)}")
    elif game=="Rock-Paper-Scissors":
        choice=st.radio("Your choice",["Rock","Paper","Scissors"],horizontal=True)
        if st.button("Play"):
            bot=random.choice(["Rock","Paper","Scissors"]); st.session_state.games_played+=1
            win={("Rock","Scissors"),("Paper","Rock"),("Scissors","Paper")}
            result="Draw" if choice==bot else ("You win!" if (choice,bot) in win else "Aryabhutt wins!")
            st.success(f"You: {choice} • Aryabhutt: {bot} • {result}")
    elif game=="Math Quiz":
        a,b=random.randint(2,20),random.randint(2,20); op=random.choice(["+","×"]); correct=a+b if op=="+" else a*b
        st.write(f"What is {a} {op} {b}?"); ans=st.number_input("Answer",step=1)
        if st.button("Check"):
            st.session_state.games_played+=1; st.success("🎉 सही!" if ans==correct else f"सही उत्तर {correct}")
    elif game=="Daily Quiz":
        if not DAILY_QUIZ: st.warning("Daily Quiz data unavailable")
        else:
            q,opts,c=random.choice(DAILY_QUIZ); st.write(q); a=st.radio("Answer",opts)
            if st.button("Check Quiz"): st.session_state.games_played+=1; st.success("🎉 सही!" if str(opts.index(a)+1)==str(c) else f"सही option: {c}")
    elif game=="Magic Ball 8":
        if st.button("Ask the Magic Ball"): st.session_state.games_played+=1; st.success(random.choice(["हाँ, आगे बढ़ो!","अभी फिर प्रयास करो।","संभावना अच्छी है।","ज्ञान से निर्णय लो, वत्स!"]))
    elif game=="Word Scramble":
        word=random.choice(["ARYABHATA","PYTHON","SCIENCE","GALAXY"]); scrambled="".join(random.sample(word,len(word))); st.write(f"Unscramble: **{scrambled}**"); ans=st.text_input("Word")
        if st.button("Check Word"): st.session_state.games_played+=1; st.success("🎉 सही!" if ans.strip().upper()==word else f"उत्तर: {word}")
    elif game=="Animal Guessing":
        animal=random.choice(["Tiger","Elephant","Peacock","Dolphin"]); clue={"Tiger":"मैं बड़ी बिल्ली हूँ","Elephant":"मेरी सूंड होती है","Peacock":"मैं भारत का राष्ट्रीय पक्षी हूँ","Dolphin":"मैं जल में रहता हूँ"}[animal]; st.write(clue); ans=st.text_input("Guess")
        if st.button("Check Animal"): st.session_state.games_played+=1; st.success("🎉 सही!" if ans.strip().lower()==animal.lower() else f"उत्तर: {animal}")
    elif game=="Color Matcher":
        target=random.choice(["Red","Blue","Green","Yellow"]); a=st.selectbox("Choose color",["Red","Blue","Green","Yellow"])
        st.write(f"Target: **{target}**")
        if st.button("Check Color"): st.session_state.games_played+=1; st.success("🎨 Match!" if a==target else f"Target था {target}")
    elif game=="Click Speed Test":
        st.write("Browser-safe version: click the button repeatedly and track your count for 5 seconds manually.")
        if st.button("🚀 Click!"): st.session_state.games_played+=1; st.success("Click registered!")

def study_page():
    st.title("📚 Study Center")
    tabs=st.tabs(["📐 Shapes","📚 Formula Bank","📖 Definitions","🌟 Sia Story","🌌 Astronomy","🏛️ Kusumpura","💻 Technology","📅 Timetable"])
    with tabs[0]:
        names=[x[0] for x in SHAPES]; sel=st.selectbox("Shape",names); c=next(x for x in SHAPES if x[0]==sel); st.code(c[1]); st.info(c[2]); st.session_state.formula_views+=1
    with tabs[1]:
        cat=st.selectbox("Formula category",list(FORMULAS.keys()));
        for f in FORMULAS[cat]: st.markdown(f"- {f}")
        st.session_state.formula_views+=1
    with tabs[2]:
        defs=core_attr("DEFINITIONS",{})
        if isinstance(defs,dict):
            for k,v in list(defs.items())[:30]: st.markdown(f"**{k}** — {v}")
        else: st.info("V5.6 definitions module is retained in the core file.")
    with tabs[3]:
        story=core_attr("STORY_POINTS",[])
        if story:
            for item in story[:20]: st.markdown(f"- {item}")
        else:
            st.write("Sia समय-यात्रा करके आर्यभट्ट के युग में जाती है, गणित और खगोल सीखती है और लौटकर conversational educational AI की कल्पना करती है।")
        st.session_state.story_points+=1
    with tabs[4]:
        for n,v,d in ASTRO_CARDS:
            with st.expander(n): st.markdown(f"### {v}\n{d}")
        st.session_state.astronomy_views+=1
    with tabs[5]:
        for n,v,d in OBS_CARDS:
            with st.expander(n): st.markdown(f"### {v}\n{d}")
    with tabs[6]:
        if TECH_CARDS:
            for item in TECH_CARDS: st.markdown(f"**{item[0]}** — {item[2] if len(item)>2 else item[1]}")
        else: st.info("Technology visualizer retained in V5.6 core.")
    with tabs[7]:
        st.write("V5.6: 4-week timetable • Monday–Saturday • 6 periods")
        for w in range(1,5):
            with st.expander(f"Week {w}"):
                st.dataframe({"Day":["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],"Focus":["Maths","Science","Astronomy","Coding","Revision","Project"]},use_container_width=True,hide_index=True)

def space_page():
    st.title("🌌 Space & Visualizers")
    for n,v,d in ASTRO_CARDS+OBS_CARDS:
        st.markdown(f"<div class='card'><b>{v} {n}</b><br>{d}</div>",unsafe_allow_html=True)
    st.subheader("☀️ Solar Eclipse Visualizer")
    st.markdown("```text\n☀️  ─────  🌑  ─────  🌍\n             ↓\n       Moon shadow\n```")
    st.subheader("📅 Space Calendar")
    st.write(datetime.now().strftime("Today: %d %B %Y"))

def analytics_page():
    st.title("📊 Data & Analytics")
    vals=[("Sessions",st.session_state.sessions),("Games Played",st.session_state.games_played),("Riddles Solved",st.session_state.riddles_solved),("Chat Questions",st.session_state.chat_questions),("Study Views",st.session_state.study_views),("Formula Views",st.session_state.formula_views),("Story Points",st.session_state.story_points),("Astronomy Views",st.session_state.astronomy_views),("Math Activity",st.session_state.math_activity),("Reports Generated",st.session_state.reports_generated)]
    cols=st.columns(5)
    for i,(k,v) in enumerate(vals): cols[i%5].markdown(f"<div class='metric'><b>{v}</b><br><span class='small'>{k}</span></div>",unsafe_allow_html=True)
    st.bar_chart({k:v for k,v in vals})

def reports_page():
    st.title("📄 Reports")
    report=f"""PROJECT ARYABHUTT — {VERSION}\nGenerated: {datetime.now():%Y-%m-%d %H:%M}\n\nSessions: {st.session_state.sessions}\nGames Played: {st.session_state.games_played}\nRiddles Solved: {st.session_state.riddles_solved}\nChat Questions: {st.session_state.chat_questions}\nStudy Views: {st.session_state.study_views}\nFormula Views: {st.session_state.formula_views}\nStory Points: {st.session_state.story_points}\nAstronomy Views: {st.session_state.astronomy_views}\nMath Activity: {st.session_state.math_activity}\nReports Generated: {st.session_state.reports_generated}\n"""
    st.text_area("Report Card",report,height=300)
    st.download_button("⬇️ Download Report",report,"project_aryabhutt_report.txt","text/plain")
    st.session_state.reports_generated += 1

def feedback_page():
    st.title("💬 Feedback")
    rating=st.slider("Rating",1,5,5); comment=st.text_area("Comment")
    if st.button("Save Feedback"):
        st.session_state.feedback.append({"rating":rating,"comment":comment,"time":datetime.now().isoformat(timespec="seconds")}); st.success("Feedback saved locally in this web session. धन्यवाद!")

def settings_page():
    st.title("⚙️ Settings & Extra Features")
    st.subheader("🔊 Voice / TTS")
    st.write("Web version में Android/Pydroid TTS की जगह browser SpeechSynthesis उपयोग हो रहा है। Chatbot के हर उत्तर के नीचे voice button है।")
    st.subheader("🔳 QR / URL Generator")
    url=st.text_input("URL",value="https://project-aryabhutt-sapphrjy4buqinxkfcwq2hl.streamlit.app/")
    if st.button("Generate QR"):
        try:
            import qrcode
            img=qrcode.make(url); st.image(img.get_image(),caption="PROJECT ARYABHUTT QR")
        except Exception as e: st.error(f"QR dependency unavailable: {e}")
    st.subheader("🎯 Focus Mode")
    st.write("Study-first mode: browser app के अंदर learning sections को प्राथमिकता देने के लिए setting.")
    st.subheader("🔐 Teacher / Admin")
    st.info("Web deployment में secure server-side admin authentication जोड़ना बाकी है; इस demo में fake rankings या fake cloud statistics नहीं दिखाए जाते।")
    st.subheader("🧑‍🎓 Student Database")
    name=st.text_input("Student name"); school=st.text_input("School");
    if st.button("Save Student") and name.strip(): st.success(f"Student record prepared: {name} • {school}")
    st.subheader("☁️ Data / Update")
    st.info("Original V5.6 remains the MASTER Pydroid file. This web app is a browser adaptation of that project.")

# ---------- render ----------
{
"Home":home,"AI Chatbot":chatbot_page,"Treasure Hunt":treasure_page,"Game Zone":game_page,
"Study Center":study_page,"Space & Visualizers":space_page,"Analytics":analytics_page,
"Reports":reports_page,"Feedback":feedback_page,"Settings":settings_page,
}[st.session_state.page]()

st.markdown("---")
st.caption("PROJECT ARYABHUTT • Web V5.6 adaptation • Original Pydroid V5.6 source preserved as MASTER/core")
