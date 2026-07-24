# Statement de SDK (≤200 palabras)

Elegimos **Qiskit** para construir y optimizar los circuitos QAOA localmente
(statevector exacto + muestreo Aer con semillas), el puente
**pytket/qnexus** para compilar y ejecutar en los emuladores H-series de
Quantinuum, y un **port de paridad a Guppy** (el SDK recomendado) ejecutado
en Selene/Quest.

**Qué funcionó.** `qiskit_to_tk` tradujo los circuitos sin fricción; el flujo
qnexus (`upload → compile → execute`) fue confiable; cada corte se recomputa
clásicamente desde los bitstrings, así que la verificación es agnóstica al
backend. El port a Guppy reproduce la media exacta dentro de 1σ estadística
(test automatizado).

**Qué no funcionó.** El endpoint de costos de qnexus falla con alias de
dispositivo (usamos una cota HQC local documentada). El emulador remoto no
expone semilla por shot: sus corridas son estadística, no réplicas exactas.
Guppy no tiene RZZ nativo (lo descompusimos como CX·RZ·CX) y sus ángulos usan
semigiros — convención tket que la documentación no explicita; la fijamos
empíricamente contra RX(π) y la cubrimos con un test de paridad.

**Qué faltó.** Acceso a una QPU real vía Nexus (solo emuladores visibles),
semillas reproducibles en el emulador remoto, y documentación clara de las
convenciones de ángulo de Guppy.
