import streamlit as st
from google import genai
import tempfile
import os

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
    div[data-testid="stForm"], div.stTextArea, div.stTextInput, div.stFileUploader {
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
    st.caption("AI Document Engine v2.0")
    st.markdown("---")
    
    api_key_input = st.text_input("Gemini API Key", type="password", help="Get a free key from Google AI Studio")
    st.markdown("---")
    st.markdown("#### 🚀 Conversion Modes")
    st.markdown("""
    * **📄 PDF Upload:** Upload a textbook chapter or lecture notes PDF; Gemini reads it natively.
    * **✨ AI Text:** Paste raw text extracts.
    * **✍️ Manual:** Classic pipe format (`Q | A`).
    """)

# Main Content
main_col, side_col = st.columns([2.2, 1], gap="large")

with main_col:
    st.markdown('<h1 class="hero-title">Smart Study-to-Anki Converter</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Upload PDFs or paste notes to instantly generate production-ready Anki flashcards.</p>', unsafe_allow_html=True)

    mode = st.radio("Select Input Mode", ["📄 Upload PDF Document", "✨ AI Text Extraction", "✍️ Manual Pipe Format"], horizontal=True)

    # 1. PDF UPLOAD MODE
    if "PDF" in mode:
        uploaded_pdf = st.file_uploader("Upload your study guide or textbook chapter", type=["pdf"])
        filename = st.text_input("Deck Filename", value="pdf_anki_deck.txt")
        
        if st.button("Extract Flashcards from PDF ✨", type="primary"):
            key_to_use = api_key_input or (st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None)
            
            if not key_to_use:
                st.error("Please provide your Gemini API Key in the sidebar.")
            elif uploaded_pdf is None:
                st.warning("Please upload a PDF file first.")
            else:
                with st.spinner("📄 Uploading and analyzing document with Gemini..."):
                    try:
                        client = genai.Client(api_key=key_to_use)
                        
                        # Save uploaded file temporarily to process with Files API
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                            tmp_file.write(uploaded_pdf.getvalue())
                            tmp_file_path = tmp_file.name

                        # Upload file using Gemini Files API
                        uploaded_file = client.files.upload(file=tmp_file_path)
                        
                        # Clean up local temp file
                        os.unlink(tmp_file_path)

                        prompt = """Analyze this document thoroughly and extract high-yield flashcards covering all key concepts, definitions, and formulas.
                        Format EACH flashcard strictly on a new line using a pipe symbol:
                        Front of Card (Question/Concept) | Back of Card (Answer/Explanation)
                        Do not include markdown code block syntax around the output or extra commentary, just the raw text pairs."""

                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[uploaded_file, prompt]
                        )

                        ai_output = response.text.strip()
                        anki_lines = []
                        for line in ai_output.split("\n"):
                            if "|" in line:
                                anki_lines.append(line.strip())

                        if anki_lines:
                            final_data = "\n".join(anki_lines)
                            st.success(f"Successfully extracted {len(anki_lines)} cards from your PDF!")
                            st.download_button(
                                label="📥 Download PDF Anki Deck (.txt)",
                                data=final_data,
                                file_name=filename if filename.endswith(".txt") else f"{filename}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                        else:
                            st.error("Could not parse flashcards from this PDF layout. Try a text-heavy PDF.")
                    except Exception as e:
                        st.error(f"Error processing document: {e}")

    # 2. AI TEXT MODE
    elif "AI Text" in mode:
        raw_text = st.text_area("Paste Raw Study Content", height=180, placeholder="Paste your article or notes here...")
        filename = st.text_input("Deck Filename", value="ai_text_deck.txt")
        
        if st.button("Generate Cards with AI ✨", type="primary"):
            key_to_use = api_key_input or (st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None)
            
            if not key_to_use:
                st.error("Please enter your Gemini API Key in the sidebar.")
            elif not raw_text.strip():
                st.warning("Please paste some text content first.")
            else:
                with st.spinner("🤖 Gemini is building flashcards..."):
                    try:
                        client = genai.Client(api_key=key_to_use)
                        prompt = f"""Extract high-yield flashcards from the text below.
                        Format EACH flashcard strictly on a new line using a pipe symbol:
                        Front of Card (Question/Concept) | Back of Card (Answer/Explanation)
                        
                        Text content:
                        {raw_text[:12000]}"""
                        
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=prompt
                        )
                        
                        ai_output = response.text.strip()
                        anki_lines = [line.strip() for line in ai_output.split("\n") if "|" in line]
                        
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
                            st.error("AI couldn't format the output properly.")
                    except Exception as e:
                        st.error(f"Generation error: {e}")

    # 3. MANUAL PIPE MODE
    else:
        notes = st.text_input("Input Manual Notes", value="What is Ohm's Law? | V = IR")
        notes_area = st.text_area("", value="Force equals what? | Mass times acceleration", height=130)
        filename = st.text_input("Deck Filename", value="manual_deck.txt")
        
        if st.button("Generate Deck (.txt)", type="primary"):
            combined_notes = f"{notes}\n{notes_area}"
            lines = combined_notes.strip().split("\n")
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

with side_col:
    st.markdown("#### 💡 PDF Pro Tips")
    st.info("Gemini handles multi-page PDFs natively. You can upload a full chapter outline or summary booklet and turn the entire file into an Anki deck within seconds.")
