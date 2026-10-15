# CHECKLIST (actualizado 15 oct)

## Hecho
- [x] Proyecto en WSL con git; datos Braatz y Rieth (Training) pineados; FaultExplainer vendorizado.
- [x] `core/`, `twin/`, `eval/`, `llm/` con tests (150+). Token Factory configurado.
- [x] Campañas: Braatz sin thinking (+ reintentos), Braatz con thinking, Rieth sin thinking (300), réplica FaultExplainer.
- [x] `claims.json` + `verify_claims.py` (hashes, claims y marcadores del README) en verde.
- [x] README en inglés con resultados; LICENSE MIT.
- [x] Evolus: agente TEP Shift Copilot (Gemma vía Token Factory), corridas grabadas, Knowledge Library cargada por API.

## Pendiente
- [ ] Rieth con thinking: n0/n2 (95/200 válidos) y n1. **Máx. 2 procesos.**
- [ ] Probar el agente con la biblioteca cuando Gemma vuelva; grabar y pinear.
- [ ] Workflow de Evolus (aprobación → agente → traducción) manejado por API; grabar ejecución.
- [x] Claims y README: anticipación y evidencia inventada con thinking (control por falla). Falta Rieth thinking.
- [ ] Demo como producto (replay en tiempo real) y despliegue con URL pública.
- [ ] Copyright del LICENSE (decide Diego).

## Entrega en lablab (antes del 18 oct, 10:00 hora de Ecuador)
- [ ] Título ≤50 caracteres, descripción corta ≤255, larga ≥100 palabras (inglés).
- [ ] Reto *Intelligent Industry* y tags (AMD Token Factory, Gemma, Evolus).
- [ ] Repo público MIT, README que funcione, `docker compose up`, `.env.example`, sin keys.
- [ ] URL de la demo en vivo (replay sin red).
- [ ] Portada 16:9, video ≤5 min (MP4 ≤300 MB) y slides PDF.
- [ ] Evidencia de AMD: `/v1/usage` de Token Factory y corridas pineadas.
- [ ] Evidencia de Evolus: agente verificado por API, biblioteca, workflow e intercambios grabados.
- [ ] `.venv/bin/python scripts/verify_claims.py` en verde.
