import fitz
import os

pdf_dir = r"C:\Users\alber\Desktop\Danish exam\exams"
q_file = os.path.join(pdf_dir, "indfoedsretsproeven-2020-06.pdf")
a_file = os.path.join(pdf_dir, "indfoedsretsproeven-2020-06-retteark.pdf")

print("--- Questions Page 3 ---")
doc = fitz.open(q_file)
# Page index 2 is page 3
text = doc[2].get_text()
print(repr(text[:500]))

print("\n--- Answers Page 1 ---")
doc2 = fitz.open(a_file)
text2 = doc2[0].get_text()
print(repr(text2[:500]))
