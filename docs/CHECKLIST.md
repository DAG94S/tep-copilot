# CHECKLIST (actualizado 17 oct)

## Hecho
- [x] Proyecto en WSL con git; datos Braatz y Rieth (Training) pineados; FaultExplainer vendorizado.
- [x] `core/`, `twin/`, `eval/`, `llm/` con tests (150+). Token Factory configurado.
- [x] Campañas: Braatz sin thinking (+ reintentos), Braatz con thinking, Rieth sin thinking (300), réplica FaultExplainer.
- [x] `claims.json` + `verify_claims.py` (hashes, claims y marcadores del README) en verde.
- [x] README en inglés con resultados; LICENSE MIT.
- [x] Evolus: agente TEP Shift Copilot (Gemma vía Token Factory), corridas grabadas, Knowledge Library cargada por API.

## Pendiente
- [x] Experimentos cerrados salvo Rieth con thinking (abajo). La campaña vieja de 95/200 se abandonó y no se reporta. Segundo modelo Qwen hecho.
- [ ] Rieth con thinking (thinkpl) + brazo sin thinking mismo despliegue: terminar, analizar, claims (18 oct temprano).
- [x] Agente con biblioteca (instrucciones v3, con «Language policy» porque Evolus inyecta un prompt oculto en italiano) grabado y pineado con Gemma y Qwen (3/3 entregas en inglés cada uno). Gemma con v2 escribió 2/3 en italiano (defecto documentado). Gemma volvió el 16 oct como `self-dploy/Gemma-4-31B-IT`.
- [x] 3.er bloque de Evolus: AI Tool «translate» por API (no hay Workflows en la UI), grabado y pineado.
- [x] Claims y README: anticipación, evidencia inventada con thinking (control por falla), segundo modelo Qwen. Rieth con thinking se repite en el despliegue nuevo (ver Pendiente).
- [x] Demo como producto (Live replay) y funciona desde un clon (datos Braatz en el repo).
- [x] Despliegue con URL pública: https://tep-copilot-demo.streamlit.app (17 oct).
- [x] Esquema del deck y guion del video: `docs/DECK_GUION.md` (17 oct). Falta exportar el deck a PDF y grabar.
- [x] Copyright del LICENSE: Diego García (17 oct).

## Entrega en lablab (antes del 18 oct, 10:00 hora de Ecuador)
- [~] Textos en `docs/ENTREGA_LABLAB.md` (borrador): falta que Diego elija título/nombre.
- [ ] Reto *Intelligent Industry* y tags (AMD Token Factory, Gemma, Evolus).
- [x] Repo público MIT: https://github.com/DAG94S/tep-copilot (17 oct; historial revisado sin keys, clon limpio pasa verify_claims). Falta comprobar `docker compose up`.
- [x] Demo en vivo: https://tep-copilot-demo.streamlit.app (Streamlit Cloud, 17 oct; flujo completo revisado con Playwright).
- [ ] Portada 16:9, video ≤5 min (MP4 ≤300 MB) y slides PDF.
- [ ] Evidencia de AMD: `/v1/usage` de Token Factory y corridas pineadas.
- [x] Evidencia de Evolus: agente, biblioteca y AI Tool translate por API, intercambios grabados y pineados.
- [x] `.venv/bin/python scripts/verify_claims.py` en verde (repetir antes de enviar).
