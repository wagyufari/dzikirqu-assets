#!/usr/bin/env python3
"""
reverse_converter.py
- Exports hadith collections and hadiths from SQLite back to JSON files.
- Recreates the original file structure with separate files per language.
- Exports subsections to separate subsection/*.json files.
- Extracts summaries to summary/(language)-(bookname)-summarized.json files.
"""

import os
import json
import sqlite3
from collections import defaultdict

# ----------------------------
# Mapping helpers
# ----------------------------

COLLECTION_NAMES = {
    1: "bukhari",
    2: "muslim",
    3: "abudawud",
    4: "tirmidhi",
    5: "nasai",
    6: "ibnmajah",
    10: "riyadussalihin",
    11: "nawawi40"
}

LANG_PREFIXES = {
    "english": "eng",
    "bahasa": "ind",
    "arabic": "ara"
}

# ----------------------------
# Export collection info
# ----------------------------

def export_collection_info(conn):
    """Export collection metadata to eng-collections.json and ind-collections.json"""
    cur = conn.cursor()
    
    for lang in ["english", "bahasa"]:
        cur.execute("""
            SELECT id, title, author, realName, description, hadithCount
            FROM hadithCollection
            WHERE language = ?
            ORDER BY id
        """, (lang,))
        
        collections = []
        for row in cur.fetchall():
            collections.append({
                "book_name": row[1],
                "author": row[2],
                "real_name": row[3],
                "description": row[4],
                "hadith_count": row[5]
            })
        
        if collections:
            prefix = LANG_PREFIXES.get(lang, lang[:3])
            filename = f"{prefix}-collections.json"
            data = {"kutub_al_sittah": collections}
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Exported {filename} ({len(collections)} collections)")

# ----------------------------
# Export hadith data
# ----------------------------

