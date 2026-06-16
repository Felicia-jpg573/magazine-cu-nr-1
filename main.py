"""
main.py
Orchestrează întregul pipeline:
1. Colectare operatori economici
2. Scanare site-uri și detecție afirmații superlative
3. Generare dashboard HTML

Utilizare:
  python main.py                        # scanare completă cu lista manuală
  python main.py --web                  # include colectare din Trusted.ro
  python main.py --limit 5             # testare pe primele 5 magazine
  python main.py --url https://...     # scanare un singur site
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime

from collector import collect_all, collect_manual_seeds
from scanner import scan_all
from dashboard import generate_dashboard

OUTPUT_DIR = Path("/mnt/user-data/outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scanner afirmații superlative — comerț electronic România"
    )
    parser.add_argument(
        "--web", action="store_true",
        help="Include colectare din Trusted.ro (mai lent, mai multe magazine)"
    )
    parser.add_argument(
        "--limit", type=int, default=0,
        help="Limitează numărul de magazine scanate (0 = toate)"
    )
    parser.add_argument(
        "--url", type=str, default="",
        help="Scanează un singur URL specificat"
    )
    parser.add_argument(
        "--delay", type=float, default=1.5,
        help="Pauza în secunde între cereri HTTP (implicit: 1.5)"
    )
    parser.add_argument(
        "--output", type=str, default="",
        help="Calea fișierului HTML de ieșire (opțional)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    start_time = time.time()

    print("=" * 60)
    print("  SCANNER CONFORMITATE PUBLICITATE — NR. 1")
    print("  Legea 158/2008 | OUG 34/2014 | Directiva 2005/29/CE")
    print("=" * 60)

    # --- Pasul 1: Colectare magazine ---
    if args.url:
        from urllib.parse import urlparse
        parsed = urlparse(args.url)
        stores = [{
            "name": parsed.netloc,
            "url": args.url.rstrip("/"),
            "source": "manual_cli"
        }]
        print(f"\n[1/3] Mod single-URL: {args.url}")
    else:
        print(f"\n[1/3] Colectare operatori economici (web={'DA' if args.web else 'NU'})...")
        stores = collect_all(use_web_sources=args.web)

    if args.limit and args.limit > 0:
        stores = stores[:args.limit]
        print(f"  Limitat la primele {args.limit} magazine.")

    print(f"  Magazine de scanat: {len(stores)}")

    # Salvare listă magazine
    stores_file = OUTPUT_DIR / "magazine_lista.json"
    stores_file.write_text(
        json.dumps(stores, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"  Lista salvată: {stores_file}")

    # --- Pasul 2: Scanare ---
    print(f"\n[2/3] Scanare afirmații superlative (delay={args.delay}s/pagină)...")
    print("  Avertisment: Scanarea completă poate dura câteva minute.\n")

    findings = scan_all(stores, delay=args.delay)

    # Salvare rezultate brute JSON
    results_file = OUTPUT_DIR / "rezultate_brute.json"
    results_file.write_text(
        json.dumps(findings, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n  Rezultate JSON salvate: {results_file}")

    # --- Pasul 3: Dashboard ---
    print(f"\n[3/3] Generare dashboard HTML...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_filename = args.output or f"raport_conformitate_{timestamp}.html"
    html_path = OUTPUT_DIR / Path(html_filename).name

    generate_dashboard(findings, stores, str(html_path))
    print(f"  Dashboard generat: {html_path}")

    # --- Sumar final ---
    elapsed = time.time() - start_time
    nonconform = sum(1 for f in findings if "NECONFORMĂ" in (f.get("verdict") or ""))
    partial = sum(1 for f in findings if "VERIFICARE" in (f.get("verdict") or ""))
    stores_hit = len(set(f["store_url"] for f in findings))

    print("\n" + "=" * 60)
    print("  SUMAR FINAL")
    print("=" * 60)
    print(f"  Magazine scanate:                  {len(stores)}")
    print(f"  Magazine cu afirmații detectate:   {stores_hit}")
    print(f"  Total afirmații:                   {len(findings)}")
    print(f"  Neconforme (lipsă sursă):          {nonconform}")
    print(f"  Necesită verificare manuală:       {partial}")
    print(f"  Timp total:                        {elapsed:.1f}s")
    print(f"\n  Dashboard: {html_path}")
    print("=" * 60)

    return str(html_path)


if __name__ == "__main__":
    html_output = main()
