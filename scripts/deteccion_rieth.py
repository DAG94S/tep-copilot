"""Sanity de detección T2 sobre Rieth (20 simulaciones por falla 1..15). Uso: python3 -m scripts.deteccion_rieth"""
import json, numpy as np
from core import datos, pca_t2
m = pca_t2.ajustar(datos.normal_ampliado())
i0 = datos.INICIO_FALLA_RIETH_TRAIN
tab = {}
fa = 0
for run in range(1, 21):
    if pca_t2.primera_alarma(m, datos.cargar_rieth(0, run).astype(float)) is not None: fa += 1
for f in range(1, 16):
    ret, previas = [], 0
    for run in range(1, 21):
        x = datos.cargar_rieth(f, run).astype(float)
        a = pca_t2.primera_alarma(m, x[:i0 + 0]) if True else None
        if a is not None: previas += 1
        a = pca_t2.primera_alarma(m, x)
        if a is not None and a >= i0: ret.append(int(a - i0))
    tab[f] = dict(detectadas=len(ret), de=20, retardo_mediano_muestras=(float(np.median(ret)) if ret else None), alarmas_antes_de_falla=previas)
out = dict(detector="T2 (core.pca_t2, 6 consecutivas, alfa 0.01) calibrado con datos.normal_ampliado() (Braatz)",
           inicio_falla_indice=i0, retardo_desde_indice_falla_en_muestras_de_3min=True,
           faultfree_corridas_con_alarma=fa, faultfree_corridas=20, fallas=tab)
json.dump(out, open("data/processed/rieth/deteccion_t2.json", "w"), indent=1)
print("faultfree con alarma:", fa, "/20")
for f, v in tab.items(): print(f, v)
