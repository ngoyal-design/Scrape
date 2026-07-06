from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from playwright.async_api import async_playwright
from scraper.colors import extract_colors
from scraper.fonts import extract_fonts
from scraper.assets import extract_assets
from scraper.meta import extract_meta
from scraper.social import extract_social_links

app = FastAPI(title="Branding Scraper API v2", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    url: str
    include_colors: bool = True
    include_fonts: bool = True
    include_assets: bool = True
    include_social: bool = True

async def render_page(url: str):
    """Use a real headless browser to fully render the page."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
        except Exception:
            # Fallback: try with domcontentloaded if networkidle times out
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)

        await page.wait_for_timeout(2000)  # Let JS settle

        html = await page.content()

        # Screenshot for pixel-based color extraction
        screenshot_bytes = await page.screenshot(full_page=False, type="png")

        # Computed styles of key elements (actual rendered colors + fonts)
        computed = await page.evaluate("""
            () => {
                const selectors = ['body','h1','h2','h3','p','a','button','nav','header','footer','.btn','[class*="btn"]','[class*="primary"]'];
                const result = {};
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el) {
                        const s = window.getComputedStyle(el);
                        result[sel] = {
                            fontFamily:      s.fontFamily,
                            fontSize:        s.fontSize,
                            fontWeight:      s.fontWeight,
                            color:           s.color,
                            backgroundColor: s.backgroundColor,
                            lineHeight:      s.lineHeight,
                        };
                    }
                }
                return result;
            }
        """)

        # CSS variables from :root (design tokens)
        css_vars = await page.evaluate("""
            () => {
                const s = getComputedStyle(document.documentElement);
                const vars = {};
                for (const prop of s) {
                    if (prop.startsWith('--')) {
                        vars[prop] = s.getPropertyValue(prop).trim();
                    }
                }
                return vars;
            }
        """)

        # All inline + embedded CSS text
        raw_css = await page.evaluate("""
            () => {
                const sheets = [];
                for (const sheet of document.styleSheets) {
                    try {
                        const rules = Array.from(sheet.cssRules || []).map(r => r.cssText).join('\\n');
                        sheets.push(rules);
                    } catch (e) {}
                }
                return sheets.join('\\n');
            }
        """)

        await browser.close()

    return html, screenshot_bytes, computed, css_vars, raw_css


@app.get("/")
def health():
    return {"status": "Branding Scraper v2 is running!"}


@app.post("/execute")
async def execute_for_glean(request: ScrapeRequest):
    url = request.url
    if not url.startswith("http"):
        url = "https://" + url
    try:
        html, screenshot_bytes, computed, css_vars, raw_css = await render_page(url)
        colors_data = extract_colors(html, computed, css_vars, raw_css, screenshot_bytes)
        fonts_data  = extract_fonts(html, computed, raw_css)
        assets_data = extract_assets(html, url)
        meta_data   = extract_meta(html, url)
        social_data = extract_social_links(html, url)
        return {
            "status":           "success",
            "url":              url,
            "site_title":       meta_data.get("title"),
            "theme_color":      meta_data.get("theme_color"),
            "primary_colors":   ", ".join(colors_data["primary_colors"]),
            "all_colors":       ", ".join(colors_data["all_colors"][:10]),
            "screenshot_colors":  ", ".join(colors_data["screenshot_colors"]),
            "font_families":    ", ".join(fonts_data["unique_families"]),
            "google_fonts":     ", ".join(fonts_data["google_fonts"]),
            "logo_url":         (assets_data.get("logos") or [None])[0],
            "favicon":          assets_data.get("favicon"),
            "og_image":         assets_data.get("og_image"),
            "social_links":     ", ".join(f"{k}: {v}" for k, v in social_data["found"].items()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape")
async def scrape_full(url: str):
    if not url.startswith("http"):
        url = "https://" + url
    try:
        html, screenshot_bytes, computed, css_vars, raw_css = await render_page(url)
        return JSONResponse(content={
            "url":          url,
            "meta":         extract_meta(html, url),
            "colors":       extract_colors(html, computed, css_vars, raw_css, screenshot_bytes),
            "fonts":        extract_fonts(html, computed, raw_css),
            "assets":       extract_assets(html, url),
            "social_links": extract_social_links(html, url),
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
