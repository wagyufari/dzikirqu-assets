#!/usr/bin/env python3
"""
converter.py
- Imports hadith collections and hadiths (eng/ara/ind) into SQLite.
- Creates hadithSection rows from hadith metadata (sections).
- Inserts subsections as separate rows in hadithSection, linked to their parent
  via the 'parentSectionId' column.
- Counts and updates the number of subsections for each parent section.
- Loads summaries from summary/(language)-(bookname)-summarized.json files.
"""

import os
import json
import sqlite3
from glob import glob

# ----------------------------
# Helpers / Detection
# ----------------------------

def get_hadith_data_lang(filename: str):
    if filename.startswith("ara-"):
        return "arabic"
    if filename.startswith("eng-"):
        return "english"
    if filename.startswith("ind-"):
        return "bahasa"
    return None

def get_collection_info_lang(filename: str):
    if filename == "eng-collections.json":
        return "english"
    if filename == "ind-collections.json":
        return "bahasa"
    return None

def get_collection_id(name: str):
    name = name.lower().replace("_", "").replace("-", "").replace(" ", "").replace("'", "")
    if "bukhari" in name:
        return 1
    if "muslim" in name:
        return 2
    if "abudawud" in name or "abidaud" in name or "abidawood" in name:
        return 3
    if "tirmidhi" in name or "tirmidzi" in name:
        return 4
    if "nasai" in name or "annasai" in name:
        return 5
    if "ibnmajah" in name or "ibnumajah" in name or "ibnmajh" in name:
        return 6
    if "riyad" in name or "riyadus" in name or "riyadh" in name or "riyadussalihin" in name or "riyadussalihin" in name:
        return 10
    if "nawawi40" in name or "arbain" in name or "nawawi" in name or "arbainannawawi" in name:
        return 11
    return None

# ----------------------------
# Summary loading
# ----------------------------

def load_summaries(cid, lang):
    """Load summaries from summary/(language)-(bookname)-summarized.json"""
    # Map collection IDs to book names
    book_names = {
        1: "bukhari",
        2: "muslim",
        3: "abudawud",
        4: "tirmidhi",
        5: "nasai",
        6: "ibnmajah",
        10: "riyadussalihin",
        11: "nawawi40"
    }
    
    # Map language codes to prefixes
    lang_prefixes = {
        "english": "eng",
        "bahasa": "ind",
        "arabic": "ara"
    }
    
    if cid not in book_names or lang not in lang_prefixes:
        return {}
    
    book_name = book_names[cid]
    lang_prefix = lang_prefixes[lang]
    
    # Check multiple possible path patterns
    possible_paths = [
        f"summarized/{lang_prefix}-{book_name}-summarized.json",
        f"summarized/{lang_prefix}-{book_name}.json",
        f"{lang_prefix}-{book_name}-summarized.json"
    ]
    
    for summary_path in possible_paths:
        if os.path.exists(summary_path):
            try:
                with open(summary_path, "r", encoding="utf-8") as f:
                    summaries_list = json.load(f)
                
                # Create a mapping from hadithnumber to summary
                summary_map = {}
                for item in summaries_list:
                    hadith_num = item.get("hadithnumber") or item.get("id")
                    summary = item.get("summary", "")
                    if hadith_num and summary:
                        summary_map[str(hadith_num)] = summary
                
                print(f"✅ Loaded {len(summary_map)} summaries from {summary_path}")
                return summary_map
            except Exception as e:
                print(f"⚠️  Error loading summaries from {summary_path}: {e}")
    
    return {}

# ----------------------------
# DB: create tables
# ----------------------------

