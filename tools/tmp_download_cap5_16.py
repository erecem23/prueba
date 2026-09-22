from __future__ import annotations
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

OUT = Path("CAP5_N113_A_N129_16_PDF")
OUT.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (compatible; BiblioRef/0.13; thesis-bundle/1.0)"
TIMEOUT = 90

def get_bytes(url: str, accept: str = "*/*", retries: int = 4) -> bytes:
    last = None
    for i in range(retries):
        try:
            req = Request(url, headers={"User-Agent": UA, "Accept": accept})
            with urlopen(req, timeout=TIMEOUT) as r:
                return r.read()
        except Exception as e:
            last = e
            if i + 1 < retries:
                time.sleep(2 ** i)
    raise RuntimeError(f"GET failed after {retries} tries: {url}: {last}")

def get_json(url: str) -> dict:
    raw = get_bytes(url, "application/json")
    return json.loads(raw.decode("utf-8"))

def valid_pdf(data: bytes) -> bool:
    return data[:5] == b"%PDF-" and len(data) >= 50000

def save_pdf(filename: str, data: bytes, source: str):
    if not valid_pdf(data):
        prefix = data[:120]
        raise RuntimeError(f"Not a valid PDF or too small: {filename}; bytes={len(data)}; prefix={prefix!r}; source={source}")
    p = OUT / filename
    p.write_bytes(data)
    print(f"OK {filename} {len(data):,} bytes <- {source}")

def download_first(filename: str, urls: list[str]):
    errors = []
    for u in urls:
        try:
            data = get_bytes(u, "application/pdf,*/*")
            if valid_pdf(data):
                save_pdf(filename, data, u)
                return
            errors.append(f"{u}: invalid {len(data)} bytes {data[:30]!r}")
        except Exception as e:
            errors.append(f"{u}: {e}")
    raise RuntimeError(filename + "\n  " + "\n  ".join(errors))

def dspace_item_pdf(item_uuid: str) -> tuple[bytes, str]:
    base = "https://rpsico.mdp.edu.ar/server/api/core/"
    # Resolve bundles from item.
    item = get_json(base + f"items/{item_uuid}")
    bundles_link = ((item.get("_links") or {}).get("bundles") or {}).get("href")
    if not bundles_link:
        bundles_link = base + f"items/{item_uuid}/bundles"
    sep = "&" if "?" in bundles_link else "?"
    bundles = get_json(bundles_link + sep + "size=100")
    blist = (((bundles.get("_embedded") or {}).get("bundles")) or [])
    if not blist:
        raise RuntimeError(f"No bundles for item {item_uuid}")
    # Prefer ORIGINAL; otherwise inspect all bundles.
    blist = sorted(blist, key=lambda b: 0 if str(b.get("name","")).upper()=="ORIGINAL" else 1)
    candidates = []
    for b in blist:
        href = (((b.get("_links") or {}).get("bitstreams") or {}).get("href"))
        if not href:
            buuid = b.get("uuid")
            if not buuid:
                continue
            href = base + f"bundles/{buuid}/bitstreams"
        sep = "&" if "?" in href else "?"
        try:
            bits = get_json(href + sep + "size=100")
        except Exception:
            continue
        for bit in (((bits.get("_embedded") or {}).get("bitstreams")) or []):
            name = str(bit.get("name") or "")
            mime = str(((bit.get("bundleName") or "")))
            fmt = bit.get("format") or {}
            mimetype = str(fmt.get("mimetype") or bit.get("mimeType") or "")
            buuid = bit.get("uuid")
            content = (((bit.get("_links") or {}).get("content") or {}).get("href"))
            if not content and buuid:
                content = base + f"bitstreams/{buuid}/content"
            if not content:
                continue
            score = 0
            if name.lower().endswith(".pdf"): score += 5
            if "pdf" in mimetype.lower(): score += 5
            if str(b.get("name","")).upper()=="ORIGINAL": score += 3
            # Avoid license/thumbnail/text-extract bundles where possible.
            low = name.lower()
            if "license" in low or "thumbnail" in low or low.endswith(".txt"): score -= 10
            candidates.append((score, name, content))
    candidates.sort(reverse=True)
    errs=[]
    for score, name, content in candidates:
        try:
            data = get_bytes(content, "application/pdf,*/*")
            if valid_pdf(data):
                return data, content
            errs.append(f"{name} {content}: invalid {len(data)}")
        except Exception as e:
            errs.append(f"{name} {content}: {e}")
    raise RuntimeError(f"No valid PDF bitstream for item {item_uuid}; " + "; ".join(errs[:8]))

