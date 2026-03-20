import fitz
import sys

def main():
    pdf_path = r"C:\Users\alber\Desktop\Danish exam\laeremateriale-til-indfoedsretsproeven.pdf"
    output_path = r"C:\Users\alber\projects\danish_test_app\src\extraction\chapter1.txt"
    try:
        doc = fitz.open(pdf_path)
        
        # Searching for the actual start and end of Chapter 1. 
        # In the TOC, Chapter 1 starts at logical page 5, Chapter 2 starts at logical page 65.
        # Let's check where the label '5' points to.
        toc = doc.get_toc(simple=False)
        chapter1_start = 4 # Default 0-indexed page 4
        chapter2_start = 64 # Default 0-indexed page 64
        
        for entry in doc.get_toc():
            if 'Kapitel 1 – Danmarks historie' in entry[1] and entry[2] > 0:
                chapter1_start = entry[2] - 1
            if 'Kapitel 2 – Det danske demokrati' in entry[1] and entry[2] > 0:
                chapter2_start = entry[2] - 1
                
        print(f"Extracting carefully from page {chapter1_start} to {chapter2_start}")
        with open(output_path, "w", encoding="utf-8") as f:
            for i in range(chapter1_start, chapter2_start):
                text = doc[i].get_text("text")
                f.write(f"--- PAGE {i+1} ---\n")
                f.write(text)
                f.write("\n")
        print(f"Wrote to {output_path}")

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
