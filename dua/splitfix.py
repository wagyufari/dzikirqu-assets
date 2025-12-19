#!/usr/bin/env python3
import json

INPUT_FILE = "hisn.json"
OUTPUT_FILE = "hisn_split_cleaned.json"

def process_text_array(text_list):
    arabic_item = None
    arabic_split_item = None

    # Identify arabic + arabic_split items
    for item in text_list:
        if item.get("language") == "arabic":
            arabic_item = item
        elif item.get("language") == "arabic_split":
            arabic_split_item = item

    # Replace Arabic text if both exist
    if arabic_item and arabic_split_item:
        arabic_item["text"] = arabic_split_item["text"]

    # Remove all arabic_split entries
    text_list = [item for item in text_list if item.get("language") != "arabic_split"]

    return text_list


def process_file(data):
    for section in data:
        for dua in section.get("data", []):
            if "text" in dua:
                dua["text"] = process_text_array(dua["text"])
    return data


def main():
    print("📥 Loading JSON...")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("🔧 Replacing Arabic text and removing arabic_split entries...")

    updated = process_file(data)

    print("💾 Saving to:", OUTPUT_FILE)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(updated, f, ensure_ascii=False, indent=2)

    print("✅ Done! Arabic text replaced and arabic_split removed.")


if __name__ == "__main__":
    main()