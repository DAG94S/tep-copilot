# STATE.md — TEP Copilot: registro de decisiones y avances

## 2026-10-09 — Cambio de proyecto y decisiones base
- **Se descarta AuditCorp-EC (SERCOP/SRI).** Motivo: los premios principales del ACT III solo se dan en 4 retos
  (Intelligent Industry, Health, Commerce, Experience) y la idea de compras públicas no encaja en ninguno.
  Solo competía por Evolus (créditos de plataforma, no efectivo). Además, su validación era circular (casos sintéticos).
- **Proyecto elegido:** copiloto de sala de control sobre el Tennessee Eastman Process que demuestra que razona.
  Reto *Intelligent Industry*, más los premios de Google (se asume Gemma, sin confirmar) y Evolus.
- **Diferenciador:** la sonda de **planta gemela disfrazada**. Es la única pieza sin antecedente encontrado;
  la calibración, la compuerta y el Pareto ya tienen trabajo previo en 2026 (ver `docs/ANTECEDENTES.md`).
- **Línea base:** FaultExplainer, GPT-4o 7/11 y o1-preview 9/11 (no 6/11, corregido). Su protocolo:
  PCA al 90%, T² con α=0,01, 6 alarmas consecutivas, top-6 contribuciones, 15 causas, acierto si la causa está en el top-3,
  n=1 por falla. Se replicará tal cual y aparte se reportará una versión robusta (n≥10, con SPE).
- **Modelo:** Gemma 4 31B (fp8) + 26B-A4B en 1×MI300X; E2B/E4B en local. Apache-2.0, no gated. Modo *thinking* desactivado.
- **Hosting de la demo:** Streamlit Community Cloud, con Render como respaldo (HF Docker Spaces ya es de pago).
- **Deadline:** 18 oct 15:00 UTC = **10:00 hora de Ecuador**.
- **Viabilidad:** ejecutable con cambios (`docs/VIABILIDAD.md`).
- **Carpeta:** se borró todo lo de AuditCorp-EC. Respaldo temporal en el scratchpad de la sesión
  (`respaldo_auditcorp_2026-10-09.tgz`). Se creó la estructura nueva.

## Pendiente antes del kickoff (12 oct)
Ver `docs/CHECKLIST.md`.

## 2026-10-09 (tarde) — Mudanza a WSL
- El proyecto pasa de OneDrive (`10_Investigacion/AMD_HACKATON`) a `~/proyectos/tep-copilot`. Motivos: TEP pesa ~1,3 GB (no debe
  sincronizarse con OneDrive), `/mnt/e` es lento para pip/Docker/git y OneDrive puede bloquear archivos. Copia verificada con SHA-256
  (25 archivos idénticos). En OneDrive solo queda `LEEME.md` apuntando aquí.
- `git init -b main`: archivos en staging, sin commit todavía.
- La memoria engram del proyecto sigue con la clave `amd_hackaton`.

## 2026-10-09 (noche) — Inscripción y crédito de GPU
- Inscrito en el ACT III; equipo `TEP_copilot` (solo, Closed); conectado al Discord de lablab.
- Solicitud de crédito AMD Developer Cloud enviada (perfiles: ORCID y GitHub DAG94S). AMD avisa demoras de hasta 5 días hábiles
  (podría llegar el 16 oct). Correo a devcloudrequests@amd.com enviado pidiendo prioridad por la fecha límite.
- **Plan B con fecha de corte:** si el martes 13 oct no hay crédito, pago por uso en AMD Developer Cloud
  (MI300X ≈ $1,99/h; campaña mínima ≈ 3 GPU-h ≈ $6; realista 10–20 h ≈ $20–40). Requiere tarjeta.
- Riesgo abierto: el crédito de $100 es solo para cuentas ADP nuevas; si la cuenta del usuario ya existía puede rechazarse.
- Preguntas pendientes en Discord (#ineedhelp): pods/créditos por equipo en el ACT III y qué tecnología cuenta para el premio de Google.

## 2026-10-09 (noche) — Datos y primer detector
- `scripts/descargar_datos.py`: espejo Braatz d00–d21 (commit `9a6c8e5f…`, licencia tipo NCSA/UIUC con atribución).
  46 archivos, 26 MB, SHA-256 en `SHA256SUMS`; segunda ejecución verifica sin cambios.
- **Schema externo:** `d00.dat` viene TRANSPUESTO (52×500, no 480×52 como indica el README del espejo).
  Normalizado en `core/datos.py`.
- `core/pca_t2.py`: PCA 90%, T² α=0,01, 6 alarmas consecutivas, contribuciones de Kourti-MacGregor. Con d00 como entrenamiento
  (500 muestras): A=31 componentes, UCL=57,02; sin falsas alarmas en d00_te.
  No detectadas: IDV 3, 9, 15 y 19. FaultExplainer reporta 3, 4, 9, 15 (usa otros datos: Rieth). **Aún no es una réplica**;
  falta correr con Rieth y fijar el protocolo exacto antes de comparar con su 7/11.
- Entorno: `.venv` (ignorado por git), `pytest` en `requirements.txt`.
