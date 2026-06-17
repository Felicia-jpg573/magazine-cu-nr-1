# Aplicație de monitorizare afirmații superlative — comerț electronic România

Aplicația identifică operatorii economici din România care comercializează online produse sau servicii descrise ca „nr. 1", „liderul pieței", „cel mai vândut" sau expresii echivalente, și verifică dacă aceștia prezintă studii sau surse justificative conform legislației în vigoare.

**Legislație aplicabilă:** Legea nr. 158/2008 privind publicitatea înșelătoare și comparativă, OUG 34/2014, Directiva 2005/29/CE privind practicile comerciale incorecte.

---

## Structura proiectului

```
├── collector.py      # Colectează URL-uri de magazine online din surse publice
├── scanner.py        # Scanează site-urile și detectează afirmații superlative
├── dashboard.py      # Generează raportul HTML interactiv
├── main.py           # Orchestrează întregul pipeline
└── README.md
```

---

## Instalare

Python 3.10 sau mai nou este necesar.

Instalează dependențele:

```bash
pip install requests beautifulsoup4 lxml jinja2
```

---

## Utilizare

### Scanare rapidă — primele 10 magazine din lista predefinită

```bash
python main.py --limit 10
```

### Scanare completă — toate magazinele din lista predefinită (40+)

```bash
python main.py
```

### Include colectare automată din Trusted.ro

```bash
python main.py --web
```

### Scanare un singur site

```bash
python main.py --url https://www.exemplu.ro
```

### Control viteză între cereri HTTP

```bash
python main.py --limit 20 --delay 2.0
```

Implicit: 1.5 secunde între cereri, valoare care respectă serverele scanate.

---

## Ce produce aplicația

După rulare, în directorul curent apar:

- `raport_conformitate_YYYYMMDD_HHMMSS.html` — dashboard interactiv cu toate constatările, filtrare, căutare și export CSV
- `rezultate_brute.json` — datele brute în format JSON pentru procesare ulterioară
- `magazine_lista.json` — lista operatorilor economici scanați

Deschide fișierul HTML în orice browser pentru a vedea raportul.

---

## Ce detectează aplicația

### Afirmații superlative monitorizate

Expresii în română: `nr. 1`, `numărul unu`, `locul 1`, `liderul pieței`, `cel mai vândut`, `cea mai bună`, `primul din România`, `brandul nr. 1` și variante.

Expresii în engleză frecvente pe site-uri românești: `#1`, `number one`, `no. 1`, `market leader`, `best selling`, `top brand`, `rank 1`.

### Indicatori de surse justificative căutați

Institute de cercetare: GfK, Nielsen, Kantar, IMAS, Ipsos, Euromonitor, Statista, Gartner.

Termeni generici: `studiu`, `sondaj`, `cercetare`, `raport`, `conform`, `potrivit`, `metodologie`, `eșantion`, `auditat`, `date verificate`.

### Verdictele atribuite

| Verdict | Semnificație |
|---|---|
| Neconformă — lipsă sursă | Nu a fost detectat niciun indicator de sursă justificativă în proximitatea afirmației |
| Necesită verificare manuală | Au fost detectați indicatori de sursă (institut, studiu, metodologie), dar validarea autenticității necesită verificare umană |

---

## Informații extrase per operator

- Denumirea comercială și URL-ul site-ului
- Persoana juridică (denumire legală și CUI), extrase automat din paginile de contact, termeni și condiții sau GDPR
- Pagina exactă unde a fost găsită afirmația, cu link direct
- Textul afirmației detectate
- Contextul din jurul afirmației (600 de caractere)
- Indicatorii de sursă găsiți
- Verdict preliminar
- Data și ora scanării

---

## Limitări

**Site-uri dinamice.** Site-urile care generează conținutul exclusiv prin JavaScript (React, Angular) necesită Playwright în loc de requests. Versiunea curentă folosește HTTP static — funcționează pentru majoritatea paginilor de prezentare și termeni, unde afirmațiile superlative apar cel mai frecvent.

**Extragerea persoanei juridice.** Funcționează când operatorul menționează explicit denumirea și CUI-ul în text accesibil pe paginile de contact, termeni sau GDPR. Informațiile stocate în imagini sau PDF-uri nu sunt extrase automat — verificarea prin RECOM (portal.onrc.ro) rămâne necesară în aceste cazuri.

**Caracterul preliminar al verdictelor.** Verdictul „Neconformă — lipsă sursă" indică absența indicatorilor textuali de sursă în paginile parcurse, nu o constatare juridică definitivă. Sursa poate exista într-un document separat sau pe o pagină neparcursă. Orice constatare necesită verificare manuală înainte de orice acțiune oficială.

**Blocarea scraperelor.** Unele site-uri blochează cererile automate. Parametrul `--delay` permite reducerea frecvenței cererilor. Pentru scanări la scară mare, utilizarea unor proxy-uri rezidențiale poate fi necesară.

---

## Surse de date pentru lista de magazine

- Listă predefinită de 40 de magazine românești reprezentative din categorii diverse (electronice, farmacie, sport, mobilă, librării, fashion, jucării, auto)
- Trusted.ro — catalog public de magazine verificate (activat cu `--web`)
- URL-uri individuale specificate manual cu `--url`

---

## Cerințe legale de reținut

O afirmație superlativă este legală în România dacă operatorul poate dovedi că se întemeiază pe un studiu de piață realizat de o entitate independentă, cu metodologie declarată, eșantion reprezentativ, teritoriu definit și dată recentă. Simpla afișare a unui logo „Nr. 1" sau a unei mențiuni fără referință verificabilă constituie publicitate înșelătoare în sensul Legii 158/2008 și poate fi sancționată de ANPC.
