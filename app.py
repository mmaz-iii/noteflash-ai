import streamlit as st

st.set_page_config(
    page_title="NoteFlash AI - Instant Study-to-Anki Converter",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern UI/UX Design
st.markdown("""
<style>
    /* Google Fonts Import */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Gradient Background Glow */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #0f172a 50%, #090d16 100%);
    }

    /* Hide Streamlit Header & Branding */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}

    /* Hero Section Styling */
    .hero-badge {
        display: inline-block;
        padding: 6px 16px;
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(129, 140, 248, 0.3);
        border-radius: 20px;
        color: #818cf8;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 12px;
    }

    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.2;
        margin-bottom: 12px;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.15rem;
        margin-bottom: 24px;
    }

    /* Card Containers */
    div[data-testid="stForm"], div.css-1r6slb0, div.stTextArea, div.stTextInput {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        backdrop-filter: blur(12px);
    }

    /* Metric Box */
    .metric-card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }

    .metric-val {
        font-size: 1.6rem;
        font-weight: 700;
        color: #6366f1;
    }

    .metric-lbl {
        font-size: 0.8rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Button Styling */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: #ffffff;
        font-weight: 600;
        font-size: 1rem;
        padding: 12px 24px;
        border-radius: 8px;
        border: none;
        box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.39);
        transition: all 0.2s ease;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px 0 rgba(99, 102, 241, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar UI
with st.sidebar:
    st.markdown("### ⚡ **NoteFlash AI**")
    st.caption("v1.2 • Production Ready")
    st.markdown("---")
    
    st.markdown("#### 📖 How It Works")
    st.markdown("""
    1. **Format Input**  
       Separate your front and back card using a pipe (`|`).
       `Question | Answer`
    2. **Convert & Export**  
       Name your file and generate the tab-separated dataset.
    3. **Import to Anki**  
       Open Anki Desktop → `File` → `Import` and select your deck.
    """)
    
    st.markdown("---")
    st.markdown("#### 💡 Pro Tip")
    st.info("You can paste AI outputs directly from ChatGPT, Claude, or Gemini into the editor!")

# Main Content Layout
main_col, side_col = st.columns([2.5, 1], gap="large")

with main_col:
    st.markdown('<div class="hero-badge">STUDY PRODUCTIVITY TOOL</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="hero-title">Transform Study Notes into Anki Decks Instantly</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Convert raw summaries and pipe-separated notes into flawless Anki flashcards in seconds.</p>', unsafe_allow_html=True)

    default_text = "What is Newton's Second Law? | F = ma\nWhat is the powerhouse of the cell? | Mitochondria\nWhat is the speed of light? | 3 x 10^8 m/s"
    
    notes = st.text_area("Input Study Notes", value=default_text, height=220, help="Format: Front Text | Back Text")

    col_name, col_btn = st.columns([1.5, 1], gap="medium")
    with col_name:
        filename = st.text_input("Deck Filename", value="physics_deck.txt", label_visibility="visible")
    
    with col_btn:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        generate_clicked = st.button("Generate Deck ✨", type="primary")

    if generate_clicked:
        if notes.strip():
            lines = notes.strip().split("\n")
            anki_lines = []
            for line in lines:
                if "|" in line:
                    parts = line.split("|", 1)
                    q = parts[0].strip()
                    a = parts[1].strip()
                    anki_lines.append(f"{q}\t{a}")
            
            if anki_lines:
                output_data = "\n".join(anki_lines)
                st.success(f"Successfully generated {len(anki_lines)} cards!")
                st.download_button(
                    label="📥 Download .txt File",
                    data=output_data,
                    file_name=filename if filename.endswith(".txt") else f"{filename}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                st.error("No valid pipe lines found. Ensure your notes use the format: Front | Back")
        else:
            st.warning("Please paste your study notes before generating.")

with side_col:
    st.markdown("#### 📊 App Stats")
    
    st.markdown("""
    <div class="metric-card" style="margin-bottom: 12px;">
        <div class="metric-val">100%</div>
        <div class="metric-lbl">Anki Compatibility</div>
    </div>
    <div class="metric-card" style="margin-bottom: 12px;">
        <div class="metric-val">Instant</div>
        <div class="metric-lbl">Conversion Speed</div>
    </div>
    <div class="metric-card">
        <div class="metric-val">UTF-8</div>
        <div class="metric-lbl">Encoding Standard</div>
    </div>
    """, unsafe_allow_html=True)