def create_tables(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hadithCollection (
            id INTEGER,
            language TEXT,
            title TEXT,
            author TEXT,
            realName TEXT,
            description TEXT,
            hadithCount INTEGER,
            PRIMARY KEY (id, language)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hadithData (
            collectionId INTEGER,
            id NUMERIC,
            arabicNumber NUMERIC,
            text TEXT,
            language TEXT,
            grades TEXT,
            reference TEXT,
            narration TEXT,
            tldr TEXT,
            narrator TEXT,
            summary TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hadithSection (
            collectionId INTEGER,
            sectionId TEXT,
            language TEXT,
            sectionTitle TEXT,
            hadithNumberFirst NUMERIC,
            hadithNumberLast NUMERIC,
            arabicNumberFirst NUMERIC,
            arabicNumberLast NUMERIC,
            parentSectionId TEXT,
            subsectionCount INTEGER
        )
    """)
    conn.commit()

# ----------------------------
# Collection info
# ----------------------------

def process_collection_info(path, lang, conn):
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    collections = data.get("kutub_al_sittah", [])
    cur = conn.cursor()
    for collection in collections:
        cid = get_collection_id(collection.get("book_name", ""))
        if not cid:
            continue
        cur.execute("""
            INSERT OR REPLACE INTO hadithCollection
            (id, language, title, author, realName, description, hadithCount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            cid, lang,
            collection.get("book_name"),
            collection.get("author"),
            collection.get("real_name"),
            collection.get("description"),
            collection.get("hadith_count")
        ))
    conn.commit()
    print(f"✅ Imported collection info: {os.path.basename(path)}")

# ----------------------------
# Hadith data + sections
# ----------------------------

def process_hadith_data(path, lang, conn):
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    basename = os.path.basename(path)
    cid = get_collection_id(basename)
    if not cid:
        print(f"⚠️  Skipped {basename} — could not determine collection ID")
        return

    # Load summaries for this collection and language
    summary_map = load_summaries(cid, lang)

    cur = conn.cursor()

    if isinstance(data, list):
        hadiths = data
        metadata = {}
    elif isinstance(data, dict):
        hadiths = data.get("hadiths", [])
        metadata = data.get("metadata", {})
    else:
        print(f"⚠️  Skipped {basename} — unknown JSON structure")
        return

    inserted = 0
    for h in hadiths:
        hadith_num = str(h.get("hadithnumber", ""))
        summary = summary_map.get(hadith_num, "")
        
        cur.execute("""
            INSERT INTO hadithData
            (collectionId, id, arabicNumber, text, language, grades, reference, narration, tldr, narrator, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cid,
            h.get("hadithnumber"),
            h.get("arabicnumber"),
            h.get("text", ""),
            lang,
            json.dumps(h.get("grades")),
            json.dumps(h.get("reference")),
            json.dumps(h.get("narration")),
            h.get("tldr"),
            h.get("narrator"),
            summary
        ))
        inserted += 1

    sections = metadata.get("sections", {})
    section_details = metadata.get("section_details", {})
    for sid, title in sections.items():
        d = section_details.get(sid, {}) if section_details else {}
        cur.execute("""
            INSERT INTO hadithSection
            (collectionId, sectionId, language, sectionTitle,
             hadithNumberFirst, hadithNumberLast, arabicNumberFirst, arabicNumberLast, parentSectionId, subsectionCount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
        """, (
            cid, str(sid), lang, title,
            d.get("hadithnumber_first"),
            d.get("hadithnumber_last"),
            d.get("arabicnumber_first"),
            d.get("arabicnumber_last"),
            None
        ))

    conn.commit()
    print(f"✅ Imported {inserted} hadiths and {len(sections)} sections from {basename}")

# ----------------------------
# Subsection processing
# ----------------------------

def process_subsection_file(path, conn):
    basename = os.path.basename(path)
    cid = get_collection_id(basename)
    if cid is None and basename.endswith("-subsection.json"):
        cid = get_collection_id(basename.replace("-subsection.json", ".json"))
    if cid is None:
        print(f"⚠️  Skipped subsection file {basename} — could not determine collection ID")
        return

    lang = get_hadith_data_lang(basename) or get_hadith_data_lang(basename.replace("-subsection", "")) or "unknown"

    with open(path, "r", encoding="utf-8") as f:
        subsections_list = json.load(f)

    cur = conn.cursor()
    inserted, skipped = 0, 0

    for sub in subsections_list:
        file_index = sub.get("fileIndex")
        section_title = sub.get("sectionTitle")
        h_first = sub.get("hadithNumberFirst")
        h_last = sub.get("hadithNumberLast")

        if h_first is None:
            print(f"  ⚠️  Skipping subsection missing hadithNumberFirst: {sub}")
            skipped += 1
            continue

        cur.execute("""
            SELECT sectionId
            FROM hadithSection
            WHERE collectionId = ?
              AND language = ?
              AND parentSectionId IS NULL
              AND hadithNumberFirst IS NOT NULL
              AND hadithNumberLast IS NOT NULL
              AND ? BETWEEN hadithNumberFirst AND hadithNumberLast
            LIMIT 1
        """, (cid, lang, h_first))
        row = cur.fetchone()

        parent_section_id = None
        if row:
            parent_section_id = row[0]
        else:
            cur.execute("""
                SELECT sectionId
                FROM hadithSection
                WHERE collectionId = ?
                  AND language = ?
                  AND parentSectionId IS NULL
                  AND ( ? <= hadithNumberLast AND ? >= hadithNumberFirst )
                LIMIT 1
            """, (cid, lang, h_last, h_first))
            row = cur.fetchone()
            if row:
                parent_section_id = row[0]

        if not parent_section_id:
            print(f"  ⚠️  No matching TOP-LEVEL section found for subsection {section_title} ({h_first}-{h_last}) in language '{lang}'")
            skipped += 1
            continue

        subsection_id = f"{parent_section_id}-{file_index}"

        cur.execute("""
            INSERT INTO hadithSection
            (collectionId, sectionId, language, sectionTitle,
             hadithNumberFirst, hadithNumberLast, parentSectionId)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            cid,
            subsection_id,
            lang,
            section_title,
            h_first,
            h_last,
            parent_section_id
        ))

        inserted += 1

    conn.commit()
    print(f"✅ Imported subsections from {basename} (inserted as new rows: {inserted}, skipped: {skipped})")


# ----------------------------
# Subsection count update
# ----------------------------

def update_subsection_counts(conn):
    cur = conn.cursor()
    # Calculate the count of children for each parent and update the parent sections
    cur.execute("""
        UPDATE hadithSection
        SET subsectionCount = (
            SELECT COUNT(T2.sectionId)
            FROM hadithSection AS T2
            WHERE T2.parentSectionId = hadithSection.sectionId
              AND T2.collectionId = hadithSection.collectionId
              AND T2.language = hadithSection.language
        )
        WHERE hadithSection.parentSectionId IS NULL
          AND hadithSection.collectionId IS NOT NULL
          AND hadithSection.language IS NOT NULL
    """)
    conn.commit()
    print("✅ Updated subsection counts for all parent sections.")


# ----------------------------
# Main flow
# ----------------------------

def main():
    json_files = sorted(glob("*.json"))
    subsection_files = sorted(glob("subsection/*.json"))

    if not json_files:
        print("No JSON files found in current directory.")
        return

    conn = sqlite3.connect("hadith0_19.sqlite")
    create_tables(conn)

    for path in json_files:
        name = os.path.basename(path)
        info_lang = get_collection_info_lang(name)
        lang = get_hadith_data_lang(name)

        if name.endswith("-subsection.json"):
            continue

        if info_lang:
            process_collection_info(path, info_lang, conn)
        elif lang:
            process_hadith_data(path, lang, conn)
        else:
            print(f"⚠️  Skipped unrecognized file: {name}")

    for path in subsection_files:
        name = os.path.basename(path)
        process_subsection_file(path, conn)


    update_subsection_counts(conn)

    conn.close()
    print("\n✅ All done. Database: hadith0_19.sqlite")

if __name__ == "__main__":
    main()