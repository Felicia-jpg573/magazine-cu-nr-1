"""
scanner.py
Accesează site-urile de comerț electronic, detectează afirmații superlative
de tip „nr. 1", „numărul 1", „liderul pieței" și verifică prezența surselor
justificative (studii, institute de cercetare, date auditate).
Extrage de asemenea persoana juridică și CUI-ul operatorului economic.
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import json
from urllib.parse import urlparse
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ---------------------------------------------------------------------------
# Tipare de afirmații superlative — Română și Engleză
# ---------------------------------------------------------------------------
SUPERLATIVE_PATTERNS = [
    r"\bnr\.?\s*1\b",
    r"\bnumărul\s+[uú]nu\b",
    r"\bnumarul\s+unu\b",
    r"\blocul\s+[î1i]nt[âaă]i\b",
    r"\blocul\s+1\b",
    r"(?<!\w)#\s*1\b",
    r"\bliderul?\s+pie[tț]ei\b",
    r"\bliderul?\s+din\s+rom[âa]nia\b",
    r"\bcel\s+mai\s+v[âa]ndut\b",
    r"\bcea\s+mai\s+v[âa]ndut[ăa]\b",
    r"\bcel\s+mai\s+bun\b",
    r"\bcea\s+mai\s+bun[ăa]\b",
    r"\bcel\s+mai\s+mare\s+(produc[aă]tor|furnizor|retailer|distribuit[oa]r)\b",
    r"\bprimul\s+din\s+rom[âa]nia\b",
    r"\bprimul\s+pe\s+pia[tț][ăa]\b",
    r"\bpozi[tț]ia\s+1\b",
    r"\bpozi[tț]ia\s+[î1i]nt[âaă]i\b",
    r"\brank\s*[:#\-]?\s*1\b",
    r"\btop\s+1\b",
    r"\bcampionul?\s+v[âa]nz[aă]rilor\b",
    r"\bcel\s+mai\s+de\s+[î]ncredere\b",
    r"\bbrand\s+nr\.?\s*1\b",
    r"\bprodus\s+nr\.?\s*1\b",
    r"\bservici[iu]\s+nr\.?\s*1\b",
    r"\bnumber\s+one\b",
    r"(?<!\w)#1\b",
    r"\bno\.?\s*1\b",
    r"\bmarket\s+leader\b",
    r"\bbest\s+selling\b",
    r"\bbest-selling\b",
    r"\btop\s+brand\b",
    r"\brank\s+1\b",
    r"\brated\s+#1\b",
    r"\brated\s+number\s+one\b",
    r"\b1st\s+in\s+romania\b",
]

# ---------------------------------------------------------------------------
# Indicatori de surse justificative
# ---------------------------------------------------------------------------
SOURCE_INDICATORS = [
    r"\bgfk\b", r"\bg\.f\.k\b",
    r"\bnielsen\b",
    r"\bkantar\b",
    r"\bimas\b",
    r"\bipsos\b",
    r"\bbain\s*&\s*company\b",
    r"\bmckinsey\b",
    r"\beuromon[iy]tor\b",
    r"\bstatista\b",
    r"\bgartner\b",
    r"\bfrost\s*&\s*sullivan\b",
    r"\bstudiu\b", r"\bstudiul\b",
    r"\bsondaj\b", r"\bsondajul\b",
    r"\bcercetare\b", r"\bcercetarea\b",
    r"\braport\b", r"\braportul\b",
    r"\bdat[eă]\s+de\s+pia[tț][ăa]\b",
    r"\bdat[eă]\s+audit[ae]\b",
    r"\bauditat\b", r"\bauditare\b",
    r"\bconform\s+studiu\b",
    r"\bpotrivit\s+studiu\b",
    r"\bconform\s+cercet[aă]rii\b",
    r"\bconform\s+raportului\b",
    r"\bconform\s+datelor\b",
    r"\bsurs[ăa]\b",
    r"\bmeto[dt]ologi[ae]\b",
    r"\be[ș]antion\b",
    r"\brespondent\b",
    r"\binterviev[au]\b",
    r"\bv[âa]nz[aă]ri\s+auditate\b",
    r"\bdate\s+oficiale\b",
    r"\bdate\s+verificate\b",
    r"\bcertificat\s+de\b",
    r"\baccreditat\b",
    r"\bstudy\b", r"\bsurvey\b",
    r"\bresearch\b", r"\breport\b",
    r"\bmarket\s+research\b",
    r"\bmarket\s+data\b",
    r"\baudited\s+sales\b",
    r"\baccording\s+to\b",
    r"\bbased\s+on\b",
]

# Pagini interne cu conținut de marketing și prezentare
TARGET_PATHS = [
    "/",
    "/despre-noi",
    "/despre",
    "/about",
    "/about-us",
    "/cine-suntem",
    "/companie",
    "/prezentare",
    "/brand",
    "/historia",
    "/istoria-noastra",
    "/produse",
    "/products",
    "/servicii",
    "/services",
]

# Pagini unde se găsesc datele juridice ale operatorului
LEGAL_PAGES = [
    "/contact",
    "/despre-noi",
    "/despre",
    "/termeni",
    "/termeni-si-conditii",
    "/termeni-conditii",
    "/politica-de-confidentialitate",
    "/gdpr",
    "/protectia-datelor",
    "/about",
    "/about-us",
    "/informatii-legale",
    "/legal",
]

# ---------------------------------------------------------------------------
# Tipare pentru extragerea persoanei juridice și CUI
# ---------------------------------------------------------------------------
CUI_PATTERN = re.compile(
    r"(?:C\.?U\.?I\.?|cod\s+fiscal|cod\s+unic|nr\.?\s*reg\.?\s*com\.?)"
    r"\s*[:\-]?\s*(RO\s*)?\d{6,10}",
    re.IGNORECASE,
)
CUI_DIGITS = re.compile(r"(RO\s*)?(\d{6,10})", re.IGNORECASE)

LEGAL_ENTITY_PATTERN = re.compile(
    r"\b([A-Z\u0102\u00C2\u00CE\u015E\u0162][A-Za-z\u0102\u00E2\u00EE"
    r"\u015F\u0163\u0103\u00E3\s&\.\-]{2,60}"
    r"\s+(?:S\.?R\.?L\.?|S\.?A\.?|S\.?N\.?C\.?|R\.?A\.?))\b",
    re.UNICODE,
)


@dataclass
class Finding:
    """O afirmație superlativă găsită pe un site."""
    store_name: str
    store_url: str
    page_url: str
    pattern_matched: str
    context: str
    has_source_indicator: bool
    source_indicators_found: list[str] = field(default_factory=list)
    verdict: str = ""
    scanned_at: str = ""
    persoana_juridica: Optional[str] = None
    cui: Optional[str] = None


def compile_patterns(pattern_list: list[str]) -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE | re.UNICODE) for p in pattern_list]


COMPILED_SUPERLATIVES = compile_patterns(SUPERLATIVE_PATTERNS)
COMPILED_SOURCES = compile_patterns(SOURCE_INDICATORS)


def extract_text_from_soup(soup: BeautifulSoup) -> str:
    """Extrage textul vizibil din pagină, fără scripturi și stiluri."""
    for tag in soup(["script", "style", "noscript", "meta", "head"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", text)


def get_context(text: str, match: re.Match, window: int = 300) -> str:
    """Extrage contextul din jurul unui match."""
    start = max(0, match.start() - window)
    end = min(len(text), match.end() + window)
    return text[start:end].strip()


def check_source_indicators(context: str) -> tuple[bool, list[str]]:
    """Verifică dacă în contextul afirmației există indicatori de sursă."""
    found = []
    for pat in COMPILED_SOURCES:
        m = pat.search(context)
        if m:
            found.append(m.group(0).lower())
    return bool(found), list(set(found))


def assign_verdict(has_source: bool, source_list: list[str]) -> str:
    """Atribuie un verdict preliminar pe baza indicatorilor de sursă găsiți."""
    strong = [s for s in source_list if any(
        kw in s for kw in [
            "gfk", "nielsen", "kantar", "imas", "ipsos",
            "studiu", "sondaj", "cercetare", "raport",
            "audit", "survey", "research", "report",
        ]
    )]
    if strong or has_source:
        return "NECESITĂ VERIFICARE MANUALĂ"
    return "NECONFORMĂ — LIPSĂ SURSĂ"


def extract_legal_entity(
    store: dict, session: requests.Session
) -> tuple[Optional[str], Optional[str]]:
    """
    Caută pe paginile juridice ale site-ului denumirea persoanei juridice
    și CUI-ul. Returnează (denumire, cui) sau (None, None).
    """
    for path in LEGAL_PAGES:
        url = store["url"].rstrip("/") + path
        try:
            resp = session.get(url, timeout=10, allow_redirects=True)
            if resp.status_code != 200:
                continue
            resp.encoding = resp.apparent_encoding or "utf-8"
            soup = BeautifulSoup(resp.text, "lxml")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = re.sub(r"\s+", " ", soup.get_text(separator=" ", strip=True))

            cui_match = CUI_PATTERN.search(text)
            cui = None
            if cui_match:
                digits = CUI_DIGITS.search(cui_match.group(0))
                if digits:
                    cui = "RO" + digits.group(2).replace(" ", "")

            pj = None
            search_zone = text
            if cui_match:
                start = max(0, cui_match.start() - 200)
                end = min(len(text), cui_match.end() + 200)
                search_zone = text[start:end]

            entity_match = LEGAL_ENTITY_PATTERN.search(search_zone)
            if entity_match:
                pj = re.sub(r"\s+", " ", entity_match.group(0).strip())

            if pj or cui:
                return pj, cui

        except Exception:
            continue

    return None, None


def fetch_page(url: str, session: requests.Session) -> Optional[BeautifulSoup]:
    """Descarcă o pagină și returnează BeautifulSoup sau None la eroare."""
    try:
        resp = session.get(url, timeout=12, allow_redirects=True)
        if resp.status_code != 200:
            return None
        resp.encoding = resp.apparent_encoding or "utf-8"
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        print(f"    [EROARE] {url}: {e}")
        return None


def scan_page(store: dict, path: str, session: requests.Session) -> list[Finding]:
    """Scanează o pagină individuală și returnează lista de constatări."""
    url = store["url"].rstrip("/") + path
    soup = fetch_page(url, session)
    if not soup:
        return []

    text = extract_text_from_soup(soup)
    findings = []

    for pat in COMPILED_SUPERLATIVES:
        for match in pat.finditer(text):
            context = get_context(text, match, window=300)
            has_src, src_list = check_source_indicators(context)
            verdict = assign_verdict(has_src, src_list)
            findings.append(Finding(
                store_name=store["name"],
                store_url=store["url"],
                page_url=url,
                pattern_matched=match.group(0),
                context=context,
                has_source_indicator=has_src,
                source_indicators_found=src_list,
                verdict=verdict,
                scanned_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                persoana_juridica=store.get("persoana_juridica"),
                cui=store.get("cui"),
            ))

    return findings


def scan_store(
    store: dict, session: requests.Session, delay: float = 1.5
) -> list[Finding]:
    """Scanează un operator economic pe mai multe pagini interne."""
    print(f"  Scanare: {store['name']} ({store['url']})")

    # Extrage persoana juridică și CUI o singură dată per operator
    pj, cui = extract_legal_entity(store, session)
    if pj or cui:
        print(f"    → Persoana juridică: {pj or '?'} | CUI: {cui or '?'}")

    store_enriched = dict(store, persoana_juridica=pj, cui=cui)
    all_findings = []

    for path in TARGET_PATHS:
        page_findings = scan_page(store_enriched, path, session)
        if page_findings:
            print(f"    → {path}: {len(page_findings)} afirmații detectate")
        all_findings.extend(page_findings)
        time.sleep(delay)

    # Deduplicare: același pattern pe aceeași pagină → o singură constatare
    seen = set()
    unique = []
    for f in all_findings:
        key = (f.page_url, f.pattern_matched.lower())
        if key not in seen:
            seen.add(key)
            unique.append(f)

    return unique


def scan_all(stores: list[dict], delay: float = 1.5) -> list[dict]:
    """Scanează toți operatorii și returnează lista serializabilă de constatări."""
    session = requests.Session()
    session.headers.update(HEADERS)

    all_findings = []
    total = len(stores)

    for idx, store in enumerate(stores, 1):
        print(f"\n[SCANNER] {idx}/{total}: {store['name']}")
        findings = scan_store(store, session, delay=delay)
        all_findings.extend([asdict(f) for f in findings])
        print(f"  Total constatări: {len(findings)}")

    return all_findings


if __name__ == "__main__":
    test_store = {"name": "Test", "url": "https://www.example.com", "source": "manual"}
    session = requests.Session()
    session.headers.update(HEADERS)
    results = scan_store(test_store, session, delay=0.5)
    for r in results:
        print(json.dumps(asdict(r), ensure_ascii=False, indent=2))
