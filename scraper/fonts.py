import re
from bs4 import BeautifulSoup

def extract_fonts(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    families = set()

    # From <style> blocks
    for style_tag in soup.find_all("style"):
        text = style_tag.get_text()
        found = re.findall(r'font-family\s*:\s*([^;}{]+)', text, re.IGNORECASE)
        for f in found:
            primary = f.split(",")[0].strip().strip('"\'')
            if primary:
                families.add(primary)

    # From inline styles
    for tag in soup.find_all(style=True):
        found = re.findall(r'font-family\s*:\s*([^;]+)', tag["style"], re.IGNORECASE)
        for f in found:
            primary = f.split(",")[0].strip().strip('"\'')
            if primary:
                families.add(primary)

    # From Google Fonts link tags
    google_fonts = []
    for link in soup.find_all("link", href=True):
        href = link["href"]
        if "fonts.googleapis.com" in href:
            matches = re.findall(r'family=([^&:]+)', href)
            google_fonts += [m.replace("+", " ") for m in matches]

    return {
        "unique_families": sorted(list(families)),
        "google_fonts": list(set(google_fonts)),
    }
