"""
collector.py
Colectează URL-uri de magazine online românești din surse publice.
Surse: Trusted.ro (catalog verificat), fallback la listă manuală.
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import re
from urllib.parse import urljoin, urlparse

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def fetch_page(url: str, timeout: int = 15) -> BeautifulSoup | None:
    """Descarcă o pagină și returnează obiectul BeautifulSoup sau None la eroare."""
    try:
        resp = SESSION.get(url, timeout=timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        print(f"  [EROARE collector] {url} → {e}")
        return None


def collect_from_trusted(max_pages: int = 5) -> list[dict]:
    """
    Extrage magazine din catalogul Trusted.ro.
    Returnează listă de dict: {name, url, source}.
    """
    stores = []
    base = "https://www.trusted.ro/magazine-online"

    for page in range(1, max_pages + 1):
        url = f"{base}?page={page}" if page > 1 else base
        print(f"  Trusted.ro pagina {page}...")
        soup = fetch_page(url)
        if not soup:
            break

        # Trusted.ro listează magazine în carduri cu link-uri externe
        for a_tag in soup.select("a[href]"):
            href = a_tag.get("href", "")
            # Filtrăm link-urile care duc spre magazine externe (nu intern pe trusted.ro)
            if (
                href.startswith("http")
                and "trusted.ro" not in href
                and is_valid_store_url(href)
            ):
                name = a_tag.get_text(strip=True) or urlparse(href).netloc
                entry = {
                    "name": name[:120],
                    "url": href.split("?")[0].rstrip("/"),
                    "source": "trusted.ro",
                }
                if entry["url"] not in [s["url"] for s in stores]:
                    stores.append(entry)

        time.sleep(1.5)

    return stores


def collect_from_gomag(max_pages: int = 3) -> list[dict]:
    """
    Extrage magazine din directorul public Gomag.ro (platforma de ecommerce).
    """
    stores = []
    base = "https://www.gomag.ro/magazine"

    for page in range(1, max_pages + 1):
        url = f"{base}/pagina-{page}" if page > 1 else base
        print(f"  Gomag.ro pagina {page}...")
        soup = fetch_page(url)
        if not soup:
            break

        for a_tag in soup.select("a[href]"):
            href = a_tag.get("href", "")
            if (
                href.startswith("http")
                and "gomag.ro" not in href
                and is_valid_store_url(href)
            ):
                name = a_tag.get_text(strip=True) or urlparse(href).netloc
                entry = {
                    "name": name[:120],
                    "url": href.split("?")[0].rstrip("/"),
                    "source": "gomag.ro",
                }
                if entry["url"] not in [s["url"] for s in stores]:
                    stores.append(entry)

        time.sleep(1.5)

    return stores


def collect_manual_seeds() -> list[dict]:
    """
    Listă de pornire cu magazine online românești mari și medii, verificate manual.
    Acoperă categorii diverse pentru testarea detectorului.
    """
    seeds = [
        {"name": "eMAG", "url": "https://www.emag.ro", "source": "manual"},
        {"name": "Altex", "url": "https://www.altex.ro", "source": "manual"},
        {"name": "Flanco", "url": "https://www.flanco.ro", "source": "manual"},
        {"name": "PCGarage", "url": "https://www.pcgarage.ro", "source": "manual"},
        {"name": "Quickmobile", "url": "https://www.quickmobile.ro", "source": "manual"},
        {"name": "Cel.ro", "url": "https://www.cel.ro", "source": "manual"},
        {"name": "Evomag", "url": "https://www.evomag.ro", "source": "manual"},
        {"name": "Vodafone RO", "url": "https://www.vodafone.ro", "source": "manual"},
        {"name": "Orange RO", "url": "https://www.orange.ro", "source": "manual"},
        {"name": "Telekom RO", "url": "https://www.telekom.ro", "source": "manual"},
        {"name": "Farmacia Tei", "url": "https://www.farmaciatei.ro", "source": "manual"},
        {"name": "Dr. Max", "url": "https://www.drmax.ro", "source": "manual"},
        {"name": "Catena", "url": "https://www.catena.ro", "source": "manual"},
        {"name": "Dedeman", "url": "https://www.dedeman.ro", "source": "manual"},
        {"name": "Leroy Merlin RO", "url": "https://www.leroymerlin.ro", "source": "manual"},
        {"name": "IKEA RO", "url": "https://www.ikea.com/ro", "source": "manual"},
        {"name": "F64", "url": "https://www.f64.ro", "source": "manual"},
        {"name": "SportVision", "url": "https://www.sportvision.ro", "source": "manual"},
        {"name": "Intersport RO", "url": "https://www.intersport.ro", "source": "manual"},
        {"name": "Decathlon RO", "url": "https://www.decathlon.ro", "source": "manual"},
        {"name": "Answear RO", "url": "https://www.answear.ro", "source": "manual"},
        {"name": "Zara RO", "url": "https://www.zara.com/ro", "source": "manual"},
        {"name": "H&M RO", "url": "https://www2.hm.com/ro_ro", "source": "manual"},
        {"name": "Elefant.ro", "url": "https://www.elefant.ro", "source": "manual"},
        {"name": "Carturesti", "url": "https://carturesti.ro", "source": "manual"},
        {"name": "Libris", "url": "https://www.libris.ro", "source": "manual"},
        {"name": "Freshful", "url": "https://www.freshful.ro", "source": "manual"},
        {"name": "Bringo", "url": "https://www.bringo.ro", "source": "manual"},
        {"name": "Glovo RO", "url": "https://glovoapp.com/ro", "source": "manual"},
        {"name": "Noriel", "url": "https://www.noriel.ro", "source": "manual"},
        {"name": "Lego RO", "url": "https://www.lego.com/ro-ro", "source": "manual"},
        {"name": "Vivre", "url": "https://www.vivre.ro", "source": "manual"},
        {"name": "Mobexpert", "url": "https://www.mobexpert.ro", "source": "manual"},
        {"name": "Diverta", "url": "https://www.diverta.ro", "source": "manual"},
        {"name": "Hervis RO", "url": "https://www.hervis.ro", "source": "manual"},
        {"name": "Sportisimo RO", "url": "https://www.sportisimo.ro", "source": "manual"},
        {"name": "Pandora RO", "url": "https://ro.pandora.net", "source": "manual"},
        {"name": "Swarovski RO", "url": "https://www.swarovski.com/ro-RO", "source": "manual"},
        {"name": "Fashion Days", "url": "https://www.fashiondays.ro", "source": "manual"},
        {"name": "eFashion", "url": "https://www.efashion.ro", "source": "manual"},
    ]
    return seeds


def is_valid_store_url(url: str) -> bool:
    """Filtrează URL-uri care nu sunt magazine (rețele sociale, CDN-uri etc.)."""
    blacklist = [
        "facebook.com", "instagram.com", "youtube.com", "twitter.com",
        "tiktok.com", "linkedin.com", "pinterest.com", "google.com",
        "cloudflare.com", "amazonaws.com", "googleapis.com",
        "w3.org", "schema.org", "jquery.com",
    ]
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    return not any(b in domain for b in blacklist) and bool(parsed.scheme in ("http", "https"))


def collect_all(use_web_sources: bool = True, max_pages: int = 3) -> list[dict]:
    """
    Punctul de intrare principal.
    Combină lista manuală cu sursele web și deduplicează după URL.
    """
    print("[COLLECTOR] Pornire colectare operatori economici...")
    all_stores = collect_manual_seeds()
    print(f"  {len(all_stores)} magazine din lista manuală.")

    if use_web_sources:
        print("  Colectare din Trusted.ro...")
        trusted = collect_from_trusted(max_pages=max_pages)
        print(f"  {len(trusted)} magazine găsite pe Trusted.ro.")
        all_stores.extend(trusted)

    # Deduplicare după URL normalizat
    seen = set()
    unique = []
    for store in all_stores:
        key = urlparse(store["url"]).netloc.lower().lstrip("www.")
        if key not in seen and key:
            seen.add(key)
            unique.append(store)

    print(f"[COLLECTOR] Total unic după deduplicare: {len(unique)} magazine.")
    return unique


if __name__ == "__main__":
    stores = collect_all(use_web_sources=False)  # Rulare rapidă fără web în test
    print(json.dumps(stores[:5], ensure_ascii=False, indent=2))
