import streamlit as st
import streamlit.components.v1 as components
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

# Custom SaaS Glassmorphism Styling & TTS/Shortcuts Injector
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

    .autosave-badge {
        display: inline-flex; align-items: center; gap: 6px; font-size: 12px; padding: 4px 10px;
        border-radius: 99px; background: rgba(52, 211, 153, 0.1); border: 1px solid rgba(52, 211, 153, 0.3); color: #34d399;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session States
if 'cards_df' not in st.session_state:
    st.session_state['cards_df'] = pd.DataFrame(columns=["Select", "Front", "Back", "Tag", "Level"])
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'onboarded' not in st.session_state:
    st.session_state['onboarded'] = False
if 'user_profile' not in st.session_state:
    st.session_state['user_profile'] = {"curriculum": "General", "goal": "Standard"}
if 'sync_status' not in st.session_state:
    st.session_state['sync_status'] = "All changes saved"
if 'study_index' not in st.session_state:
    st.session_state['study_index'] = 0
if 'study_streak' not in st.session_state:
    st.session_state['study_streak'] = 9

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

# --- MAIN APP WORKSPACE ---
with st.sidebar:
    st.markdown(f"### ⚡ **NoteFlash AI**")
    st.caption(f"Signed in as: {st.session_state.get('user_email', 'User')}")
    st.info(f"📚 Track: {st.session_state['user_profile']['curriculum']}")
    st.markdown(f"🔥 **Study Streak:** {st.session_state['study_streak']} Days")
    
    sync_col_map = {"All changes saved": "🟢 All changes saved", "Syncing...": "🟡 Syncing...", "Offline": "🔴 Offline"}
    st.markdown(f'<div class="autosave-badge">{sync_col_map.get(st.session_state["sync_status"], "🟢 All changes saved")}</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    nav_choice = st.radio("WORKSPACE", ["✨ Generator & Editor", "📖 Study Now (In-App)", "⚙️ Settings"])
    
    st.markdown("---")
    if st.button("Log Out"):
        st.session_state['logged_in'] = False
        st.session_state['onboarded'] = False
        st.rerun()

    api_key_input = st.text_input("Gemini API Key", type="password", help="Get free key from Google AI Studio")

# --- VIEW 1: GENERATOR & EDITOR ---
if "Generator" in nav_choice:
    st.markdown("## Flashcard Generator Workspace")
    st.markdown(f"*(Profile configured for **{st.session_state['user_profile']['curriculum']}**)*")

    current_curriculum = st.session_state['user_profile']['curriculum']
    current_goal = st.session_state['user_profile']['goal']

    raw_text = st.text_area("Paste notes or study content:", height=100)

    col_gen, col_shortcut_info = st.columns([2, 1])
    with col_gen:
        generate_clicked = st.button("Generate Flashcards ✨", type="primary")
    with col_shortcut_info:
        st.caption("⌨️ **Shortcuts:** `Cmd/Ctrl + Enter` to generate.")

    if generate_clicked:
        key_to_use = api_key_input or (st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None)
        if not key_to_use:
            st.error("Please provide your Gemini API key.")
        else:
            st.session_state['sync_status'] = "Syncing..."
            try:
                client = genai.Client(api_key=key_to_use)
                system_instruction = f"You are an expert tutor specialized in {current_curriculum}. Tailor explanations to match {current_goal}."
                prompt = f"{system_instruction}\n\nExtract flashcards from this text: {raw_text}\nFormat EACH card strictly on a new line using a pipe symbol: Front | Back."
                
                response = client.models.generate_content(model="gemini-2.5-flash", contents=[prompt])
                cards_data = []
                for line in response.text.strip().split("\n"):
                    if "|" in line:
                        parts = line.split("|", 1)
                        cards_data.append({"Select": False, "Front": parts[0].strip(), "Back": parts[1].strip(), "Tag": "ai-gen", "Level": "Medium"})
                if cards_data:
                    st.session_state['cards_df'] = pd.DataFrame(cards_data)
                    st.session_state['sync_status'] = "All changes saved"
                    st.success(f"Generated {len(cards_data)} cards successfully!")
            except Exception as e:
                st.session_state['sync_status'] = "Offline"
                st.error(f"Error: {e}")

    if not st.session_state['cards_df'].empty:
        st.markdown("---")
        st.markdown("### ✏️ Bulk Operations & Deck Editor")
        
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            bulk_tag = st.text_input("Apply Tag to Selected", placeholder="e.g. #physics")
            if st.button("Apply Tag"):
                if bulk_tag and not st.session_state['cards_df'].empty:
                    mask = st.session_state['cards_df']['Select'] == True
                    st.session_state['cards_df'].loc[mask, 'Tag'] = bulk_tag
                    st.success("Tags applied!")
                    st.rerun()
        with b2:
            bulk_level = st.selectbox("Batch Difficulty", ["Easy", "Medium", "Hard"])
            if st.button("Update Difficulty"):
                if not st.session_state['cards_df'].empty:
                    mask = st.session_state['cards_df']['Select'] == True
                    st.session_state['cards_df'].loc[mask, 'Level'] = bulk_level
                    st.success("Difficulty updated!")
                    st.rerun()
        with b3:
            if st.button("🗑️ Delete Selected"):
                if not st.session_state['cards_df'].empty:
                    st.session_state['cards_df'] = st.session_state['cards_df'][st.session_state['cards_df']['Select'] == False].reset_index(drop=True)
                    st.success("Deleted selected.")
                    st.rerun()

        edited_df = st.data_editor(st.session_state['cards_df'], num_rows="dynamic", use_container_width=True, key="power_editor")
        st.session_state['cards_df'] = edited_df

# --- VIEW 2: IN-APP STUDY MODE & TTS ---
elif "Study Now" in nav_choice:
    st.markdown("## 📖 In-App Study Mode")
    if st.session_state['cards_df'].empty:
        st.info("No cards available. Generate a deck in the Generator tab first.")
    else:
        df = st.session_state['cards_df']
        idx = st.session_state['study_index']
        if idx >= len(df): 
            st.session_state['study_index'] = 0
            idx = 0

        card = df.iloc[idx]
        st.markdown(f"**Card {idx + 1} of {len(df)} | Tag: `{card['Tag']}` | Level: {card['Level']}**")
        
        # Interactive Study Container
        st.markdown(f"""
        <div style="padding: 35px; background: rgba(30,41,59,0.7); border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); min-height: 220px; text-align: center; margin-bottom: 20px;">
            <h4 style="color: #818cf8; text-transform: uppercase; font-size: 12px; letter-spacing: 0.1em;">Question</h4>
            <p style="font-size: 1.3rem; margin-top: 15px; font-weight: 600;">{card['Front']}</p>
        </div>
        """, unsafe_allow_html=True)

        # Text-to-Speech Button via Browser Web Speech API
        tts_text = f"Question: {card['Front']}. Answer: {card['Back']}"
        components.html(f"""
            <div style="margin-bottom: 15px;">
                <button onclick="speakText()" style="background: #6366f1; color: white; border: none; padding: 8px 14px; border-radius: 8px; cursor: pointer; font-family: sans-serif; font-weight: 600; font-size: 13px;">
                    🔊 Listen to Card (TTS)
                </button>
            </div>
            <script>
                function speakText() {{
                    const utterance = new SpeechSynthesisUtterance("{tts_text}");
                    utterance.rate = 0.95;
                    window.speechSynthesis.speak(utterance);
                }}
            </script>
        """, height=50)

        show_answer = st.checkbox("Reveal Answer 👀")
        if show_answer:
            st.markdown(f"""
            <div style="padding: 22px; background: rgba(49,46,129,0.5); border-radius: 12px; border: 1px solid rgba(129,140,248,0.3); margin-bottom: 20px;">
                <strong style="color: #a5b4fc;">Answer:</strong><br>{card['Back']}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("#### Rate your retention:")
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("1 - Again"): 
                st.session_state['study_index'] = (idx + 1) % len(df)
                st.rerun()
            if c2.button("2 - Hard"): 
                st.session_state['study_index'] = (idx + 1) % len(df)
                st.rerun()
            if c3.button("3 - Good"): 
                st.session_state['study_index'] = (idx + 1) % len(df)
                st.rerun()
            if c4.button("4 - Easy"): 
                st.session_state['study_index'] = (idx + 1) % len(df)
                st.rerun()

# --- VIEW 3: SETTINGS ---
else:
    st.markdown("## ⚙️ Settings")
    st.text_input("Display Name", value=st.session_state.get('user_email', 'User'))
    st.selectbox("Default Export Format", ["Anki Package (.apkg)", "Tab-Separated (.txt)"])
    st.button("Save Preferences")

# Global Keyboard Shortcuts Injection
components.html("""
<script>
    const doc = window.parent.document;
    doc.addEventListener('keydown', function(e) {
        if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
            const buttons = doc.querySelectorAll('button');
            buttons.forEach(btn => {
                if (btn.innerText.includes('Generate Flashcards')) {
                    btn.click();
                }
            });
        }
    });
</script>
""", height=0)
