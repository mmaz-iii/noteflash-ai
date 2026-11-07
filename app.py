import streamlit as st
from google import genai
import tempfile
import os
import pandas as pd
import genanki
import random

st.set_page_config(
    page_title="NoteFlash AI — Pro Suite",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom SaaS Glassmorphism Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    :root {
        --bg-1: #090d16; --bg-2: #1e1b4b;
        --glass: rgba(255, 255, 255, 0.04);
        --border: rgba(255, 255, 255, 0.09);
        --text: #e6e8f2; --muted: #8b90a8;
        --indigo: #6366f1; --indigo-light: #a5b4fc;
        --success: #34d399; --radius: 16px;
    }
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; color: var(--text); }
    .stApp { background: linear-gradient(135deg, var(--bg-1) 0%, #0f1229 45%, var(--bg-2) 100%); background-attachment: fixed; }
    header, footer { visibility: hidden; }

    div[data-testid="stForm"], div.stTextArea, div.stTextInput, div.stFileUploader, div[data-testid="stDataFrame"] {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(18px) !important;
    }

    .stButton>button {
        width: 100%; background: linear-gradient(180deg, #7174f5 0%, #5458e8 100%);
        border: 1px solid rgba(165,180,252,0.5); color: #fff; font-weight: 600;
        padding: 10px 16px; border-radius: 12px;
        box-shadow: 0 0 24px rgba(99,102,241,0.45);
        transition: all 0.2s ease;
    }
    .stButton>button:hover { background: linear-gradient(180deg, #7f82f7 0%, #6064ee 100%); transform: translateY(-1px); }
</style>
""", unsafe_allow_html=True)

# Initialize Session States
if 'cards_df' not in st.session_state:
    st.session_state['cards_df'] = pd.DataFrame(columns=["Front", "Back", "Tag", "Level"])
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'onboarded' not in st.session_state:
    st.session_state['onboarded'] = False
if 'user_profile' not in st.session_state:
    st.session_state['user_profile'] = {"curriculum": "General", "goal": "Standard"}

# --- AUTHENTICATION GATE ---
if not st.session_state['logged_in']:
    st.markdown("## ⚡ Welcome to NoteFlash AI")
    st.caption("Sign in to access your high-end flashcard workspace.")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        with st.form("auth_form"):
            st.markdown("### Secure Sign In / Sign Up")
            email_input = st.text_input("Email Address")
            pass_input = st.text_input("Password", type="password")
            submit_auth = st.form_submit_button("Continue with Email")
            
            if submit_auth and email_input:
                st.session_state['logged_in'] = True
                st.session_state['user_email'] = email_input
                st.rerun()
                
        if st.button("🌐 Continue with Google / School Account"):
            st.session_state['logged_in'] = True
            st.session_state['user_email'] = "user@school.edu"
            st.rerun()
    st.stop()

# --- ACADEMIC ONBOARDING WIZARD ---
if not st.session_state['onboarded']:
    st.markdown("## 🎓 Academic Onboarding Wizard")
    st.caption("Step 1 of 2: Tailor NoteFlash AI to your precise educational track.")
    
    with st.form("onboard_wizard"):
        curriculum = st.selectbox(
            "Select your educational level or curriculum:",
            ["CBSE Board (Grade 9-12)", "High School / AP", "Undergraduate University", "Medical (USMLE / MCAT)", "Law (LSAT / Bar)", "General Self-Study"]
        )
        study_goal = st.selectbox(
            "Primary learning objective:",
            ["High-Yield Exam Prep & Formulas", "Exhaustive Conceptual Mastery", "Quick Vocabulary & Definitions"]
        )
        complete_wizard = st.form_submit_button("Save Profile & Launch Workspace ✨", type="primary")
        
        if complete_wizard:
            st.session_state['user_profile'] = {"curriculum": curriculum, "goal": study_goal}
            st.session_state['onboarded'] = True
            st.rerun()
    st.stop()

# --- MAIN APP WORKSPACE (Post-Auth & Onboarding) ---
with st.sidebar:
    st.markdown(f"### ⚡ **NoteFlash AI**")
    st.caption(f"Signed in as: {st.session_state.get('user_email', 'User')}")
    st.info(f"📚 Track: {st.session_state['user_profile']['curriculum']}")
    
    if st.button("Log Out"):
        st.session_state['logged_in'] = False
        st.session_state['onboarded'] = False
        st.rerun()

    st.markdown("---")
    api_key_input = st.text_input("Gemini API Key", type="password", help="Get free key from Google AI Studio")

st.markdown("## Flashcard Generator Workspace")
st.markdown(f"*(Profile configured for **{st.session_state['user_profile']['curriculum']}** — Focus: **{st.session_state['user_profile']['goal']}**)*")

# Dynamic Prompt Tuning utilizing user profile data
current_curriculum = st.session_state['user_profile']['curriculum']
current_goal = st.session_state['user_profile']['goal']

raw_text = st.text_area("Paste notes or study content:", height=120)
if st.button("Generate Flashcards", type="primary"):
    key_to_use = api_key_input or (st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None)
    if not key_to_use:
        st.error("Please provide your Gemini API key.")
    else:
        try:
            client = genai.Client(api_key=key_to_use)
            system_instruction = f"You are an expert tutor specialized in {current_curriculum}. Tailor explanations and difficulty to match {current_goal}."
            prompt = f"{system_instruction}\n\nExtract flashcards from this text: {raw_text}\nFormat EACH card strictly on a new line using a pipe symbol: Front | Back."
            
            response = client.models.generate_content(model="gemini-2.5-flash", contents=[prompt])
            cards_data = []
            for line in response.text.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|", 1)
                    cards_data.append({"Front": parts[0].strip(), "Back": parts[1].strip(), "Tag": "ai-gen", "Level": "Medium"})
            if cards_data:
                st.session_state['cards_df'] = pd.DataFrame(cards_data)
                st.success(f"Generated {len(cards_data)} cards adapted for {current_curriculum}!")
        except Exception as e:
            st.error(f"Error: {e}")

if not st.session_state['cards_df'].empty:
    st.markdown("### Deck Editor")
    st.session_state['cards_df'] = st.data_editor(st.session_state['cards_df'], num_rows="dynamic", use_container_width=True)
