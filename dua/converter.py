#!/usr/bin/env python3
"""
Convert hisn.json -> prayers.sqlite

A Python rewrite of dua-converter.js, following the same logic:
 - Loads local hisn.json
 - Creates SQLite DB with two tables:
      prayerSection(id, language, name)
      prayerData(id, section_id, language, text, source, repetition, headnote, footnote)
 - Inserts multi-language section names and prayers exactly like dua-converter.js
"""

import json
import sqlite3
from pathlib import Path
import sys

INPUT_JSON = Path("hisn.json")
OUTPUT_DB = Path("dua0_32.sqlite")


def create_tables(conn: sqlite3.Connection):
    """Create the same schema used in dua-converter.js."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prayerSection (
            id INTEGER NOT NULL,
            language TEXT NOT NULL,
            name TEXT NOT NULL,
            "order" INTEGER NOT NULL,
            PRIMARY KEY (id, language)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prayerData (
            id INTEGER NOT NULL,
            section_id INTEGER NOT NULL,
            language TEXT NOT NULL,
            text TEXT NOT NULL,
            source TEXT,
            repetition INTEGER,
            headnote TEXT,
            footnote TEXT,
            PRIMARY KEY (id, language),
            FOREIGN KEY (section_id) REFERENCES prayerSection(id)
        );
    """)

    conn.commit()


def insert_section(conn, section_id, section):
    cursor = conn.cursor()

    for name_obj in section["name"]:
        cursor.execute("""
            INSERT OR IGNORE INTO prayerSection (id, language, name, "order")
            VALUES (?, ?, ?, ?)
        """, (
            section_id,
            name_obj["language"],
            name_obj["text"],
            section["order"]
        ))

    conn.commit()


def insert_prayers(conn: sqlite3.Connection, section_id: int, prayers, starting_prayer_id: int):
    """Insert prayers per language and return next prayer ID."""
    cursor = conn.cursor()
    prayer_id = starting_prayer_id

    for prayer in prayers:
        # Gather text by language
        text_map = {
            entry["language"]: entry["text"]
            for entry in prayer.get("text", [])
        }

        # Serialize JSON fields as strings (dua-converter.js does the same)
        source_json = json.dumps(prayer.get("source", []), ensure_ascii=False)
        headnote_json = json.dumps(prayer.get("headnote", []), ensure_ascii=False)
        footnote_json = json.dumps(prayer.get("footnote", []), ensure_ascii=False)
        repetition = prayer.get("repetition")

        for lang, text in text_map.items():
            cursor.execute("""
                INSERT INTO prayerData
                (id, section_id, language, text, source, repetition, headnote, footnote)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                prayer_id,
                section_id,
                lang,
                text,
                source_json,
                repetition,
                headnote_json,
                footnote_json
            ))

        prayer_id += 1

    conn.commit()
    return prayer_id


def convert(input_path: Path, output_path: Path):
    if not input_path.exists():
        print(f"❌ ERROR: Cannot find JSON file: {input_path}")
        sys.exit(1)

    print(f"📥 Loading {input_path} ...")
    data = json.loads(input_path.read_text("utf-8"))

    conn = sqlite3.connect(output_path)
    create_tables(conn)

    print("📦 Inserting sections and prayers...")

    section_id = 1
    prayer_id = 1

    for section in data:
        insert_section(conn, section_id, section)
        prayer_id = insert_prayers(conn, section_id, section.get("data", []), prayer_id)
        section_id += 1

    conn.close()

    print("✅ Conversion complete!")
    print(f"📄 Output database: {output_path}")
    print(f"📊 Total sections: {section_id - 1}")
    print(f"🙏 Total prayers: {prayer_id - 1}")


if __name__ == "__main__":
    convert(INPUT_JSON, OUTPUT_DB)