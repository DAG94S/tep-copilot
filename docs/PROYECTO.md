# PROYECTO — TEP Copilot (nombre provisional)

**Fecha de decisión:** 2026-10-09 · **Evento:** AMD Developer Hackathon ACT III (lablab.ai), del 12 al 18 oct 2026.
**Entrega:** 18 oct, 15:00 UTC (10:00 en Ecuador) · **Equipo:** Diego García (solo).

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

## 7. Plan
| Fecha | Trabajo |
|---|---|
| 9–11 oct | Pipeline determinista local, planta gemela, prompts con Gemma 4 E2B en Ollama, cliente Evolus con mocks |
| 12 oct | Kickoff, workspace de Evolus desde el enlace del evento, primer flujo completo |
| 13–14 oct | GPU: campaña grabada (≤3 GPU-h). **Congelar el alcance el 14** |
| 15 oct | Integración con Evolus · **destruir el droplet** |
| 16 oct | App, Docker, despliegue |
| 17 oct | README con afirmaciones verificadas, deck y video de 3 min |
| 18 oct | Enviar **antes de las 10:00 de Ecuador** |

## 8. Riesgos principales
1. **La GPU puede llegar tarde** (aprobación de 2–3 días hábiles). Pedir el crédito ya y diseñar la campaña para ≤3 GPU-h.
2. **Alcance excesivo.** Congelarlo el 14 de octubre.
3. **Evolus no se puede probar hasta el 12.** Usar solo 2 bloques y grabar sus salidas para el replay.

## 9. Preguntas abiertas
- ¿Qué tecnología cuenta para el premio de Google?
- ¿Cuántos créditos de Evolus consume cada llamada? Medirlo el día 1 con `creditsConsumed`.
- Nombre comercial definitivo. "FloodGate" queda descartado porque probablemente ya existe.
