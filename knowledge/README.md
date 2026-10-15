# knowledge/ — documentos para la Knowledge Library de Evolus

Tres documentos en inglés (el idioma del agente) para subir a una biblioteca de conocimiento de Evolus
con `scripts/evolus_biblioteca.py`:

- `tep_process_description.md`: descripción de la planta Tennessee Eastman (Downs y Vogel, 1993): unidades,
  corrientes, las 41 XMEAS, las 11 XMV y las 15 IDV. Las tablas salen de `core/tep.py`.
- `alarm_response_procedure.md`: procedimiento genérico de respuesta a alarmas, ILUSTRATIVO (no es un SOP real),
  alineado en términos generales con ISA-18.2 y EEMUA 191. Regla de oro: ni el copiloto ni el agente operan el proceso.
- `inspection_guide_by_disturbance.md`: qué inspeccionaría mantenimiento para confirmar o descartar cada IDV(1)-(15),
  solo con verbos inspect/check/verify/measure/sample.

`tests/test_knowledge.py` comprueba con `core.compuerta.ordenes_de_control` que ninguno contiene órdenes de control.

## Salvedad importante

Estos documentos describen TEP con sus nombres reales (reactor, condenser, XMEAS(k), IDV(k)...). Por eso el agente
con biblioteca solo debe usarse sobre la vista original (nivel 0). En la planta gemela disfrazada
(otros nombres y unidades) la biblioteca revelaría qué planta es y rompería la prueba de que el sistema razona
y no recita.
