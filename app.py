import streamlit as st

st.set_page_config(page_title="NoteFlash AI", page_icon="⚡", layout="centered")

st.title("⚡ NoteFlash AI: Instant Study-to-Anki Converter")
st.write("Convert your study notes into clean, tab-separated Anki flashcard decks instantly.")

# Text input for notes
raw_input = st.text_area(
    "Paste your study notes below (Format: Question | Answer)", 
    height=200, 
    placeholder="What is Newton's Second Law? | F = ma\nWhat is the powerhouse of the cell? | Mitochondria"
)

if st.button("Generate Anki Deck (.txt)"):
    if raw_input.strip():
        lines = raw_input.strip().split("\n")
        # Anki header format for tab-separated files
        deck_content = "#separator:tab\n#html:true\n"
        valid_count = 0
        
        for line in lines:
            if "|" in line:
                q, a = line.split("|", 1)
                deck_content += f"{q.strip()}\t{a.strip()}\n"
                valid_count += 1
        
        if valid_count > 0:
            st.success(f"Successfully generated {valid_count} flashcards!")
            st.download_button(
                label="📥 Download Anki Import File",
                data=deck_content,
                file_name="noteflash_deck.txt",
                mime="text/plain"
            )
        else:
            st.error("Please use the pipe symbol (|) to separate your questions and answers.")
    else:
            st.warning("Please enter some notes first!")