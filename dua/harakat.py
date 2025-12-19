#!/usr/bin/env python3

import os
import json
import time
from pathlib import Path
from typing import Optional, Dict

import google.generativeai as genai

# --------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------

GEMINI_MODEL = "gemini-2.0-flash"   # or gemini-2.0-flash-lite if cheaper
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# --------------------------------------------------------------------
# Helper: call Gemini with retry (same pattern as translate.py)
# --------------------------------------------------------------------

def call_gemini_with_retry(prompt: str,
                           retries: int = 5,
                           delay: float = 2.0) -> str:
    """
    Calls Gemini with exponential-backoff retry.
    """
    for attempt in range(retries):
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            out = model.generate_content(prompt)
            return out.text.strip()

        except Exception as e:
            print(f"[WARN] Gemini error: {e} (attempt {attempt+1}/{retries})")
            time.sleep(delay)
            delay *= 1.8

    raise RuntimeError("Gemini failed after retries")

# --------------------------------------------------------------------
# MAIN: function to add harakat to Arabic text
# --------------------------------------------------------------------

def add_harakat(arabic_text: str) -> str:
    """
    Sends Arabic text to Gemini and requests fully diacritized version.
    """

    prompt = f"""
You are an expert in fully-correct Arabic diacritization.

TASK:
- Complete the harakat and fix incorrect ones to the following Arabic text.
- Keep the text EXACT; do not translate.
- Do not add explanations.
- Output only the diacritized Arabic.

TEXT:
{arabic_text}
"""

    return call_gemini_with_retry(prompt)

# --------------------------------------------------------------------
# Example batch processor for hisn.json (optional)
# --------------------------------------------------------------------

def process_hisn_json(input_path: str,
                      output_path: str):
    """
    Loads hisn.json, diacritizes all Arabic text entries,
    and saves hisn_harakat.json.
    """
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))

    for section in data:
        for row in section.get("data", []):
            for t in row.get("text", []):
                if t["language"] == "arabic":
                    original = t["text"]
                    print(f"→ Adding harakat: {original[:40]}...")
                    t["text"] = add_harakat(original)

    Path(output_path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved: {output_path}")


# --------------------------------------------------------------------
# Run directly
# --------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=False,
        default="hisn.json", help="Path to hisn.json")
    parser.add_argument("--output", required=False,
        default="hisn_harakat.json", help="Output JSON")

    args = parser.parse_args()

    process_hisn_json(args.input, args.output)