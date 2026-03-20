import json
import os
import re
import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.genai import types

load_dotenv()

# Constants
SOURCE_FILE = "src/extraction/chapter1.txt"
OUTPUT_FILE = "app/data/output_generated_questions.json"
MODEL_NAME = "gemini-flash-latest"

class Option(BaseModel):
    option_letter: str
    option_text: str

class Question(BaseModel):
    file_name: str = "chapter1"
    question: str
    question_number: str
    options: List[Option]
    answer_letter: str
    is_verified: bool = False

def read_source_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

async def run_with_agent(agent: Agent, prompt: str) -> str:
    runner = Runner(
        app_name="InMemoryRunner",
        agent=agent,
        session_service=InMemorySessionService(),
        artifact_service=InMemoryArtifactService(),
        memory_service=InMemoryMemoryService(),
        auto_create_session=True
    )
    response_text = ""
    content = types.Content(parts=[types.Part(text=prompt)])
    async for event in runner.run_async(
        user_id="user", 
        session_id="session", 
        new_message=content
    ):
        if hasattr(event, "content") and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
    return response_text

async def main_async():
    if not os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY") == "YOUR_API_KEY_HERE":
        print("Please set your GOOGLE_API_KEY in the .env file.")
        return

    # Load existing questions
    existing_questions = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                existing_questions = data.get("questions", [])
            print(f"Loaded {len(existing_questions)} existing questions.")
        except Exception as e:
            print(f"Warning: Could not load existing questions: {e}")

    # Determine starting question number
    start_num = 1
    if existing_questions:
        try:
            nums = [int(q["question_number"]) for q in existing_questions if q["question_number"].isdigit()]
            if nums:
                start_num = max(nums) + 1
        except Exception:
            start_num = len(existing_questions) + 1

    print("Reading source text...")
    source_text = read_source_text(SOURCE_FILE)

    # 1. Generator Agent
    generator = Agent(
        name="generator",
        model=MODEL_NAME,
        instruction=f"""
        You are an expert at creating citizenship test questions.
        Based on the provided text from 'Chapter 1 - Danish History', generate 20 NEW multiple-choice questions.
        Avoid duplicating the topics already covered in these existing questions: {json.dumps([q['question'] for q in existing_questions[-10:]], ensure_ascii=False)}
        
        Rules:
        1. Each question must have 2 or 3 options.
        2. Only one option must be correct.
        3. The questions should be in Danish.
        4. Follow the JSON structure exactly.
        5. Set 'file_name' to 'chapter1'.
        6. Start 'question_number' from {start_num}.
        
        JSON Schema:
        {{
            "questions": [
                {{
                    "file_name": "chapter1",
                    "question": "Question text here?",
                    "question_number": "{start_num}",
                    "options": [
                        {{"option_letter": "A", "option_text": "Option A"}},
                        {{"option_letter": "B", "option_text": "Option B"}}
                    ],
                    "answer_letter": "A"
                }}
            ]
        }}
        """
    )

    print(f"Generating 20 new questions starting from #{start_num}...")
    gen_response_text = await run_with_agent(generator, f"Text content:\n{source_text}\n\nGenerate 20 questions.")
    
    json_match = re.search(r'\{.*\}', gen_response_text, re.DOTALL)
    if not json_match:
        print("Failed to parse JSON from generator response.")
        print(gen_response_text)
        return
    
    try:
        raw_questions = json.loads(json_match.group())
        new_questions_data = raw_questions.get("questions", [])
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return

    # 2. Critic Agent (Batch Verification)
    critic = Agent(
        name="critic",
        model=MODEL_NAME,
        instruction=f"""
        You are a fact-checker for the Danish citizenship test.
        Your task is to verify if the answers to the provided questions are explicitly stated in the text.
        
        For each question, reply with its question_number and either 'VERIFIED' or 'NOT_FOUND'.
        
        Text content for verification:
        {source_text}
        """
    )

    print(f"Verifying {len(new_questions_data)} new questions in batch...")
    q_batch_text = "\n\n".join([
        f"Num: {q['question_number']}\nQ: {q['question']}\nAns: {q['answer_letter']}" 
        for q in new_questions_data
    ])
    
    critic_response_text = await run_with_agent(critic, f"Please verify these questions:\n{q_batch_text}")
    print("Critic response received:")
    # print(critic_response_text)

    # Process results
    for q in new_questions_data:
        pattern = rf"\b{q['question_number']}\b\s*[:\-]?\s*(VERIFIED|NOT_FOUND)"
        match = re.search(pattern, critic_response_text, re.IGNORECASE)
        if match and "VERIFIED" in match.group(1).upper():
            q["is_verified"] = True
        else:
            q["is_verified"] = False

    # Combine and save
    all_questions = existing_questions + new_questions_data
    output_data = {"questions": all_questions}
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Successfully added {len(new_questions_data)} questions. Total: {len(all_questions)}. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main_async())
