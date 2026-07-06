from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extract_assets(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")

    # Favicon
    favicon = None
    icon_link = soup.find("link", rel=lambda r: r and "icon" in r)
    if icon_link:
        favicon = urljoin(base_url, icon_link.get("href", ""))

    # OG Image
    og_image = None
    og_tag = soup.find("meta", property="og:image")
    if og_tag:
        og_image = og_tag.get("content")

    # Logo images
    logos = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "").lower()
        cls = " ".join(img.get("class", [])).lower()
        if any(k in alt + src + cls for k in ["logo", "brand", "mark"]):
            logos.append(urljoin(base_url, src))

    # All images (top 20)
    all_images = list(set(
        urljoin(base_url, img.get("src", ""))
        for img in soup.find_all("img") if img.get("src")
    ))

    return {
        "favicon":    favicon,
        "og_image":   og_image,
        "logos":      logos[:5],
        "all_images": all_images[:20],
    }
