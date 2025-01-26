import os
import streamlit as st
import speech_recognition as sr
from dotenv import load_dotenv
import pyperclip

# Fix Groq import
try:
    from groq import Groq
except ImportError:
    from groq.client import Groq

# Load environment variables
load_dotenv()

# Custom CSS for Premium Look
def set_custom_style():
    st.markdown("""
    <style>
    /* Global Styling */
    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        background-color: #f4f6f9;
        color: #2c3e50;
    }

    /* Header Styling */
    .stApp > header {
        background-color: transparent;
    }

    /* Container Styling */
    .stContainer {
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin-bottom: 20px;
    }

    /* Button Styling */
    .stButton > button {
        background-color: #3498db;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background-color: #2980b9;
        transform: scale(1.05);
    }

    /* Input Styling */
    .stTextArea > div > textarea {
        border-radius: 10px;
        border: 1.5px solid #e0e4e8;
        background-color: #f8f9fa;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Sidebar Styling */
    .css-1aumxhk {
        background-color: #2c3e50;
        color: white;
    }

    .css-1aumxhk .stRadio > label {
        color: white !important;
    }

    /* Team Member Cards */
    .team-card {
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 15px;
        text-align: center;
        transition: transform 0.3s ease;
    }

    .team-card:hover {
        transform: translateY(-10px);
    }

    /* Expander Styling */
    .stExpander {
        border-radius: 10px;
        border: 1.5px solid #e0e4e8;
    }
    </style>
    """, unsafe_allow_html=True)

# Predefined Common Network Errors
COMMON_ERRORS = {
    "DNS_PROBE_FINISHED_NO_INTERNET": "DNS resolution failed. Unable to connect to internet.",
    "Connection Timed Out": "Network connection could not be established within expected timeframe.",
    "No Route to Host": "Network path to destination is unavailable.",
    "Connection Refused": "Remote server rejected connection attempt.",
    "SSL Handshake Failed": "Secure connection could not be established.",
}

# Language to BCP-47 Code Mapping for Speech Recognition
LANGUAGE_CODES = {
    'English': 'en-US', 'Urdu': 'ur-PK', 'Spanish': 'es-ES',
    'French': 'fr-FR', 'Arabic': 'ar-SA', 'Afrikaans': 'af-ZA',
    'Zulu': 'zu-ZA', 'Xhosa': 'xh-ZA', 'Sotho': 'st-ZA',
    'Tswana': 'tn-ZA'
}

# Initialize Groq client
def initialize_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY not found in .env file")
        return None
    return Groq(api_key=api_key)

# Error classification system
def classify_error(text):
    error_types = {
        "DNS": ["dns", "domain", "server"],
        "SSL": ["ssl", "certificate", "handshake"],
        "Connection": ["connection", "timeout", "refused", "route"]
    }
    text_lower = text.lower()
    for etype, keywords in error_types.items():
        if any(kw in text_lower for kw in keywords):
            return etype
    return "Network"

# Severity detection
def get_severity(text):
    text_lower = text.lower()
    if "critical" in text_lower: return "Critical"
    if "warning" in text_lower: return "Warning"
    if "severe" in text_lower: return "Critical"
    return "Info"

