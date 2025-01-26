import os
import streamlit as st
import pyperclip
from groq import Groq
from gtts import gTTS
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client
def initialize_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY not found in .env file")
        return None
    return Groq(api_key=api_key)

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

# Text-to-speech conversion
def text_to_speech(text, language='en'):
    """Convert text to speech using gTTS."""
    try:
        tts = gTTS(text=text, lang=language, slow=False)
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        tts.save(temp_audio.name)
        return temp_audio.name
    except Exception as e:
        st.error(f"Error generating speech: {str(e)}")
        return None

# Translator Page
def translator_page():
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
        if st.button("🎤 Start Recording (Simulated)"):
            st.info("Simulating voice input... Please type your input below.")
            input_text = st.text_input("Type your voice input here:")

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

        # Text-to-Speech for Explanation
        if st.button("🔊 Listen to Explanation"):
            audio_file = text_to_speech(explanation, lang_code)
            if audio_file:
                st.audio(audio_file)
                os.unlink(audio_file)  # Clean up temporary file

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

# Main function
def main():
    st.set_page_config(
        page_title="Network Log Translator",
        page_icon="🌐",
        layout="wide"
    )

    # Sidebar Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["🌐 Translator"])

    # Page Routing
    if page == "🌐 Translator":
        translator_page()

# Run the app
if __name__ == "__main__":
    main()
