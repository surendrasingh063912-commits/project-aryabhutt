
import os, json, math, random, html
from datetime import datetime, date

import streamlit as st
import streamlit.components.v1 as components

# Optional Gemini
try:
    from google import genai
except Exception:
    genai = None

APP_NAME = "PROJECT ARYABHUTT"
VERSION = "V5.6 WEB • RESTORED STUDY EDITION"
GEMINI_MODEL = "gemini-3.8-flash"

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
        key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        pass
    if not key:
        return None, "GEMINI_API_KEY नहीं मिला"
    try:
        return genai.Client(api_key=key), "ready"
    except Exception as e:
        return None, str(e)[:120]

def gemini_answer(prompt):
    """Hindi-first Aryabhatt persona with short conversational memory."""
    client, status = gemini_client()
    if client is None:
        return None, status

    history = st.session_state.get("chat_history", [])[-8:]
    context_lines = []
    for role, msg in history:
        label = "विद्यार्थी" if role == "user" else "आर्यभट्ट"
        context_lines.append(f"{label}: {msg}")
    conversation = "\n".join(context_lines)

    system_prompt = (
        "आप PROJECT ARYABHUTT के 'आचार्य आर्यभट्ट' ज्ञान-सहायक हैं।\\n"
        "आपका संवाद एक शांत, विद्वान, जिज्ञासु और सम्मानपूर्ण आचार्य जैसा होना चाहिए—सरल, स्वाभाविक और आत्मीय; "
        "बच्चों जैसी भाषा, baby-talk, 'young learner', 'kid', 'बच्चा' या बनावटी संबोधन बिल्कुल न करें।\\n"
        "मुख्य उत्तर हमेशा स्वाभाविक, स्पष्ट और सहज हिंदी (देवनागरी) में दें। "
        "प्रश्न English में हो तब भी उत्तर हिंदी में दें, जब तक उपयोगकर्ता स्पष्ट रूप से English answer न मांगे।\\n"
        "जरूरी scientific/proper terms English में रख सकते हैं और उनका अर्थ हिंदी में समझाएँ।\\n"
        "उत्तर तथ्यात्मक, उपयोगी और पर्याप्त हों। तथ्य न गढ़ें। जहाँ जानकारी निश्चित न हो, साफ बताएं।\\n"
        "आर्यभट्ट की वैज्ञानिक परंपरा से प्रेरित होकर गणित, तर्क, observation, प्रमाण और जिज्ञासा को प्रोत्साहित करें; "
        "लेकिन स्वयं को वास्तविक ऐतिहासिक आर्यभट्ट न बताएं।\\n"
        "हर उत्तर को जबरन एक ही वाक्य से समाप्त न करें। संदर्भ के अनुसार कभी-कभी "
        "'आयुष्मान भव।' या 'ज्ञान की ज्योति जलाए रखो।' जैसे सम्मानपूर्ण समापन कह सकते हैं। "
        "जहाँ स्वाभाविक हो, अंत में एक छोटा विचारोत्तेजक follow-up प्रश्न पूछें ताकि संवाद जारी रहे।\\n\\n"
        "पिछली बातचीत का संदर्भ:\\n" + (conversation or "कोई पिछली बातचीत नहीं") + "\\n\\n"
        "नया प्रश्न: " + str(prompt)
    )
    try:
        r = client.models.generate_content(model=GEMINI_MODEL, contents=system_prompt)
        text = getattr(r, "text", None)
        if text and str(text).strip():
            return str(text).strip(), "🟢 Gemini Online"
        return None, "Gemini ने उत्तर नहीं दिया"
    except Exception as e:
        return None, str(e).replace("\n", " ")[:180]

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
        ans, status = gemini_answer(q)
        if ans is None:
            # Small offline knowledge fallback
            low=q.lower()
            if "abdul kalam" in low or "कलाम" in q:
                ans="डॉ. ए.पी.जे. अब्दुल कलाम भारत के प्रसिद्ध वैज्ञानिक और भारत के पूर्व राष्ट्रपति थे। उन्हें 'मिसाइल मैन ऑफ इंडिया' कहा जाता है।"
            elif "aryabhat" in low or "आर्यभट्ट" in q:
                ans="आर्यभट्ट प्राचीन भारत के महान गणितज्ञ और खगोलविद थे। उनके कार्यों ने गणित और खगोल विज्ञान की परंपरा को महत्वपूर्ण रूप से प्रभावित किया।"
            elif "planet" in low or "ग्रह" in q:
                ans="हमारे सौरमंडल में आठ ग्रह हैं: बुध, शुक्र, पृथ्वी, मंगल, बृहस्पति, शनि, यूरेनस और नेपच्यून।"
            else:
                ans=("इस समय Gemini से उत्तर प्राप्त नहीं हो सका। कृपया थोड़ी देर बाद यही प्रश्न फिर पूछें। "
                     "यदि समस्या बनी रहे, तो Streamlit Secrets में GEMINI_API_KEY की जाँच करें।")
            status="🟡 Offline / Gemini unavailable"
        st.session_state.chat_history.append(("assistant",ans))
        st.rerun()
    client, s = gemini_client()
    st.caption(("🟢 Gemini Online तैयार" if client else "🟡 Offline Knowledge Book उपलब्ध") + " • " + ("हिंदी-first • Browser Voice" if client else s))

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
    c1.metric("Registered Schools",len(st.session_state.schools))
    c2.metric("Registered Students",len(st.session_state.students))
    if st.session_state.schools:
        st.dataframe([{"School":k,"Students":v} for k,v in st.session_state.schools.items()],use_container_width=True)
    else:
        st.info("अभी demo session में कोई school registered नहीं है। Teacher/Admin से school जोड़ सकते हैं।")
    st.caption("⚠️ Web demo में ये records current app session के हैं; यह fake nationwide statistic नहीं है और अभी permanent multi-school cloud database नहीं है.")