# Generate explanation using Groq API
def generate_explanation(client, log_text, language='en'):
    try:
        system_prompts = {
            'en': "You are a network troubleshooting assistant in English.",
            'es': "Eres un asistente de solución de problemas de red en español.",
            'fr': "Vous êtes un assistant de dépannage réseau en français.",
            'ur': "آپ اردو میں نیٹ ورک ٹروبل شوٹنگ اسسٹنٹ ہیں۔",
            'ar': "أنت مساعد استكشاف أخطاء الشبكة باللغة العربية.",
            'af': "Jy is 'n netwerk-probleemoplossingsassistent in Afrikaans.",
            'zu': "Ungusizo lokuxazulula amaproblem emseth-network ngesiZulu.",
            'xh': "Ungomnxeba wokusungula amaproblem emanyango ekuqhubekeni ngesiXhosa.",
            'st': "O moagi wa bothata ba network ka Sesotho.",
            'tn': "O thutapulamolemo ya network ka Setswana."
        }
        
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": f"{system_prompts.get(language, 'en')} Provide detailed analysis and step-by-step solutions."},
                {"role": "user", "content": f"Analyze this network error: {log_text}"}
            ],
            temperature=0.3,
            max_tokens=1200
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# Speech-to-text conversion
def speech_to_text(language_code):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... (5 second timeout)")
        try:
            audio = r.listen(source, timeout=5)
            return r.recognize_google(audio, language=language_code)
        except sr.WaitTimeoutError:
            st.warning("Listening timed out")
            return ""
        except Exception as e:
            st.error(f"Recognition error: {str(e)}")
            return ""

# Landing Page
def landing_page():
    set_custom_style()
    st.title("🌐 Network Log Translator")
    st.markdown("""
    ### Simplify Complex Network Errors with AI-Powered Troubleshooting

    **Cutting-edge solutions for network diagnostics:**
    - 🛠️ Instant Error Analysis
    - 🌍 Multilingual Support
    - 🎤 Voice & Text Inputs
    - 📋 Quick Diagnostic Commands
    """)
    
    cols = st.columns([1, 1, 1])
    with cols[1]:
        st.image("https://ideogram.ai/assets/image/lossless/response/fjemlPTxRSagPZPIt9w44Q", 
                 use_column_width=True, 
                 caption="AI-Powered Network Diagnostics")

# About Us Page
def about_us_page():
    set_custom_style()
    st.title("👥 Network Solutions Team")
    
    team_members = [
        {"name": "Humam", "role": "Backend Developer", "image": "https://via.placeholder.com/150.png?text=Humam"},
        {"name": "Muhammad Ibrahim Qasmi", "role": "Data Scientist", "image": "https://media.licdn.com/dms/image/v2/D4D03AQFCNX1cJg9J8w/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1732156800150?e=1743638400&v=beta&t=5nk_TRhQGlSX-I0tp0cf9ZHwJzFOLrLWWkxTdTrn6EU"},
        {"name": "Ahmad Fakhar", "role": "AI Engineer", "image": "https://media.licdn.com/dms/image/v2/D4D03AQFrxTgmUio4Mw/profile-displayphoto-shrink_100_100/profile-displayphoto-shrink_100_100/0/1732197610882?e=1743638400&v=beta&t=we1bOWBoC3ZrXcus979HRY1yT9tRUsKa3dc7-JWZSXI"},
        {"name": "Muhammad Zia", "role": "UI/UX Designer", "image": "https://via.placeholder.com/150.png?text=Zia"},
        {"name": "Tayyab Sajjad", "role": "Data Scientist", "image": "https://media.licdn.com/dms/image/v2/D4E03AQELdwDpn2a9Bg/profile-displayphoto-shrink_100_100/profile-displayphoto-shrink_100_100/0/1732042661073?e=1743638400&v=beta&t=6vX_f7IeZETm70ZZ8x-h6_vH6uDJ9f-2S6SGPVcHIOU"},
        {"name": "Frank", "role": "Project Manager", "image": "https://via.placeholder.com/150.png?text=Frank"}
    ]

    st.markdown("### Our Dedicated Team of Network Experts")
    
    rows = [team_members[i:i+3] for i in range(0, len(team_members), 3)]
    for row in rows:
        cols = st.columns(3)
        for col, member in zip(cols, row):
            with col:
                with st.container():
                    st.image(member['image'], width=150, use_column_width=False)
                    st.markdown(f"**{member['name']}**")
                    st.caption(member['role'])

