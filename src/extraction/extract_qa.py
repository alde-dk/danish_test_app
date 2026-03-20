import fitz
import re
import os
import json
import glob

def is_header_or_footer(line):
    line_lower = line.lower()
    if "indfødsretsprøven" in line_lower: return True
    if "kl." in line_lower and "·" in line_lower: return True
    if re.match(r"^\d+\s*·", line): return True
    return False

def parse_questions(q_file):
    doc = fitz.open(q_file)
    questions = []
    current_q = None
    current_opt = None
    
    # Text usually starts on page 3 (index 2), but let's iterate safely
    start_idx = 2 if len(doc) >= 3 else 0
    for i in range(start_idx, len(doc)):
        page = doc[i]
        text = page.get_text("text") 
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines:
            if is_header_or_footer(line):
                continue
                
            q_match = re.match(r"^(\d+)\.\s+(.*)", line)
            if q_match:
                if current_q:
                    questions.append(current_q)
                current_q = {
                    "question_number": q_match.group(1),
                    "question": q_match.group(2),
                    "options": []
                }
                current_opt = None
                continue
                
            opt_match = re.match(r"^([A-Z])[:\)]\s+(.*)", line)
            if opt_match and current_q is not None:
                current_opt = {
                    "option_letter": opt_match.group(1),
                    "option_text": opt_match.group(2)
                }
                current_q["options"].append(current_opt)
                continue
                
            # Continuation of previous text
            if current_opt is not None:
                current_opt["option_text"] += " " + line
            elif current_q is not None:
                current_q["question"] += " " + line

    if current_q:
        questions.append(current_q)
        
    return questions

def parse_answers(a_file):
    if not os.path.exists(a_file):
        return {}
    doc = fitz.open(a_file)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
        
    answers = {}
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    current_num = None
    for line in lines:
        if re.match(r"^\d+$", line):
            current_num = line
        elif re.match(r"^[A-Z]$", line) and current_num is not None:
            answers[current_num] = line
            current_num = None
            
    return answers

def process_exams(exams_dir):
    all_data = {"questions": []}
    
    search_pattern = os.path.join(exams_dir, "indfoedsretsproeven-*.pdf")
    q_files = [f for f in glob.glob(search_pattern) if not f.endswith("-retteark.pdf")]
    
    for q_path in q_files:
        filename = os.path.basename(q_path)
        base_name = filename.replace(".pdf", "")
        
        a_path = os.path.join(exams_dir, f"{base_name}-retteark.pdf")
        
        print(f"Processing {filename}...")
        questions = parse_questions(q_path)
        answers = parse_answers(a_path)
        
        # Merge question and answers
        for q in questions:
            q_num = q["question_number"]
            formatted_q = {
                "file_name": base_name,
                "question": q["question"].strip(),
                "question_number": q_num,
                "options": q["options"]
            }
            
            ans_letter = answers.get(q_num)
            if ans_letter:
                formatted_q["answer_letter"] = ans_letter
                
                # Validation
                valid_letters = [opt["option_letter"] for opt in q["options"]]
                if ans_letter not in valid_letters:
                    print(f"  Warning: answer '{ans_letter}' not in options {valid_letters} for Q{q_num}")
            else:
                print(f"  Warning: No answer found for Q{q_num} in {filename}")
                
            all_data["questions"].append(formatted_q)
            
    return all_data

if __name__ == "__main__":
    exams_dir = r"C:\Users\alber\Desktop\Danish exam\exams"
    output_file = r"C:\Users\alber\projects\danish_test_app\src\output.json"
    
    data = process_exams(exams_dir)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"\nDONE! Wrote {len(data['questions'])} questions to {output_file}")
    
    # Just output the first parsed question for sanity check
    if data['questions']:
        print("\nSample first question in JSON:")
        print(json.dumps(data['questions'][0], ensure_ascii=False, indent=2))
