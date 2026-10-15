"""Knowledge Library de Evolus (RAG): subir documentos, importar URL, listar.

SIN VERIFICAR (documentado en evolus.ai/developers, no probado):
  POST /memories/{libraryId}/documents?language=en      multipart `file` -> 201 (indexa en segundo plano)
  POST /memories/{libraryId}/documents/import-url       JSON {title, url}
  GET  /memories/{libraryId}/documents                  lista + estado de indexación
  GET  /memories/document-formats
Son funciones sobre ClienteEvolus: reutilizan throttle, reintentos y grabación (sin cabeceras).
"""
from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path

from .cliente import ClienteEvolus


def sha256_archivo(ruta) -> str:
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def subir_documento(cliente: ClienteEvolus, library_id: str, ruta, idioma: str = "en"):
    """Sube un archivo local. La grabación guarda nombre, tamaño y sha256, no el contenido."""
    ruta = Path(ruta)
    datos = ruta.read_bytes()
    mime = mimetypes.guess_type(ruta.name)[0] or "text/markdown"
    resumen = {"archivo": ruta.name, "bytes": len(datos),
               "sha256": hashlib.sha256(datos).hexdigest(), "language": idioma}
    return cliente._pedir("POST", f"/memories/{library_id}/documents?language={idioma}",
                          archivos={"file": (ruta.name, datos, mime)}, grabar=resumen)


def importar_url(cliente: ClienteEvolus, library_id: str, titulo: str, url: str):
    return cliente._pedir("POST", f"/memories/{library_id}/documents/import-url",
                          json={"title": titulo, "url": url})


def listar_documentos(cliente: ClienteEvolus, library_id: str):
    return cliente._pedir("GET", f"/memories/{library_id}/documents")


def formatos_documento(cliente: ClienteEvolus):
    return cliente._pedir("GET", "/memories/document-formats")
