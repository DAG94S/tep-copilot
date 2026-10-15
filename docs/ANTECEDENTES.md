# ANTECEDENTES — reglas, ganadores anteriores y trabajo previo

## Reglas del ACT III (https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-iii)
- 4 retos principales: Intelligent Industry (partner Vibe Generation), Health and Wellbeing, Reinvent Commerce y Create a New Kind of Experience.
- Requisito: una parte significativa del trabajo corre en AMD, y esa parte debe verse en el producto que se muestra.
- Premios de partners acumulables: Google $5k y Evolus €1.011 (plan y créditos).
- Track de Evolus:
  - el modelo es abierto y servido en AMD (las bases dicen "vLLM propio en AMD Developer Cloud"; el FAQ general acepta
    Token Factory y no hubo crédito de GPU → usamos Token Factory y lo declaramos);
  - al menos 2 bloques de Evolus;
  - Evolus manejado vía REST;
  - app en contenedor, repo público MIT y README que funcione.
- Criterios: Application of Technology, Presentation, Business Value y Originality.
- Entrega: título, descripciones, portada, video (≤5 min), slides PDF, repo público y URL de la demo.
- Según la guía de cumplimiento de un participante del ACT II, el filtro inicial revisa el repo, el deck y la URL, **no el video**.

## Ganadores anteriores y por qué ganaron
| Proyecto | Evento | Clave |
|---|---|---|
| Chaos Economy | ACT I, gran premio | Titular medido: un modelo de 3B con GRPO supera a Nemotron de 120B |
| Intelligence for Existing CCTV | ACT II, 1.º Unicorn | Todo en 1×MI300X, Gemma, respuestas con evidencia en video, "sin infraestructura nueva" |
| AgeBand | ACT II, 2.º | "El LLM estima, la capa determinista decide"; p95, tok/s, $/1k turnos; 462 tests |
| CacheForge | ACT II, 3.º | Optimización específica de la MI300X; −36% de TTFT medido |

Patrones que se repiten:
1. Un número titular medido.
2. Una frase-invariante de seguridad.
3. Un "¿por qué AMD?" real.
4. Evidencia junto a cada respuesta.
5. "Funciona sobre lo que ya tienes".
6. Gemma servido en AMD.

## Trabajo previo que hay que citar (el espacio está muy explorado)
**Investigación:**
- FaultExplainer (Khan et al., Computers & Chemical Engineering 2025; arXiv 2412.14492; github li-group/FaultExplainer, MIT).
- TEP RCA Workbench de Chennan Li (https://chennanli.github.io/posts/04-tep-agentic-rca-workbench/): arquitectura casi idéntica
  (detección determinista, herramientas de solo lectura, compuerta humana, regex contra verbos de control).
- AIChE 2025: framework multiagente con RAG sobre TEP.
- Kunze & Fay 2025: causa raíz de inundaciones de alarmas con un grafo causal adaptativo en TEP.
- Zhou & Liang 2026 (IEEE DataPort, DOI 10.21227/m4y0-dp64): 13.273 llamadas a LLM sobre TEP, calibración.

**Hackathons con ideas parecidas:** NexusOps (AMD ACT II), Sentinel (AMD Developer Challenge), OCE (ET AI Hackathon 2.0), IndustrialPilot (Devpost).

**Conclusión:** un copiloto de causa raíz con humano en el circuito no es original por sí mismo.
La parte defendible es la **sonda de planta gemela disfrazada** (no se encontró ningún antecedente). Revisar a fondo antes de afirmarlo en el pitch.

## Gancho del problema (verificado)
HSE, *The explosion and fires at the Texaco Refinery, Milford Haven, 24 July 1994* (HSE Books 1997):
- 275 alarmas en los últimos 10,7 minutos;
- una alarma cada 2 o 3 segundos;
- 87% de las alarmas configuradas como alta prioridad;
- 26 heridos y unos £48M en daños (HSE chis6).

Objetivo EEMUA 191: ≤1 alarma cada 10 minutos en operación normal y ≤10 en los primeros 10 minutos tras una perturbación grave.

## Competidores vistos en ACT III (lablab, 14 oct)
- **FactoryPilot** (Qwen2.5-VL en vLLM sobre MI300X según su texto): foto + log de sensores + manual en biblioteca de Evolus,
  5 guardrails deterministas, "calibrated confidence", TTFT y tok/s en la app, workflow de Evolus con aprobación.
- **Industrial Fault Copilot** (Java/Spring + Evolus): diagnóstico con citas del manual del variador ABB ACS580 y escalamiento.
- Ambos *prometen* verificación; ninguno publica medidas sobre un benchmark con línea base. Nuestra ventaja: todo medido.
