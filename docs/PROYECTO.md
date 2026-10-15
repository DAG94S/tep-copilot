# PROYECTO — TEP Copilot (nombre provisional)

**Fecha de decisión:** 2026-10-09 · **Evento:** AMD Developer Hackathon ACT III (lablab.ai), del 12 al 18 oct 2026.
**Entrega:** 18 oct, 15:00 UTC (10:00 en Ecuador) · **Equipo:** Diego García (solo).

## 0. Estado al 15 oct (madrugada) — LEER PRIMERO
**Cambios de base:** sin GPU propia (Token Factory, ver AGENTS.md); todo lo que diga MI300X/vLLM/droplet abajo es el plan
original y ya no aplica. Detalle cronológico y cifras en `STATE.md`; cifras citables solo las de `claims.json`.

**Pitch revisado (14 oct, tras verificar dentro de cada falla):**
1. *"No deja que el modelo invente evidencia":* con thinking, Gemma acierta algo más (top-1 11→15 de 36) pero la evidencia
   rechazada por la compuerta sube de 22 % a 36 % por caso (peor en 24 de 36 pares, Wilcoxon p=0,00015).
2. *"La tarjeta llega antes que la inundación":* 4/4 fallas con inundación (≥10 alarmas/10 min) anticipadas
   (9, 615, 1.488 y 1.143 min); en IDV1 e IDV6 antes de la primera alarma. Salvedad: alarmas de nuestro sistema de límites.
3. *"El disfraz cuesta esfuerzo, no acierto (salvo IDV8)":* Rieth 10 fallas × 10 corridas, top-1 45/46/44, top-3 74/67/69,
   caída concentrada en IDV8 (10→5→5), IC95 por clusters de falla [−4, 17] pp; con thinking, tokens de razonamiento +30 %.
4. *Réplica FaultExplainer:* Gemma 4 31B 8/11 vs GPT-4o 7/11 y o1-preview 9/11 (protocolo k=5 declarado).

**Descartado (no usar):** "la compuerta sabe cuándo confiar" y "el acuerdo entre muestras predice el acierto": eran
confusión por falla (dentro de falla, top-3 p=0,09 y top-1 nada). "Colapsa inundaciones" tampoco: mediana 5,5 alarmas por tarjeta.

**Hecho:** campañas Braatz sin/con thinking, Rieth sin thinking (300), réplica FE, métricas operativas y de anticipación,
README en inglés con 33 marcadores verificados, agente de Evolus + Knowledge Library cargada por API (2 bloques).
**En curso:** Rieth con thinking n0/n2: 95/200 válidos; detenido el 15 oct ~01:30 UTC por 429 y luego Gemma 500.

## 1. A qué premios apunta
Un solo proyecto compite por varios premios a la vez, como permiten las reglas:
- **Reto principal *Intelligent Industry*** (premios de AMD, $5k repartidos entre retos).
- **Premio de Google** ($5k). Se asume que es para el mejor uso de Gemma, como en el ACT II. **Hay que confirmarlo en Discord.**
- **Track de Evolus** (€1.011 en plan y créditos).
- **Premio especial de Vibe Generation.** Criterios: valor cuantificado, ejecución técnica, diseño del flujo humano + IA.

## 2. Problema
En una perturbación de planta, los operadores reciben inundaciones de alarmas. En Milford Haven (1994) fueron
**275 alarmas en 10,7 minutos**, a razón de una cada 2 o 3 segundos (informe HSE). La alarma crítica sonó 25 minutos antes de la explosión y nadie la vio.
La guía EEMUA fija como objetivo un máximo de 10 alarmas en los primeros 10 minutos tras una perturbación grave.
Ya hay copilotos con LLM para diagnosticar fallas, pero ninguno demuestra si **razona sobre la planta**
o **recita la literatura de TEP**, que está en todos los datos de entrenamiento.

## 3. Producto
Un copiloto que colapsa la inundación de alarmas en **una tarjeta de causa raíz con evidencia verificada**.
El operador la aprueba y Evolus genera la orden de trabajo, el informe de traspaso de turno y la traducción.
El copiloto incluye su propia auditoría: la **sonda de planta gemela**.

Frase del pitch: *"Every team will show you an AI that diagnoses faults. We show you one that proves it isn't reciting the textbook."*