def export_hadith_data(conn):
    """Export hadiths with metadata (sections) back to JSON files"""
    cur = conn.cursor()
    
    # Get all unique collection/language combinations
    cur.execute("""
        SELECT DISTINCT collectionId, language
        FROM hadithData
        ORDER BY collectionId, language
    """)
    
    combinations = cur.fetchall()
    
    for cid, lang in combinations:
        book_name = COLLECTION_NAMES.get(cid)
        if not book_name:
            print(f"⚠️  Unknown collection ID {cid}, skipping")
            continue
        
        prefix = LANG_PREFIXES.get(lang, lang[:3])
        filename = f"{prefix}-{book_name}.json"
        
        # Fetch hadiths
        cur.execute("""
            SELECT id, arabicNumber, text, grades, reference, narration, tldr, narrator
            FROM hadithData
            WHERE collectionId = ? AND language = ?
            ORDER BY id
        """, (cid, lang))
        
        hadiths = []
        for row in cur.fetchall():
            hadith = {
                "hadithnumber": row[0],
                "arabicnumber": row[1],
                "text": row[2]
            }
            
            # Parse JSON fields
            if row[3]:  # grades
                try:
                    hadith["grades"] = json.loads(row[3])
                except:
                    hadith["grades"] = row[3]
            
            if row[4]:  # reference
                try:
                    hadith["reference"] = json.loads(row[4])
                except:
                    hadith["reference"] = row[4]
            
            if row[5]:  # narration
                try:
                    hadith["narration"] = json.loads(row[5])
                except:
                    hadith["narration"] = row[5]
            
            if row[6]:  # tldr
                hadith["tldr"] = row[6]
            
            if row[7]:  # narrator
                hadith["narrator"] = row[7]
            
            hadiths.append(hadith)
        
        # Fetch sections (parent sections only)
        cur.execute("""
            SELECT sectionId, sectionTitle, hadithNumberFirst, hadithNumberLast,
                   arabicNumberFirst, arabicNumberLast
            FROM hadithSection
            WHERE collectionId = ? AND language = ? AND parentSectionId IS NULL
            ORDER BY sectionId
        """, (cid, lang))
        
        sections = {}
        section_details = {}
        
        for row in cur.fetchall():
            sid = row[0]
            sections[sid] = row[1]
            section_details[sid] = {
                "hadithnumber_first": row[2],
                "hadithnumber_last": row[3],
                "arabicnumber_first": row[4],
                "arabicnumber_last": row[5]
            }
        
        # Build output structure
        output = {
            "hadiths": hadiths,
            "metadata": {
                "sections": sections,
                "section_details": section_details
            }
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Exported {filename} ({len(hadiths)} hadiths, {len(sections)} sections)")

# ----------------------------
# Export subsections
# ----------------------------

def export_subsections(conn):
    """Export subsections to subsection/*.json files"""
    os.makedirs("subsection", exist_ok=True)
    
    cur = conn.cursor()
    
    # Get all unique collection/language combinations with subsections
    cur.execute("""
        SELECT DISTINCT collectionId, language
        FROM hadithSection
        WHERE parentSectionId IS NOT NULL
        ORDER BY collectionId, language
    """)
    
    combinations = cur.fetchall()
    
    for cid, lang in combinations:
        book_name = COLLECTION_NAMES.get(cid)
        if not book_name:
            continue
        
        prefix = LANG_PREFIXES.get(lang, lang[:3])
        filename = f"subsection/{prefix}-{book_name}-subsection.json"
        
        # Fetch subsections
        cur.execute("""
            SELECT sectionId, sectionTitle, hadithNumberFirst, hadithNumberLast, parentSectionId
            FROM hadithSection
            WHERE collectionId = ? AND language = ? AND parentSectionId IS NOT NULL
            ORDER BY sectionId
        """, (cid, lang))
        
        subsections = []
        for row in cur.fetchall():
            # Extract fileIndex from sectionId (format: "parentId-fileIndex")
            section_id = row[0]
            file_index = section_id.split("-")[-1] if "-" in section_id else "0"
            
            subsections.append({
                "fileIndex": file_index,
                "sectionTitle": row[1],
                "hadithNumberFirst": row[2],
                "hadithNumberLast": row[3]
            })
        
        if subsections:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(subsections, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Exported {filename} ({len(subsections)} subsections)")

# ----------------------------
# Export summaries
# ----------------------------

def export_summaries(conn):
    """Export summaries to summarized/(language)-(bookname)-summarized.json files"""
    os.makedirs("summarized", exist_ok=True)
    
    cur = conn.cursor()
    
    # Get all unique collection/language combinations with summaries
    cur.execute("""
        SELECT DISTINCT collectionId, language
        FROM hadithData
        WHERE summary IS NOT NULL AND summary != ''
        ORDER BY collectionId, language
    """)
    
    combinations = cur.fetchall()
    
    for cid, lang in combinations:
        book_name = COLLECTION_NAMES.get(cid)
        if not book_name:
            continue
        
        prefix = LANG_PREFIXES.get(lang, lang[:3])
        filename = f"summarized/{prefix}-{book_name}-summarized.json"
        
        # Fetch hadiths with summaries
        cur.execute("""
            SELECT id, summary
            FROM hadithData
            WHERE collectionId = ? AND language = ? AND summary IS NOT NULL AND summary != ''
            ORDER BY id
        """, (cid, lang))
        
        summaries = []
        for row in cur.fetchall():
            summaries.append({
                "hadithnumber": row[0],
                "summary": row[1]
            })
        
        if summaries:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(summaries, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Exported {filename} ({len(summaries)} summaries)")

# ----------------------------
# Main flow
# ----------------------------

def main():
    db_path = "hadith1_0.sqlite"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    
    print("Exporting collection info...")
    export_collection_info(conn)
    
    print("\nExporting hadith data...")
    export_hadith_data(conn)
    
    print("\nExporting subsections...")
    export_subsections(conn)
    
    print("\nExporting summaries...")
    export_summaries(conn)
    
    conn.close()
    print("\n✅ All done. JSON files exported successfully!")

if __name__ == "__main__":
    main()