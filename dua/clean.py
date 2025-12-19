import json

def ensure_arabic_text(obj):
    """
    Recursively checks for all 'text' arrays in the object.
    If an Arabic entry is missing, inserts an empty Arabic entry.
    """

    if isinstance(obj, dict):
        # If this dict contains a "text" list
        if "text" in obj and isinstance(obj["text"], list):
            has_arabic = any(item.get("language") == "arabic" for item in obj["text"])
            if not has_arabic:
                obj["text"].insert(0, {"language": "arabic", "text": ""})

        # Continue scanning nested dictionaries
        for value in obj.values():
            ensure_arabic_text(value)

    elif isinstance(obj, list):
        # Scan list contents
        for item in obj:
            ensure_arabic_text(item)


# ---------- Run on your JSON file -------------

# Load file
with open("hisn.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Process
ensure_arabic_text(data)

# Save back
with open("hisn.updated.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done: Arabic entries ensured.")