# -------------------- TEACHER / ADMIN --------------------
def admin():
    section("Teacher / Admin Dashboard","🔐")
    if not st.session_state.admin_ok:
        st.info("Teacher/Admin area सुरक्षित है। Demo password को production में Streamlit Secret ADMIN_PASSWORD से बदल सकते हैं।")
        with st.form("admin_login"):
            pw=st.text_input("Admin password",type="password")
            ok=st.form_submit_button("🔓 Login")
        if ok:
            if pw==admin_password():
                st.session_state.admin_ok=True
                st.success("Teacher/Admin access enabled.")
                st.rerun()
            else:
                st.error("Password सही नहीं है.")
        return
    c1,c2,c3=st.columns(3)
    c1.metric("🏫 Schools",len(st.session_state.schools))
    c2.metric("🧑‍🎓 Students",len(st.session_state.students))
    c3.metric("💬 Chats",st.session_state.chat)
    t1,t2,t3=st.tabs(["🏫 Manage Schools","🧑‍🎓 Student Database","📊 Activity"])
    with t1:
        with st.form("school_form"):
            school=st.text_input("School name")
            num=st.number_input("Number of students",0,100000,0)
            save=st.form_submit_button("➕ Add / Update School")
        if save and school.strip():
            st.session_state.schools[school.strip()]=int(num)
            st.success("School saved.")
        if st.session_state.schools:
            for s,n in st.session_state.schools.items():
                st.write(f"🏫 **{s}** — {n} students")
    with t2:
        with st.form("student_form"):
            name=st.text_input("Student name")
            school=st.text_input("Student's school")
            save=st.form_submit_button("🧑‍🎓 Save Student")
        if save and name.strip():
            st.session_state.students.append({"name":name.strip(),"school":school.strip()})
            st.success("Student saved.")
        if st.session_state.students:
            st.dataframe(st.session_state.students,use_container_width=True)
    with t3:
        st.write("Real activity recorded in this web session:")
        st.json({k:v for k,v in {
            "sessions":st.session_state.sessions,"games":st.session_state.games,
            "riddles":st.session_state.riddles,"chat":st.session_state.chat,
            "study_views":st.session_state.study_views,"formula_views":st.session_state.formula_views,
            "story_points":st.session_state.story_points,"astronomy_views":st.session_state.astronomy_views
        }.items()})
    if st.button("🔒 Logout Admin"):
        st.session_state.admin_ok=False
        st.rerun()

