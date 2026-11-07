import streamlit as st
from google import genai
import tempfile
import os
import pandas as pd
import genanki
import random

st.set_page_config(
    page_title="NoteFlash AI — Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Design System (Extracted from v0 HTML Artifact)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    :root {
        --bg-1: #090d16;
        --bg-2: #1e1b4b;
        --glass: rgba(255, 255, 255, 0.04);
        --glass-strong: rgba(255, 255, 255, 0.07);
        --border: rgba(255, 255, 255, 0.09);
        --border-strong: rgba(255, 255, 255, 0.16);
        --text: #e6e8f2;
        --muted: #8b90a8;
        --indigo: #6366f1;
        --indigo-light: #a5b4fc;
        --success: #34d399;
        --radius: 16px;
    }

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
        color: var(--text);
    }

    .stApp {
        background: linear-gradient(135deg, var(--bg-1) 0%, #0f1229 45%, var(--bg-2) 100%);
        background-attachment: fixed;
    }

    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Glassmorphism Containers */
    div[data-testid="stForm"], div.stTextArea, div.stTextInput, div.stFileUploader, div[data-testid="stDataFrame"], div.metric-container {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(18px) !important;
        -webkit-backdrop-filter: blur(18px) !important;
    }

    /* Glowing Primary Button */
    .stButton>button {
        width: 100%;
        background: linear-gradient(180deg, #7174f5 0%, #5458e8 100%);
        border: 1px solid rgba(165,180,252,0.5);
        color: #fff;
        font-weight: 600;
        padding: 10px 16px;
        border-radius: 12px;
        box-shadow: 0 0 0 1px rgba(99,102,241,0.4), 0 0 24px rgba(99,102,241,0.45);
        transition: all 0.2s ease;
    }
    
    .stButton>button:hover {
        background: linear-gradient(180deg, #7f82f7 0%, #6064ee 100%);
        box-shadow: 0 0 0 1px rgba(99,102,241,0.6), 0 0 36px rgba(99,102,241,0.7);
        transform: translateY(-1px);
    }

    /* Card Flip Preview Component */
    .flashcard-container {
        perspective: 1200px; width: 100%; aspect-ratio: 4 / 3; margin-top: 10px;
    }
    .flashcard-inner {
        position: relative; width: 100%; height: 100%; text-align: center;
        transition: transform 0.7s cubic-bezier(.2,.8,.2,1); transform-style: preserve-3d; cursor: pointer;
    }
    .flashcard-container:hover .flashcard-inner { transform: rotateY(180deg); }
    .face {
        position: absolute; inset: 0; backface-visibility: hidden; -webkit-backface-visibility: hidden;
        border-radius: 18px; padding: 22px; display: flex; flex-direction: column;
        border: 1px solid rgba(255, 255, 255, 0.16);
    }
    .face.front { background: linear-gradient(155deg, rgba(49,46,129,0.6), rgba(15,18,41,0.85)); box-shadow: 0 30px 60px -30px rgba(99,102,241,0.6); color: #818cf8; }
    .face.back { background: linear-gradient(155deg, rgba(30,27,75,0.9), rgba(9,13,22,0.95)); transform: rotateY(180deg); box-shadow: 0 30px 60px -30px rgba(99,102,241,0.6); color: #d4d7ea; }
</style>
""", unsafe_allow_html=True)

# Initialize Session States
if 'cards_df' not in st.session_state:
    st.session_state['cards_df'] = pd.DataFrame([
        {"Front": "What does ATP stand for?", "Back": "Adenosine triphosphate — primary energy carrier.", "Tag": "biology", "Level": "Easy"},
        {"Front": "Where does glycolysis occur?", "Back": "In the cytoplasm of the cell.", "Tag": "biology", "Level": "Medium"},
        {"Front": "What is the time complexity of binary search?", "Back": "O(log n)", "Tag": "cs", "Level": "Medium"}
    ])
if 'total_generated' not in st.session_state:
    st.session_state['total_generated'] = 1245

# Sidebar Navigation Workspace
with st.sidebar:
    st.markdown("### ⚡ **NoteFlash AI**")
    st.caption("v3.5 Pro Suite")
    st.markdown("---")
    
    nav_choice = st.radio(
        "WORKSPACE",
        ["✨ Generator", "📚 My Decks", "📊 Study Stats", "⚙️ Settings"],
        label_visibility="visible"
    )
    
    st.markdown("---")
    api_key_input = st.text_input("Gemini API Key", type="password", help="Get free key from Google AI Studio")
    
    st.markdown("---")
    st.markdown("📦 **AI Credits**")
    st.progress(62, text="620 / 1,000 Credits")
    st.caption("Resets in 12 days")
    st.button("Upgrade to Pro", type="primary")

# MAIN VIEWS LOGIC
if "Generator" in nav_choice:
    # Top Metrics Row matching v0 design
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total cards", st.session_state['total_generated'], "+48 this week")
    with m2:
        st.metric("Decks", "14", "+2 this week")
    with m3:
        st.metric("Study streak", "9d", "Personal best")
    with m4:
        st.metric("Retention", "87%", "+4.2%")

    st.markdown("---")

    col_main, col_preview = st.columns([1.6, 1], gap="large")

    with col_main:
        st.markdown("## Flashcard Generator")
        st.caption("Turn notes, lectures, and PDFs into study-ready decks in seconds.")

        input_mode = st.radio("Source", ["📄 PDF Upload", "✨ AI Text Paste", "✍️ Manual Format"], horizontal=True)

        raw_content = None
        uploaded_pdf = None

        if "PDF" in input_mode:
            uploaded_pdf = st.file_uploader("Drop a PDF here or browse", type=["pdf"], help="Lecture slides, textbook chapters up to 25 MB")
        elif "AI Text" in input_mode:
            raw_content = st.text_area("Paste notes", height=130, placeholder="Paste lecture notes or article...")
        else:
            raw_content = st.text_area("Manual Format (Front | Back)", value="What is Ohm's Law? | V = IR\nForce equals what? | Mass times acceleration", height=130)

        c1, c2 = st.columns(2)
        with c1:
            card_count = st.selectbox("Max Cards", [5, 10, 15, 20], index=1)
        with c2:
            card_style = st.selectbox("Style", ["Q & A", "Definition", "Cloze"])

        deck_title = st.text_input("Anki Deck Title", value="NoteFlash_Master_Deck")

        if st.button("Generate Cards ✨", type="primary"):
            key_to_use = api_key_input or (st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None)
            
            if not key_to_use and "Manual" not in input_mode:
                st.error("Please provide your Gemini API Key in the sidebar.")
            else:
                cards_data = []
                if "Manual" in input_mode:
                    for line in raw_content.split("\n"):
                        if "|" in line:
                            p = line.split("|", 1)
                            cards_data.append({"Front": p[0].strip(), "Back": p[1].strip(), "Tag": "manual", "Level": "Medium"})
                else:
                    with st.status("🤖 Gemini processing documents...", expanded=True) as status:
                        try:
                            client = genai.Client(api_key=key_to_use)
                            payload = []
                            if uploaded_pdf:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                                    tmp.write(uploaded_pdf.getvalue())
                                    tmp_path = tmp.name
                                file_ref = client.files.upload(file=tmp_path)
                                os.unlink(tmp_path)
                                payload = [file_ref]
                            else:
                                payload = [f"Content: {raw_content[:12000]}"]

                            prompt = f"Extract high-yield flashcards in {card_style} format. Format EACH card on a new line using a pipe: Front | Back. No extra commentary."
                            response = client.models.generate_content(model="gemini-2.5-flash", contents=payload + [prompt])

                            for line in response.text.strip().split("\n"):
                                if "|" in line:
                                    p = line.split("|", 1)
                                    cards_data.append({"Front": p[0].strip(), "Back": p[1].strip(), "Tag": "ai-gen", "Level": "Medium"})
                            
                            status.update(label="Extraction successful!", state="complete", expanded=False)
                        except Exception as e:
                            status.update(label="Generation failed.", state="error")
                            st.error(f"Error: {e}")

                if cards_data:
                    st.session_state['cards_df'] = pd.DataFrame(cards_data)
                    st.session_state['total_generated'] += len(cards_data)
                    st.success(f"Generated {len(cards_data)} flashcards successfully!")

    with col_preview:
        st.markdown("### 👁️ Live Preview")
        st.caption("Hover to flip card")
        
        sample_front = "What is the powerhouse of the cell?"
        sample_back = "Mitochondria"
        if not st.session_state['cards_df'].empty:
            sample_front = st.session_state['cards_df'].iloc[0]['Front']
            sample_back = st.session_state['cards_df'].iloc[0]['Back']

        st.markdown(f"""
        <div class="flashcard-container">
            <div class="flashcard-inner">
                <div class="face front">
                    <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.1em;">Question</div>
                    <div style="flex:1; display:flex; align-items:center; justify-content:center; font-size:16px; font-weight:600; text-align:center;">{sample_front}</div>
                    <div style="font-size:11px; color:var(--muted);">Tap to reveal answer</div>
                </div>
                <div class="face back">
                    <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.1em; color:#a5b4fc;">Answer</div>
                    <div style="flex:1; display:flex; align-items:center; justify-content:center; font-size:15px; text-align:center;">{sample_back}</div>
                    <div style="font-size:11px; color:var(--muted);">Tap to see question</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Export Actions (.apkg and .txt)
        if not st.session_state['cards_df'].empty:
            deck_id = random.randrange(1 << 30, 1 << 31)
            model_id = random.randrange(1 << 30, 1 << 31)
            my_model = genanki.Model(model_id, 'NoteFlash Pro Model', fields=[{'name': 'Front'}, {'name': 'Back'}], templates=[{'name': 'Card 1', 'qfmt': '{{Front}}', 'afmt': '{{FrontSide}}<hr id="answer">{{Back}}'}])
            my_deck = genanki.Deck(deck_id, deck_title)
            for _, row in st.session_state['cards_df'].iterrows():
                my_deck.add_note(genanki.Note(model=my_model, fields=[row['Front'], row['Back']]))
            
            pkg_path = f"{deck_title}.apkg"
            genanki.Package(my_deck).write_to_file(pkg_path)
            
            with open(pkg_path, "rb") as f:
                st.download_button("📥 Download Native .apkg Package", f, file_name=pkg_path, mime="application/octet-stream", use_container_width=True)

    # Interactive Deck Editor Table
    if not st.session_state['cards_df'].empty:
        st.markdown("---")
        st.markdown("### ✏️ Deck Editor")
        st.caption("Click any cell to edit • Add or remove rows dynamically")
        edited_df = st.data_editor(st.session_state['cards_df'], num_rows="dynamic", use_container_width=True, key="main_editor")
        st.session_state['cards_df'] = edited_df

elif "My Decks" in nav_choice:
    st.markdown("### 📚 Saved Decks")
    st.info("Your archived Anki packages ready for download.")
    st.markdown("""
    * 🧬 **Biology Chapter 4 - Cell Structure** (84 cards • `.apkg`)
    * ⚡ **Physics Grade 10 - Electricity** (112 cards • `.apkg`)
    * 📐 **Mathematics - Trigonometry Formulas** (45 cards • `.apkg`)
    """)

elif "Study Stats" in nav_choice:
    st.markdown("### 📊 Analytics & Retention")
    st.metric("Overall Mastery Score", "91.4%", "+2.1% this month")
    st.metric("Total Study Hours", "28.5 hrs")
    st.success("You are in the top 5% of active students this week!")

else:
    st.markdown("### ⚙️ Settings")
    st.text_input("Default Deck Author", value="Muhammed Mazin")
    st.selectbox("Export Format", ["Anki Package (.apkg)", "Tab-Separated (.txt)"])
    st.toggle("Dark Mode Glow Effects", value=True)
    st.button("Save Preferences")
