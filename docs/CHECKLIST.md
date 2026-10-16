# CHECKLIST (actualizado 16 oct)

## Hecho
- [x] Proyecto en WSL con git; datos Braatz y Rieth (Training) pineados; FaultExplainer vendorizado.
- [x] `core/`, `twin/`, `eval/`, `llm/` con tests (150+). Token Factory configurado.
- [x] Campañas: Braatz sin thinking (+ reintentos), Braatz con thinking, Rieth sin thinking (300), réplica FaultExplainer.
- [x] `claims.json` + `verify_claims.py` (hashes, claims y marcadores del README) en verde.
- [x] README en inglés con resultados; LICENSE MIT.
- [x] Evolus: agente TEP Shift Copilot (Gemma vía Token Factory), corridas grabadas, Knowledge Library cargada por API.

## Pendiente
- [x] Experimentos cerrados (16 oct). Rieth con thinking detenido en 95/200 (Gemma retirado; no se reporta). Segundo modelo Qwen hecho.
- [x] Agente con biblioteca (instrucciones v2) grabado y pineado, sobre Qwen (Gemma retirado). Repetir con Gemma si vuelve.
- [x] 3.er bloque de Evolus: AI Tool «translate» por API (no hay Workflows en la UI), grabado y pineado.
- [x] Claims y README: anticipación, evidencia inventada con thinking (control por falla), segundo modelo Qwen. Rieth thinking detenido en 95/200 (Gemma retirado).
- [x] Demo como producto (Live replay) y funciona desde un clon (datos Braatz en el repo).
- [ ] Despliegue con URL pública (domingo).
- [ ] Esquema del deck y guion del video (viernes).
- [ ] Copyright del LICENSE (decide Diego).

## Entrega en lablab (antes del 18 oct, 10:00 hora de Ecuador)
- [~] Textos en `docs/ENTREGA_LABLAB.md` (borrador): falta que Diego elija título/nombre.
- [ ] Reto *Intelligent Industry* y tags (AMD Token Factory, Gemma, Evolus).
- [ ] Repo público MIT, README que funcione, `docker compose up`, `.env.example`, sin keys.
- [ ] URL de la demo en vivo (replay sin red).
- [ ] Portada 16:9, video ≤5 min (MP4 ≤300 MB) y slides PDF.
- [ ] Evidencia de AMD: `/v1/usage` de Token Factory y corridas pineadas.
- [x] Evidencia de Evolus: agente, biblioteca y AI Tool translate por API, intercambios grabados y pineados.
- [x] `.venv/bin/python scripts/verify_claims.py` en verde (65/65; repetir antes de enviar).
