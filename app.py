import streamlit as st
from google import genai

st.set_page_config(
    page_title="NoteFlash AI - AI Study Converter",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #0f172a 50%, #090d16 100%); }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .hero-title {
        font-size: 2.5rem; font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #94a3b8 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    .hero-subtitle { color: #94a3b8; font-size: 1.05rem; margin-bottom: 20px; }
    div[data-testid="stForm"], div.stTextArea, div.stTextInput {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
    }
    .stButton>button {
        width: 100%; background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: #ffffff; font-weight: 600; padding: 12px; border-radius: 8px; border: none;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.markdown("### ⚡ **NoteFlash AI**")
    st.caption("AI-Powered Edition")
    st.markdown("---")
    
    # API Key Input for Streamlit secrets or manual entry
    api_key_input = st.text_input("Gemini API Key", type="password", help="Get a free key from Google AI Studio")
    st.markdown("---")
    st.markdown("#### 🤖 AI Mode vs Manual Mode")
    st.markdown("""
    * **AI Mode:** Paste unformatted notes or text chapters. Gemini automatically scans and builds flashcards.
    * **Manual Mode:** Standard `Front | Back` pipe syntax.
    """)

# Main Content
main_col, side_col = st.columns([2.2, 1], gap="large")

with main_col:
    st.markdown('<h1 class="hero-title">Smart Study-to-Anki Converter</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Transform messy textbook chapters or raw notes into structured flashcards instantly.</p>', unsafe_allow_html=True)

    mode = st.radio("Select Conversion Engine", ["✨ AI Auto-Extract (Gemini)", "✍️ Manual Pipe Format (`Q | A`)"], horizontal=True)

    if "AI" in mode:
        raw_text = st.text_area("Paste Raw Study Content / Chapter Text", height=200, placeholder="Paste a Wikipedia article, textbook summary, or class notes here...")
        filename = st.text_input("Deck Filename", value="ai_smart_deck.txt")
        
        if st.button("Generate Cards with AI ✨", type="primary"):
            key_to_use = api_key_input or (st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None)
            
            if not key_to_use:
                st.error("Please enter your Gemini API Key in the sidebar.")
            elif not raw_text.strip():
                st.warning("Please paste some text content first.")
            else:
                with st.spinner("🤖 Gemini is analyzing text and building flashcards..."):
                    try:
                        client = genai.Client(api_key=key_to_use)
                        prompt = f"""You are an expert study assistant. Read the text below and extract high-yield flashcards.
                        Format EACH flashcard strictly on a new line using a pipe symbol:
                        Front of Card (Question/Concept) | Back of Card (Answer/Explanation)
                        Do not include extra headings or bullet symbols, just the raw pairs.
                        
                        Text content:
                        {raw_text[:12000]}"""
                        
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=prompt
                        )
                        
                        ai_output = response.text.strip()
                        anki_lines = []
                        for line in ai_output.split("\n"):
                            if "|" in line:
                                anki_lines.append(line.strip())
                        
                        if anki_lines:
                            final_data = "\n".join(anki_lines)
                            st.success(f"Successfully extracted {len(anki_lines)} AI flashcards!")
                            st.download_button(
                                label="📥 Download AI Anki Deck (.txt)",
                                data=final_data,
                                file_name=filename if filename.endswith(".txt") else f"{filename}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                        else:
                            st.error("AI couldn't format the output properly. Try providing more structured text.")
                    except Exception as e:
                        st.error(f"Generation error: {e}")

    else:
        notes = st.text_area("Input Manual Notes", value="What is Ohm's Law? | V = IR\nForce equals what? | Mass times acceleration", height=200)
        filename = st.text_input("Deck Filename", value="manual_deck.txt")
        
        if st.button("Generate Deck (.txt)", type="primary"):
            if notes.strip():
                lines = notes.strip().split("\n")
                anki_lines = []
                for line in lines:
                    if "|" in line:
                        parts = line.split("|", 1)
                        anki_lines.append(f"{parts[0].strip()}\t{parts[1].strip()}")
                
                if anki_lines:
                    output_data = "\n".join(anki_lines)
                    st.success(f"Successfully formatted {len(anki_lines)} cards!")
                    st.download_button(
                        label="📥 Download .txt File",
                        data=output_data,
                        file_name=filename if filename.endswith(".txt") else f"{filename}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                else:
                    st.error("No valid pipe lines found. Use format: Front | Back")
            else:
                st.warning("Please enter your notes.")

with side_col:
    st.markdown("#### 💡 Pro Tips")
    st.info("With AI Mode enabled, you can paste full textbook chapters or PDF summaries and let Gemini handle the heavy lifting of question creation.")
