import json
import os
import time
from google import generativeai as genai

# Configure Gemini API
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

def split_arabic_text_batch(texts, batch_size=10):
    """
    Split multiple Arabic texts with ✦ separators using Gemini API
    
    Args:
        texts: List of Arabic texts to split
        batch_size: Number of texts to process in one API call
    
    Returns:
        List of split Arabic texts with ✦ separators
    """
    model = genai.GenerativeModel('gemini-flash-lite-latest')
    
    all_split_texts = []
    
    # Process in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        # Create numbered list for batch processing
        numbered_texts = "\n".join([f"{j+1}. {text}" for j, text in enumerate(batch)])
        
        prompt = f"""Split the following Arabic prayer texts into readable phrases by inserting the ✦ symbol between natural phrase breaks.

Rules:
- Insert ✦ between meaningful phrase boundaries (not after every word)
- Keep phrases that naturally go together
- Aim for 3-5 words per phrase typically
- Maintain the original Arabic text exactly, only add ✦ symbols
- Provide ONLY the split texts in the same numbered format, one per line
- Do not add explanations, notes, or extra text

Examples:
Input: اَلْحَمْـدُ لِلَّهِ الَّذِي أَحْـيَانَا بَعْـدَ مَا أَمَاتَـنَا وَإِلَيْهِ النُّـشُورُ
Output: اَلْحَمْـدُ لِلَّهِ ✦ الَّذِي أَحْـيَانَا ✦ بَعْـدَ مَا أَمَاتَـنَا ✦ وَإِلَيْهِ النُّـشُورُ

Now split these texts:

{numbered_texts}"""
        
        try:
            response = model.generate_content(prompt)
            split_texts = response.text.strip()
            
            # Parse the numbered responses
            lines = split_texts.split('\n')
            batch_results = []
            
            for line in lines:
                line = line.strip()
                if line:
                    # Remove number prefix if present
                    if '. ' in line:
                        parts = line.split('. ', 1)
                        if len(parts) > 1:
                            batch_results.append(parts[1])
                        else:
                            batch_results.append(line)
                    else:
                        batch_results.append(line)
            
            # If we didn't get enough results, use original text
            while len(batch_results) < len(batch):
                batch_results.append(batch[len(batch_results)])
            
            all_split_texts.extend(batch_results[:len(batch)])
            
            # Small delay to avoid rate limiting
            if i + batch_size < len(texts):
                time.sleep(0.5)
                
        except Exception as e:
            print(f"  Error splitting batch {i//batch_size + 1}: {e}")
            # Fall back to original texts for this batch
            all_split_texts.extend(batch)
    
    return all_split_texts

def collect_arabic_texts(data):
    """
    Collect all Arabic texts that need splitting
    
    Returns:
        Tuple of (arabic_texts, metadata) where metadata contains 
        references to update the original data
    """
    arabic_texts = []
    metadata = []
    
    for entry_idx, entry in enumerate(data):
        for prayer_idx, prayer in enumerate(entry['data']):
            # Find the Arabic text
            for text_idx, text_item in enumerate(prayer['text']):
                if text_item['language'] == 'arabic':
                    arabic_texts.append(text_item['text'])
                    metadata.append((entry_idx, prayer_idx, text_idx))
                    break
    
    return arabic_texts, metadata

def process_hisn_json(input_file='hisn.json', output_file='hisn_split.json', batch_size=10):
    """
    Process hisn.json file to split Arabic texts with ✦ separators
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
        batch_size: Number of texts to process per API call
    """
    # Load the JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("Collecting Arabic texts to split...")
    arabic_texts, metadata = collect_arabic_texts(data)
    
    print(f"Found {len(arabic_texts)} Arabic texts to process")
    
    # Split all Arabic texts in batches
    if arabic_texts:
        print(f"\nSplitting Arabic texts in batches of {batch_size}...")
        split_texts = split_arabic_text_batch(arabic_texts, batch_size)
        
        # Apply split texts back to data
        for idx, (entry_idx, prayer_idx, text_idx) in enumerate(metadata):
            data[entry_idx]['data'][prayer_idx]['text'][text_idx]['text'] = split_texts[idx]
        
        print(f"✓ Completed splitting {len(split_texts)} Arabic texts")
    
    # Save the updated JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Splitting complete! Output saved to {output_file}")
    print(f"  Total texts processed: {len(arabic_texts)}")
    print(f"  API calls made: ~{(len(arabic_texts) + batch_size - 1) // batch_size}")

if __name__ == '__main__':
    # Check if GEMINI_API_KEY is set
    if not os.environ.get('GEMINI_API_KEY'):
        print("Error: GEMINI_API_KEY environment variable is not set")
        print("Please set it with: export GEMINI_API_KEY='your-api-key'")
        exit(1)
    
    # You can adjust batch_size here (default is 10)
    # Larger batches = fewer API calls but may be less accurate
    process_hisn_json(batch_size=10)