import json

with open("hisn.json") as f:
    data = json.load(f)

for i, section in enumerate(data):
    for j, prayer in enumerate(section.get("data", [])):
        if isinstance(prayer, list):
            print(f"❌ Section {i} prayer {j} is a list, expected an object")