records = [
    # UNLP: exact public bitstreams, with handle download fallback.
    dict(file="UNLP_2016_Aguirre_Javier.pdf", direct=[
        "https://sedici.unlp.edu.ar/bitstream/handle/10915/53590/Documento_completo.pdf-PDFA2u.pdf?isAllowed=y&sequence=3",
        "https://sedici.unlp.edu.ar/bitstream/handle/10915/53590/Documento_completo.pdf-PDFA.pdf?isAllowed=y&sequence=3",
    ]),
    dict(file="UNLP_2017_Fernandez_Raone_Martina.pdf", direct=[
        "https://sedici.unlp.edu.ar/bitstream/handle/10915/59898/Documento_completo.pdf-PDFA.pdf?isAllowed=y&sequence=3",
        "https://sedici.unlp.edu.ar/bitstream/handle/10915/59898/Documento_completo.pdf?sequence=1&isAllowed=y",
    ]),
    dict(file="UNLP_2018_Grassi_Maria_Cecilia.pdf", direct=[
        "https://sedici.unlp.edu.ar/bitstream/handle/10915/77425/Documento_completo.pdf-PDFA.pdf?isAllowed=y&sequence=1",
        "https://sedici.unlp.edu.ar/bitstream/handle/10915/77425/Documento_completo.pdf?sequence=1&isAllowed=y",
    ]),
    dict(file="UNLP_2025_Yaccarini_Cecilia.pdf", direct=[
        "https://sedici.unlp.edu.ar/bitstream/handle/10915/189173/Documento_completo.pdf-PDFA.pdf?isAllowed=y&sequence=1",
        "https://sedici.unlp.edu.ar/bitstream/handle/10915/189173/Documento_completo.pdf?sequence=1&isAllowed=y",
    ]),

    # UNMdP: current DSpace item UUIDs; selected direct bitstreams are fallbacks.
    dict(file="UNMdP_2015_Ventura_Ana_Clara.pdf", item="8ae095cc-bafe-4799-8823-789db4cf55e3", direct=[
        "https://rpsico.mdp.edu.ar/bitstream/handle/123456789/246/TD05.pdf?isAllowed=y&sequence=3",
    ]),
    dict(file="UNMdP_2016_Fasciglione_Maria_Paola.pdf", item="970a2f0a-bd37-4e84-b079-68ba6d294b0e"),
    dict(file="UNMdP_2019_Baumgart_Amalia.pdf", item="6f66678d-09bb-4e3d-b20d-5a2968ac1c36"),
    dict(file="UNMdP_2020_Zamora_Eliana_V.pdf", item="f8efc188-c517-4333-a87b-30ff29e72e29", direct=[
        "https://ri.conicet.gov.ar/bitstream/handle/11336/116280/CONICET_Digital_Nro.46053c32-20f2-42b2-b162-ccd3cedafc19_A.pdf?isAllowed=y&sequence=2",
    ]),
    dict(file="UNMdP_2024_Paneiva_Pompa_Juan_Pablo.pdf", item="18906751-9a63-481b-9beb-64c08d34cbad", direct=[
        "https://rpsico.mdp.edu.ar/bitstreams/a8dbe799-3dff-4259-b826-3e0c7414523b/download",
    ]),
    dict(file="UNMdP_2024_Said_Andrea_Giselle.pdf", item="59763b72-213e-4da5-9aae-192adcbb2345", direct=[
        "https://rpsico.mdp.edu.ar/server/api/core/bitstreams/3a083735-02aa-44d4-b914-e2e4b2969f99/content",
    ]),
    dict(file="UNMdP_2024_Tolosa_Dante_Orlando.pdf", item="3c904d41-ef4a-4f68-88db-7ce91fae9e11", direct=[
        "https://rpsico.mdp.edu.ar/bitstreams/6ba7f0df-28d9-48cb-8ef3-d22bce56c65e/download",
    ]),
    dict(file="UNMdP_2025_Demateis_Mariano.pdf", item="dfa2d361-395d-42c9-bba6-a6a5da670933", direct=[
        "https://rpsico.mdp.edu.ar/bitstreams/1796a928-76c7-4285-9eab-0981b20e92f5/download",
    ]),
    dict(file="UNMdP_2025_Garcia_Matias_Jonas.pdf", item="4dbece1e-0ed6-4606-8d80-3b5750da1525", direct=[
        "https://rpsico.mdp.edu.ar/server/api/core/bitstreams/de3bbceb-e1dc-43c2-8f8c-a9e8341b46f6/content",
    ]),
    dict(file="UNMdP_2025_Gelpi_Trudo_Rosario.pdf", item="6d43fa66-a553-4acc-9ff3-991cff13f3cc", direct=[
        "https://rpsico.mdp.edu.ar/bitstreams/bdb6d697-83ce-4f62-8df9-1310f91371ff/download",
    ]),
    dict(file="UNMdP_2025_Gonzalez_Patricio_Esteban.pdf", item="f3d2e38c-25ca-4f5f-8459-1f4dc7000d1b", direct=[
        "https://rpsico.mdp.edu.ar/server/api/core/bitstreams/5cce352e-91d6-4c84-84b3-2152646b9e79/content",
    ]),
    dict(file="UNMdP_2025_Revollo_Sarmiento_Elsa_Araceli.pdf", item="0967a16f-c2c5-45c1-a8d1-0b40037ef1b0", direct=[
        "https://rpsico.mdp.edu.ar/bitstreams/070540fd-5761-4e84-87d6-100414437ae4/download",
    ]),
]

