import json
import os
import re
import asyncio
import argparse
import time
from typing import List, Dict, Any, Optional, Tuple
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
OUTPUT_FILE = "app/data/output_generated_questions.json"
REFERENCE_FILE = "app/data/output.json"
MODEL_NAME = "gemini-flash-latest"

class Option(BaseModel):
    option_letter: str
    option_text: str

class Question(BaseModel):
    file_name: str
    question: str
    question_number: str
    options: List[Option]
    answer_letter: str
    source_quote: str = ""
    is_verified: bool = False

def read_source_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def get_chunks(text: str, chunk_size: int = 5000, overlap: int = 500) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

async def run_with_agent(agent: Agent, prompt: str) -> Tuple[str, Dict[str, Any]]:
    start_time = time.perf_counter()
    runner = Runner(
        app_name="InMemoryRunner",
        agent=agent,
        session_service=InMemorySessionService(),
        artifact_service=InMemoryArtifactService(),
        memory_service=InMemoryMemoryService(),
        auto_create_session=True
    )
    response_text = ""
    usage_metadata = {}
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
        
        if hasattr(event, "usage_metadata") and event.usage_metadata:
            usage_metadata = {
                "prompt_token_count": getattr(event.usage_metadata, "prompt_token_count", 0),
                "candidates_token_count": getattr(event.usage_metadata, "candidates_token_count", 0),
                "total_token_count": getattr(event.usage_metadata, "total_token_count", 0),
            }

    duration = time.perf_counter() - start_time
    return response_text, {"duration": round(duration, 2), "usage": usage_metadata}

async def main_async(chapter: int, count: int):
    if not os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY") == "YOUR_API_KEY_HERE":
        print("Please set your GOOGLE_API_KEY in the .env file.")
        return

    source_file = f"src/extraction/chapter{chapter}.txt"
    if not os.path.exists(source_file):
        print(f"Error: Source file {source_file} not found.")
        return

    # Load existing questions
    existing_generated = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                existing_generated = data.get("questions", [])
        except Exception: pass

    existing_reference = []
    if os.path.exists(REFERENCE_FILE):
        try:
            with open(REFERENCE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                existing_reference = data.get("questions", [])
        except Exception: pass

    # Build a lookup set for normalized question text (Optimization 1)
    existing_lookup = {re.sub(r'\W+', '', q["question"]).lower() for q in existing_generated + existing_reference}
    print(f"DEBUG: Initialized duplicate lookup with {len(existing_lookup)} questions.")

    # Determine starting question number
    start_num = 1
    if existing_generated:
        try:
            nums = [int(q["question_number"]) for q in existing_generated if q["question_number"].isdigit()]
            if nums: start_num = max(nums) + 1
        except Exception: start_num = len(existing_generated) + 1

    source_text = read_source_text(source_file)
    chunks = get_chunks(source_text) # Optimization 2
    print(f"DEBUG: Split chapter into {len(chunks)} chunks.")

    new_questions_total = []
    chunk_idx = 0
    
    while len(new_questions_total) < count and chunk_idx < len(chunks):
        current_chunk = chunks[chunk_idx]
        questions_needed = count - len(new_questions_total)
        batch_size = min(10, questions_needed) # Generate in batches of 10 max
        
        print(f"\n--- Processing Chunk {chunk_idx+1}/{len(chunks)} (Batch: {batch_size}) ---")
        
        generator = Agent(
            name="generator",
            model=MODEL_NAME,
            instruction=f"""
            You are an expert at creating citizenship test questions.
            Based on the provided text chunk from 'Chapter {chapter}', generate {batch_size} NEW multiple-choice questions.
            
            Rules:
            1. Each question must have 2 or 3 options.
            2. Only one option must be correct.
            3. The questions should be in Danish.
            4. Follow the JSON structure exactly.
            5. IMPORTANT: Include a 'source_quote' field containing the EXACT sentence from the text that proves the answer.
            6. Set 'file_name' to 'chapter{chapter}'.
            """
        )

        gen_resp, gen_stats = await run_with_agent(generator, f"Text chunk:\n{current_chunk}\n\nGenerate {batch_size} questions.")
        print(f"Generation took {gen_stats['duration']}s ({gen_stats['usage'].get('total_token_count', 0)} tokens)")

        json_match = re.search(r'\{.*\}', gen_resp, re.DOTALL)
        if not json_match:
            print("Failed to parse JSON. Skipping chunk.")
            chunk_idx += 1
            continue

        try:
            raw_batch = json.loads(json_match.group()).get("questions", [])
        except Exception:
            chunk_idx += 1
            continue

        # LOCAL DUPLICATE FILTERING (Optimization 1)
        valid_batch = []
        for q in raw_batch:
            norm_q = re.sub(r'\W+', '', q["question"]).lower()
            if norm_q not in existing_lookup:
                q["question_number"] = str(start_num + len(new_questions_total) + len(valid_batch))
                existing_lookup.add(norm_q)
                valid_batch.append(q)
            else:
                print(f"DEBUG: Filtered out duplicate: {q['question'][:50]}...")

        if not valid_batch:
            chunk_idx += 1
            continue

        # CRITIC VERIFICATION (Optimization 3 - Quote based)
        critic = Agent(
            name="critic",
            model=MODEL_NAME,
            instruction="""
            You are a fact-checker. You will be given a question, an answer, and a source quote.
            Verify if the source quote explicitly supports the answer to the question.
            Reply with the question number and either 'VERIFIED' or 'NOT_FOUND'.
            """
        )

        critic_prompt = "\n\n".join([
            f"Num: {q['question_number']}\nQ: {q['question']}\nAns: {q['answer_letter']}\nQuote: {q['source_quote']}" 
            for q in valid_batch
        ])
        
        print(f"Verifying {len(valid_batch)} questions using source quotes...")
        critic_resp, critic_stats = await run_with_agent(critic, critic_prompt)
        print(f"Verification took {critic_stats['duration']}s ({critic_stats['usage'].get('total_token_count', 0)} tokens)")

        for q in valid_batch:
            pattern = rf"\b{q['question_number']}\b\s*[:\-]?\s*(VERIFIED|NOT_FOUND)"
            match = re.search(pattern, critic_resp, re.IGNORECASE)
            # Hallucination check: Quote must exist in chunk
            if q['source_quote'] in current_chunk and match and "VERIFIED" in match.group(1).upper():
                q["is_verified"] = True
                new_questions_total.append(q)
            else:
                print(f"DEBUG: Question #{q['question_number']} failed verification or quote hallucinated.")

        chunk_idx += 1

    # Combine and save
    final_list = existing_generated + new_questions_total[:count]
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"questions": final_list}, f, indent=2, ensure_ascii=False)

    print(f"\nDONE: Added {len(new_questions_total[:count])} questions. Total: {len(final_list)}. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimized question generator.")
    parser.add_argument("--chapter", type=int, default=1, choices=range(1, 7), help="Chapter number (1-6)")
    parser.add_argument("--count", type=int, default=20, help="Number of questions to generate")
    args = parser.parse_args()
    asyncio.run(main_async(args.chapter, args.count))
