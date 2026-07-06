from bs4 import BeautifulSoup

def extract_meta(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    return {
        "title":           soup.title.string.strip() if soup.title else None,
        "description":     (soup.find("meta", attrs={"name": "description"}) or {}).get("content"),
        "og_title":        (soup.find("meta", property="og:title") or {}).get("content"),
        "og_description":  (soup.find("meta", property="og:description") or {}).get("content"),
        "twitter_card":    (soup.find("meta", attrs={"name": "twitter:card"}) or {}).get("content"),
        "theme_color":     (soup.find("meta", attrs={"name": "theme-color"}) or {}).get("content"),
    }
