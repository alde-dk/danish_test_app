import fitz
import sys

def main():
    pdf_path = r"C:\Users\alber\Desktop\Danish exam\laeremateriale-til-indfoedsretsproeven.pdf"
    try:
        doc = fitz.open(pdf_path)
        toc = doc.get_toc()
        print("TOC:")
        for t in toc:
            print(t)
        
        # If no TOC, just print first 5 pages text
        if not toc:
            print("No TOC found. Printing first few pages...")
            for i in range(min(15, len(doc))):
                print(f"--- PAGE {i+1} ---")
                text = doc[i].get_text("text")
                print(text[:500])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
