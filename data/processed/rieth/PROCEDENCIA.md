# Procedencia: Rieth et al. (2017), partición de entrenamiento

- Fuente: Rieth, Amsel, Tran & Cook (2017), Harvard Dataverse, doi:10.7910/DVN/6C3JR1 (dominio público, CC0).
- Archivos usados: `TEP_FaultFree_Training.RData` y `TEP_Faulty_Training.RData` (MD5 verificado contra Dataverse; SHA-256 en `SHA256SUMS`). No se usó ningún `*_Testing`.
- Extraído: simulaciones `simulationRun` 1..20 de las fallas 1..20 (Faulty_Training NO trae la falla 21) y de FaultFree, 500 muestras x 52 variables (xmeas_1..41, xmv_1..11, mismo orden que `core.datos.cargar`). Falla introducida en la muestra 21 (índice 20).
- Comandos (2026-10-14):
  1. `/usr/bin/time -v Rscript scripts/extraer_rieth.R` (R 4.5.3, base). Pico de RAM medido: **3.086.372 kB (~3,1 GB)**, 15,6 s.
  2. `.venv/bin/python scripts/convertir_rieth.py` -> `faulty_train_f01..f20.npz`, `faultfree_train.npz` (claves `x` (20,500,52) float32, `runs`).
- Intento descartado: pyreadr superó 5,5 GB de RSS (5.892.072 kB, abortado), por eso se usó R.
- Sanity de detección T² (calibración Braatz `normal_ampliado`): `deteccion_t2.json` (generado por `scripts/deteccion_rieth.py`).
