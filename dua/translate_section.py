import json
import os
import time
from google import generativeai as genai

# Configure Gemini API
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

def translate_section_names(section_names, target_language, batch_size=10):
    """
    Translate section names in a single API call
    
    Args:
        section_names: List of section name texts to translate
        target_language: Target language ('bahasa' or 'transliteration')
        batch_size: Number of texts to translate in one call
    
    Returns:
        List of translated section names
    """
    model = genai.GenerativeModel('gemini-flash-lite-latest')
    
    all_translations = []
    
    # Process in batches
    for i in range(0, len(section_names), batch_size):
        batch = section_names[i:i + batch_size]
        
        # Create numbered list for batch translation
        numbered_texts = "\n".join([f"{j+1}. {text}" for j, text in enumerate(batch)])
        
        if target_language == 'bahasa':
            prompt = f"""Translate the following Islamic prayer section names from English to Bahasa Indonesia (Indonesian language).
These are titles/headings for different prayer occasions (e.g., "When waking up", "Before sleeping", etc.).
Provide ONLY the translations in the same numbered format, one per line.
Do not add any explanations, notes, or extra text.

{numbered_texts}"""
        elif target_language == 'transliteration':
            prompt = f"""Provide Arabic transliteration for the following Islamic prayer section names.
These are titles/headings for different prayer occasions (e.g., "When waking up", "Before sleeping", etc.).
Use standard Arabic transliteration conventions.
Provide ONLY the transliterations in the same numbered format, one per line.
Do not add any explanations, notes, or extra text.

{numbered_texts}"""
        else:
            raise ValueError("target_language must be 'bahasa' or 'transliteration'")
        
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
            if i + batch_size < len(section_names):
                time.sleep(0.5)
                
        except Exception as e:
            print(f"  Error translating batch {i//batch_size + 1}: {e}")
            # Fall back to original texts for this batch
            all_translations.extend(batch)
    
    return all_translations

def collect_section_names(data):
    """
    Collect all section names that need translation
    
    Returns:
        Tuple of (english_names, metadata)
        where metadata contains references to update the original data
    """
    english_names = []
    metadata = []
    
    for entry_idx, entry in enumerate(data):
        # Check if 'name' exists and has content
        if 'name' in entry and entry['name']:
            # Get the English name
            english_name = None
            for name_item in entry['name']:
                if name_item['language'] == 'english':
                    english_name = name_item['text']
                    break
            
            if english_name:
                english_names.append(english_name)
                metadata.append(entry_idx)
    
    return english_names, metadata

def process_section_names(input_file='hisn.json', output_file='hisn_sections_translated.json', batch_size=10):
    """
    Process hisn.json file to translate section names
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
        batch_size: Number of texts to translate per API call
    """
    # Load the JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("Collecting section names to translate...")
    english_names, metadata = collect_section_names(data)
    
    print(f"Found {len(english_names)} section names")
    print(f"Section names: {english_names}")
    
    # Translate to Bahasa
    if english_names:
        print(f"\nTranslating section names to Bahasa in batches of {batch_size}...")
        bahasa_translations = translate_section_names(english_names, 'bahasa', batch_size)
        
        # Apply translations back to data
        for idx, entry_idx in enumerate(metadata):
            # Check if bahasa translation already exists
            has_bahasa = any(n['language'] == 'bahasa' for n in data[entry_idx]['name'])
            if not has_bahasa:
                data[entry_idx]['name'].append({
                    'language': 'bahasa',
                    'text': bahasa_translations[idx]
                })
        print(f"✓ Completed {len(bahasa_translations)} Bahasa translations")
    
    # Translate to Transliteration
    if english_names:
        print(f"\nTranslating section names to Transliteration in batches of {batch_size}...")
        translit_translations = translate_section_names(english_names, 'transliteration', batch_size)
        
        # Apply translations back to data
        for idx, entry_idx in enumerate(metadata):
            # Check if transliteration already exists
            has_translit = any(n['language'] == 'transliteration' for n in data[entry_idx]['name'])
            if not has_translit:
                data[entry_idx]['name'].append({
                    'language': 'transliteration',
                    'text': translit_translations[idx]
                })
        print(f"✓ Completed {len(translit_translations)} Transliteration translations")
    
    # Save the updated JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Translation complete! Output saved to {output_file}")
    print(f"  Total section names translated: {len(english_names)}")
    print(f"  Languages added: Bahasa, Transliteration")

if __name__ == '__main__':
    # Check if GEMINI_API_KEY is set
    if not os.environ.get('GEMINI_API_KEY'):
        print("Error: GEMINI_API_KEY environment variable is not set")
        print("Please set it with: export GEMINI_API_KEY='your-api-key'")
        exit(1)
    
    # You can adjust batch_size here (default is 10)
    process_section_names(batch_size=10)