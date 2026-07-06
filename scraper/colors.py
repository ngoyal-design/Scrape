import re
from bs4 import BeautifulSoup

def extract_colors(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    colors = set()

    # From inline style attributes
    for tag in soup.find_all(style=True):
        hex_found = re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}\b', tag["style"])
        colors.update(hex_found)

    # From <style> blocks
    for style_tag in soup.find_all("style"):
        text = style_tag.get_text()
        hex_found = re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}\b', text)
        colors.update(hex_found)
        rgb_found = re.findall(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', text)
        for r, g, b in rgb_found:
            colors.add(f"#{int(r):02x}{int(g):02x}{int(b):02x}")

    # From linked CSS (skip external, just parse what's in the page)
    common_skip = {"#000", "#fff", "#000000", "#ffffff", "#333", "#666", "#999", "#ccc", "#eee"}
    filtered = sorted([c.lower() for c in colors if c.lower() not in common_skip])

    return {
        "unique_colors": filtered[:20],
    }
