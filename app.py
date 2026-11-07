import streamlit as st
from google import genai
import tempfile
import os
import pandas as pd
import genanki
import random

st.set_page_config(
    page_title="NoteFlash AI - Pro Suite",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Styling & Card Flip CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #0f172a 50%, #090d16 100%); }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .hero-title {
        font-size: 2.3rem; font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #94a3b8 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    .hero-subtitle { color: #94a3b8; font-size: 1rem; margin-bottom: 16px; }

    div[data-testid="stForm"], div.stTextArea, div.stTextInput, div.stFileUploader, div[data-testid="stDataFrame"] {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        backdrop-filter: blur(10px);
    }

    .stButton>button {
        width: 100%; background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: #ffffff; font-weight: 600; padding: 12px; border-radius: 8px; border: none;
        box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.35);
    }
    
    /* Card Flip Component */
    .flashcard-container {
        perspective: 1000px; width: 100%; height: 160px; margin-top: 10px; margin-bottom: 15px;
    }
    .flashcard-inner {
        position: relative; width: 100%; height: 100%; text-align: center;
        transition: transform 0.6s; transform-style: preserve-3d; cursor: pointer;
    }
    .flashcard-container:hover .flashcard-inner { transform: rotateY(180deg); }
    .flashcard-front, .flashcard-back {
        position: absolute; width: 100%; height: 100%;-webkit-backface-visibility: hidden;
        backface-visibility: hidden; border-radius: 10px; display: flex; align-items: center;
        justify-content: center; padding: 16px; font-size: 0.95rem; font-weight: 600;
        border: 1px solid rgba(129, 140, 248, 0.3);
    }
    .flashcard-front { background: rgba(30, 41, 59, 0.8); color: #818cf8; }
    .flashcard-back { background: rgba(49, 46, 129, 0.6); color: #e2e8f0; transform: rotateY(180deg); }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration & Controls
with st.sidebar:
    st.markdown("### ⚡ **NoteFlash AI**")
    st.caption("Pro Engine v3.0")
    st.markdown("---")
    
    api_key_input = st.text_input("Gemini API Key", type="password", help="Get free key from Google AI Studio")
    st.markdown("---")
    
    st.markdown("#### 🎛️ AI Difficulty & Style")
    card_focus = st.selectbox("Content Focus", ["High-Yield Concepts & Formulas", "Definitions & Terminology", "Comprehensive Q&A"])
    card_depth = st.select_slider("Extraction Depth", options=["Concise", "Balanced", "Exhaustive"], value="Balanced")
    deck_name = st.text_input("Anki Deck Title", value="NoteFlash_Master_Deck")

# Main Interface Layout
main_col, side_col = st.columns([2.3, 1], gap="large")

with main_col:
    st.markdown('<h1 class="hero-title">Professional Study-to-Anki Suite</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Upload documents, inspect flashcards interactively, and export `.apkg` packages.</p>', unsafe_allow_html=True)

    input_mode = st.radio("Source Input", ["📄 PDF Document", "✨ AI Text Paste", "✍️ Manual Pipe Format"], horizontal=True)

    raw_content = None
    uploaded_pdf = None

    if "PDF" in input_mode:
        uploaded_pdf = st.file_uploader("Upload textbook chapter or study notes PDF", type=["pdf"])
    elif "AI Text" in input_mode:
        raw_content = st.text_area("Paste raw study content", height=150, placeholder="Paste your article or notes summary...")
    else:
        raw_content = st.text_input("Manual Cards (Front | Back)", value="What is Ohm's Law? | V = IR")
        manual_area = st.text_area("", value="Power formula? | P = VI", height=100)
        if manual_area:
            raw_content = f"{raw_content}\n{manual_area}"

    if st.button("✨ Generate & Process Flashcards", type="primary"):
        key_to_use = api_key_input or (st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None)
        
        if not key_to_use and "Manual" not in input_mode:
            st.error("Please provide your Gemini API Key in the sidebar.")
        else:
            cards_data = []
            
            if "Manual" in input_mode:
                for line in raw_content.split("\n"):
                    if "|" in line:
                        parts = line.split("|", 1)
                        cards_data.append({"Front": parts[0].strip(), "Back": parts[1].strip()})
            else:
                # Multi-Step Processing Indicator using st.status
                with st.status("Executing AI Extraction Pipeline...", expanded=True) as status:
                    try:
                        client = genai.Client(api_key=key_to_use)
                        
                        status.update(label="Step 1/3: Parsing document structure...", state="running")
                        contents_payload = []
                        
                        if uploaded_pdf:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                                tmp.write(uploaded_pdf.getvalue())
                                tmp_path = tmp.name
                            uploaded_file_ref = client.files.upload(file=tmp_path)
                            os.unlink(tmp_path)
                            contents_payload = [uploaded_file_ref]
                        else:
                            contents_payload = [f"Text content: {raw_content[:12000]}"]

                        status.update(label=f"Step 2/3: Applying AI filter ({card_focus} - {card_depth})...", state="running")
                        prompt = f"""Extract high-yield flashcards focusing on {card_focus} with {card_depth.lower()} depth.
                        Format EACH card strictly on a new line using a pipe symbol:
                        Front of Card | Back of Card
                        No extra formatting or markdown blocks."""
                        
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=contents_payload + [prompt]
                        )

                        status.update(label="Step 3/3: Formatting card datasets...", state="running")
                        for line in response.text.strip().split("\n"):
                            if "|" in line:
                                p = line.split("|", 1)
                                cards_data.append({"Front": p[0].strip(), "Back": p[1].strip()})

                        status.update(label="Flashcard extraction complete!", state="complete", expanded=False)
                    except Exception as e:
                        status.update(label="Pipeline failed.", state="error")
                        st.error(f"Error: {e}")

            if cards_data:
                st.session_state['cards_df'] = pd.DataFrame(cards_data)
                st.success(f"Successfully generated {len(cards_data)} flashcards!")

    # Interactive Card Editor Table & Preview
    if 'cards_df' in st.session_state and not st.session_state['cards_df'].empty:
        st.markdown("### ✏️ Interactive Card Editor")
        st.caption("Review or edit your cards below before exporting.")
        
        edited_df = st.data_editor(
            st.session_state['cards_df'], 
            num_rows="dynamic", 
            use_container_width=True,
            key="card_table"
        )
        st.session_state['cards_df'] = edited_df

        # Live Card Flip Preview Component
        st.markdown("### 👁️ Live Card Flip Preview")
        sample_row = edited_df.iloc[0] if len(edited_df) > 0 else {"Front": "Question", "Back": "Answer"}
        st.markdown(f"""
        <div class="flashcard-container">
            <div class="flashcard-inner">
                <div class="flashcard-front"><b>Q:</b>&nbsp; {sample_row['Front']}</div>
                <div class="flashcard-back"><b>A:</b>&nbsp; {sample_row['Back']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Export options (.apkg and .txt)
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            # Generate .apkg Package
            deck_id = random.randrange(1 << 30, 1 << 31)
            model_id = random.randrange(1 << 30, 1 << 31)
            
            my_model = genanki.Model(
                model_id, 'NoteFlash Pro Model',
                fields=[{'name': 'Front'}, {'name': 'Back'}],
                templates=[{
                    'name': 'Card 1',
                    'qfmt': '{{Front}}',
                    'afmt': '{{FrontSide}}<hr id="answer">{{Back}}',
                }]
            )
            my_deck = genanki.Deck(deck_id, deck_name)
            for _, row in edited_df.iterrows():
                my_deck.add_note(genanki.Note(model=my_model, fields=[row['Front'], row['Back']]))
            
            pkg_path = f"{deck_name}.apkg"
            genanki.Package(my_deck).write_to_file(pkg_path)
            
            with open(pkg_path, "rb") as f:
                st.download_button(
                    label="📥 Download Native .apkg Deck",
                    data=f,
                    file_name=pkg_path,
                    mime="application/octet-stream",
                    use_container_width=True
                )

        with col_dl2:
            txt_data = "\n".join([f"{r['Front']}\t{r['Back']}" for _, r in edited_df.iterrows()])
            st.download_button(
                label="📥 Download Tab-Separated .txt",
                data=txt_data,
                file_name=f"{deck_name}.txt",
                mime="text/plain",
                use_container_width=True
            )

with side_col:
    st.markdown("#### 📊 Export Analytics")
    if 'cards_df' in st.session_state and not st.session_state['cards_df'].empty:
        total_cards = len(st.session_state['cards_df'])
        est_time = round(total_cards * 0.75) # ~45 seconds saved per card vs manual typing
        st.metric("Total Cards Generated", total_cards)
        st.metric("Est. Study Time Saved", f"{est_time} mins")
        st.metric("Deck Format", "UTF-8 / Anki Ready")
    else:
        st.info("Generate cards to view session analytics and stats.")
