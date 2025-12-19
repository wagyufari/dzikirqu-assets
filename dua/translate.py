import json
import os
import time
from google import generativeai as genai

# Configure Gemini API
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

def translate_batch(texts, target_language, batch_size=10):
    """
    Translate multiple texts in a single API call
    
    Args:
        texts: List of texts to translate
        target_language: Target language ('english' or 'bahasa')
        batch_size: Number of texts to translate in one call
    
    Returns:
        List of translated texts
    """
    model = genai.GenerativeModel('gemini-flash-lite-latest')
    
    all_translations = []
    
    # Process in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        # Create numbered list for batch translation
        numbered_texts = "\n".join([f"{j+1}. {text}" for j, text in enumerate(batch)])
        
        if target_language == 'english':
            prompt = f"""Translate the following Arabic prayer texts to English. 
Provide ONLY the translations in the same numbered format, one per line.
Do not add any explanations, notes, or extra text.

{numbered_texts}"""
        elif target_language == 'bahasa':
            prompt = f"""Translate the following Arabic prayer texts to Bahasa Indonesia (Indonesian language).
Provide ONLY the translations in the same numbered format, one per line.
Do not add any explanations, notes, or extra text.

{numbered_texts}"""
        else:
            raise ValueError("target_language must be 'english' or 'bahasa'")
        
        try:
            response = model.generate_content(prompt)
            translations_text = response.text.strip()
            
            # Parse the numbered responses
            lines = translations_text.split('\n')
            batch_translations = []
            
            for line in lines:
                line = line.strip()
                if line:
                    # Remove number prefix if present
                    if '. ' in line:
                        parts = line.split('. ', 1)
                        if len(parts) > 1:
                            batch_translations.append(parts[1])
                        else:
                            batch_translations.append(line)
                    else:
                        batch_translations.append(line)
            
            # If we didn't get enough translations, pad with the original text
            while len(batch_translations) < len(batch):
                batch_translations.append(batch[len(batch_translations)])
            
            all_translations.extend(batch_translations[:len(batch)])
            
            # Small delay to avoid rate limiting
            if i + batch_size < len(texts):
                time.sleep(0.5)
                
        except Exception as e:
            print(f"  Error translating batch {i//batch_size + 1}: {e}")
            # Fall back to original texts for this batch
            all_translations.extend(batch)
    
    return all_translations

def collect_texts_to_translate(data):
    """
    Collect all Arabic texts that need translation
    
    Returns:
        Tuple of (texts_needing_english, texts_needing_bahasa, metadata)
        where metadata contains references to update the original data
    """
    english_needed = []
    bahasa_needed = []
    english_metadata = []
    bahasa_metadata = []
    
    for entry_idx, entry in enumerate(data):
        for prayer_idx, prayer in enumerate(entry['data']):
            # Get the Arabic text
            arabic_text = None
            for text_item in prayer['text']:
                if text_item['language'] == 'arabic':
                    arabic_text = text_item['text']
                    break
            
            if arabic_text:
                # Check if English translation needed
                has_english = any(t['language'] == 'english' for t in prayer['text'])
                if not has_english:
                    english_needed.append(arabic_text)
                    english_metadata.append((entry_idx, prayer_idx))
                
                # Check if Bahasa translation needed
                has_bahasa = any(t['language'] == 'bahasa' for t in prayer['text'])
                if not has_bahasa:
                    bahasa_needed.append(arabic_text)
                    bahasa_metadata.append((entry_idx, prayer_idx))
    
    return english_needed, bahasa_needed, english_metadata, bahasa_metadata

def process_hisn_json(input_file='hisn.json', output_file='hisn_translated.json', batch_size=10):
    """
    Process hisn.json file with batch translation
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
        batch_size: Number of texts to translate per API call
    """
    # Load the JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("Collecting texts to translate...")
    english_needed, bahasa_needed, english_metadata, bahasa_metadata = collect_texts_to_translate(data)
    
    print(f"Found {len(english_needed)} texts needing English translation")
    print(f"Found {len(bahasa_needed)} texts needing Bahasa translation")
    
    # Translate all English texts in batches
    if english_needed:
        print(f"\nTranslating to English in batches of {batch_size}...")
        english_translations = translate_batch(english_needed, 'english', batch_size)
        
        # Apply translations back to data
        for idx, (entry_idx, prayer_idx) in enumerate(english_metadata):
            data[entry_idx]['data'][prayer_idx]['text'].append({
                'language': 'english',
                'text': english_translations[idx]
            })
        print(f"✓ Completed {len(english_translations)} English translations")
    
    # Translate all Bahasa texts in batches
    if bahasa_needed:
        print(f"\nTranslating to Bahasa in batches of {batch_size}...")
        bahasa_translations = translate_batch(bahasa_needed, 'bahasa', batch_size)
        
        # Apply translations back to data
        for idx, (entry_idx, prayer_idx) in enumerate(bahasa_metadata):
            data[entry_idx]['data'][prayer_idx]['text'].append({
                'language': 'bahasa',
                'text': bahasa_translations[idx]
            })
        print(f"✓ Completed {len(bahasa_translations)} Bahasa translations")
    
    # Save the updated JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Translation complete! Output saved to {output_file}")
    print(f"  Total translations: {len(english_needed) + len(bahasa_needed)}")
    print(f"  API calls made: ~{(len(english_needed) + len(bahasa_needed) + batch_size - 1) // batch_size}")

if __name__ == '__main__':
    # Check if GEMINI_API_KEY is set
    if not os.environ.get('GEMINI_API_KEY'):
        print("Error: GEMINI_API_KEY environment variable is not set")
        exit(1)
    
    # You can adjust batch_size here (default is 10)
    process_hisn_json(batch_size=10)