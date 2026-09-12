with open('ldplayer_automation.py', 'r') as f:
    content = f.read()

target = """                    if matched:
                        bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                        if len(bounds_match) == 2:
                            x1, y1 = int(bounds_match[0][0]), int(bounds_match[0][1])
                            x2, y2 = int(bounds_match[1][0]), int(bounds_match[1][1])
                            cx = (x1 + x2) // 2
                            cy = (y1 + y2) // 2
                            if cy >= min_y and (max_y is None or cy <= max_y):
                                candidates.append((cx, cy, clickable))
                                break
            if candidates:
                if prefer_clickable:
                    clickables = [c for c in candidates if c[2]]
                    if clickables:
                        return (clickables[0][0], clickables[0][1])
                return (candidates[0][0], candidates[0][1])"""

replacement = """                    if matched:
                        bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                        if len(bounds_match) == 2:
                            x1, y1 = int(bounds_match[0][0]), int(bounds_match[0][1])
                            x2, y2 = int(bounds_match[1][0]), int(bounds_match[1][1])
                            cx = (x1 + x2) // 2
                            cy = (y1 + y2) // 2
                            area = (x2 - x1) * (y2 - y1)
                            if cy >= min_y and (max_y is None or cy <= max_y) and area > 0:
                                candidates.append((cx, cy, clickable, area))
                                break
            if candidates:
                candidates.sort(key=lambda x: x[3]) # Sort by smallest area first
                if prefer_clickable:
                    clickables = [c for c in candidates if c[2]]
                    if clickables:
                        return (clickables[0][0], clickables[0][1])
                return (candidates[0][0], candidates[0][1])"""

content = content.replace(target, replacement)
with open('ldplayer_automation.py', 'w') as f:
    f.write(content)
print("Patched find text coords!")
