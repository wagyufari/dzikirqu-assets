import json
import os
import time
import google.generativeai as genai
from typing import Dict, Tuple, Optional
from tqdm import tqdm
from datetime import datetime

# =====================
# Gemini Setup
# =====================
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel(
    model_name="gemini-flash-lite-latest",
    generation_config={
        "temperature": 0,
        "top_p": 1,
        "max_output_tokens": 50,
    }
)

# =====================
# Configuration
# =====================
INPUT_FILE = "uthmani.json"
OUTPUT_FILE = "uthmani_classified_dua_only.json"
CHECKPOINT_FILE = "classification_checkpoint.json"
CHECKPOINT_INTERVAL = 50  # Save checkpoint every N verses
LOG_FILE = "classification_log.txt"

# =====================
# Checkpoint Management
# =====================
def save_checkpoint(data: dict, processed_keys: list, stats: dict):
    """Save progress checkpoint"""
    checkpoint = {
        "timestamp": datetime.now().isoformat(),
        "processed_keys": processed_keys,
        "stats": stats,
        "last_key": processed_keys[-1] if processed_keys else None
    }
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    
    # Also save partial results
    with open(f"{OUTPUT_FILE}.temp", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_checkpoint() -> Optional[dict]:
    """Load checkpoint if exists"""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Warning: Could not load checkpoint: {e}")
    return None

def log_message(message: str):
    """Append message to log file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

# =====================
# Prompt Builder
# =====================
def build_prompt(ayah_text: str) -> str:
    return f"""
You are classifying a Qur'anic ayah.

Definition:
- Du'a: direct supplication or request made to Allah.

Rules:
- Respond ONLY in valid JSON.
- Use lowercase true/false.
- No explanations.

Ayah (Arabic):
"{ayah_text}"

Return format:
{{
  "contains_dua": true|false
}}
""".strip()

# =====================
# Gemini Call with Retry
# =====================
def classify_ayah(text: str, max_retries: int = 3) -> Tuple[Dict[str, bool], bool]:
    """Returns (result_dict, success_flag)"""
    for attempt in range(max_retries):
        try:
            response = model.generate_content(build_prompt(text))
            result = json.loads(response.text)
            
            if "contains_dua" in result:
                return {"contains_dua": result["contains_dua"]}, True
            else:
                raise ValueError("Missing 'contains_dua' key in response.")

        except (json.JSONDecodeError, ValueError) as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            log_message(f"ERROR: Classification failed - {str(e)}")
            return {"contains_dua": False}, False
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            log_message(f"ERROR: Unexpected error - {str(e)}")
            return {"contains_dua": False}, False
    
    return {"contains_dua": False}, False

# =====================
# Main Processing
# =====================
def main():
    print("=" * 70)
    print("🤲 Qur'an Ayah Du'a Classification System (Enhanced)")
    print("=" * 70)
    
    # Initialize log
    log_message("=" * 50)
    log_message("NEW CLASSIFICATION SESSION STARTED")
    log_message("=" * 50)
    
    # Load data
    print(f"\n📂 Loading {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {INPUT_FILE} not found!")
        log_message(f"FATAL ERROR: {INPUT_FILE} not found!")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: {INPUT_FILE} is not valid JSON!")
        log_message(f"FATAL ERROR: {INPUT_FILE} is not valid JSON!")
        return
    
    total_verses = len(data)
    verse_keys = list(data.keys())
    print(f"✅ Loaded {total_verses} verses\n")
    log_message(f"Loaded {total_verses} verses from {INPUT_FILE}")
    
    # Check for checkpoint
    checkpoint = load_checkpoint()
    processed_keys = []
    start_index = 0
    
    stats = {
        "total": total_verses,
        "processed": 0,
        "skipped_empty": 0,
        "dua_found": 0,
        "errors": 0,
        "start_time": datetime.now().isoformat()
    }
    
    if checkpoint:
        print(f"📍 Checkpoint found from {checkpoint['timestamp']}")
        print(f"   Last processed: {checkpoint.get('last_key', 'N/A')}")
        response = input("   Resume from checkpoint? (y/n): ").strip().lower()
        
        if response == 'y':
            processed_keys = checkpoint["processed_keys"]
            stats.update(checkpoint["stats"])
            start_index = len(processed_keys)
            print(f"✅ Resuming from verse #{start_index + 1}/{total_verses}\n")
            log_message(f"RESUMED from checkpoint at verse {start_index + 1}")
        else:
            print("🔄 Starting fresh classification\n")
            log_message("User chose to start fresh")
            if os.path.exists(CHECKPOINT_FILE):
                os.remove(CHECKPOINT_FILE)
    else:
        print("🔄 Starting fresh classification\n")
        log_message("No checkpoint found - starting fresh")
    
    # Progress bar with enhanced info
    remaining = total_verses - start_index
    pbar = tqdm(
        total=remaining,
        initial=0,
        desc="🔍 Classifying",
        unit="ayah",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] Du'a: {postfix}"
    )
    pbar.set_postfix_str(f"{stats['dua_found']}")
    
    try:
        for i in range(start_index, total_verses):
            verse_key = verse_keys[i]
            verse = data[verse_key]
            ayah_text = verse.get("text", "").strip()
            
            # Handle empty text
            if not ayah_text:
                verse["contains_dua"] = False
                stats["skipped_empty"] += 1
                processed_keys.append(verse_key)
                tqdm.write(f"  ⚠️  {verse_key}: EMPTY | Skipped")
                log_message(f"SKIPPED (empty): {verse_key}")
                pbar.update(1)
                continue
            
            # Classify
            result, success = classify_ayah(ayah_text)
            
            # Store result
            verse["contains_dua"] = result["contains_dua"]
            
            if not success:
                verse["classification_error"] = "Failed after retries"
                stats["errors"] += 1
            
            # Update statistics
            stats["processed"] += 1
            if result["contains_dua"]:
                stats["dua_found"] += 1
            
            processed_keys.append(verse_key)
            
            # Print result
            icon = "✨" if result["contains_dua"] else "❌"
            status = "Du'a" if result["contains_dua"] else "No Du'a"
            error_indicator = " [ERROR]" if not success else ""
            progress_info = f"[{i+1}/{total_verses}]"
            tqdm.write(f"  {icon} {progress_info} {verse_key}: {status}{error_indicator} | {ayah_text[:45]}...")
            
            # Log significant events
            if result["contains_dua"]:
                log_message(f"DUA FOUND: {verse_key}")
            if not success:
                log_message(f"ERROR: {verse_key} - Classification failed")
            
            # Update progress bar postfix
            pbar.set_postfix_str(f"{stats['dua_found']}")
            pbar.update(1)
            
            # Checkpoint save
            if (i + 1) % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(data, processed_keys, stats)
                tqdm.write(f"  💾 Checkpoint saved at verse {i+1}/{total_verses}")
                log_message(f"CHECKPOINT: Saved at verse {i+1}")
            
            # Rate limiting
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user!")
        print("💾 Saving checkpoint...")
        save_checkpoint(data, processed_keys, stats)
        log_message("INTERRUPTED: User stopped process, checkpoint saved")
        print("✅ Checkpoint saved. Run again to resume.\n")
        pbar.close()
        return
    
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        print("💾 Saving emergency checkpoint...")
        save_checkpoint(data, processed_keys, stats)
        log_message(f"FATAL ERROR: {str(e)} - Emergency checkpoint saved")
        pbar.close()
        return
    
    pbar.close()
    
    # Save final results
    print(f"\n💾 Saving final results to {OUTPUT_FILE}...")
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✅ Results saved successfully!")
        log_message(f"SUCCESS: Final results saved to {OUTPUT_FILE}")
        
        # Clean up checkpoint files
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
        if os.path.exists(f"{OUTPUT_FILE}.temp"):
            os.remove(f"{OUTPUT_FILE}.temp")
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        log_message(f"ERROR: Could not save final results - {str(e)}")
        return
    
    # Calculate elapsed time
    if "start_time" in stats:
        start = datetime.fromisoformat(stats["start_time"])
        elapsed = datetime.now() - start
        elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
    else:
        elapsed_str = "N/A"
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 CLASSIFICATION SUMMARY")
    print("=" * 70)
    print(f"Total verses:           {stats['total']}")
    print(f"Successfully processed: {stats['processed']}")
    print(f"Skipped (empty):        {stats['skipped_empty']}")
    print(f"Errors:                 {stats['errors']}")
    print(f"\n🤲 Du'a found:           {stats['dua_found']} ({stats['dua_found']/stats['total']*100:.1f}%)")
    print(f"⏱️  Time elapsed:         {elapsed_str}")
    print("=" * 70)
    print(f"\n📝 Log saved to: {LOG_FILE}")
    print("✅ Classification completed successfully!\n")
    
    log_message(f"COMPLETED: {stats['dua_found']} Du'as found in {elapsed_str}")
    log_message("=" * 50)

if __name__ == "__main__":
    main()