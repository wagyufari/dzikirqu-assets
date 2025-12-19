import requests
from bs4 import BeautifulSoup
import json
import re
import time

def clean_text(text):
    """Remove extra whitespace and clean text"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())

def scrape_chapter(chapter_num):
    """Scrape a single chapter"""
    url = f"http://www.hisnulmuslim.com/index-page-chapitre-id_chapitre-{chapter_num}-lang-en.html"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get chapter title
        h2 = soup.find('h2')
        if not h2:
            return None
        
        chapter_title = clean_text(h2.text).replace(f'Chapter {chapter_num} - ', '')
        
        # Find all content sections
        middle_div = soup.find('div', id='middle')
        if not middle_div:
            return None
        
        # Extract invocations
        invocations = []
        
        # Find all <strong> tags that indicate invocation numbers
        strongs = middle_div.find_all('strong')
        
        for strong in strongs:
            try:
                invoc_num = strong.text.strip()
                if not invoc_num.isdigit():
                    continue
                
                # Get English translation (next text after <strong>)
                english_text = ""
                current = strong.next_sibling
                while current:
                    if isinstance(current, str):
                        text = clean_text(current)
                        if text and text != '-':
                            english_text = text.strip('"').strip()
                            break
                    current = current.next_sibling
                
                if not english_text:
                    continue
                
                # Get Arabic text (in <p class="txt_ar">)
                arabic_p = strong.find_next('p', class_='txt_ar')
                arabic_text = ""
                if arabic_p:
                    arabic_text = clean_text(arabic_p.text)
                
                # Get transliteration (in <p class="txt_trans">)
                trans_p = strong.find_next('p', class_='txt_trans')
                trans_text = ""
                if trans_p:
                    trans_text = clean_text(trans_p.text)
                
                # Build invocation object
                invocation = {
                    "number": int(invoc_num),
                    "text": []
                }
                
                if arabic_text:
                    invocation["text"].append({
                        "language": "arabic",
                        "text": arabic_text
                    })
                
                if english_text:
                    invocation["text"].append({
                        "language": "english",
                        "text": english_text
                    })
                
                if trans_text:
                    invocation["text"].append({
                        "language": "transliteration",
                        "text": trans_text
                    })
                
                if invocation["text"]:
                    invocations.append(invocation)
                    
            except Exception as e:
                print(f"Error parsing invocation in chapter {chapter_num}: {e}")
                continue
        
        if not invocations:
            return None
        
        # Build chapter object
        chapter = {
            "chapter": chapter_num,
            "name": [
                {
                    "text": chapter_title,
                    "language": "english"
                }
            ],
            "data": invocations
        }
        
        return chapter
        
    except Exception as e:
        print(f"Error scraping chapter {chapter_num}: {e}")
        return None

def scrape_all_chapters(start=2, end=132):
    """Scrape all chapters"""
    all_chapters = []
    
    for i in range(start, end + 1):
        print(f"Scraping chapter {i}...")
        chapter = scrape_chapter(i)
        
        if chapter:
            all_chapters.append(chapter)
            print(f"✓ Chapter {i}: {chapter['name'][0]['text']} ({len(chapter['data'])} invocations)")
        else:
            print(f"✗ Chapter {i}: Failed or empty")
        
        # Be respectful to the server
        time.sleep(1)
    
    return all_chapters

def save_to_json(data, filename='hisnulmuslim.json'):
    """Save data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nData saved to {filename}")

if __name__ == "__main__":
    print("Hisnulmuslim Web Scraper")
    print("=" * 50)
    
    # Scrape all chapters
    chapters = scrape_all_chapters(2, 132)
    
    print(f"\nTotal chapters scraped: {len(chapters)}")
    
    # Save to JSON
    save_to_json(chapters)
    
    # Print sample
    if chapters:
        print("\nSample output (first chapter):")
        print(json.dumps(chapters[0], ensure_ascii=False, indent=2))