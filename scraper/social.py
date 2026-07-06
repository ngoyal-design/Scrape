from bs4 import BeautifulSoup
import re

SOCIAL_PATTERNS = {
    "facebook":  r"(facebook\.com/(?!sharer|share|dialog)[^\s\"'?#]+)",
    "instagram": r"(instagram\.com/[^\s\"'?#/]+)",
    "twitter":   r"((?:twitter|x)\.com/(?!intent|share)[^\s\"'?#/]+)",
    "linkedin":  r"(linkedin\.com/(?:company|in)/[^\s\"'?#/]+)",
    "youtube":   r"(youtube\.com/(?:@|channel/|c/)[^\s\"'?#]+)",
    "tiktok":    r"(tiktok\.com/@[^\s\"'?#/]+)",
    "pinterest": r"(pinterest\.com/[^\s\"'?#/]+)",
    "github":    r"(github\.com/[^\s\"'?#/]+)",
    "discord":   r"(discord\.(?:gg|com/invite)/[^\s\"'?#/]+)",
    "whatsapp":  r"(wa\.me/[^\s\"'?#/]+)",
    "telegram":  r"(t\.me/[^\s\"'?#/]+)",
    "threads":   r"(threads\.net/@[^\s\"'?#/]+)",
}

def extract_social_links(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    found = {}
    all_hrefs = [a.get("href", "") for a in soup.find_all("a", href=True)]
    raw_text = str(soup)

    for platform, pattern in SOCIAL_PATTERNS.items():
        matches = set()
        for href in all_hrefs:
            m = re.search(pattern, href, re.IGNORECASE)
            if m:
                url = m.group(1)
                if not url.startswith("http"):
                    url = "https://" + url
                matches.add(url)
        if not matches:
            for m in re.finditer(pattern, raw_text, re.IGNORECASE):
                url = m.group(1)
                if not url.startswith("http"):
                    url = "https://" + url
                matches.add(url)
        if matches:
            found[platform] = sorted(matches, key=len)[0]

    return {
        "found":              found,
        "count":              len(found),
        "platforms_detected": list(found.keys()),
    }
