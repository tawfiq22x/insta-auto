import re
with open('ldplayer_automation.py', 'r') as f:
    content = f.read()

target = """            match = re.search(pattern, xml_str, re.IGNORECASE)
            if match:
                x1, y1, x2, y2 = map(int, match.groups())
                cy = (y1 + y2) // 2
                if cy >= min_y and (max_y is None or cy <= max_y):
                    return ((x1 + x2) // 2, cy)"""

replacement = """            matches = re.finditer(pattern, xml_str, re.IGNORECASE)
            valid_matches = []
            for match in matches:
                x1, y1, x2, y2 = map(int, match.groups())
                cy = (y1 + y2) // 2
                area = (x2 - x1) * (y2 - y1)
                if cy >= min_y and (max_y is None or cy <= max_y) and area > 0:
                    valid_matches.append(((x1 + x2) // 2, cy, area))
            if valid_matches:
                valid_matches.sort(key=lambda x: x[2])
                return (valid_matches[0][0], valid_matches[0][1])"""

content = content.replace(target, replacement)
with open('ldplayer_automation.py', 'w') as f:
    f.write(content)
print("Patched regex fallback!")