failures=[]
for rec in records:
    fn=rec["file"]
    try:
        if rec.get("item"):
            try:
                data, src = dspace_item_pdf(rec["item"])
                save_pdf(fn, data, src)
                continue
            except Exception as e:
                print(f"WARN DSpace API failed for {fn}: {e}")
        urls=rec.get("direct") or []
        if urls:
            download_first(fn, urls)
        else:
            raise RuntimeError("no fallback URL")
    except Exception as e:
        failures.append((fn, str(e)))
        print(f"FAIL {fn}: {e}", file=sys.stderr)

# Save manifest whether or not the run succeeds.
manifest = {
    "expected": len(records),
    "downloaded": len(list(OUT.glob("*.pdf"))),
    "files": [{"name": p.name, "bytes": p.stat().st_size} for p in sorted(OUT.glob("*.pdf"))],
    "failures": failures,
}
(OUT / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "LEEME.txt").write_text(
    "Complemento del corpus bibliográfico del Capítulo 5: N=113 -> N=129.\n"
    "Incluye exclusivamente las 16 tesis faltantes (UNLP=4; UNMdP=12; UNC=0).\n"
    "Nombres normalizados para carga directa en BiblioRef.\n",
    encoding="utf-8"
)

if failures or manifest["downloaded"] != len(records):
    print(json.dumps(manifest, ensure_ascii=False, indent=2), file=sys.stderr)
    sys.exit(1)

print(json.dumps(manifest, ensure_ascii=False, indent=2))