# -------------------- GAMES --------------------
def games():
    section("Game Zone — 10 Games + Daily Quiz","🎮")
    game=st.selectbox("Choose a game",[
        "Guess the Number","Flip a Coin","Rock-Paper-Scissors","Color Matcher",
        "Roll the Dice","Math Quiz","Magic Ball 8","Word Scramble",
        "Animal Guessing","Click Speed Test","Daily Quiz"
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
    else:
        qs=[("How many planets are in our solar system?","8"),
            ("Largest planet?","Jupiter"),
            ("Aryabhata was a?","mathematician"),
            ("Earth's natural satellite?","moon"),
            ("What does AI learn from?","data")]
        score=0
        for i,(q,a) in enumerate(qs):
            x=st.text_input(q,key=f"daily_{i}")
            if x.strip().lower()==a.lower(): score+=1
        if st.button("Check Daily Quiz"):
            st.session_state.games+=1
            st.success(f"Score: {score}/{len(qs)}")

# -------------------- TREASURE HUNT --------------------
def treasure_hunt():
    section("Treasure Hunt — Mission Save Sia","🧩")
    st.write("20-question web mission based on the V5.6 learning themes: maths, astronomy, science, technology and Sia's story.")
    questions=[
        ("Who is the project named after?","Aryabhata"),
        ("How many planets are in our solar system?","8"),
        ("What is Earth's natural satellite?","Moon"),
        ("Which planet is the largest?","Jupiter"),
        ("Which planet is famous for rings?","Saturn"),
        ("What is the name of our galaxy?","Milky Way"),
        ("What does a computer process?","data"),
        ("What does AI work with to learn patterns?","data"),
        ("What is the formula for rectangle area?","l*b"),
        ("What is the formula for circle area?","pi*r2"),
        ("What is 7 × 8?","56"),
        ("What is 25% of 100?","25"),
        ("Which planet is called the Red Planet?","Mars"),
        ("Which planet is closest to the Sun?","Mercury"),
        ("What happens in Earth rotation?","day"),
        ("What is a code?","instructions"),
        ("What does a network connect?","devices"),
        ("What is a gnomon useful for studying?","shadow"),
        ("What is a timetable useful for?","study"),
        ("What did Sia turn imagination into?","R-AI"),
    ]
    with st.form("treasure_form"):
        answers=[]
        for i,(q,a) in enumerate(questions,1):
            answers.append(st.text_input(f"{i}. {q}",key=f"hunt_{i}"))
        submitted=st.form_submit_button("🚀 Finish Mission")
    if submitted:
        score=0
        for ans,(_,expected) in zip(answers,questions):
            a=ans.strip().lower()
            e=expected.lower()
            if e in a or (e=="data" and "data" in a) or (e=="day" and ("day" in a or "night" in a)):
                score+=1
        st.session_state.riddles+=score
        st.success(f"Mission complete: {score}/{len(questions)}")
        if score>=15: st.balloons()
        st.info("Learning tip: score se zyada important hai ki galat answers ko dobara samjha जाए।")

# -------------------- REPORTS / FEEDBACK / SETTINGS --------------------
def reports():
    section("Reports","📄")
    st.write("A transparent activity report for this web session.")
    report={"Version":VERSION,"Generated":datetime.now().isoformat(timespec="seconds"),
            "Sessions":st.session_state.sessions,"Games":st.session_state.games,
            "Riddles":st.session_state.riddles,"Chat Questions":st.session_state.chat,
            "Study Views":st.session_state.study_views,"Formula Views":st.session_state.formula_views,
            "Story Points Read":st.session_state.story_points,"Astronomy Views":st.session_state.astronomy_views,
            "Registered Schools":len(st.session_state.schools),"Registered Students":len(st.session_state.students)}
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

# -------------------- SIDEBAR / ROUTING --------------------
with st.sidebar:
    st.markdown("### 🪷 PROJECT ARYABHUTT")
    st.caption("V5.6 WEB • Learn • Visualize • Practice • Explore • Track")
    page=st.radio("Menu",[
        "Home","AI Chatbot","Treasure Hunt","Game Zone","Study Center",
        "Space & Visualizers","Data & Analytics","Reports","Feedback","Settings",
        "Teacher / Admin"
    ])
    st.divider()
    lang=st.selectbox("🌐 Language",["हिन्दी","English"])
    st.caption("Original V5.6 Pydroid source is preserved as MASTER/core.")
    st.caption("Web adaptation restores the larger Study Center and admin/data screens.")

if page=="Home": home()
elif page=="AI Chatbot": chatbot()
elif page=="Game Zone": games()
elif page=="Study Center": study_center()
elif page=="Space & Visualizers": space_visualizers()
elif page=="Data & Analytics": analytics()
elif page=="Reports": reports()
elif page=="Feedback": feedback()
elif page=="Settings": settings()
elif page=="Teacher / Admin": admin()
elif page=="Treasure Hunt": treasure_hunt()