## 4. Arquitectura
```
Datos TEP (pineados con SHA)
 ├─ core/  [determinista] límites de alarma desde datos sin falla → eventos, tasa EEMUA,
 │          detección de inundación, orden de primera alarma ("first-out")
 ├─ core/  [determinista] PCA T²/SPE + contribución por variable
 ├─ llm/   [AMD MI300X] Gemma 4 en vLLM-ROCm → JSON con las causas top-3 y los sensores de evidencia.
 │          Autoconsistencia: k muestras en lote → voto → la confianza es el % de acuerdo
 ├─ core/  [compuerta] ¿cada sensor citado se desvió de verdad, y en la dirección que dice?
 │          ¿Hay verbos de control prohibidos? Si el acuerdo es bajo → INCIERTO, escalar a supervisor
 └─ evolus/ [REST] el agente corre sobre el vLLM propio · Workflow al aprobar → orden de trabajo +
            traspaso de turno + AI Tool de traducción · Knowledge Library con la descripción del proceso y los SOP
```

## 5. Evaluación
**Núcleo obligatorio:**
1. **Replicar FaultExplainer** con Gemma 4 31B (fp8) y 26B-A4B usando su protocolo exacto:
   PCA al 90%, T² con α=0,01, 6 alarmas consecutivas, top-6 contribuciones, 15 causas, top-3, n=1.
   Línea base: GPT-4o **7/11** y o1-preview **9/11**. PCA no detecta las fallas 3, 4, 9 ni 15.
2. **Sonda de planta gemela disfrazada:** variables, unidades y componentes renombrados, y descripción reescrita.
   Si la precisión cae frente a TEP original → hay memorización. **Cualquiera de los dos resultados sirve para el pitch.**
3. **Compuerta de sensores**: tasa de afirmaciones bloqueadas por no estar respaldadas.
4. **Versión robusta** (n≥10 corridas por falla, con SPE), reportada aparte de la réplica.

**Extras si sobra tiempo:** calibración completa, leave-fault-out en todas las fallas,
Pareto entre E2B, E4B, 12B, 26B-A4B y 31B con ablaciones del scaffold.

**Métricas para el pitch:** acierto top-1/top-3, caída de acierto en la gemela, alarmas→tarjetas,
p95 desde la alarma hasta la tarjeta en MI300X, tok/s, $ por incidente.

## 6. Decisiones técnicas
- vLLM-ROCm `v0.31.0` fijado por digest, con `--attention-backend TRITON_ATTN`; 31B en fp8 (1,2–1,45× más rápido que bf16).
- Modo *thinking* desactivado por defecto.
- El endpoint se expone con `--api-key`.
- Los datos pesados (`Faulty_Testing`) se procesan en el droplet. En local se usa el espejo Braatz d00–d21.
- La descripción del proceso sale de FaultExplainer `backend/prompts.py` (MIT). No se copia el paper (CC BY-NC-ND) y el diagrama de flujo se redibuja.
- Demo en Streamlit con replay (GPU apagada) y modo vivo. Tres audiencias: operador, mantenimiento y gerencia.

## 7. Plan (revisado 15 oct)
| Fecha | Trabajo |
|---|---|
| jue 15 | Gemma de vuelta → probar el agente con biblioteca; reanudar Rieth thinking n0/n2 (**2 procesos**); Workflow de Evolus (3.er bloque: aprobación → agente → traducción al italiano) |
| vie 16 | Rieth thinking n1; claims + README; demo "producto" (replay en tiempo real: alarmas → tarjeta → aprobar → Evolus); Docker y despliegue |
| sáb 17 | Deck, video (≤5 min), portada; reintentos si hacen falta |
| dom 18 | Enviar **antes de las 10:00 de Ecuador** |

## 8. Riesgos principales (revisado 15 oct)
1. **Token Factory inestable:** Gemma degenera o da 500 a ratos; 429 con más de 2 procesos. Reanudar con `--continuar`.
2. **Competidores muy parecidos** (FactoryPilot, Industrial Fault Copilot): ganar por evidencia medida y por la demo.
3. **Evolus:** las bases piden vLLM propio; usamos Token Factory (declararlo). Hacen falta ≥2 bloques visibles por API.
4. **Alcance:** no abrir frentes nuevos (descartado el benchmark del catálogo de modelos).

## 9. Preguntas abiertas
- ¿Qué tecnología cuenta para el premio de Google?
- ¿Cuántos créditos de Evolus consume cada llamada? Medirlo el día 1 con `creditsConsumed`.
- Nombre comercial definitivo. "FloodGate" queda descartado porque probablemente ya existe.
