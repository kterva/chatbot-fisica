#!/usr/bin/env python3
"""Extrae texto de los PDF en documents/ y lo guarda como .txt en context/.

Uso:
    python scripts/extract_pdf_text.py                  # procesa todos los PDF de documents/
    python scripts/extract_pdf_text.py archivo.pdf       # procesa un único PDF (ruta dentro de documents/ o absoluta)

Este script se ejecuta manualmente por el administrador; no está expuesto vía API
(evita aceptar subida de archivos arbitrarios desde el navegador en esta fase).
"""

import sys
from pathlib import Path

from pypdf import PdfReader

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "documents"
CONTEXT_DIR = PROJECT_ROOT / "context"


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(pdf_path)
    pages_text = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(text.strip() for text in pages_text if text.strip())


def process_pdf(pdf_path: Path) -> None:
    print(f"Procesando {pdf_path.name}...")
    text = extract_pdf_text(pdf_path)
    if not text:
        print(f"  Aviso: no se pudo extraer texto de {pdf_path.name} (¿PDF escaneado sin OCR?)")
        return

    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CONTEXT_DIR / f"{pdf_path.stem}.txt"
    output_path.write_text(text, encoding="utf-8")
    print(f"  Guardado en {output_path.relative_to(PROJECT_ROOT)}")


def resolve_target(arg: str) -> Path:
    path = Path(arg)
    if not path.is_absolute():
        candidate = DOCUMENTS_DIR / arg
        if candidate.is_file():
            return candidate
    return path


def main() -> None:
    if len(sys.argv) > 1:
        targets = [resolve_target(arg) for arg in sys.argv[1:]]
    else:
        targets = sorted(DOCUMENTS_DIR.glob("*.pdf"))

    if not targets:
        print(f"No se encontraron PDF en {DOCUMENTS_DIR}")
        return

    for pdf_path in targets:
        if not pdf_path.is_file():
            print(f"Aviso: no existe {pdf_path}, se omite.")
            continue
        process_pdf(pdf_path)


if __name__ == "__main__":
    main()