# Translator Page
def translator_page():
    set_custom_style()
    st.title("🌐 Smart Network Troubleshooter")
    
    # Initialize session state
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    # Initialize Groq client
    groq_client = initialize_groq_client()
    if not groq_client:
        return

    # Common Errors Grid
    st.subheader("Common Network Issues")
    cols = st.columns(3)
    for idx, (error, desc) in enumerate(COMMON_ERRORS.items()):
        with cols[idx % 3]:
            if st.button(error, help=desc, key=f"err_{idx}"):
                st.session_state.input_text = desc

    # Language Selection
    lang_col1, lang_col2 = st.columns([2, 1])
    with lang_col1:
        selected_lang = st.selectbox("Output Language", list(LANGUAGE_CODES.keys()))
    with lang_col2:
        input_method = st.radio("Input Method", ["Text", "Voice"])

    # Input Section
    input_text = ""
    if input_method == "Text":
        input_text = st.text_area("Network Error Details", 
                                value=st.session_state.get('input_text', ''),
                                height=100)
    else:
        voice_lang = st.selectbox("Voice Input Language", list(LANGUAGE_CODES.keys()))
        if st.button("🎤 Start Recording"):
            input_text = speech_to_text(LANGUAGE_CODES[voice_lang])
            if input_text:
                st.session_state.input_text = input_text

    # Main Processing
    if st.button("Analyze Error", type="primary"):
        if not input_text.strip():
            st.warning("Please enter error details")
            return

        with st.status("🔍 Analyzing Error...", expanded=True) as status:
            # Generate Explanation
            lang_code = next(
                (v[:2] for k, v in LANGUAGE_CODES.items() if k.lower().startswith(selected_lang[:2].lower())),
                'en'  # Default to English
            )
            explanation = generate_explanation(groq_client, input_text, lang_code)
            
            if not explanation:
                st.error("Failed to generate explanation")
                return

            # Error Classification
            error_category = classify_error(explanation)
            severity_level = get_severity(explanation)
            
            # Update History
            st.session_state.history.append({
                'error': input_text,
                'explanation': explanation,
                'category': error_category,
                'severity': severity_level
            })
            
            status.update(label="Analysis Complete", state="complete")

        # Display Results
        st.subheader(f"{severity_level} Issue", divider="rainbow")
        st.markdown(f"**Category:** :label: `{error_category}`")
        
        with st.expander("Detailed Analysis", expanded=True):
            st.markdown(explanation)

        # Quick Fixes
        QUICK_FIXES = {
            "DNS": "ipconfig /flushdns",
            "SSL": "sudo update-ca-certificates",
            "Connection": "ping 8.8.8.8",
            "Network": "netsh winsock reset"
        }
        
        if error_category in QUICK_FIXES:
            fix = QUICK_FIXES[error_category]
            st.code(fix, language="bash")
            if st.button("📋 Copy Command", key="copy_cmd"):
                pyperclip.copy(fix)
                st.toast("Command copied to clipboard!")

        # History Section
        st.subheader("Recent Analyses", divider="gray")
        for entry in reversed(st.session_state.history[-3:]):
            with st.expander(f"{entry['severity']} - {entry['error'][:30]}..."):
                st.caption(f"**Category:** {entry['category']}")
                st.write(entry['explanation'])
                
    # Feedback System
    st.divider()
    feedback = st.radio("Was this helpful?", [":thumbsup:", ":thumbsdown:"], 
                       index=None, horizontal=True)
    if feedback:
        st.success("Thank you for your feedback!")

def main():
    st.set_page_config(
        page_title="Network Log Translator",
        page_icon="🌐",
        layout="wide"
    )

    # Sidebar Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["🏠 Landing Page", "🌐 Translator", "👥 About Us"])

    # Page Routing
    if page == "🏠 Landing Page":
        landing_page()
    elif page == "🌐 Translator":
        translator_page()
    elif page == "👥 About Us":
        about_us_page()

# Run the app
if __name__ == "__main__":
    main()
