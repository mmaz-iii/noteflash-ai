import streamlit as st

st.set_page_config(
    page_title="NoteFlash AI - Study to Anki",
    page_icon="⚡",
    layout="centered"
)

st.title("⚡ NoteFlash AI: Instant Study-to-Anki Converter")
st.markdown("Transform your study notes into clean, tab-separated Anki flashcard decks instantly.")

# Sidebar Instructions
with st.sidebar:
    st.header("📖 How to Use")
    st.markdown("""
    1. **Format your notes** using a pipe symbol (`|`):  
       `Question | Answer`
    2. **Paste** them into the text area.
    3. **Download** the `.txt` file.
    4. **Import** into Anki via `File > Import`.
    """)
    st.markdown("---")
    st.markdown("🚀 *Built for fast, frictionless studying.*")

# Main Interface
st.subheader("Paste your study notes below")
default_text = "What is Newton's Second Law? | F = ma\nWhat is the powerhouse of the cell? | Mitochondria"

notes = st.text_area("Notes Input", value=default_text, height=220, label_visibility="collapsed")

col1, col2 = st.columns([2, 1])
with col1:
    filename = st.text_input("Output Filename", value="anki_deck.txt")

if st.button("Generate Anki Deck (.txt)", type="primary"):
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
            st.success(f"Successfully formatted {len(anki_lines)} flashcards!")
            st.download_button(
                label="📥 Download Anki File",
                data=output_data,
                file_name=filename if filename.endswith(".txt") else f"{filename}.txt",
                mime="text/plain"
            )
        else:
            st.error("No valid lines found. Make sure to separate questions and answers using `|`.")
    else:
        st.warning("Please enter some notes first.")
