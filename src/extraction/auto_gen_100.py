import json
import random
import re

def generate_questions():
    with open('chapter1.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_page = "1"
    sentences_by_page = []
    
    sentence_endings = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        page_match = re.match(r'^--- PAGE (\d+) ---$', line)
        if page_match:
            current_page = page_match.group(1)
            continue
            
        parts = sentence_endings.split(line)
        for part in parts:
            part = part.strip()
            # Lowered the length threshold to capture more sentences
            if len(part) > 15 and " " in part:
                sentences_by_page.append({'page': current_page, 'text': part})
                
    # Less strict filtering
    good_sentences = [
        s for s in sentences_by_page 
        if any(w[0].isupper() for w in s['text'].split() if len(w) > 2) or re.search(r'\d+', s['text'])
    ]
    
    if len(good_sentences) < 100:
        good_sentences = sentences_by_page
        
    random.seed(42)
    selected = random.sample(good_sentences, max(100, min(150, len(good_sentences))))
    
    questions = []
    i = 0
    while len(questions) < 100 and i < len(selected):
        item = selected[i]
        i += 1
        
        text = item['text']
        page = item['page']
        
        words = text.split()
        if len(words) < 4:
            continue
            
        split_idx = len(words) // 2 + 1
        q_text = " ".join(words[:split_idx]) + " ... ?"
        correct_ans = " ".join(words[split_idx:]).rstrip('.')
        
        # Pick 2 random wrong answers
        wrong_candidates = []
        for w in random.sample(sentences_by_page, 20):
            wrong_ans = " ".join(w['text'].split()[len(w['text'].split())//2:]).rstrip('.')
            if len(wrong_ans) > 3 and wrong_ans != correct_ans:
                wrong_candidates.append(wrong_ans)
                if len(wrong_candidates) == 2:
                    break
        
        if len(wrong_candidates) < 2:
            wrong_candidates = ["I 1849", "omkring 1000"]
            
        options = [
            {"option_letter": "A", "option_text": correct_ans},
            {"option_letter": "B", "option_text": wrong_candidates[0]},
            {"option_letter": "C", "option_text": wrong_candidates[1]}
        ]
        
        random.shuffle(options)
        
        correct_letter = "A"
        for idx, opt in enumerate(options):
            letter = chr(65 + idx)
            opt["option_letter"] = letter
            if opt["option_text"] == correct_ans:
                correct_letter = letter
                
        q_obj = {
            "file_name": "laeremateriale-til-indfoedsretsproeven",
            "chapter": "1",
            "page": page,
            "question": q_text,
            "question_number": str(len(questions) + 1),
            "options": options,
            "answer_letter": correct_letter
        }
        questions.append(q_obj)
        
    final_output = {
        "questions": questions
    }
    
    out_path = r'C:\Users\alber\projects\danish_test_app\app\data\output.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)
        
    print(f"Generated {len(questions)} questions and saved to {out_path}.")

if __name__ == '__main__':
    generate_questions()
