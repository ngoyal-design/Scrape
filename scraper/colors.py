import re
import io
from PIL import Image
from colorthief import ColorThief
from bs4 import BeautifulSoup

SKIP_COLORS = {
    "#000000", "#ffffff", "#000", "#fff",
    "#333333", "#666666", "#999999", "#cccccc",
    "#eeeeee", "#f0f0f0", "#333", "#666", "#999", "#ccc", "#eee",
}

def rgb_to_hex(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"

def normalize_color(color_str: str) -> str:
    if not color_str:
        return ""
    rgb = re.match(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', color_str)
    if rgb:
        return rgb_to_hex(int(rgb[1]), int(rgb[2]), int(rgb[3]))
    if color_str.startswith("#"):
        c = color_str.lower()
        if len(c) == 4:  # expand #rgb → #rrggbb
            c = "#" + c[1]*2 + c[2]*2 + c[3]*2
        return c
    return color_str

def is_useful_color(hex_color: str) -> bool:
    if not hex_color or not hex_color.startswith("#"):
        return False
    if hex_color.lower() in SKIP_COLORS:
        return False
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        # Skip near-white (all channels > 240)
        if r > 240 and g > 240 and b > 240:
            return False
        # Skip near-black (all channels < 20)
        if r < 20 and g < 20 and b < 20:
            return False
        # Skip near-grey (channels within 10 of each other)
        if abs(r - g) < 10 and abs(g - b) < 10 and abs(r - b) < 10:
            return False
    except Exception:
        return False
    return True

def extract_screenshot_colors(screenshot_bytes: bytes, count: int = 8) -> list:
    """Use ColorThief to extract dominant colors from the actual rendered screenshot."""
    try:
        img_io = io.BytesIO(screenshot_bytes)
        ct = ColorThief(img_io)
        palette = ct.get_palette(color_count=count + 2, quality=5)
        colors = []
        for rgb in palette:
            hex_color = rgb_to_hex(*rgb)
            if is_useful_color(hex_color):
                colors.append(hex_color)
        return colors[:count]
    except Exception:
        return []

def extract_computed_colors(computed: dict) -> list:
    """Extract colors from browser-computed styles (most accurate)."""
    colors = set()
    for el, props in computed.items():
        for key in ["color", "backgroundColor"]:
            val = props.get(key, "")
            if val and val not in ("", "transparent", "rgba(0, 0, 0, 0)", "rgba(0,0,0,0)"):
                c = normalize_color(val)
                if is_useful_color(c):
                    colors.add(c)
    return list(colors)

def extract_css_var_colors(css_vars: dict) -> list:
    """Extract colors from CSS custom properties (design tokens)."""
    colors = []
    for key, val in css_vars.items():
        val = val.strip()
        if re.match(r'^#[0-9a-fA-F]{3,8}$', val):
            c = normalize_color(val)
            if is_useful_color(c):
                colors.append(c)
        elif re.match(r'^rgba?\(', val):
            c = normalize_color(val)
            if is_useful_color(c):
                colors.append(c)
    return colors

def extract_raw_css_colors(raw_css: str) -> list:
    """Extract hex colors from raw CSS text."""
    hex_colors = re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}\b', raw_css)
    colors = set()
    for c in hex_colors:
        normalized = normalize_color(c)
        if is_useful_color(normalized):
            colors.add(normalized)
    return list(colors)

def extract_colors(html: str, computed: dict, css_vars: dict, raw_css: str, screenshot_bytes: bytes) -> dict:
    # Method 1: Screenshot pixel analysis (most accurate — like a color picker)
    screenshot_colors = extract_screenshot_colors(screenshot_bytes)

    # Method 2: Browser computed styles (exact rendered values)
    computed_colors = extract_computed_colors(computed)

    # Method 3: CSS design tokens / variables
    var_colors = extract_css_var_colors(css_vars)

    # Method 4: Raw CSS hex values (fallback)
    raw_colors = extract_raw_css_colors(raw_css)

    # Merge all, prioritize screenshot + computed (most reliable)
    seen = set()
    primary = []
    for c in screenshot_colors + computed_colors:
        if c not in seen:
            seen.add(c)
            primary.append(c)

    all_colors = list(primary)
    for c in var_colors + raw_colors:
        if c not in seen:
            seen.add(c)
            all_colors.append(c)

    return {
        "primary_colors":    primary[:8],
        "all_colors":        all_colors[:20],
        "screenshot_colors": screenshot_colors,
        "computed_colors":   computed_colors,
        "css_var_colors":    var_colors,
        "element_colors": {
            el: {
                "text":       normalize_color(props.get("color", "")),
                "background": normalize_color(props.get("backgroundColor", "")),
            }
            for el, props in computed.items()
        }
    }
