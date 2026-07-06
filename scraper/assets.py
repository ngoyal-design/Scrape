from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extract_assets(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")

    # Favicon (multiple fallback locations)
    favicon = None
    for rel in [["shortcut icon"], ["icon"], ["apple-touch-icon"]]:
        icon_link = soup.find("link", rel=rel)
        if not icon_link:
            icon_link = soup.find("link", rel=lambda r: r and any(x in r for x in ["icon"]))
        if icon_link and icon_link.get("href"):
            favicon = urljoin(base_url, icon_link["href"])
            break

    # OG Image (social share preview)
    og_image = None
    for prop in ["og:image", "twitter:image", "twitter:image:src"]:
        tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        if tag and tag.get("content"):
            og_image = tag["content"]
            break

    # Logo detection — multiple strategies
    logos = []

    # Strategy 1: img with logo in alt/src/class/id
    for img in soup.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "").lower()
        cls = " ".join(img.get("class", [])).lower()
        img_id = img.get("id", "").lower()
        if any(k in alt + src + cls + img_id for k in ["logo", "brand", "wordmark", "logotype"]):
            full_url = urljoin(base_url, src)
            if full_url not in logos:
                logos.append(full_url)

    # Strategy 2: SVG elements with logo-related class/id
    for svg in soup.find_all("svg"):
        cls = " ".join(svg.get("class", [])).lower()
        svg_id = svg.get("id", "").lower()
        if any(k in cls + svg_id for k in ["logo", "brand"]):
            logos.append("(inline SVG logo detected)")

    # Strategy 3: <a> tags linking to homepage often wrap the logo
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if href in ["/", "#", base_url]:
            img = a.find("img")
            if img and img.get("src"):
                full_url = urljoin(base_url, img["src"])
                if full_url not in logos:
                    logos.append(full_url)

    # All images (deduplicated, top 20)
    all_images = list(dict.fromkeys(
        urljoin(base_url, img.get("src", ""))
        for img in soup.find_all("img") if img.get("src")
    ))

    return {
        "favicon":    favicon,
        "og_image":   og_image,
        "logos":      logos[:5],
        "all_images": all_images[:20],
    }
