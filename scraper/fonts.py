import re
from bs4 import BeautifulSoup

SYSTEM_FONTS = {
    "sans-serif", "serif", "monospace", "cursive", "fantasy",
    "-apple-system", "blinkmacsystemfont", "system-ui",
    "segoe ui", "helvetica neue", "helvetica", "arial",
    "times new roman", "georgia", "verdana", "tahoma",
}

def is_real_font(name: str) -> bool:
    return name.lower().strip().strip('"\'') not in SYSTEM_FONTS

def extract_fonts(html: str, computed: dict, raw_css: str) -> dict:
    families = {}
    seen = set()

    # Method 1: Computed styles (what the browser actually renders — most accurate)
    for el, props in computed.items():
        family_str = props.get("fontFamily", "")
        if not family_str:
            continue
        primary = family_str.split(",")[0].strip().strip('"\'')
        if primary and primary not in seen:
            seen.add(primary)
            families[primary] = {
                "source":     "computed",
                "element":    el,
                "size":       props.get("fontSize"),
                "weight":     props.get("fontWeight"),
                "lineHeight": props.get("lineHeight"),
            }

    # Method 2: Google Fonts links
    soup = BeautifulSoup(html, "lxml")
    google_fonts = []
    for link in soup.find_all("link", href=True):
        href = link["href"]
        if "fonts.googleapis.com" in href:
            matches = re.findall(r'family=([^&:|\)]+)', href)
            for m in matches:
                name = m.replace("+", " ").split(":")[0].strip()
                google_fonts.append(name)
                if name not in seen:
                    seen.add(name)
                    families[name] = {"source": "google_fonts"}

    # Method 3: @font-face declarations
    custom_fonts = re.findall(
        r'@font-face\s*\{[^}]*font-family\s*:\s*["\']?([^"\';\}]+)',
        raw_css, re.IGNORECASE
    )
    for f in custom_fonts:
        name = f.strip().strip('"\'')
        if name and name not in seen:
            seen.add(name)
            families[name] = {"source": "font-face"}

    # Method 4: CSS font-family rules
    css_fonts = re.findall(r'font-family\s*:\s*([^;}{]+)', raw_css, re.IGNORECASE)
    for f in css_fonts:
        primary = f.split(",")[0].strip().strip('"\'')
        if primary and primary not in seen:
            seen.add(primary)
            families[primary] = {"source": "css"}

    # Filter: separate brand fonts from system fonts
    brand_fonts   = [f for f in families if is_real_font(f)]
    system_fonts  = [f for f in families if not is_real_font(f)]

    return {
        "unique_families": sorted(list(families.keys())),
        "brand_fonts":     brand_fonts,
        "system_fonts":    system_fonts,
        "google_fonts":    list(set(google_fonts)),
        "font_details":    families,
    }
