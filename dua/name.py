import json

# Load hisn.json
with open("hisn.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Ensure the root is a list of sections
sections = data if isinstance(data, list) else [data]

index = 0

for section in sections:
    name_items = section.get("name", [])
    for item in name_items:
        if item.get("language") == "bahasa":
            print(index, item.get("text"))
            index += 1


