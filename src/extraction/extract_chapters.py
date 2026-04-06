import fitz
import os
import re

def extract_chapter(doc, start_page, end_page, output_path):
    print(f"Extracting from page {start_page + 1} to {end_page}...")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for i in range(start_page, end_page):
                text = doc[i].get_text("text")
                f.write(f"--- PAGE {i+1} ---\n")
                f.write(text)
                f.write("\n")
        print(f"Successfully wrote to {output_path}")
    except Exception as e:
        print(f"Error writing to {output_path}: {e}")

def main():
    pdf_path = "src/extraction/pdf/laeremateriale-til-indfoedsretsproeven.pdf"
    output_dir = "src/extraction"
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return

    try:
        doc = fitz.open(pdf_path)
        toc = doc.get_toc()
        
        # We'll look for "Kapitel X" at level 1
        chapter_pages = []
        for entry in toc:
            level, title, page = entry
            if level == 1:
                # Normalize title: replace \t, \xa0 with space, etc.
                norm_title = title.replace('\t', ' ').replace('\xa0', ' ').strip()
                match = re.search(r'Kapitel (\d+)', norm_title)
                if match:
                    chap_num = int(match.group(1))
                    chapter_pages.append({
                        'number': chap_num,
                        'title': norm_title,
                        'start_page': page - 1 # 0-indexed
                    })
        
        # Sort by chapter number
        chapter_pages.sort(key=lambda x: x['number'])
        
        target_chapters = [2, 3, 4, 5, 6]
        
        for i in range(len(chapter_pages)):
            chap = chapter_pages[i]
            if chap['number'] in target_chapters:
                start_page = chap['start_page']
                # End page is the start of the next chapter (at level 1), or the end of the document
                if i + 1 < len(chapter_pages):
                    end_page = chapter_pages[i+1]['start_page']
                else:
                    end_page = len(doc)
                
                output_filename = f"chapter{chap['number']}.txt"
                output_path = os.path.join(output_dir, output_filename)
                
                print(f"Chapter {chap['number']}: {chap['title']}")
                extract_chapter(doc, start_page, end_page, output_path)

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
