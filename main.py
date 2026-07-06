from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
from scraper.colors import extract_colors
from scraper.fonts import extract_fonts
from scraper.assets import extract_assets
from scraper.meta import extract_meta
from scraper.social import extract_social_links

app = FastAPI(title="Branding Scraper API", version="1.0")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

class ScrapeRequest(BaseModel):
    url: str
    include_colors: bool = True
    include_fonts: bool = True
    include_assets: bool = True
    include_social: bool = True

async def fetch_page(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
        response = await client.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.text

@app.get("/")
def health():
    return {"status": "Branding Scraper is running!"}

@app.post("/execute")
async def execute_for_glean(request: ScrapeRequest):
    """Glean-compatible flat endpoint."""
    url = request.url
    if not url.startswith("http"):
        url = "https://" + url
    try:
        html = await fetch_page(url)
        colors_data = extract_colors(html)
        fonts_data  = extract_fonts(html)
        assets_data = extract_assets(html, url)
        meta_data   = extract_meta(html, url)
        social_data = extract_social_links(html, url)
        return {
            "status":         "success",
            "url":            url,
            "site_title":     meta_data.get("title"),
            "theme_color":    meta_data.get("theme_color"),
            "primary_colors": ", ".join(colors_data["unique_colors"][:6]),
            "font_families":  ", ".join(fonts_data["unique_families"]),
            "logo_url":       (assets_data.get("logos") or [None])[0],
            "favicon":        assets_data.get("favicon"),
            "og_image":       assets_data.get("og_image"),
            "social_links":   ", ".join(f"{k}: {v}" for k, v in social_data["found"].items()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape")
async def scrape_full(url: str):
    """Full detail endpoint."""
    if not url.startswith("http"):
        url = "https://" + url
    try:
        html = await fetch_page(url)
        return JSONResponse(content={
            "url":          url,
            "meta":         extract_meta(html, url),
            "colors":       extract_colors(html),
            "fonts":        extract_fonts(html),
            "assets":       extract_assets(html, url),
            "social_links": extract_social_links(html, url),
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
