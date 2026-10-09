
import os, json, math, random, html, time, sqlite3, uuid
from datetime import datetime, date

import streamlit as st
import streamlit.components.v1 as components

# Optional Gemini
try:
    from google import genai
    from google.genai import types as genai_types
except Exception:
    genai = None
    genai_types = None

APP_NAME = "PROJECT ARYABHUTT"
VERSION = "V5.6 WEB • RESTORED STUDY + 50-QUESTION CHALLENGES"
GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_FALLBACK_MODELS = ("gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite")

st.set_page_config(page_title=APP_NAME, page_icon="🪷", layout="wide")

# -------------------- SESSION STATE --------------------
DEFAULTS = {
    "sessions": 0, "games": 0, "riddles": 0, "chat": 0,
    "study_views": 0, "formula_views": 0, "story_points": 0,
    "astronomy_views": 0, "math_activity": 0, "reports": 0,
    "schools": {}, "students": [], "chat_history": [],
    "admin_ok": False, "focus_mode": False,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v
st.session_state.sessions += 1 if not st.session_state.get("_session_counted") else 0
st.session_state["_session_counted"] = True

# -------------------- LOCAL ACTIVITY DATABASE --------------------
# SQLite persists across app reruns on the same writable host. Hosted platforms may
# reset local files on redeploy; use a hosted database for permanent school-wide records.
DB_PATH = os.environ.get("ARYABHUTT_DB_PATH", os.path.join(os.getcwd(), "aryabhutt_activity.db"))

def db_connect():
    conn=sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory=sqlite3.Row
    return conn

def db_init():
    with db_connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS schools(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, note TEXT DEFAULT '', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY, first_name TEXT NOT NULL, school_id INTEGER REFERENCES schools(id), class_section TEXT DEFAULT '', created_at TEXT NOT NULL, active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS app_sessions(id TEXT PRIMARY KEY, student_id INTEGER NOT NULL REFERENCES students(id), started_at TEXT NOT NULL, last_seen_at TEXT NOT NULL, ended_at TEXT DEFAULT '', estimated_minutes INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS activity_events(id INTEGER PRIMARY KEY, session_id TEXT, student_id INTEGER, page TEXT DEFAULT '', event_type TEXT NOT NULL, details TEXT DEFAULT '', created_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_sessions_student ON app_sessions(student_id);
        CREATE INDEX IF NOT EXISTS idx_events_created ON activity_events(created_at);
        """)

def now_text(): return datetime.now().astimezone().isoformat(timespec="seconds")
def db_rows(query, params=()):
    with db_connect() as con: return [dict(r) for r in con.execute(query,params).fetchall()]
def db_stats():
    with db_connect() as con:
        return {"schools":con.execute("SELECT COUNT(*) FROM schools").fetchone()[0],"students":con.execute("SELECT COUNT(*) FROM students WHERE active=1").fetchone()[0],"sessions":con.execute("SELECT COUNT(*) FROM app_sessions").fetchone()[0],"events":con.execute("SELECT COUNT(*) FROM activity_events").fetchone()[0]}
def db_add_school(name,note=''):
    with db_connect() as con: con.execute("INSERT INTO schools(name,note,created_at) VALUES(?,?,?)",(name,note,now_text()))
def db_add_student(name,school_id=None,class_section=''):
    with db_connect() as con: con.execute("INSERT INTO students(first_name,school_id,class_section,created_at) VALUES(?,?,?,?)",(name,school_id,class_section,now_text()))
def db_get_or_add_student(name,school_id=None,class_section=''):
    with db_connect() as con:
        row=con.execute("SELECT id FROM students WHERE lower(first_name)=lower(?) AND COALESCE(school_id,0)=COALESCE(?,0) AND class_section=? AND active=1 ORDER BY id LIMIT 1",(name,school_id,class_section)).fetchone()
        if row: return row[0]
        cur=con.execute("INSERT INTO students(first_name,school_id,class_section,created_at) VALUES(?,?,?,?)",(name,school_id,class_section,now_text()))
        return cur.lastrowid
def log_event(event_type,page=None,details=None):
    sid=st.session_state.get("current_session_id"); student_id=st.session_state.get("student_id")
    if not student_id: return
    created=now_text(); detail_text=json.dumps(details or {},ensure_ascii=False)
    with db_connect() as con:
        con.execute("INSERT INTO activity_events(session_id,student_id,page,event_type,details,created_at) VALUES(?,?,?,?,?,?)",(sid,student_id,page or st.session_state.get("current_page",""),event_type,detail_text,created))
        if sid:
            row=con.execute("SELECT started_at FROM app_sessions WHERE id=?",(sid,)).fetchone()
            minutes=0
            if row:
                try: minutes=max(0,int((datetime.fromisoformat(created)-datetime.fromisoformat(row[0])).total_seconds()//60))
                except Exception: pass
            con.execute("UPDATE app_sessions SET last_seen_at=?, estimated_minutes=? WHERE id=?",(created,minutes,sid))
def rows_to_csv(rows):
    import csv, io
    if not rows: return ''
    out=io.StringIO(); writer=csv.DictWriter(out,fieldnames=list(rows[0].keys())); writer.writeheader(); writer.writerows(rows); return out.getvalue()

db_init()

# -------------------- DATA FROM V5.6 CORE --------------------
STORY_POINTS = [
"सिया ने रात के आकाश में चमकते तारे देखे और सीखा कि हर चमकता बिंदु एक जैसा नहीं होता। कुछ तारे हैं, कुछ ग्रह और कुछ दूर की आकाशगंगाओं से आते प्रकाश के स्रोत हैं।",
"आर्यभट्ट से प्रेरित होकर सिया ने समझा कि कठिन सवाल का पहला कदम सही सवाल पूछना है। विज्ञान में जिज्ञासा अक्सर खोज की शुरुआत बनती है।",
"शून्य केवल 'कुछ नहीं' बताने वाला चिह्न नहीं है। स्थान-मूल्य पद्धति में उसका स्थान संख्या का अर्थ बदल सकता है।",
"सिया ने 10, 100 और 1000 की तुलना करके place value समझी। उसने जाना कि एक ही अंक अलग स्थान पर अलग मान दे सकता है।",
"एक दिन उसने छाया की लंबाई नापी। इससे उसे पता चला कि सूर्य की स्थिति बदलने पर छाया भी बदलती है।",
"सिया ने सीखा कि पृथ्वी घूमती है। इसी घूर्णन से दिन और रात का चक्र जुड़ा है।",
"पृथ्वी सूर्य की परिक्रमा करती है। इस गति और पृथ्वी के झुकाव का संबंध ऋतुओं को समझने में महत्वपूर्ण है।",
"चंद्रमा का आकार वास्तव में रोज़ बदल नहीं जाता। हमें सूर्य से प्रकाशित उसका अलग-अलग भाग दिखाई देता है।",
"सिया ने जाना कि सूर्य एक तारा है और पृथ्वी उससे प्रकाश तथा ऊर्जा प्राप्त करती है।",
"उसने सीखा कि ग्रह अपनी कक्षा में सूर्य की परिक्रमा करते हैं और अलग-अलग ग्रहों की विशेषताएँ अलग होती हैं।",
"सिया ने मंगल के लाल रंग और वहाँ की सतह के बारे में पढ़ा और समझा कि हर ग्रह पृथ्वी जैसा नहीं होता।",
"बृहस्पति सबसे बड़ा ग्रह है और उसके वातावरण में विशाल तूफानी क्षेत्र देखा गया है।",
"शनि के वलय मुख्यतः बर्फ और चट्टानी कणों से बने हैं।",
"यूरेनस और नेपच्यून को ice giants कहा जाता है क्योंकि उनके अंदरूनी हिस्सों की संरचना गैस दानवों से अलग है।",
"सिया ने जाना कि हमारी आकाशगंगा का नाम Milky Way है।",
"तारों को देखकर केवल कहानी बनाना पर्याप्त नहीं; नियमित प्रेक्षण और मापन वैज्ञानिक सोच को मजबूत करते हैं।",
"किसी घटना को समझने के लिए पहले observation, फिर measurement और फिर explanation किया जा सकता है।",
"छाया की लंबाई समय और सूर्य की स्थिति के बारे में संकेत दे सकती है।",
"पुराने खगोलविदों ने आकाशीय चक्रों को समझने के लिए लंबे समय तक नियमित observations किए।",
"सिया ने सीखा कि calendar बनाने में सूर्य, चंद्रमा और ऋतुओं के चक्रों का अध्ययन उपयोगी हो सकता है।",
"उसने पानी की नियंत्रित गति से समय मापने वाले जल-घड़ी जैसे विचारों के बारे में पढ़ा।",
"गणित और खगोल विज्ञान में angle measurement महत्वपूर्ण भूमिका निभाता है।",
"आर्यभट्ट की परंपरा ने सिया को गणितीय गणना और खगोलीय प्रेक्षण के संबंध को समझने के लिए प्रेरित किया।",
"सिया ने समझा कि zero और place value जैसे विचार गणितीय notation को शक्तिशाली बनाते हैं।",
"किसी कठिन समस्या को छोटे भागों में बाँटना problem solving को आसान बना सकता है।",
"गलत उत्तर मिलने पर केवल उत्तर बदलना नहीं, बल्कि अपनी प्रक्रिया जाँचना भी जरूरी है।",
"विज्ञान में 'मुझे नहीं पता' एक उपयोगी शुरुआत हो सकती है, यदि उसके बाद जाँच करने का प्रयास हो।",
"सिया ने जाना कि computer instructions को code के रूप में लिखा जा सकता है।",
"उसने समझा कि algorithm किसी समस्या को हल करने के लिए step-by-step निर्देश देता है।",
"AI data से patterns सीखकर prediction या generation जैसे काम कर सकता है, लेकिन उसके उत्तरों को जाँचना भी जरूरी है।",
"सिया ने cyber safety में strong passwords, updates और privacy की भूमिका समझी।",
"Internet कई networks को जोड़ने वाला विशाल network है।",
"Cloud services network के माध्यम से computing और data resources उपलब्ध करा सकती हैं।",
"Robot sensors और programmed instructions की मदद से काम कर सकता है।",
"Microchip में बहुत से electronic components छोटे क्षेत्र में integrated होते हैं।",
"सिया ने जाना कि educational technology का लक्ष्य केवल मनोरंजन नहीं, learning को अधिक interactive बनाना भी है।",
"Visual learning में diagram और model किसी concept को समझने में मदद कर सकते हैं।",
"Game-based practice सही तरीके से उपयोग करने पर repetition को रोचक बना सकती है।",
"Quiz से विद्यार्थी अपनी समझ जाँच सकता है, लेकिन केवल score ही learning का पूरा माप नहीं है।",
"Timetable छोटे learning sessions को नियमित बनाने में मदद कर सकता है।",
"Analytics में वास्तविक activity दर्ज करना fake ranking बनाने से अधिक ईमानदार है।",
"Data में school और student records अलग-अलग रखे जाएँ तो reporting आसान होती है।",
"Teacher dashboard का उद्देश्य learning activity को समझने और सहायता देने में मदद करना होना चाहिए।",
"एक अच्छा educational app विद्यार्थी को सवाल पूछने, समझने, अभ्यास करने और वापस देखने का रास्ता देता है।",
"Accessibility और सरल भाषा अधिक विद्यार्थियों को learning tools इस्तेमाल करने में मदद करती है।",
"Indian scientific heritage को modern technology के साथ प्रस्तुत करने से इतिहास और innovation के बीच संबंध दिखाया जा सकता है।",
"सिया ने अपनी imagination को R-AI के विचार से जोड़ा और फिर उसे वास्तविक educational software बनाने की प्रेरणा मिली।",
"आखिरी सीख: imagination तभी innovation बनती है जब उसे छोटे-छोटे experiments, coding और testing में बदला जाए।",
]

DEFINITIONS = [
("Natural Number","प्राकृतिक संख्या","1,2,3… जैसी गिनती की संख्याएँ।","उदाहरण: 7"),
("Whole Number","पूर्ण संख्या","0 सहित प्राकृतिक संख्याएँ।","उदाहरण: 0, 7"),
("Integer","पूर्णांक","…,−2,−1,0,1,2…","उदाहरण: −3"),
("Rational Number","परिमेय","p/q के रूप में लिखी जा सके जहाँ q≠0।","उदाहरण: 3/4"),
("Irrational Number","अपरिमेय","जिसे p/q के रूप में ठीक-ठीक नहीं लिख सकते।","उदाहरण: √2"),
("Prime Number","अभाज्य","केवल 1 और स्वयं से विभाजित होने वाली संख्या।","उदाहरण: 13"),
("Composite Number","भाज्य","दो से अधिक गुणनखंड वाली संख्या।","उदाहरण: 12"),
("Factor","गुणनखंड","जो संख्या किसी संख्या को बिना शेष विभाजित करे।","12 के factors: 1,2,3,4,6,12"),
("Multiple","गुणज","किसी संख्या के 1,2,3… से गुणनफल।","5 के multiples: 5,10,15…"),
("Constant","अचर","जिसका मान स्थिर रहता है।","x + 5 में 5 constant है।"),
("Variable","चर","जिसका मान बदल सकता है।","x + 5 में x variable है।"),
("Coefficient","गुणांक","चर के साथ गुणा होने वाली संख्या।","3x में 3 coefficient है।"),
("Mean","माध्य","सभी मानों का योग ÷ मानों की संख्या।","2,4,6 का mean = 4"),
("Median","मध्यिका","क्रम में रखने पर बीच का मान।","1,3,8 का median = 3"),
("Mode","बहुलक","सबसे अधिक बार आने वाला मान।","2,2,5 का mode = 2"),
("Range","परास","अधिकतम − न्यूनतम।","2,5,9 → range 7"),
("Perimeter","परिमाप","आकृति की बाहरी सीमा की कुल लंबाई।","वर्ग का perimeter = 4a"),
("Area","क्षेत्रफल","समतल आकृति द्वारा घेरा गया क्षेत्र।","वर्ग = a²"),
("Volume","आयतन","त्रि-आयामी वस्तु द्वारा घेरा गया स्थान।","घन = a³"),
("Angle","कोण","दो किरणों के बीच का झुकाव।","समकोण = 90°"),
("Triangle","त्रिभुज","तीन भुजाओं वाली आकृति।","तीन sides"),
("Quadrilateral","चतुर्भुज","चार भुजाओं वाली आकृति।","चार sides"),
("Circle","वृत्त","केंद्र से समान दूरी पर स्थित बिंदुओं का समुच्चय।","radius r"),
("Radius","त्रिज्या","केंद्र से वृत्त की परिधि तक दूरी।","diameter = 2r"),
("Diameter","व्यास","केंद्र से होकर जाने वाली chord की लंबाई।","d = 2r"),
("Fraction","भिन्न","पूर्ण के भाग को दर्शाने वाली संख्या।","3/4"),
("Ratio","अनुपात","दो समान प्रकार की राशियों की तुलना।","2:3"),
("Proportion","समानुपात","दो अनुपातों की समानता।","2:3 = 4:6"),
("Percentage","प्रतिशत","प्रति सौ का मान।","25% = 25/100"),
("Profit","लाभ","SP, CP से अधिक होने पर अंतर।","Profit = SP−CP"),
("Loss","हानि","CP, SP से अधिक होने पर अंतर।","Loss = CP−SP"),
("Discount","छूट","Marked Price से दी गई कमी।","Discount = MP−SP"),
("Principal","मूलधन","ब्याज गणना में प्रारंभिक धन।","P"),
("Interest","ब्याज","मूलधन पर मिलने/देने वाला अतिरिक्त धन।","SI/CI"),
("Speed","चाल","दूरी तय करने की दर।","speed = distance/time"),
("Distance","दूरी","दो स्थानों के बीच लंबाई।","d"),
("Time","समय","घटना की अवधि।","t"),
("Probability","प्रायिकता","घटना के होने की संभावना का माप।","0 से 1 के बीच"),
("Data","आँकड़े","एकत्र की गई सूचनाएँ।","marks, counts आदि"),
("Frequency","आवृत्ति","किसी मान के आने की संख्या।","कितनी बार आया"),
("Equation","समीकरण","दो बराबर व्यंजकों को दर्शाने वाला कथन।","2x+1=5"),
("Expression","व्यंजक","संख्या, चर और संक्रियाओं का संयोजन।","3x+2"),
("Line","रेखा","दोनों दिशाओं में अनंत तक जाने वाला straight path।","↔"),
("Ray","किरण","एक endpoint से एक दिशा में अनंत तक जाती है।","→"),
("Segment","रेखाखंड","दो endpoints के बीच रेखा का भाग।","AB"),
("Parallel Lines","समांतर रेखाएँ","एक ही समतल में जो कभी नहीं मिलतीं।","∥"),
("Perpendicular","लंबवत","90° पर मिलने वाली रेखाएँ।","⊥"),
("Symmetry","सममिति","दोनों भागों का संतुलित/दर्पण जैसा विन्यास।","mirror line"),
("Polygon","बहुभुज","रेखाखंडों से बनी बंद आकृति।","triangle, pentagon"),
("Congruent","सर्वांगसम","आकार और माप में समान आकृतियाँ।","same shape & size"),
("Similar","समरूप","आकार समान, अनुपात समान आकृतियाँ।","same shape"),
("LCM","लघुत्तम समापवर्त्य","साझा गुणजों में सबसे छोटा।","LCM(4,6)=12"),
("HCF","महत्तम समापवर्तक","साझा गुणनखंडों में सबसे बड़ा।","HCF(12,18)=6"),
]

FORMULAS = {
"Arithmetic / अंकगणित":[
"a + b = b + a — addition commutative",
"a × b = b × a — multiplication commutative",
"a + (b + c) = (a + b) + c — associative addition",
"a × (b + c) = ab + ac — distributive law",
"Dividend = Divisor × Quotient + Remainder",
"Average = Sum of observations ÷ Number of observations",
],
"Fractions & Percentage / भिन्न":[
"Percentage = (Part ÷ Whole) × 100",
"Part = Percentage × Whole ÷ 100",
"Fraction addition: a/b + c/d = (ad + bc)/bd",
"Fraction multiplication: a/b × c/d = ac/bd",
"New value after increase = Original × (1 + r/100)",
"New value after decrease = Original × (1 − r/100)",
],
"Profit/Loss / लाभ-हानि":[
"Profit = SP − CP",
"Loss = CP − SP",
"Profit% = Profit ÷ CP × 100",
"Loss% = Loss ÷ CP × 100",
"Discount = MP − SP",
"Discount% = Discount ÷ MP × 100",
],
"Geometry / ज्यामिति":[
"Rectangle area = l × b",
"Rectangle perimeter = 2(l + b)",
"Square area = a²",
"Square perimeter = 4a",
"Triangle area = ½ × base × height",
"Circle area = πr²",
"Circle circumference = 2πr",
"Parallelogram area = base × height",
],
"Speed / समय":[
"Speed = Distance ÷ Time",
"Distance = Speed × Time",
"Time = Distance ÷ Speed",
],
}

ASTRO = [
("☿ Mercury","सबसे छोटा और सूर्य के सबसे निकट ग्रह।","Planet visual","gray"),
("♀ Venus","सौरमंडल का दूसरा ग्रह; इसका वातावरण बहुत घना है।","Planet visual","cream"),
("🌍 Earth","तीसरा ग्रह और हमारा home planet।","Planet visual","blue"),
("♂ Mars","लाल ग्रह; इसकी सतह पर विशाल canyon system है।","Planet visual","red"),
("♃ Jupiter","सौरमंडल का सबसे बड़ा ग्रह; Great Red Spot एक विशाल storm system है।","Planet visual","orange"),
("♄ Saturn","अपने prominent rings के लिए प्रसिद्ध।","Planet visual","gold"),
("♅ Uranus","Ice giant; इसकी rotation axis बहुत अधिक tilted है।","Planet visual","cyan"),
("♆ Neptune","सबसे दूर का आठवाँ ग्रह; तेज हवाओं के लिए प्रसिद्ध।","Planet visual","blue"),
("☀️ Solar Eclipse","Moon सूर्य और Earth के बीच आकर कुछ क्षेत्रों में सूर्य की रोशनी को block करता है।","Eclipse visual","sun"),
("🌕 Lunar Eclipse","Earth की shadow Moon पर पड़ने पर lunar eclipse होता है।","Eclipse visual","moon"),
("🔄 Earth Rotation","Earth अपने axis पर घूमती है; day-night cycle इससे जुड़ा है।","Rotation visual","earth"),
("🛰️ Earth Revolution","Earth सूर्य की परिक्रमा करती है; एक चक्कर लगभग एक वर्ष लेता है।","Orbit visual","orbit"),
("🌌 Milky Way","हमारी galaxy का नाम Milky Way है; इसमें बहुत से तारे हैं।","Galaxy visual","space"),
("🌍🌙 Earth–Moon","Moon Earth की परिक्रमा करता है और gravity दोनों के बीच महत्वपूर्ण है।","Orbit visual","moon"),
("🪐 Solar System","Sun, आठ planets, dwarf planets, moons, asteroids और comets का विशाल system।","System visual","system"),
]

KUSUMPURA = [
("🏛️ Kusumpura","प्राचीन भारतीय गणित और खगोल अध्ययन से जुड़ा स्थान/परंपरा।"),
("☀️ Gnomon","छाया की दिशा और लंबाई से सूर्य की स्थिति तथा समय के संकेतों का अध्ययन।"),
("🌞 Shadow Study","छाया प्रेक्षण प्राचीन खगोलीय गणनाओं का सरल तरीका था।"),
("🔭 Star Observation","रात्रि आकाश का नियमित observation तारों और ग्रहों की गति समझने में मदद करता है।"),
("💧 Water Clock","नियंत्रित जल-प्रवाह से समय मापने की प्राचीन तकनीक।"),
("☀️ Sun Path","दिनभर सूर्य के apparent path और shadow changes का observation।"),
("📅 Calendar Study","चंद्र कलाओं, ऋतुओं और खगोलीय cycles का अध्ययन calendar बनाने में सहायक।"),
("🪐 Planet Motion","ग्रहों की गति देखकर गणना और mathematical models विकसित किए जा सकते हैं।"),
("📐 Angle Measurement","आकाश में किसी object की ऊँचाई/दिशा समझने के लिए angle measurement उपयोगी है।"),
("🪷 Aryabhata Legacy","गणितीय calculation और astronomical observation को जोड़ने वाली भारतीय वैज्ञानिक परंपरा।"),
]

TECH = [
("🖥️ Computer","कंप्यूटर data को process करके useful result देता है।","0101 1010","CPU"),
("🤖 AI","AI data से patterns सीखकर prediction/generation जैसे काम कर सकता है।","DATA → PATTERN → OUTPUT","AI"),
("🤖 Robot","Sensors और programmed instructions की मदद से robot काम कर सकता है।","SENSOR → CONTROL → ACTION","ROBOT"),
("🐍 Coding","Code instructions का sequence है जिससे computer कोई task करता है।","if x > 0:\\n  learn()","CODE"),
("🌐 Internet","Internet जुड़े हुए networks का विशाल तंत्र है।","PC ↔ NETWORK ↔ CLOUD ↔ PHONE","NET"),
("☁️ Cloud","Cloud में computing resources और data network के माध्यम से उपलब्ध हो सकते हैं।","DEVICE ↔ CLOUD","CLOUD"),
("🔗 Network","Network devices को data exchange के लिए जोड़ता है।","💻 ─ 🌐 ─ 💻","LINK"),
("🔲 Microchip","Microchip में बहुत से electronic components छोटे क्षेत्र में integrated होते हैं।","• • • CPU • • •","CHIP"),
("🛡️ Cyber Safety","Strong passwords, updates और privacy habits digital safety में मदद करते हैं।","🔑 + 🔄 + 🔒","SAFE"),
("🚀 Future Tech","AI, robotics, space और green technology का उपयोग शिक्षा/विज्ञान में किया जा सकता है।","AI + ROBOT + SPACE","FUTURE"),
]

SHAPES = [
("Triangle","तीन भुजाएँ","½ × base × height"),
("Square","चार बराबर भुजाएँ","a²"),
("Rectangle","विपरीत भुजाएँ बराबर","l × b"),
("Rhombus","सभी भुजाएँ बराबर","½d₁d₂"),
("Parallelogram","विपरीत भुजाएँ parallel","base × height"),
("Trapezium","एक जोड़ी parallel sides","½(a+b)h"),
("Kite","दो-दो आसन्न sides बराबर","½d₁d₂"),
("Circle","केंद्र से समान दूरी","πr²"),
("Ellipse","अंडाकार आकृति","—"),
("Pentagon","पाँच भुजाएँ","—"),
("Hexagon","छह भुजाएँ","—"),
("Octagon","आठ भुजाएँ","—"),
]

# -------------------- STYLE --------------------
st.markdown("""
<style>
.block-container{padding-top:1.4rem;padding-bottom:3rem}
.hero{padding:1.4rem 1.5rem;border-radius:20px;background:linear-gradient(135deg,#f7f0ff,#eef7ff);border:1px solid #ddd}
.hero h1{margin:0;font-size:2.1rem}.muted{color:#64748b}
.card{padding:1rem;border:1px solid #e2e8f0;border-radius:16px;background:#fff;margin:.45rem 0}
.fact{padding:1rem;border-radius:16px;background:#fff7ed;border:1px solid #fed7aa}
.visual{min-height:150px;border-radius:18px;background:radial-gradient(circle at 50% 35%,#334155,#0f172a 60%,#020617);display:flex;align-items:center;justify-content:center;color:white;text-align:center;padding:1rem}
.bigplanet{width:105px;height:105px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:2.4rem;margin:auto;box-shadow:0 0 35px rgba(255,255,255,.18)}
</style>
""", unsafe_allow_html=True)

# -------------------- HELPERS --------------------
def section(title, icon=""):
    st.subheader(f"{icon} {title}")

def visual_box(label, symbol="🌌", detail=""):
    st.markdown(f'<div class="visual"><div><div style="font-size:4rem">{symbol}</div><b>{html.escape(label)}</b><div style="opacity:.85">{html.escape(detail)}</div></div></div>', unsafe_allow_html=True)

def admin_password():
    try:
        return str(st.secrets.get("ADMIN_PASSWORD","aryabhutt"))
    except Exception:
        return "aryabhutt"

def gemini_client():
    if genai is None:
        return None, "google-genai package नहीं मिला"
    key = None
    try:
        key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    except Exception:
        pass
    if not key:
        return None, "GEMINI_API_KEY नहीं मिला"
    try:
        # Bound network wait so the chat never spins for minutes.
        http_options = genai_types.HttpOptions(timeout=20000) if genai_types else None
        if http_options is not None:
            return genai.Client(api_key=key, http_options=http_options), "ready"
        return genai.Client(api_key=key), "ready"
    except Exception as e:
        return None, str(e)[:120]

def gemini_answer(prompt):
    """Hindi-first Aryabhatt-inspired persona; network wait is bounded by HttpOptions."""
    client, status = gemini_client()
    if client is None:
        return None, status

    history = st.session_state.get("chat_history", [])[-8:]
    context_lines = []
    for role, msg in history:
        label = "जिज्ञासु विद्यार्थी" if role == "user" else "आचार्य आर्यभट्ट"
        context_lines.append(f"{label}: {msg}")
    conversation = "\n".join(context_lines)

    system_prompt = (
        "तुम PROJECT ARYABHUTT के 'आचार्य आर्यभट्ट' से प्रेरित ज्ञान-सहायक हो।\n"
        "आवाज़ और अंदाज़: प्राचीन भारतीय विद्वान आचार्य जैसा आत्मीय, धैर्यवान, ज्ञानपूर्ण और सहज; कठोर या रोबोट जैसा नहीं।\n"
        "विद्यार्थी को 'वत्स', 'प्रिय बालक' या 'प्रिय जिज्ञासु' कह सकते हो। संबोधन में 'आप/आपको/आपसे' बार-बार मत कहो; सहज और स्नेहपूर्ण 'तुम/तुम्हें/तुमसे' प्रयोग करो।"
        "एक ही उत्तर में बार-बार संबोधन न दो। 'बच्चे' या baby-talk न करो।\n"
        "उत्तर मुख्यतः सरल, स्वाभाविक हिंदी देवनागरी में हो, भले प्रश्न अंग्रेज़ी में हो। वैज्ञानिक/तकनीकी शब्द ज़रूरत पर अंग्रेज़ी में रखकर समझाओ।\n"
        "पहले प्रश्न का सीधा और उपयोगी उत्तर दो। ज़रूरत से ज़्यादा भूमिका न बाँधो। तथ्य न गढ़ो; अनिश्चितता साफ बताओ।\n"
        "गणित, तर्क, प्रमाण, प्रेक्षण और जिज्ञासा को प्रोत्साहित करो। स्वयं को ऐतिहासिक आर्यभट्ट होने का दावा मत करो; कहो कि शैली उनसे प्रेरित है।\n"
        "हर उत्तर के अंत में यह छोटा, आत्मीय समापन जोड़ो: '🌼 ज्ञान की ज्योति जलाए रखो, प्रिय बालक। आयुष्मान भवः!\nअब बताओ, अगली कौन-सी जिज्ञासा सुलझाएँ?'\n\n"
        "पिछली बातचीत का संदर्भ:\n" + (conversation or "यह पहली बातचीत है।") + "\n\n"
        "नया प्रश्न: " + str(prompt)
    )
    errors = []
    try:
        preferred_model = str(st.secrets.get("GEMINI_MODEL", GEMINI_MODEL)).strip() or GEMINI_MODEL
    except Exception:
        preferred_model = GEMINI_MODEL
    for model_name in dict.fromkeys((preferred_model, *GEMINI_FALLBACK_MODELS)):
        try:
            r = client.models.generate_content(model=model_name, contents=system_prompt)
            answer = getattr(r, "text", None)
            if answer and str(answer).strip():
                answer = str(answer).strip()
                signoff = "🌼 ज्ञान की ज्योति जलाए रखो, प्रिय बालक। आयुष्मान भवः!\nअब बताओ, अगली कौन-सी जिज्ञासा सुलझाएँ?"
                for marker in ("🌼 ज्ञान की ज्योति जलाए रखो", "आयुष्मान भवः", "आयुष्मान भव।"):
                    pos = answer.find(marker)
                    if pos >= 0:
                        answer = answer[:pos].rstrip()
                        break
                answer = answer + "\n\n" + signoff
                return answer, f"🟢 Gemini Online ({model_name})"
            errors.append(f"{model_name}: empty response")
        except Exception as e:
            errors.append(f"{model_name}: {str(e).replace(chr(10), ' ')[:130]}")
    return None, "Gemini models tried: " + " | ".join(errors[:3])

def browser_voice(text, key):
    """Render a browser Hindi voice button for the supplied answer."""
    safe = json.dumps(str(text), ensure_ascii=False)
    components.html(f"""
    <div style="font-family:system-ui;margin:4px 0 10px;">
      <button id="speak-{key}" style="padding:8px 14px;border-radius:10px;border:1px solid #888;background:#fff;cursor:pointer;font-size:15px;">🔊 उत्तर सुनें</button>
      <span id="voice-status-{key}" style="margin-left:8px;font-size:13px;color:#666;"></span>
    </div>
    <script>
      const btn = document.getElementById("speak-{key}");
      const status = document.getElementById("voice-status-{key}");
      const text = {safe};
      btn.onclick = () => {{
        if (!('speechSynthesis' in window)) {{
          status.textContent = 'इस browser में voice उपलब्ध नहीं है।';
          return;
        }}
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = 'hi-IN';
        u.rate = 0.92;
        u.pitch = 1.0;
        u.onstart = () => status.textContent = '🔊 सुनाया जा रहा है…';
        u.onend = () => status.textContent = '✓ पूरा हुआ';
        u.onerror = () => status.textContent = 'Voice शुरू नहीं हो सकी।';
        window.speechSynthesis.speak(u);
      }};
    </script>
    """, height=52)

# -------------------- HOME --------------------
def home():
    st.markdown(f"""<div class="hero">
    <h1>🪷 {APP_NAME}</h1>
    <div class="muted">AI-Assisted Educational Learning Platform • {VERSION}</div>
    <p><b>From Imagination to Innovation — From Aryabhata's Knowledge to AI-Assisted Learning.</b></p>
    </div>""", unsafe_allow_html=True)
    cols=st.columns(4)
    for c, t, v in zip(cols,["🤖 AI","🎮 Games","📚 Study","📊 Track"],["AI Chatbot","10 Games + Quiz","8 Learning Areas","Real Activity"]):
        c.metric(t,v)
    st.info("ASK → UNDERSTAND → VISUALIZE → PRACTICE → PLAY → TRACK")
    section("Sia: R-AI Adventure — Project Inspiration","🌟")
    st.write("सिया की science-fiction journey — प्राचीन भारत, आर्यभट्ट की ज्ञान-परंपरा और भविष्य के conversational AI की कल्पना — से PROJECT ARYABHUTT की real educational software journey प्रेरित हुई।")
    st.success("“अगर एक कहानी की Sia अपनी imagination को R-AI में बदलने की कल्पना कर सकती है, तो आज का विद्यार्थी भी अपनी imagination और technology को मिलाकर कुछ नया बना सकता है।”")
    section("What is restored in this edition","🧩")
    st.write("V5.6 core के study content को छोटा करके नहीं, बल्कि web-friendly cards, tabs, visuals और dashboards में प्रस्तुत किया गया है।")

# -------------------- AI CHAT --------------------
# -------------------- EXPANDABLE OFFLINE KNOWLEDGE BANK --------------------
# Curated local answers: available even when Gemini or internet is unavailable.
OFFLINE_KB = [
# Astronomy
({"astronomy","खगोल विज्ञान","खगोलविज्ञान","universe","ब्रह्मांड","universe क्या"}, "ब्रह्मांड में space, time, matter और energy शामिल हैं। इसमें अरबों galaxies हैं; हमारा सौरमंडल Milky Way galaxy में है।"),
({"big bang","बिग बैंग","universe origin","ब्रह्मांड की उत्पत्ति"}, "Big Bang मॉडल के अनुसार ब्रह्मांड लगभग 13.8 अरब वर्ष पहले अत्यंत गर्म और घनी अवस्था से फैलना शुरू हुआ। यह अंतरिक्ष में किसी एक स्थान पर साधारण विस्फोट जैसा नहीं था।"),
({"sun","सूर्य","सूरज"}, "सूर्य हमारे सौरमंडल का तारा है। इसके केंद्र में nuclear fusion से ऊर्जा निकलती है, जो प्रकाश और ऊष्मा के रूप में हम तक पहुँचती है।"),
({"moon","चंद्रमा","चाँद","चांद"}, "चंद्रमा पृथ्वी का प्राकृतिक उपग्रह है। इसकी कलाएँ सूर्य, पृथ्वी और चंद्रमा की बदलती स्थिति के कारण दिखाई देती हैं।"),
({"black hole","ब्लैक होल","कृष्ण विवर"}, "ब्लैक होल अंतरिक्ष का ऐसा क्षेत्र है जहाँ गुरुत्वाकर्षण इतना प्रबल होता है कि घटना क्षितिज के भीतर से प्रकाश भी बाहर नहीं निकल सकता।"),
({"light year","प्रकाश वर्ष"}, "प्रकाश-वर्ष दूरी की इकाई है, समय की नहीं। प्रकाश एक वर्ष में लगभग 9.46 ट्रिलियन किलोमीटर चलता है।"),
({"gravity","गुरुत्वाकर्षण","गुरुत्व बल"}, "गुरुत्वाकर्षण वह आकर्षण है जो द्रव्यमान वाली वस्तुओं के बीच होता है। इसी कारण वस्तुएँ पृथ्वी की ओर गिरती हैं और ग्रह सूर्य की परिक्रमा करते हैं।"),
({"eclipse","ग्रहण","सूर्य ग्रहण","चंद्र ग्रहण"}, "सूर्य ग्रहण तब होता है जब चंद्रमा सूर्य और पृथ्वी के बीच आता है। चंद्र ग्रहण तब होता है जब पृथ्वी की छाया चंद्रमा पर पड़ती है।"),
({"mars","मंगल","red planet","लाल ग्रह"}, "मंगल को लाल ग्रह कहते हैं क्योंकि उसकी सतह की धूल में iron oxide यानी जंग जैसे यौगिक हैं।"),
({"jupiter","बृहस्पति","largest planet","सबसे बड़ा ग्रह"}, "बृहस्पति सौरमंडल का सबसे बड़ा ग्रह है। उसके वातावरण में Great Red Spot नाम का विशाल तूफानी क्षेत्र है।"),
({"saturn","शनि","rings of saturn","शनि के छल्ले"}, "शनि अपने स्पष्ट वलयों के लिए प्रसिद्ध है। ये मुख्यतः बर्फ के कणों, धूल और चट्टानी पदार्थ से बने हैं।"),
({"milky way","आकाशगंगा","मंदाकिनी"}, "हमारी galaxy को Milky Way कहते हैं। सूर्य इसके अनेक तारों में से एक है।"),
({"rotation","घूर्णन","दिन और रात","day and night"}, "पृथ्वी का अपनी धुरी पर घूमना घूर्णन कहलाता है। इसी से दिन और रात का चक्र बनता है; एक घूर्णन लगभग 24 घंटे का है।"),
({"revolution","परिक्रमण","ऋतु","seasons","मौसम क्यों बदलते"}, "पृथ्वी सूर्य की परिक्रमा करती है और उसकी धुरी लगभग 23.5° झुकी है। धुरी का झुकाव और परिक्रमा मिलकर ऋतुओं का मुख्य कारण बनते हैं।"),
({"planet","planets","ग्रह","सौरमंडल","solar system"}, "सौरमंडल में आठ ग्रह हैं: बुध, शुक्र, पृथ्वी, मंगल, बृहस्पति, शनि, अरुण (यूरेनस) और वरुण (नेपच्यून)। सभी सूर्य की परिक्रमा करते हैं।"),
({"star","तारा","तारे"}, "तारे गर्म गैस/प्लाज़्मा के विशाल गोले हैं। उनके केंद्र में fusion ऊर्जा पैदा कर सकता है; सूर्य भी एक तारा है।"),
# Mathematics
({"zero","शून्य","0 का महत्व"}, "शून्य संख्या के रूप में और place-value notation में महत्वपूर्ण है। उदाहरण: 205 में शून्य बताता है कि दहाई के स्थान पर कोई दहाई नहीं है।"),
({"pi","पाई","π"}, "π वृत्त की परिधि और व्यास का अनुपात है। इसका लगभग मान 3.14159 है; वृत्त का क्षेत्रफल πr² होता है।"),
({"pythagoras","पाइथागोरस","पाइथागोरस प्रमेय"}, "समकोण त्रिभुज में कर्ण² = आधार² + लंब²। इसे a² + b² = c² लिखते हैं, जहाँ c कर्ण है।"),
({"prime number","अभाज्य संख्या","prime"}, "अभाज्य संख्या 1 से बड़ी ऐसी पूर्ण संख्या है जिसके केवल दो धनात्मक भाजक होते हैं: 1 और स्वयं। उदाहरण: 2, 3, 5, 7, 11।"),
({"fraction","भिन्न","fractions"}, "भिन्न किसी पूर्ण के भाग को दर्शाती है। a/b में b शून्य नहीं हो सकता; जैसे 3/4 का अर्थ चार बराबर भागों में से तीन भाग है।"),
({"percentage","प्रतिशत","percent","%"}, "प्रतिशत का अर्थ प्रति सौ है। x% of N = (x/100) × N। उदाहरण: 200 का 25% = 50।"),
({"algebra","बीजगणित","variable","चर"}, "बीजगणित में अक्षर या symbols अज्ञात अथवा बदलती राशियों को दर्शाते हैं। उदाहरण: x + 3 = 7 में x = 4।"),
({"area of circle","वृत्त का क्षेत्रफल","circle area"}, "वृत्त का क्षेत्रफल A = πr² है, जहाँ r त्रिज्या है। परिधि C = 2πr होती है।"),
({"area of rectangle","आयत का क्षेत्रफल","rectangle area"}, "आयत का क्षेत्रफल = लंबाई × चौड़ाई। परिमाप = 2 × (लंबाई + चौड़ाई)।"),
({"area of triangle","त्रिभुज का क्षेत्रफल","triangle area"}, "त्रिभुज का क्षेत्रफल = ½ × आधार × ऊँचाई।"),
({"prime factors","गुणनखंड","hcf","महत्तम समापवर्तक","lcm","लघुत्तम समापवर्त्य"}, "HCF सबसे बड़ा साझा गुणनखंड है। LCM सबसे छोटा साझा धनात्मक गुणज है। उदाहरण: 12 और 18 का HCF = 6 तथा LCM = 36।"),
({"pythagoras theorem","समकोण त्रिभुज"}, "समकोण त्रिभुज में सबसे लंबी भुजा कर्ण कहलाती है और कर्ण² = अन्य दो भुजाओं के वर्गों का योग होता है।"),
({"speed","चाल","गति","distance","दूरी"}, "औसत चाल = कुल दूरी ÷ कुल समय। दूरी = चाल × समय। इकाइयों को एक जैसा रखना ज़रूरी है, जैसे km और hours।"),
({"probability","प्रायिकता","संभावना"}, "समान रूप से संभावित परिणामों में प्रायिकता = अनुकूल परिणामों की संख्या ÷ कुल संभावित परिणामों की संख्या। इसका मान 0 से 1 के बीच होता है।"),
# Science
({"photosynthesis","प्रकाश संश्लेषण","प्रकाशसंश्लेषण"}, "हरे पौधे प्रकाश ऊर्जा की सहायता से पानी और कार्बन डाइऑक्साइड से glucose बनाते हैं और ऑक्सीजन छोड़ते हैं। इस प्रक्रिया को प्रकाश संश्लेषण कहते हैं।"),
({"atom","परमाणु","molecule","अणु"}, "परमाणु पदार्थ की रासायनिक पहचान की मूल इकाई है। अणु दो या अधिक परमाणुओं के रासायनिक बंध से बन सकता है।"),
({"force","बल","newton law","न्यूटन के नियम"}, "बल वस्तु की गति या आकार बदल सकता है। न्यूटन का दूसरा नियम F = ma बताता है कि कुल बल = द्रव्यमान × त्वरण।"),
({"electricity","बिजली","विद्युत धारा","current"}, "विद्युत धारा आवेश के प्रवाह की दर है। सरल परिपथ में battery, conducting wires और device का बंद रास्ता होना चाहिए।"),
({"water cycle","जल चक्र","वाष्पीकरण","evaporation"}, "जल चक्र में वाष्पीकरण, संघनन, वर्षण और पानी का धरती पर बहना/भूमि में जाना शामिल है। सूर्य इसकी ऊर्जा का प्रमुख स्रोत है।"),
({"states of matter","पदार्थ की अवस्थाएँ","solid liquid gas","ठोस द्रव गैस"}, "पदार्थ की सामान्य अवस्थाएँ ठोस, द्रव और गैस हैं। प्लाज़्मा भी एक महत्वपूर्ण अवस्था है। कणों की व्यवस्था और ऊर्जा से गुण बदलते हैं।"),
({"acid base","अम्ल क्षार","ph scale","पीएच"}, "जलीय विलयन में pH 7 से कम सामान्यतः अम्लीय, 7 के आसपास उदासीन और 7 से अधिक क्षारीय होता है; तापमान और विलयन की प्रकृति भी मायने रखते हैं।"),
({"human heart","हृदय","heart"}, "मानव हृदय चार कक्षों वाला पेशीय अंग है। यह रक्त को फेफड़ों और शरीर के अन्य भागों तक पंप करता है।"),
({"dna","डीएनए","genetics","आनुवंशिकी"}, "DNA में जीवों के विकास और कार्य से जुड़ी आनुवंशिक जानकारी संग्रहित होती है। जीन DNA के विशिष्ट भाग होते हैं।"),
({"climate change","जलवायु परिवर्तन","global warming","ग्लोबल वार्मिंग"}, "मानवीय गतिविधियों से बढ़ी greenhouse gases पृथ्वी की औसत सतह का तापमान बढ़ा रही हैं। ऊर्जा बचत, स्वच्छ ऊर्जा और पारिस्थितिकी संरक्षण मदद कर सकते हैं।"),
# History and civics
({"aryabhata","आर्यभट्ट","aryabhata"}, "आचार्य आर्यभट्ट प्राचीन भारत के गणितज्ञ और खगोलविद थे। उनकी रचना आर्यभटीय लगभग 499 ईस्वी की है। उन्होंने गणित और खगोल-विज्ञान में महत्वपूर्ण योगदान दिया।"),
({"indus valley","सिंधु घाटी सभ्यता","हड़प्पा","हड़प्पा सभ्यता"}, "सिंधु घाटी सभ्यता की प्रमुख बस्तियों में हड़प्पा और मोहनजोदड़ो शामिल हैं। नगर नियोजन, जल निकासी और व्यापार इसकी उल्लेखनीय विशेषताएँ थीं।"),
({"ashoka","अशोक","सम्राट अशोक"}, "सम्राट अशोक मौर्य वंश के शासक थे। कलिंग युद्ध के बाद उनके शासन में धम्म, नैतिक आचरण और शिलालेखों का महत्व बढ़ा।"),
({"akbar","अकबर","मुगल"}, "अकबर मुगल साम्राज्य का शासक था। उसका शासन प्रशासन, राजस्व व्यवस्था और विभिन्न समुदायों के साथ संबंधों के लिए अध्ययन किया जाता है।"),
({"1857","revolt of 1857","1857 का विद्रोह","प्रथम स्वतंत्रता संग्राम"}, "1857 का विद्रोह ब्रिटिश ईस्ट इंडिया कंपनी के शासन के विरुद्ध व्यापक सैन्य और नागरिक विद्रोह था। इसके कारण राजनीतिक, आर्थिक, सैन्य और सामाजिक थे।"),
({"independence day","स्वतंत्रता दिवस","15 august","15 अगस्त"}, "भारत 15 अगस्त 1947 को ब्रिटिश शासन से स्वतंत्र हुआ। भारत हर वर्ष 15 अगस्त को स्वतंत्रता दिवस मनाता है।"),
({"constitution","संविधान","26 january","गणतंत्र दिवस"}, "भारत का संविधान 26 नवंबर 1949 को अपनाया गया और 26 जनवरी 1950 से लागू हुआ। इसलिए 26 जनवरी को गणतंत्र दिवस मनाया जाता है।"),
({"mahatma gandhi","महात्मा गांधी","गांधीजी"}, "महात्मा गांधी ने भारतीय स्वतंत्रता आंदोलन में अहिंसक प्रतिरोध और सत्याग्रह को प्रमुख बनाया।"),
({"rani lakshmibai","रानी लक्ष्मीबाई","झांसी की रानी"}, "रानी लक्ष्मीबाई झाँसी की शासक थीं और 1857 के विद्रोह में ब्रिटिश शासन के विरुद्ध संघर्ष के लिए जानी जाती हैं।"),
# Sanskrit
({"sanskrit","संस्कृत","देवभाषा"}, "संस्कृत भारत की प्राचीन शास्त्रीय भाषाओं में से एक है। इसमें वेद, उपनिषद, महाकाव्य, नाटक, दर्शन और गणित/खगोल-विज्ञान से जुड़े ग्रंथ रचे गए।"),
({"namaste in sanskrit","संस्कृत में नमस्ते","नमः","नमस्ते का अर्थ"}, "‘नमस्ते’ अभिवादन है; इसे सामान्यतः ‘आपको नमस्कार’ या ‘मैं आपके प्रति सम्मान प्रकट करता/करती हूँ’ के भाव में समझा जाता है।"),
({"रामः","राम शब्द","rama in sanskrit","राम शब्द रूप"}, "राम शब्द (पुल्लिंग, अकारान्त) के प्रथमा एकवचन में ‘रामः’, द्विवचन में ‘रामौ’ और बहुवचन में ‘रामाः’ आते हैं। यह केवल आरम्भिक उदाहरण है; पूरा शब्दरूप आठ विभक्तियों में पढ़ा जाता है।"),
({"गम् धातु","gam dhatu","संस्कृत धातु","धातु रूप"}, "‘गम्’ धातु का अर्थ जाना है। लट् लकार, प्रथम पुरुष, एकवचन में रूप ‘गच्छति’ होता है—अर्थात् वह जाता है।"),
({"संस्कृत वर्णमाला","sanskrit alphabet","स्वर व्यंजन"}, "संस्कृत वर्णमाला में स्वर और व्यंजन पढ़े जाते हैं। पाठ्यपुस्तक/परंपरा के अनुसार सूची में कुछ अंतर हो सकता है; सामान्यतः अ, आ, इ, ई आदि स्वर और क, ख, ग आदि व्यंजन सिखाए जाते हैं।"),
({"विद्या ददाति विनयम्","सुभाषित","संस्कृत श्लोक"}, "‘विद्या ददाति विनयम्’ का अर्थ है—विद्या विनम्रता देती है। यह संस्कृत में शिक्षा के महत्व पर प्रचलित सुभाषित का आरम्भिक अंश है।"),
# Language, computing and environment
({"algorithm","एल्गोरिदम","कलन विधि"}, "Algorithm किसी समस्या को हल करने के स्पष्ट, क्रमबद्ध चरणों का समूह है। एक ही समस्या के लिए कई सही algorithms हो सकते हैं।"),
({"python programming","python","पाइथन कोडिंग","coding"}, "Python एक high-level programming language है। इसका उपयोग automation, data analysis, education, web apps और AI में होता है।"),
({"internet","इंटरनेट","network"}, "Internet दुनिया भर के अनेक computer networks को जोड़ता है। किसी लिंक या वेबसाइट पर जाने से पहले स्रोत और सुरक्षा की जाँच करना अच्छा अभ्यास है।"),
({"cyber safety","साइबर सुरक्षा","password","पासवर्ड"}, "हर खाते के लिए अलग मजबूत पासवर्ड/पासफ्रेज़ रखें, two-factor authentication चालू करें, संदिग्ध लिंक न खोलें और OTP या पासवर्ड किसी को न दें।"),
({"pollution","प्रदूषण","air pollution","वायु प्रदूषण"}, "प्रदूषण हवा, पानी, मिट्टी या ध्वनि की गुणवत्ता को नुकसान पहुँचा सकता है। स्रोत घटाना, कचरे का सही प्रबंधन और स्वच्छ ऊर्जा महत्वपूर्ण उपाय हैं।"),
({"ecosystem","पारिस्थितिकी तंत्र","food chain","खाद्य श्रृंखला"}, "पारिस्थितिकी तंत्र में जीव और उनका निर्जीव पर्यावरण परस्पर क्रिया करते हैं। खाद्य श्रृंखला ऊर्जा के एक जीव से दूसरे जीव तक जाने का सरल मॉडल है।"),
]

def offline_answer(question):
    """Return a locally stored answer or None; never requires network access."""
    q = str(question).lower().strip()
    # Common school prompts should work offline even when Gemini is busy.
    if any(x in q for x in ("bharat per 5 points", "भारत पर 5 बिंदु", "भारत पर पांच बिंदु", "भारत के बारे में 5", "5 points on india", "5 points on bharat", "भारत पर पाँच बिंदु")):
        return ("वत्स, भारत के विषय में पाँच प्रमुख बिंदु प्रस्तुत हैं:\n"
                "1. भारत दक्षिण एशिया में स्थित एक देश है।\n"
                "2. भारत की राजधानी नई दिल्ली है।\n"
                "3. भारत एक लोकतांत्रिक गणराज्य है और इसका संविधान देश के शासन का आधार है।\n"
                "4. भारत में अनेक भाषाएँ, परंपराएँ, त्योहार और सांस्कृतिक विरासतें हैं।\n"
                "5. भारत की अर्थव्यवस्था में कृषि, उद्योग, सेवाएँ, विज्ञान और तकनीक महत्वपूर्ण भूमिका निभाते हैं।\n\n"
                "🌼 ज्ञान की ज्योति जलाए रखो। आयुष्मान भवः!\nअब बताओ, भारत के इतिहास पर पाँच बिंदु चाहोगे या भूगोल पर? ")
    # Basic arithmetic parser: allow digits, spaces, decimal points and arithmetic operators.
    import re, ast, operator
    expr = q
    if not re.fullmatch(r'[\d\s.+*/()%\-]+', expr):
        match = re.search(r'(?<![\w.])\d+(?:\.\d+)?(?:\s*[+*/%\-]\s*\d+(?:\.\d+)?|\s*\*\*\s*\d+)+(?:\s*[+*/%\-]\s*\d+(?:\.\d+)?)*', q)
        if match:
            expr = match.group(0)
    if re.fullmatch(r'[\d\s.+*/()%\-]+', expr) and any(ch.isdigit() for ch in expr):
        try:
            node = ast.parse(expr, mode='eval')
            ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod, ast.USub: operator.neg, ast.UAdd: operator.pos}
            def calc(n):
                if isinstance(n, ast.Expression): return calc(n.body)
                if isinstance(n, ast.Constant) and isinstance(n.value, (int,float)): return n.value
                if isinstance(n, ast.BinOp) and type(n.op) in ops: return ops[type(n.op)](calc(n.left), calc(n.right))
                if isinstance(n, ast.UnaryOp) and type(n.op) in ops: return ops[type(n.op)](calc(n.operand))
                raise ValueError('unsupported')
            val=calc(node)
            if abs(val) < 10**15: return f"गणना का उत्तर: {val:g}"
        except Exception: pass
    best=None; bestscore=0
    for keys, answer in OFFLINE_KB:
        score=0
        for k in keys:
            if k in q: score=max(score, len(k) + 4)
        if score>bestscore: bestscore=score; best=answer
    if best: return best + "\n\nज्ञान की ज्योति जलाए रखो।"
    if any(x in q for x in ["hello","hi","hey","नमस्ते","नमस्कार","प्रणाम"]):
        return "नमस्ते! मैं PROJECT ARYABHUTT का ऑफलाइन ज्ञान-सहायक हूँ। गणित, खगोल-विज्ञान, विज्ञान, इतिहास, संस्कृत, तकनीक और पर्यावरण से प्रश्न पूछ सकते हैं।"
    return None

def chatbot():
    section("आर्यभट्ट — AI Knowledge Chat","🤖")
    st.caption("Continuous conversation • Gemini Online • V5.6 Offline Knowledge Book • Hindi-first • Browser Voice")
    for idx, (role, msg) in enumerate(st.session_state.chat_history):
        with st.chat_message("user" if role=="user" else "assistant"):
            st.write(msg)
            if role == "assistant":
                browser_voice(msg, f"chat-{idx}")
    q = st.chat_input("अपना सवाल पूछो…")
    if q:
        st.session_state.chat_history.append(("user",q))
        st.session_state.chat += 1
        log_event("chat_question",page="AI Chatbot",details={"source":"student_prompt"})
        ans, status = gemini_answer(q)
        if ans is None:
            ans = offline_answer(q)
            if ans is None:
                detail = str(status).replace("\n", " ").strip()[:160]
                if "503" in detail or "UNAVAILABLE" in detail or "high demand" in detail.lower():
                    ans = ("वत्स, इस समय Gemini ज्ञान-सेवा पर बहुत अधिक अनुरोध हैं, इसलिए उत्तर अभी प्राप्त नहीं हो पाया। "
                           "मैंने दोबारा प्रयास किया, पर सेवा उपलब्ध नहीं हुई। प्रश्न को थोड़ी देर बाद फिर भेजना।\n\n"
                           "🌼 ज्ञान की ज्योति जलाए रखो। आयुष्मान भवः!\nतब तक चाहो तो प्रश्न को छोटे हिस्सों में लिखो या ऑफलाइन ज्ञान-संग्रह में उपलब्ध विषय पूछो।")
                else:
                    ans = ("वत्स, यह प्रश्न अभी मेरे स्थानीय ऑफलाइन ज्ञान-संग्रह में नहीं मिला। "
                           "Gemini/इंटरनेट उपलब्ध होने पर इसे फिर पूछना, या प्रश्न को स्पष्ट विषय और छोटे वाक्य में लिखना।\n\n"
                           "🌼 ज्ञान की ज्योति जलाए रखो। आयुष्मान भवः!\nध्यान रहे: ऑफलाइन संग्रह में चुने हुए विषयों के उत्तर हैं, दुनिया के हर प्रश्न का पूरा विश्वकोश नहीं।")
            status = "🟡 Offline Knowledge Book"
        st.session_state.chat_history.append(("assistant",ans))
        st.rerun()
    client, s = gemini_client()
    st.caption(("🔵 Gemini क्लाइंट कॉन्फ़िगर है — वास्तविक कनेक्शन प्रश्न भेजने पर जाँचा जाएगा" if client else "🟡 Offline Knowledge Book उपलब्ध") + " • " + ("हिंदी-first • Browser Voice" if client else s))

# -------------------- STUDY CENTER --------------------
def study_center():
    section("Study Center • ज्ञान कक्ष","📚")
    tabs=st.tabs(["📐 Shapes","📚 Formula Bank","📖 Definitions","🌟 Sia Story","🌌 Astronomy","🏛️ Kusumpura","💻 Technology","📅 Timetable"])
    with tabs[0]:
        for name,desc,formula in SHAPES:
            with st.expander(f"📐 {name}"):
                st.markdown(f"**{desc}**")
                visual_box(name, "△" if name=="Triangle" else "⬡" if name in ("Hexagon","Pentagon","Octagon") else "○", formula)
                st.write("Formula / idea:",formula)
                st.session_state.formula_views += 1
    with tabs[1]:
        cat=st.selectbox("Formula category",list(FORMULAS))
        for f in FORMULAS[cat]:
            st.markdown(f'<div class="card">📘 {html.escape(f)}</div>',unsafe_allow_html=True)
        st.session_state.formula_views += 1
    with tabs[2]:
        c1,c2=st.columns(2)
        with c1:
            start=st.number_input("Start card",1,len(DEFINITIONS),1)
        with c2:
            count=st.slider("How many cards",5,min(20,len(DEFINITIONS)),10)
        subset=DEFINITIONS[int(start)-1:int(start)-1+int(count)]
        st.caption(f"Showing {len(subset)} of {len(DEFINITIONS)} bilingual definitions")
        for en,hi,meaning,ex in subset:
            with st.expander(f"📘 {en} — {hi}"):
                st.write("**अर्थ / Meaning:**",meaning)
                st.write("**Example:**",ex)
        st.session_state.study_views += 1
    with tabs[3]:
        n=st.radio("कितने points पढ़ने हैं?",[5,10,20,30,50],horizontal=True)
        st.progress(n/50)
        st.caption(f"{n}/50 learning points")
        for i,p in enumerate(STORY_POINTS[:n],1):
            st.markdown(f'<div class="card"><b>🌟 {i:02d}</b><br>{html.escape(p)}</div>',unsafe_allow_html=True)
        if st.button("✅ Mark these story points as read"):
            st.session_state.story_points += n
            st.success(f"{n} story points tracked.")
    with tabs[4]:
        astronomy_tab()
    with tabs[5]:
        for name,desc in KUSUMPURA:
            with st.expander(name):
                visual_box(name,name.split()[0] if name else "🏛️",desc)
                st.write("💡",desc)
    with tabs[6]:
        for name,desc,diagram,label in TECH:
            with st.expander(name):
                visual_box(name,"💻" if "Computer" in name else "🤖" if "AI" in name or "Robot" in name else "🌐",diagram)
                st.write("💡",desc)
                st.code(diagram, language="text")
    with tabs[7]:
        st.info("4-week timetable — web demo में editable study plan.")
        for week in range(1,5):
            with st.expander(f"Week {week}"):
                for d in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]:
                    st.write(f"**{d}:** Maths • Science • Astronomy • Coding • Quiz")

def astronomy_tab():
    st.markdown("### 🌌 Astronomy Explorer")
    st.write("यहाँ केवल eclipse नहीं — पूरे solar system, planets, Earth-Moon, Milky Way और ancient observation topics हैं।")
    cols=st.columns(3)
    for i,(name,fact,kind,theme) in enumerate(ASTRO):
        with cols[i%3]:
            st.markdown(f'<div class="card"><h4>{name}</h4><p>{html.escape(fact)}</p></div>',unsafe_allow_html=True)
            if "Mercury" in name: sym="☿"
            elif "Venus" in name: sym="♀"
            elif "Earth" in name: sym="🌍"
            elif "Mars" in name: sym="♂"
            elif "Jupiter" in name: sym="♃"
            elif "Saturn" in name: sym="♄"
            elif "Uranus" in name: sym="♅"
            elif "Neptune" in name: sym="♆"
            elif "Solar" in name: sym="☀️"
            elif "Lunar" in name: sym="🌕"
            elif "Milky" in name: sym="🌌"
            else: sym="🪐"
            visual_box(name,sym,kind)
    st.session_state.astronomy_views += 1
    st.info("🔭 Verified science reference for judges: NASA's Solar System image gallery and planet pages can be opened from the project resources.")

# -------------------- SPACE & VISUALIZERS --------------------
def space_visualizers():
    section("Space & Visualizers","🌌")
    st.write("Interactive visual learning: planets + eclipse geometry + astronomy facts.")
    st.markdown("### ☀️ Solar System Visual")
    visual_box("Sun → Mercury → Venus → Earth → Mars → Jupiter → Saturn → Uranus → Neptune","☀️","Planet order from the Sun")
    st.markdown("### 🌑 Solar Eclipse")
    visual_box("SUN → MOON → EARTH","🌑","Moon's shadow can fall on parts of Earth")
    st.markdown("### 🌕 Lunar Eclipse")
    visual_box("SUN → EARTH → MOON","🌕","Earth's shadow can fall on the Moon")
    st.markdown("### ✨ Amazing Astronomy Facts")
    facts=[
        "हमारे solar system में 8 planets हैं।",
        "Jupiter solar system का largest planet है।",
        "Saturn अपने prominent rings के लिए प्रसिद्ध है।",
        "Mercury Sun के सबसे करीब और solar system का smallest planet है।",
        "Uranus और Neptune ice giants हैं।",
        "Milky Way हमारी galaxy है।",
        "Solar eclipse में Moon Sun और Earth के बीच आ सकता है।",
        "Lunar eclipse में Earth की shadow Moon पर पड़ सकती है।",
    ]
    for f in facts: st.markdown(f"• {f}")
    st.link_button("🛰️ Open official NASA Solar System image gallery", "https://science.nasa.gov/gallery/our-solar-system-images/")
    st.caption("Science facts are presented in a school-level form. The project also provides visual cards so the astronomy section is not text-only.")

# -------------------- ANALYTICS --------------------
def analytics():
    section("Data & Analytics","📊")
    data=[
        ("Sessions",st.session_state.sessions),
        ("Games Played",st.session_state.games),
        ("Riddles Solved",st.session_state.riddles),
        ("Chat Questions",st.session_state.chat),
        ("Study Views",st.session_state.study_views),
        ("Formula Views",st.session_state.formula_views),
        ("Story Points Read",st.session_state.story_points),
        ("Astronomy Views",st.session_state.astronomy_views),
        ("Math Activity",st.session_state.math_activity),
        ("Reports Generated",st.session_state.reports),
    ]
    cols=st.columns(5)
    for i,(k,v) in enumerate(data):
        cols[i%5].metric(k,v)
    st.markdown("### 🏫 Database Summary")
    c1,c2=st.columns(2)
    stats=db_stats()
    c1.metric("Registered Schools",stats["schools"])
    c2.metric("Registered Students",stats["students"])
    saved_schools=db_rows("SELECT name AS School, note AS Note, created_at AS 'Added at' FROM schools ORDER BY name")
    if saved_schools:
        st.dataframe(saved_schools,use_container_width=True,hide_index=True)
    else:
        st.info("अभी कोई स्कूल दर्ज नहीं है। Teacher/Admin से स्कूल जोड़ सकते हैं।")
    st.caption("⚠️ SQLite रिकॉर्ड इसी running host पर सेव होते हैं। Streamlit Cloud redeploy/restart पर local file मिट सकती है; official permanent records के लिए hosted database जोड़ें।")

# -------------------- TEACHER / ADMIN --------------------
def admin():
    section("Teacher / Admin Dashboard", "🔐")
    if not st.session_state.admin_ok:
        if admin_password() == "aryabhutt":
            st.warning("डेमो पासवर्ड अभी भी चालू है। प्रकाशित करने से पहले Streamlit Secrets में मजबूत ADMIN_PASSWORD सेट करें।")
        with st.form("admin_login"):
            pw=st.text_input("Admin password",type="password")
            ok=st.form_submit_button("🔓 Login")
        if ok:
            if pw==admin_password():
                st.session_state.admin_ok=True; st.success("Teacher/Admin login successful."); st.rerun()
            else: st.error("पासवर्ड सही नहीं है।")
        return
    stats=db_stats(); c1,c2,c3,c4=st.columns(4)
    c1.metric("🏫 Schools",stats["schools"]); c2.metric("🧑‍🎓 Registered students",stats["students"])
    c3.metric("🕒 Sessions",stats["sessions"]); c4.metric("📚 Activities",stats["events"])
    t1,t2,t3=st.tabs(["🏫 स्कूल जोड़ें","🧑‍🎓 बच्चे जोड़ें","📊 Attendance / Activity"])
    with t1:
        with st.form("add_school_form"):
            school_name=st.text_input("School name")
            school_note=st.text_input("Optional note / location")
            save_school=st.form_submit_button("➕ Add school")
        if save_school and school_name.strip():
            try: db_add_school(school_name.strip(),school_note.strip()); st.success("School saved."); st.rerun()
            except sqlite3.IntegrityError: st.warning("यह स्कूल पहले से मौजूद है।")
        schools=db_rows("SELECT id, name, note, created_at FROM schools ORDER BY name")
        if schools: st.dataframe(schools,use_container_width=True,hide_index=True)
    with t2:
        schools=db_rows("SELECT id, name FROM schools ORDER BY name")
        school_opts={row["name"]:row["id"] for row in schools}
        with st.form("add_student_form"):
            name=st.text_input("बच्चे का पहला नाम")
            school_label=st.selectbox("School",["(Select school)"]+list(school_opts.keys()))
            class_section=st.text_input("Class / section (optional)")
            save_student=st.form_submit_button("➕ Add student")
        if save_student and name.strip():
            school_id=school_opts.get(school_label)
            db_add_student(name.strip(),school_id,class_section.strip())
            st.success("बच्चा student register में जोड़ दिया गया।")
        students=db_rows("SELECT s.id AS ID,s.first_name AS Name,COALESCE(sc.name,'Not specified') AS School,s.class_section AS Class,s.created_at AS 'Added at',COUNT(ss.id) AS Sessions,COALESCE(SUM(ss.estimated_minutes),0) AS 'Approx. active minutes' FROM students s LEFT JOIN schools sc ON sc.id=s.school_id LEFT JOIN app_sessions ss ON ss.student_id=s.id WHERE s.active=1 GROUP BY s.id ORDER BY s.created_at DESC")
        if students: st.dataframe(students,use_container_width=True,hide_index=True)
    with t3:
        sessions=db_rows("SELECT ss.started_at AS started_at,ss.last_seen_at AS 'Last activity',ss.ended_at AS 'Time out (if recorded)',s.first_name AS Student,COALESCE(sc.name,'Not specified') AS School,s.class_section AS Class,ss.estimated_minutes AS 'Approx. active minutes' FROM app_sessions ss JOIN students s ON s.id=ss.student_id LEFT JOIN schools sc ON sc.id=s.school_id ORDER BY ss.started_at DESC LIMIT 500")
        for row in sessions:
            try:
                stamp=datetime.fromisoformat(row.pop("started_at"))
                row["Date"]=stamp.date().isoformat()
                row["Day"]=stamp.strftime("%A")
                row["Time in"]=stamp.strftime("%H:%M:%S %Z")
            except Exception:
                row["Date"]=""; row["Day"]=""; row["Time in"]=""
        st.caption("Time-out exact नहीं हो सकता जब बच्चा tab बंद कर दे; active minutes start और last activity से अनुमानित हैं।")
        if sessions: st.dataframe(sessions,use_container_width=True,hide_index=True)
        else: st.info("अभी कोई student session दर्ज नहीं है।")
        events=db_rows("SELECT e.created_at AS 'Date & time',s.first_name AS Student,e.page AS Page,e.event_type AS Activity,e.details AS Details FROM activity_events e LEFT JOIN students s ON s.id=e.student_id ORDER BY e.created_at DESC LIMIT 500")
        st.markdown("#### Recent activity")
        if events: st.dataframe(events,use_container_width=True,hide_index=True)
        if sessions: st.download_button("📥 Download attendance CSV", rows_to_csv(sessions), file_name="aryabhutt_attendance.csv", mime="text/csv")
    if st.button("🔒 Logout Admin"):
        st.session_state.admin_ok=False; st.rerun()

# -------------------- QUESTION BANKS / CHALLENGES --------------------
QUESTION_COUNTS = [5, 10, 15, 20, 50]
CHALLENGE_QUESTIONS = [
    {"hi": 'हमारे सौरमंडल में कितने ग्रह हैं?', "en": 'How many planets are in our Solar System?', "type": "mcq", "options_hi": ['7', '8', '9'], "options_en": ['7', '8', '9'], "correct": 1},
    {"hi": 'सौरमंडल का सबसे बड़ा ग्रह कौन-सा है?', "en": 'Which is the largest planet in the Solar System?', "type": "mcq", "options_hi": ['मंगल', 'बृहस्पति', 'शुक्र'], "options_en": ['Mars', 'Jupiter', 'Venus'], "correct": 1},
    {"hi": 'पृथ्वी का प्राकृतिक उपग्रह कौन है?', "en": 'What is Earth’s natural satellite?', "type": "mcq", "options_hi": ['चंद्रमा', 'सूर्य', 'मंगल'], "options_en": ['Moon', 'Sun', 'Mars'], "correct": 0},
    {"hi": 'लाल ग्रह किसे कहा जाता है?', "en": 'Which planet is called the Red Planet?', "type": "mcq", "options_hi": ['शुक्र', 'मंगल', 'बुध'], "options_en": ['Venus', 'Mars', 'Mercury'], "correct": 1},
    {"hi": 'सूर्य के सबसे निकट कौन-सा ग्रह है?', "en": 'Which planet is closest to the Sun?', "type": "mcq", "options_hi": ['बुध', 'पृथ्वी', 'शनि'], "options_en": ['Mercury', 'Earth', 'Saturn'], "correct": 0},
    {"hi": 'वलयों के लिए प्रसिद्ध ग्रह कौन-सा है?', "en": 'Which planet is famous for its rings?', "type": "mcq", "options_hi": ['शनि', 'बुध', 'मंगल'], "options_en": ['Saturn', 'Mercury', 'Mars'], "correct": 0},
    {"hi": 'हमारी आकाशगंगा का नाम क्या है?', "en": 'What is the name of our galaxy?', "type": "short", "answer": 'Milky Way', "options_hi": [], "options_en": []},
    {"hi": 'दिन और रात मुख्यतः किस कारण होते हैं?', "en": 'What mainly causes day and night?', "type": "mcq", "options_hi": ['पृथ्वी का घूर्णन', 'पृथ्वी की परिक्रमा', 'चंद्रमा की गति'], "options_en": ['Earth’s rotation', 'Earth’s revolution', 'Moon’s motion'], "correct": 0},
    {"hi": 'पृथ्वी सूर्य की एक परिक्रमा लगभग कितने समय में करती है?', "en": 'About how long does Earth take to orbit the Sun?', "type": "mcq", "options_hi": ['24 घंटे', '365 दिन', '30 दिन'], "options_en": ['24 hours', '365 days', '30 days'], "correct": 1},
    {"hi": 'सूर्य क्या है?', "en": 'What is the Sun?', "type": "mcq", "options_hi": ['ग्रह', 'तारा', 'उपग्रह'], "options_en": ['Planet', 'Star', 'Satellite'], "correct": 1},
    {"hi": 'आर्यभट्ट किस क्षेत्र से जुड़े महान विद्वान थे?', "en": 'Aryabhata was a renowned scholar of which field?', "type": "mcq", "options_hi": ['गणित और खगोल-विज्ञान', 'संगीत', 'चित्रकला'], "options_en": ['Mathematics and astronomy', 'Music', 'Painting'], "correct": 0},
    {"hi": '7 × 8 कितना होता है?', "en": 'What is 7 × 8?', "type": "short", "answer": '56', "options_hi": [], "options_en": []},
    {"hi": '100 का 25% कितना है?', "en": 'What is 25% of 100?', "type": "short", "answer": '25', "options_hi": [], "options_en": []},
    {"hi": 'आयत का क्षेत्रफल कैसे निकालते हैं?', "en": 'How do you calculate the area of a rectangle?', "type": "mcq", "options_hi": ['लंबाई × चौड़ाई', '2 × लंबाई', 'लंबाई + चौड़ाई'], "options_en": ['Length × width', '2 × length', 'Length + width'], "correct": 0},
    {"hi": 'वृत्त के क्षेत्रफल का सूत्र कौन-सा है?', "en": 'Which is the formula for the area of a circle?', "type": "mcq", "options_hi": ['2πr', 'πr²', 'πd'], "options_en": ['2πr', 'πr²', 'πd'], "correct": 1},
    {"hi": 'त्रिभुज के कोणों का योग कितना होता है?', "en": 'What is the sum of the interior angles of a triangle?', "type": "mcq", "options_hi": ['90°', '180°', '360°'], "options_en": ['90°', '180°', '360°'], "correct": 1},
    {"hi": 'एक दर्जन में कितनी वस्तुएँ होती हैं?', "en": 'How many items are in a dozen?', "type": "mcq", "options_hi": ['10', '12', '20'], "options_en": ['10', '12', '20'], "correct": 1},
    {"hi": 'अभाज्य संख्या का सही उदाहरण कौन-सा है?', "en": 'Which is an example of a prime number?', "type": "mcq", "options_hi": ['9', '11', '15'], "options_en": ['9', '11', '15'], "correct": 1},
    {"hi": 'जल का रासायनिक सूत्र क्या है?', "en": 'What is the chemical formula of water?', "type": "short", "answer": 'H2O', "options_hi": [], "options_en": []},
    {"hi": 'पौधे प्रकाश-संश्लेषण में कौन-सी गैस लेते हैं?', "en": 'Which gas do plants take in for photosynthesis?', "type": "mcq", "options_hi": ['ऑक्सीजन', 'कार्बन डाइऑक्साइड', 'हीलियम'], "options_en": ['Oxygen', 'Carbon dioxide', 'Helium'], "correct": 1},
    {"hi": 'मनुष्य साँस लेने के लिए मुख्यतः कौन-सी गैस उपयोग करता है?', "en": 'Which gas do humans mainly use for respiration?', "type": "mcq", "options_hi": ['ऑक्सीजन', 'नाइट्रोजन', 'हाइड्रोजन'], "options_en": ['Oxygen', 'Nitrogen', 'Hydrogen'], "correct": 0},
    {"hi": 'समुद्र तल पर पानी लगभग किस तापमान पर उबलता है?', "en": 'At about what temperature does water boil at sea level?', "type": "mcq", "options_hi": ['0°C', '100°C', '50°C'], "options_en": ['0°C', '100°C', '50°C'], "correct": 1},
    {"hi": 'बल की SI इकाई क्या है?', "en": 'What is the SI unit of force?', "type": "short", "answer": 'Newton', "options_hi": [], "options_en": []},
    {"hi": 'ध्वनि किसमें यात्रा नहीं कर सकती?', "en": 'Through which medium can sound not travel?', "type": "mcq", "options_hi": ['हवा', 'पानी', 'निर्वात'], "options_en": ['Air', 'Water', 'Vacuum'], "correct": 2},
    {"hi": 'मानव शरीर में रक्त पंप करने वाला अंग कौन है?', "en": 'Which organ pumps blood in the human body?', "type": "mcq", "options_hi": ['फेफड़े', 'हृदय', 'यकृत'], "options_en": ['Lungs', 'Heart', 'Liver'], "correct": 1},
    {"hi": 'पृथ्वी की सतह का अधिकांश भाग किससे ढका है?', "en": 'What covers most of Earth’s surface?', "type": "mcq", "options_hi": ['पानी', 'रेत', 'बर्फ'], "options_en": ['Water', 'Sand', 'Ice'], "correct": 0},
    {"hi": 'जल का जमने का तापमान लगभग कितना है?', "en": 'At about what temperature does water freeze?', "type": "mcq", "options_hi": ['0°C', '100°C', '25°C'], "options_en": ['0°C', '100°C', '25°C'], "correct": 0},
    {"hi": 'कंप्यूटर मुख्यतः किस जानकारी को संसाधित करता है?', "en": 'What does a computer primarily process?', "type": "short", "answer": 'data', "options_hi": [], "options_en": []},
    {"hi": 'AI पैटर्न सीखने के लिए आम तौर पर किसका उपयोग करता है?', "en": 'What does AI commonly use to learn patterns?', "type": "mcq", "options_hi": ['डेटा', 'केवल रंग', 'कोई जानकारी नहीं'], "options_en": ['Data', 'Only colours', 'No information'], "correct": 0},
    {"hi": 'वेबसाइट खोलने के लिए सामान्यतः किसका उपयोग होता है?', "en": 'What is commonly used to open a website?', "type": "mcq", "options_hi": ['ब्राउज़र', 'कैलकुलेटर', 'कम्पास'], "options_en": ['Browser', 'Calculator', 'Compass'], "correct": 0},
    {"hi": 'मजबूत पासवर्ड कैसा होना चाहिए?', "en": 'What should a strong password be like?', "type": "mcq", "options_hi": ['आसान और सबको पता', 'लंबा और अनुमान लगाना कठिन', 'अपना नाम मात्र'], "options_en": ['Easy and public', 'Long and hard to guess', 'Just your name'], "correct": 1},
    {"hi": 'किसी अनजान व्यक्ति को OTP देना चाहिए?', "en": 'Should you share an OTP with a stranger?', "type": "mcq", "options_hi": ['हाँ', 'नहीं', 'केवल ऑनलाइन'], "options_en": ['Yes', 'No', 'Only online'], "correct": 1},
    {"hi": 'एल्गोरिदम क्या है?', "en": 'What is an algorithm?', "type": "short", "answer": 'algorithm', "options_hi": [], "options_en": []},
    {"hi": 'नेटवर्क किन चीज़ों को जोड़ सकता है?', "en": 'What can a network connect?', "type": "mcq", "options_hi": ['डिवाइस', 'केवल किताबें', 'केवल बादल'], "options_en": ['Devices', 'Only books', 'Only clouds'], "correct": 0},
    {"hi": 'QR कोड को पढ़ने के लिए किसकी ज़रूरत हो सकती है?', "en": 'What may be used to read a QR code?', "type": "mcq", "options_hi": ['कैमरा या स्कैनर', 'थर्मामीटर', 'कम्पास'], "options_en": ['Camera or scanner', 'Thermometer', 'Compass'], "correct": 0},
    {"hi": 'पर्यावरण प्रदूषण कम करने का एक तरीका क्या है?', "en": 'What is one way to reduce environmental pollution?', "type": "mcq", "options_hi": ['कचरा नदी में डालना', 'कचरे का सही प्रबंधन', 'पेड़ काटना'], "options_en": ['Dump waste in rivers', 'Manage waste properly', 'Cut trees'], "correct": 1},
    {"hi": 'खाद्य श्रृंखला किसका प्रवाह दिखाती है?', "en": 'What does a food chain show?', "type": "mcq", "options_hi": ['ऊर्जा का प्रवाह', 'सड़क का नक्शा', 'ग्रहों की दूरी'], "options_en": ['Flow of energy', 'Road map', 'Planet distances'], "correct": 0},
    {"hi": 'नवीकरणीय ऊर्जा का उदाहरण क्या है?', "en": 'Which is an example of renewable energy?', "type": "short", "answer": 'solar energy', "options_hi": [], "options_en": []},
    {"hi": 'पृथ्वी के सबसे निकट तारा कौन है?', "en": 'Which star is closest to Earth?', "type": "mcq", "options_hi": ['सूर्य', 'सीरियस', 'ध्रुव तारा'], "options_en": ['Sun', 'Sirius', 'Polaris'], "correct": 0},
    {"hi": 'चंद्रमा का अपना प्रकाश होता है?', "en": 'Does the Moon produce its own visible light?', "type": "mcq", "options_hi": ['हाँ', 'नहीं, यह सूर्य का प्रकाश परावर्तित करता है', 'केवल दिन में'], "options_en": ['Yes', 'No, it reflects sunlight', 'Only in daytime'], "correct": 1},
    {"hi": 'छाया बनने के लिए क्या आवश्यक है?', "en": 'What is needed to form a shadow?', "type": "mcq", "options_hi": ['प्रकाश और कोई वस्तु', 'केवल ध्वनि', 'केवल हवा'], "options_en": ['Light and an object', 'Sound only', 'Air only'], "correct": 0},
    {"hi": 'सही समय-सारणी किसमें मदद करती है?', "en": 'How does a timetable help?', "type": "mcq", "options_hi": ['काम व्यवस्थित करने में', 'समय रोकने में', 'गुरुत्वाकर्षण हटाने में'], "options_en": ['Organising tasks', 'Stopping time', 'Removing gravity'], "correct": 0},
    {"hi": 'पृथ्वी का आकार सबसे अच्छा किससे वर्णित होता है?', "en": 'Which best describes Earth’s shape?', "type": "mcq", "options_hi": ['लगभग गोलाकार', 'समतल चौकोर', 'त्रिकोणीय'], "options_en": ['Nearly spherical', 'Flat square', 'Triangular'], "correct": 0},
    {"hi": 'विटामिन D का प्राकृतिक स्रोत क्या हो सकता है?', "en": 'What can be a natural source of vitamin D?', "type": "short", "answer": 'thermometer', "options_hi": [], "options_en": []},
    {"hi": 'पानी बचाने का अच्छा तरीका कौन-सा है?', "en": 'Which is a good way to conserve water?', "type": "mcq", "options_hi": ['नल खुला छोड़ना', 'लीक ठीक करना', 'साफ पानी बहाना'], "options_en": ['Leave taps running', 'Fix leaks', 'Waste clean water'], "correct": 1},
    {"hi": 'किस उपकरण से तापमान मापा जाता है?', "en": 'Which instrument measures temperature?', "type": "mcq", "options_hi": ['थर्मामीटर', 'बारोमीटर', 'कम्पास'], "options_en": ['Thermometer', 'Barometer', 'Compass'], "correct": 0},
    {"hi": 'कम्पास मुख्यतः क्या बताता है?', "en": 'What does a compass mainly indicate?', "type": "short", "answer": 'direction', "options_hi": [], "options_en": []},
    {"hi": 'प्रोग्रामिंग में कोड क्या होता है?', "en": 'What is code in programming?', "type": "mcq", "options_hi": ['कंप्यूटर को दिए गए निर्देश', 'एक खनिज', 'मौसम'], "options_en": ['Instructions for a computer', 'A mineral', 'Weather'], "correct": 0},
    {"hi": 'पुस्तकालय का मुख्य उद्देश्य क्या है?', "en": 'What is the main purpose of a library?', "type": "mcq", "options_hi": ['पढ़ने और सीखने के संसाधन देना', 'खेल का मैदान होना', 'खाना पकाना'], "options_en": ['Provide reading and learning resources', 'Be a playground', 'Cook food'], "correct": 0},
    {"hi": 'वैज्ञानिक प्रयोग करते समय क्या करना चाहिए?', "en": 'What should you do during a scientific experiment?', "type": "mcq", "options_hi": ['ध्यान से निरीक्षण और रिकॉर्ड', 'परिणाम गढ़ना', 'सुरक्षा नियम भूलना'], "options_en": ['Observe and record carefully', 'Invent results', 'Ignore safety'], "correct": 0},
]

RIDDLE_QUESTIONS = [
    ("I have hands but cannot clap. What am I?", ["clock", "घड़ी"]),
    ("I have keys but open no locks. What am I?", ["piano", "keyboard", "पियानो", "कीबोर्ड"]),
    ("The more you take, the more you leave behind. What are they?", ["footsteps", "footprints", "कदमों के निशान"]),
    ("I have a face and two hands but no arms or legs. What am I?", ["clock", "घड़ी"]),
    ("What gets wetter as it dries?", ["towel", "तौलिया"]),
    ("What has one eye but cannot see?", ["needle", "सुई"]),
    ("What has many teeth but cannot bite?", ["comb", "कंघी"]),
    ("What has a neck but no head?", ["bottle", "बोतल"]),
    ("What can travel around the world while staying in a corner?", ["stamp", "डाक टिकट"]),
    ("What has words but never speaks?", ["book", "किताब"]),
    ("What has four legs but cannot walk?", ["table", "chair", "मेज", "कुर्सी"]),
    ("What goes up but never comes down?", ["age", "उम्र"]),
    ("What has a ring but no finger?", ["telephone", "phone", "टेलीफोन"]),
    ("What can you catch but not throw?", ["cold", "सर्दी"]),
    ("What has a head and a tail but no body?", ["coin", "सिक्का"]),
    ("What has cities but no houses, rivers but no water?", ["map", "नक्शा"]),
    ("What has to be broken before you can use it?", ["egg", "अंडा"]),
    ("What has branches but no fruit, trunk, or leaves?", ["bank", "बैंक"]),
    ("What begins with T, ends with T, and has T inside?", ["teapot", "टीपॉट"]),
    ("What has 13 hearts but no other organs?", ["deck of cards", "cards", "ताश की गड्डी"]),
    ("What has a thumb and four fingers but is not alive?", ["glove", "दस्ताना"]),
    ("What has a bed but never sleeps and a mouth but never eats?", ["river", "नदी"]),
    ("What can fill a room but takes no space?", ["light", "प्रकाश"]),
    ("What has a bottom at the top?", ["legs", "your legs", "पैर"]),
    ("What has an endless supply of letters but starts empty?", ["mailbox", "letterbox", "डाक पेटी"]),
    ("What has a spine but no bones?", ["book", "किताब"]),
    ("What has ears but cannot hear?", ["corn", "मक्का"]),
    ("What kind of room has no doors or windows?", ["mushroom", "मशरूम"]),
    ("What can be cracked, made, told, and played?", ["joke", "चुटकुला"]),
    ("What has a bark but no bite?", ["tree", "पेड़"]),
    ("What has a tail and a head but no legs?", ["coin", "सिक्का"]),
    ("What goes through towns and over hills but never moves?", ["road", "सड़क"]),
    ("What can you serve but never eat?", ["tennis ball", "volleyball", "ball"]),
    ("What has lots of eyes but cannot see?", ["potato", "आलू"]),
    ("What has many needles but does not sew?", ["pine tree", "pine", "चीड़ का पेड़"]),
    ("What has a tongue but cannot talk?", ["shoe", "जूता"]),
    ("What has a lock but no key?", ["hair", "बाल"]),
    ("What can run but never walks?", ["water", "पानी"]),
    ("What has no life but can die?", ["battery", "बैटरी"]),
    ("What has a roof but no walls?", ["tent", "तंबू"]),
    ("What can be opened but has no lid or door?", ["mind", "मन"]),
    ("What has a ring around its finger but is not a person?", ["saturn", "शनि"]),
    ("What is always in front of you but cannot be seen?", ["future", "भविष्य"]),
    ("What has a heart that doesn't beat?", ["artichoke", "अर्टिचोक"]),
    ("What is full of holes but still holds water?", ["sponge", "स्पंज"]),
    ("What has a face but no eyes, nose, or mouth?", ["clock", "घड़ी"]),
    ("What has a web but is not a website?", ["spider", "मकड़ी"]),
    ("What gets bigger the more you take away?", ["hole", "गड्ढा"]),
    ("What has an eye at the center but cannot see?", ["hurricane", "storm", "तूफान"]),
    ("What can you keep after giving it to someone?", ["your word", "promise", "वादा"]),
]


def _normalise_answer(value):
    value = str(value or "").strip().lower()
    for ch in ".,!?;:()[]{}\"'`^":
        value = value.replace(ch, "")
    return " ".join(value.split())

def answer_matches(given, accepted):
    g = _normalise_answer(given)
    if not g:
        return False
    for option in accepted:
        a = _normalise_answer(option)
        if g == a:
            return True
        if len(a) >= 5 and (a in g or g in a):
            return True
    return False

def question_challenge(title, key_prefix, counter="games"):
    """50 bilingual questions: multiple choice plus short answer; offline-capable."""
    section(title, "🧠")
    use_hindi = st.session_state.get("lang", "हिन्दी") == "हिन्दी"
    count_label = "कितने सवाल हल करने हैं?" if use_hindi else "Number of questions"
    count = st.selectbox(count_label, QUESTION_COUNTS, index=1, key=f"{key_prefix}_count")
    chosen = CHALLENGE_QUESTIONS[:count]
    st.caption(("सही विकल्प चुनें या उत्तर लिखें।" if use_hindi else "Choose the correct option or type your answer.") + f" • {len(CHALLENGE_QUESTIONS)} प्रश्न उपलब्ध")
    with st.form(f"{key_prefix}_form"):
        answers=[]
        for i,q in enumerate(chosen,1):
            question=q["hi"] if use_hindi else q["en"]
            st.markdown(f"**{i}. {question}**")
            if q["type"] == "mcq":
                opts=q["options_hi"] if use_hindi else q["options_en"]
                pick_label="अपना उत्तर चुनें" if use_hindi else "Select an answer"
                answers.append(st.radio(pick_label,opts,index=None,key=f"{key_prefix}_answer_{i}"))
            else:
                input_label="उत्तर लिखें" if use_hindi else "Type your answer"
                answers.append(st.text_input(input_label,key=f"{key_prefix}_answer_{i}"))
        submitted=st.form_submit_button("✅ उत्तर जाँचें / Check answers")
    if submitted:
        score=0; details=[]
        for i,(q,answer) in enumerate(zip(chosen,answers),1):
            if q["type"] == "mcq":
                opts=q["options_hi"] if use_hindi else q["options_en"]
                correct_text=opts[q["correct"]]
                ok=answer == correct_text
            else:
                expected=str(q.get("answer", "")).strip().lower()
                got=_normalise_answer(answer)
                accepted={expected}
                translations={"milky way":{"आकाशगंगा"},"56":{"fifty six","छप्पन"},"25":{"twenty five","पच्चीस"},"h2o":{"water","पानी"},"newton":{"न्यूटन"},"data":{"डेटा"},"algorithm":{"एल्गोरिदम"},"solar energy":{"सौर ऊर्जा"},"thermometer":{"थर्मामीटर"},"direction":{"दिशा"}}
                accepted.update(translations.get(expected,set()))
                ok=got in accepted
                correct_text=q.get("answer", "")
                if use_hindi: correct_text=next(iter(translations.get(expected,{correct_text}))) if translations.get(expected) else correct_text
            if ok: score+=1
            else: details.append((i,q["hi"] if use_hindi else q["en"],correct_text))
        st.session_state[f"{key_prefix}_last_score"] = score
        st.session_state[f"{key_prefix}_last_total"] = len(chosen)
        if counter in st.session_state: st.session_state[counter]+=1
        log_event("quiz_submitted", details={"quiz":key_prefix,"score":score,"total":len(chosen)})
        st.success(("तुम्हारा स्कोर" if use_hindi else "Your score") + f": {score}/{len(chosen)}")
        if details:
            with st.expander("गलत उत्तर देखें / Review answers"):
                for number,question,correct_answer in details:
                    st.write(f"{number}. {question}")
                    st.caption(("सही उत्तर: " if use_hindi else "Correct answer: ")+str(correct_answer))
        else: st.balloons()

def riddle_challenge(title, bank, key_prefix, counter="games"):
    section(title,"🧩")
    count=st.selectbox("कितनी पहेलियाँ?",QUESTION_COUNTS,index=1,key=f"{key_prefix}_count")
    with st.form(f"{key_prefix}_form"):
        answers=[st.text_input(f"{i}. {q}",key=f"{key_prefix}_answer_{i}") for i,(q,_accepted) in enumerate(bank[:count],1)]
        submitted=st.form_submit_button("उत्तर जाँचें")
    if submitted:
        score=sum(answer_matches(ans,item[1]) for ans,item in zip(answers,bank[:count]))
        st.session_state[counter]+=1
        st.session_state.riddles+=score
        log_event("riddle_submitted",details={"quiz":key_prefix,"score":score,"total":count})
        st.success(f"स्कोर: {score}/{count}")
        if score==count: st.balloons()
        else: st.info("अच्छी कोशिश! गलत उत्तरों को देखकर फिर प्रयास करो।")

# -------------------- GAMES --------------------
def games():
    section("Game Zone — 10 Games + Daily Quiz","🎮")
    game=st.selectbox("Choose a game",[
        "Guess the Number","Flip a Coin","Rock-Paper-Scissors","Color Matcher",
        "Roll the Dice","Math Quiz","Magic Ball 8","Word Scramble",
        "Animal Guessing","Click Speed Test","Daily Quiz","AI Challenge","Riddle Challenge"
    ])
    if game=="Guess the Number":
        target=st.session_state.setdefault("guess_target",random.randint(1,20))
        g=st.number_input("Guess 1–20",1,20,10)
        if st.button("Check Guess"):
            st.session_state.games+=1
            if g==target:
                st.success("🎉 Correct!")
                st.session_state.pop("guess_target",None)
            elif g<target: st.info("थोड़ा बड़ा number try करो.")
            else: st.info("थोड़ा छोटा number try करो.")
    elif game=="Flip a Coin":
        if st.button("Flip"):
            st.session_state.games+=1
            st.success(random.choice(["Heads","Tails"]))
    elif game=="Rock-Paper-Scissors":
        p=st.selectbox("Your choice",["Rock","Paper","Scissors"])
        if st.button("Play"):
            st.session_state.games+=1
            bot=random.choice(["Rock","Paper","Scissors"])
            st.write("Computer:",bot)
            if p==bot: st.info("Draw")
            elif (p,bot) in [("Rock","Scissors"),("Paper","Rock"),("Scissors","Paper")]: st.success("You win!")
            else: st.warning("Try again!")
    elif game=="Color Matcher":
        colors=["Red","Blue","Green","Yellow","Purple"]
        target=random.choice(colors)
        choice=st.selectbox("Match this color",colors,index=0)
        st.write("Target:",target)
        if st.button("Check Color"):
            st.session_state.games+=1
            st.success("Correct!") if choice==target else st.error("Not a match.")
    elif game=="Roll the Dice":
        if st.button("Roll Dice"):
            st.session_state.games+=1
            st.success(f"🎲 You rolled {random.randint(1,6)}")
    elif game=="Math Quiz":
        a,b=random.randint(2,20),random.randint(2,20)
        ans=st.number_input(f"{a} × {b} = ?",0,1000,0)
        if st.button("Check Math"):
            st.session_state.games+=1
            if ans==a*b: st.success("Correct!")
            else: st.error(f"Answer: {a*b}")
    elif game=="Magic Ball 8":
        q=st.text_input("Ask a yes/no question")
        if st.button("Ask Magic Ball") and q.strip():
            st.session_state.games+=1
            st.info(random.choice(["Yes","No","Maybe","Think again","Very likely"]))
    elif game=="Word Scramble":
        words=["ARYABHATTA","SCIENCE","ASTRONOMY","PYTHON","MATHEMATICS"]
        word=st.session_state.setdefault("scramble_word",random.choice(words))
        scrambled="".join(random.sample(word,len(word)))
        st.write("Unscramble:",scrambled)
        ans=st.text_input("Your answer",key="scramble_answer")
        if st.button("Check Word"):
            st.session_state.games+=1
            if ans.strip().upper()==word: st.success("Correct!")
            else: st.info(f"Hint: starts with {word[0]}")
    elif game=="Animal Guessing":
        animals={"Lion":"roars","Elephant":"has a trunk","Penguin":"cannot fly","Dolphin":"lives in water"}
        animal=random.choice(list(animals))
        st.write("Clue:",animals[animal])
        if st.button("Reveal Animal"):
            st.session_state.games+=1
            st.success(animal)
    elif game=="Click Speed Test":
        st.write("Tap the button as many times as you can.")
        if "clicks" not in st.session_state: st.session_state.clicks=0
        if st.button("⚡ CLICK"):
            st.session_state.clicks+=1
            st.session_state.games+=1
        st.metric("Clicks recorded",st.session_state.clicks)
        if st.button("Reset Click Test"): st.session_state.clicks=0
    elif game == "Daily Quiz":
        question_challenge("Daily Quiz — दैनिक प्रश्न", "daily_quiz")
    elif game == "AI Challenge":
        st.info("AI Challenge: science, maths, astronomy, coding और reasoning का mixed challenge. यह curated question bank offline भी चलता है।")
        question_challenge("AI Challenge — Aryabhutt Brain Quest", "ai_challenge")
    else:
        riddle_challenge("Riddle Challenge — 50 पहेलियाँ", RIDDLE_QUESTIONS, "riddle_challenge")

# -------------------- TREASURE HUNT --------------------
def treasure_hunt():
    st.write("Maths, astronomy, science, technology और Sia's story पर आधारित 50-question mission. पहले अपनी challenge length चुनें।")
    question_challenge("Treasure Hunt — Mission Save Sia", "treasure", counter="games")

# -------------------- REPORTS / FEEDBACK / SETTINGS --------------------
def reports():
    section("Reports","📄")
    st.write("A transparent activity report for this web session.")
    report={"Version":VERSION,"Generated":datetime.now().isoformat(timespec="seconds"),
            "Sessions":st.session_state.sessions,"Games":st.session_state.games,
            "Riddles":st.session_state.riddles,"Chat Questions":st.session_state.chat,
            "Study Views":st.session_state.study_views,"Formula Views":st.session_state.formula_views,
            "Story Points Read":st.session_state.story_points,"Astronomy Views":st.session_state.astronomy_views,
            "Registered Schools":db_stats()["schools"],"Registered Students":db_stats()["students"]}
    st.json(report)
    st.download_button("📥 Download Report JSON",json.dumps(report,ensure_ascii=False,indent=2),file_name="aryabhutt_report.json")
    if st.button("Generate / Count Report"):
        st.session_state.reports+=1
        st.success("Report generated.")

def feedback():
    section("Feedback","💬")
    with st.form("feedback"):
        rating=st.radio("How was the experience?",["Excellent","Good","Okay","Needs Improvement"])
        comment=st.text_area("Comment")
        if st.form_submit_button("Save Feedback"):
            st.success("Feedback saved for this session. धन्यवाद!")

def settings():
    section("Settings & Extra Features","⚙️")
    st.write("🔊 **Voice / TTS:** Browser SpeechSynthesis can be used by the browser/device. Native Android/Pydroid TTS remains part of the original V5.6 source.")
    st.write("🔳 **QR / URL:** Project URL")
    st.code("https://project-aryabhutt-sapphrjy4buqinxkfcwq2hl.streamlit.app/")
    st.write("🎯 **Focus Mode**")
    st.session_state.focus_mode=st.toggle("Study-first mode",st.session_state.focus_mode)
    st.write("☁️ **Data / Update:** Web demo is an adaptation of the original V5.6 MASTER; it does not pretend to be a full cloud database.")
    st.write("🔐 **Teacher/Admin:** Use the sidebar option to open the secured dashboard.")
    st.markdown("### 🧪 Gemini connection test")
    st.caption("यह एक छोटा live request भेजकर API key, model और network की जाँच करता है।")
    if st.button("Test Gemini now / Gemini जाँचें"):
        with st.spinner("Gemini से संपर्क किया जा रहा है…"):
            test_answer, test_status = gemini_answer("केवल 'Gemini connection OK' लिखो।")
        if test_answer:
            st.success(f"Live Gemini response मिला: {test_status}")
            log_event("gemini_test_passed",page="Settings")
        else:
            st.error("Gemini live request सफल नहीं हुआ। API key दोबारा न बदलें जब तक error न देखें।")
            st.code(str(test_status)[:700])
            log_event("gemini_test_failed",page="Settings",details={"error":str(test_status)[:180]})

# -------------------- OFFLINE LIBRARY + QR SCANNER --------------------
def offline_library():
    section("Offline Knowledge Library • ऑफलाइन ज्ञान-संग्रह", "📚")
    st.info(f"इस संस्करण में {len(OFFLINE_KB)} curated विषय-समूहों के स्थानीय उत्तर हैं। ये इंटरनेट के बिना भी काम करते हैं; यह हर संभव प्रश्न का संपूर्ण विश्वकोश नहीं है।")
    subject = st.selectbox("विषय चुनें", ["सभी विषय", "Astronomy / खगोल-विज्ञान", "Mathematics / गणित", "Science / विज्ञान", "History / इतिहास", "Sanskrit / संस्कृत", "Technology / तकनीक", "Environment / पर्यावरण"])
    query = st.text_input("प्रश्न या keyword खोजें", placeholder="जैसे black hole, प्रकाश संश्लेषण, राम शब्द रूप, 12*8")
    if query.strip():
        answer=offline_answer(query)
        if answer: st.success(answer)
        else: st.warning("इस शब्द का उत्तर अभी offline bank में नहीं मिला। खोज के लिए दूसरा keyword आज़माएँ।")
    st.markdown("### उपलब्ध स्थानीय विषय")
    for label, keys in [
        ("खगोल-विज्ञान", "सौरमंडल, ग्रह, सूर्य, चंद्रमा, ब्लैक होल, आकाशगंगा, ग्रहण, गुरुत्वाकर्षण"),
        ("गणित", "शून्य, π, प्रतिशत, भिन्न, बीजगणित, क्षेत्रफल, HCF/LCM, चाल और दूरी; सरल arithmetic calculator"),
        ("विज्ञान", "प्रकाश संश्लेषण, परमाणु, बल, विद्युत, जल चक्र, पदार्थ की अवस्थाएँ, हृदय, DNA, जलवायु"),
        ("इतिहास / नागरिक शास्त्र", "आर्यभट्ट, सिंधु घाटी सभ्यता, अशोक, अकबर, 1857, स्वतंत्रता दिवस, संविधान, गांधी"),
        ("संस्कृत", "संस्कृत भाषा, अभिवादन, राम शब्द रूप, गम् धातु, वर्णमाला, सुभाषित"),
        ("तकनीक / पर्यावरण", "algorithm, Python, internet, cyber safety, pollution, ecosystem"),
    ]:
        with st.expander(label): st.write(keys)
    st.caption("नए प्रश्नों के लिए इस स्थानीय knowledge bank में curated Q&A जोड़कर इसे आगे बढ़ाया जा सकता है।")

def scanner_page():
    section("QR Scanner • स्कैनर", "🔎")
    st.write("QR कोड स्कैन करने के लिए कैमरा अनुमति दें। कैमरा ब्राउज़र में ही चलता है; अगर कैमरा उपलब्ध न हो तो QR की तस्वीर अपलोड करें।")
    components.html(r'''<div style="font-family:Arial,sans-serif;color:inherit">
      <video id="qr-video" autoplay playsinline style="width:100%;max-width:480px;border-radius:12px;background:#111"></video>
      <p id="qr-status">कैमरा शुरू करने के लिए बटन दबाएँ।</p>
      <button id="qr-start" style="padding:10px 14px;border-radius:8px">📷 कैमरा शुरू करें</button>
      <button id="qr-stop" style="padding:10px 14px;border-radius:8px">रोकें</button>
      <div id="qr-result" style="overflow-wrap:anywhere;margin-top:10px;font-weight:bold"></div>
      <script>
      (()=>{const v=document.getElementById('qr-video'),s=document.getElementById('qr-status'),r=document.getElementById('qr-result');let stream=null,active=false,detector=null;
      document.getElementById('qr-start').onclick=async()=>{try{if(!('BarcodeDetector'in window)){s.textContent='इस ब्राउज़र में live QR detection उपलब्ध नहीं है। QR तस्वीर अपलोड करने वाला विकल्प नीचे है।';return;} detector=new BarcodeDetector({formats:['qr_code']});stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}});v.srcObject=stream;active=true;s.textContent='QR को कैमरे के सामने रखें…';scan();}catch(e){s.textContent='कैमरा नहीं खुला: '+e.message+'। अनुमति जाँचें या QR तस्वीर अपलोड करें।';}};
      async function scan(){if(!active||!detector)return;try{const codes=await detector.detect(v);if(codes.length){r.textContent='स्कैन परिणाम: '+codes[0].rawValue;s.textContent='QR सफलतापूर्वक पढ़ लिया गया।';active=false;return;}}catch(e){}requestAnimationFrame(scan);}
      document.getElementById('qr-stop').onclick=()=>{active=false;if(stream)stream.getTracks().forEach(t=>t.stop());v.srcObject=null;s.textContent='कैमरा रोक दिया गया।';};})();
      </script></div>''', height=430)
    st.markdown("**QR तस्वीर अपलोड करें**")
    image_file=st.file_uploader("QR कोड की तस्वीर चुनें", type=["png","jpg","jpeg","webp"], key="qr_upload")
    if image_file:
        st.image(image_file, caption="अपलोड की गई तस्वीर", width=260)
        try:
            import cv2, numpy as np
            image_file.seek(0)
            arr=np.frombuffer(image_file.read(),np.uint8)
            image=cv2.imdecode(arr,cv2.IMREAD_COLOR)
            value, points, _ = cv2.QRCodeDetector().detectAndDecode(image)
            if value: st.success("स्कैन परिणाम"); st.code(value)
            else: st.warning("QR नहीं पढ़ पाया। साफ़, सीधी और अच्छी रोशनी वाली तस्वीर आज़माएँ।")
        except Exception:
            st.info("तस्वीर दिख रही है, लेकिन इस सर्वर पर image decoder उपलब्ध नहीं है। Chrome में ऊपर live camera scanner आज़माएँ।")

# -------------------- STUDENT CHECK-IN --------------------
if not st.session_state.get("student_id"):
    st.title("🪷 PROJECT ARYABHUTT")
    st.subheader("शुरू करने से पहले अपना नाम लिखें / Student check-in")
    st.write("ताकि Teacher/Admin को पढ़ाई के sessions और activity का रिकॉर्ड दिख सके। केवल पहला नाम माँगा जाता है।")
    schools=db_rows("SELECT id,name FROM schools ORDER BY name")
    school_map={r["name"]:r["id"] for r in schools}
    with st.form("student_checkin_form"):
        first_name=st.text_input("बच्चे का पहला नाम / First name",max_chars=60)
        school_label=st.selectbox("स्कूल / School",["Not specified / नहीं बताया"]+list(school_map.keys()))
        class_section=st.text_input("कक्षा / Section (optional)",max_chars=40)
        begin=st.form_submit_button("📚 पढ़ाई शुरू करें / Start learning")
    if begin:
        clean_name=" ".join(first_name.split())
        if not clean_name: st.error("कृपया पहला नाम लिखें।")
        else:
            school_id=school_map.get(school_label)
            student_id=db_get_or_add_student(clean_name,school_id,class_section.strip())
            session_id=uuid.uuid4().hex
            started=now_text()
            with db_connect() as con:
                con.execute("INSERT INTO app_sessions(id,student_id,started_at,last_seen_at,estimated_minutes) VALUES(?,?,?,?,0)",(session_id,student_id,started,started))
            st.session_state.student_id=student_id
            st.session_state.student_name=clean_name
            st.session_state.student_school=school_label
            st.session_state.current_session_id=session_id
            log_event("app_open",page="Check-in",details={"school":school_label,"class_section":class_section.strip()})
            st.rerun()
    st.caption("Privacy: this demo records the first name, optional school/class, session time and learning activity. Use school approval and a hosted database before relying on records for official attendance.")
    st.stop()

with st.sidebar:
    st.caption(f"👋 विद्यार्थी: {st.session_state.get('student_name','')}")
    if st.button("Switch student / विद्यार्थी बदलें"):
        sid=st.session_state.get("current_session_id")
        if sid:
            ended=now_text()
            with db_connect() as con:
                con.execute("UPDATE app_sessions SET ended_at=?,last_seen_at=? WHERE id=?",(ended,ended,sid))
        st.session_state.pop("student_id",None); st.session_state.pop("student_name",None); st.session_state.pop("current_session_id",None); st.rerun()

# -------------------- SIDEBAR / ROUTING --------------------
with st.sidebar:
    st.markdown("### 🪷 PROJECT ARYABHUTT")
    st.caption("V5.6 WEB • Learn • Visualize • Practice • Explore • Track")
    page=st.radio("Menu",[
        "Home","AI Chatbot","AI Challenge","Offline Knowledge Library","QR Scanner","Treasure Hunt","Game Zone","Study Center",
        "Space & Visualizers","Data & Analytics","Reports","Feedback","Settings",
        "Teacher / Admin"
    ])
    st.divider()
    lang=st.selectbox("🌐 Language",["हिन्दी","English"])
    st.session_state["lang"] = lang
    st.caption("Original V5.6 Pydroid source is preserved as MASTER/core.")
    st.caption("Web adaptation restores the larger Study Center and admin/data screens.")

if st.session_state.get("current_page") != page:
    st.session_state["current_page"] = page
    log_event("page_visit",page=page)
else:
    # Update session heartbeat without creating a new activity row on every rerun.
    sid=st.session_state.get("current_session_id")
    if sid:
        touched=now_text()
        with db_connect() as con:
            row=con.execute("SELECT started_at FROM app_sessions WHERE id=?",(sid,)).fetchone()
            if row:
                try: minutes=max(0,int((datetime.fromisoformat(touched)-datetime.fromisoformat(row[0])).total_seconds()//60))
                except Exception: minutes=0
                con.execute("UPDATE app_sessions SET last_seen_at=?,estimated_minutes=? WHERE id=?",(touched,minutes,sid))

if page=="Home": home()
elif page=="AI Chatbot": chatbot()
elif page=="AI Challenge": question_challenge("AI Challenge — Aryabhutt Brain Quest", "sidebar_ai_challenge")
elif page=="Offline Knowledge Library": offline_library()
elif page=="QR Scanner": scanner_page()
elif page=="Game Zone": games()
elif page=="Study Center": study_center()
elif page=="Space & Visualizers": space_visualizers()
elif page=="Data & Analytics": analytics()
elif page=="Reports": reports()
elif page=="Feedback": feedback()
elif page=="Settings": settings()
elif page=="Teacher / Admin": admin()
elif page=="Treasure Hunt": treasure_hunt()
