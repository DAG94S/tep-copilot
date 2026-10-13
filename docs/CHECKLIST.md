# CHECKLIST

## Antes del kickoff (12 oct)
**Te toca a ti:**
- [ ] **HOY:** AMD AI Developer Program → Member Perks → Request Cloud Credits → elegir **AMD Developer Cloud** (no Fireworks).
      El formulario pide afiliación, cargo, uso previsto y un perfil público (LinkedIn o GitHub). Aprobación en 2–3 días hábiles.
      El crédito se activa con el enlace del correo y caduca 30 días después de activarlo.
- [ ] Inscribirse en lablab ACT III y en su Discord. Preguntar qué tecnología cuenta para el premio de Google.
- [ ] Crear la cuenta de GitHub para el repo público (si se usa una nueva) y la de Streamlit Community Cloud.
- [ ] Instalar Ollama en Windows y bajar `gemma4:e2b-it-qat`.

**Me toca a mí (Claude):**
- [ ] Mover el proyecto a WSL e inicializar git (pendiente de tu decisión).
- [ ] `scripts/descargar_datos.py`: espejo Braatz d00–d21, `prompts.py` y CSV de FaultExplainer, y FaultFree_Training → `SHA256SUMS`.
- [ ] `core/`: alarmas, PCA T²/SPE, contribuciones y compuerta, con tests.
- [ ] `twin/`: la planta gemela disfrazada.
- [ ] Prompts probados con E2B en local.
- [ ] Cliente de Evolus con mocks. **No crear el workspace antes del enlace del evento.**

## Entrega en lablab (antes del 18 oct, 10:00 hora de Ecuador)
- [ ] Título de 50 caracteres o menos, descripción corta de 255 o menos y descripción larga de 100 palabras o más (en inglés).
- [ ] Reto *Intelligent Industry* y tags (AMD Developer Cloud, ROCm, Gemma, Evolus).
- [ ] Repo público MIT, README que funcione, `docker compose up`, `.env.example`, sin keys.
- [ ] URL de la demo en vivo (replay que funcione con la GPU apagada).
- [ ] Portada 16:9, video de 5 min o menos (MP4, 300 MB o menos) y slides PDF.
- [ ] Evidencia de AMD: logs de vLLM, modelo, `rocm-smi`, benchmarks en `data/runs/`.
- [ ] Evidencia de Evolus: IDs de workflow y estadísticas de uso.
- [ ] `scripts/verify_claims.py` en verde.
