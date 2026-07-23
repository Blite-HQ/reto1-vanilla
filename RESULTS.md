# Resultados (generado por reproduce.py — no editar a mano)

Entorno: Python 3.12.3, cvxpy 1.9.2, networkx 3.6.1, numpy 2.5.1, qiskit 2.5.1, qiskit-aer 0.17.2, scipy 1.18.0

## Líneas base clásicas

| instancia | óptimo | GW (mejor) | cota SDP | greedy | SA (mejor) |
|---|---|---|---|---|---|
| cr6-uniforme | 5 | 5 | 5.2 | 5 | 5 |
| cr8-uniforme | 7 | 7 | 7.5 | 7 | 7 |
| cr8-voltaje | 1150 | 1150 | 1242.0 | 1150 | 1150 |
| ieee14-flujo | 57070 | 57070 | 57766.9 | 56814 | 57070 |
| ieee30-flujo | 32170 | 32170 | 33076.8 | 30197 | 31862 |
| ieee9-uniforme | 9 | 9 | 9.0 | 9 | 9 |

## QAOA local (statevector exacto + muestreo Aer)

| instancia | p | r = ⟨cut⟩/óptimo (media ± σ) | r mejor muestra |
|---|---|---|---|
| cr6-uniforme | 1 | 0.8286 ± 0.0000 | 1.0000 |
| cr6-uniforme | 2 | 0.8849 ± 0.0084 | 1.0000 |
| cr6-uniforme | 3 | 0.9305 ± 0.0024 | 1.0000 |
| cr8-uniforme | 1 | 0.8609 ± 0.0000 | 1.0000 |
| cr8-uniforme | 2 | 0.9040 ± 0.0061 | 1.0000 |
| cr8-uniforme | 3 | 0.9307 ± 0.0113 | 1.0000 |
| cr8-voltaje | 1 | 0.8588 ± 0.0000 | 1.0000 |
| cr8-voltaje | 2 | 0.9036 ± 0.0000 | 1.0000 |
| cr8-voltaje | 3 | 0.9200 ± 0.0132 | 1.0000 |
| ieee14-flujo | 1 | 0.7606 ± 0.0000 | 1.0000 |
| ieee14-flujo | 2 | 0.8421 ± 0.0012 | 1.0000 |
| ieee14-flujo | 3 | 0.8605 ± 0.0170 | 1.0000 |
| ieee9-uniforme | 1 | 0.7312 ± 0.0000 | 1.0000 |
| ieee9-uniforme | 2 | 0.8170 ± 0.0000 | 1.0000 |
| ieee9-uniforme | 3 | 0.8488 ± 0.0189 | 1.0000 |

## Emuladores Quantinuum (vía Nexus, ángulos optimizados localmente)

| instancia | p | device | shots | r media | r mejor muestra |
|---|---|---|---|---|---|
| cr6-uniforme | 1 | H2-1LE | 1024 | 0.8211 | 1.0000 |
| cr6-uniforme | 1 | H2-Emulator | 256 | 0.8148 | 1.0000 |
| cr6-uniforme | 2 | H2-1LE | 1024 | 0.8898 | 1.0000 |
| cr6-uniforme | 3 | H2-1LE | 1024 | 0.9324 | 1.0000 |
| cr8-uniforme | 1 | H2-1LE | 1024 | 0.8556 | 1.0000 |
| cr8-uniforme | 1 | H2-Emulator | 1024 | 0.8556 | 1.0000 |
| cr8-uniforme | 2 | H2-1LE | 1024 | 0.9088 | 1.0000 |
| cr8-uniforme | 2 | H2-Emulator | 1024 | 0.9021 | 1.0000 |
| cr8-uniforme | 3 | H2-1LE | 1024 | 0.9441 | 1.0000 |
| cr8-uniforme | 3 | H2-Emulator | 1024 | 0.9344 | 1.0000 |
| cr8-voltaje | 1 | H2-1LE | 1024 | 0.8596 | 1.0000 |
| cr8-voltaje | 2 | H2-1LE | 1024 | 0.9020 | 1.0000 |
| cr8-voltaje | 3 | H2-1LE | 1024 | 0.9154 | 1.0000 |
| ieee14-flujo | 1 | H2-1LE | 1024 | 0.7591 | 1.0000 |
| ieee14-flujo | 2 | H2-1LE | 1024 | 0.8422 | 1.0000 |
| ieee14-flujo | 3 | H2-1LE | 1024 | 0.8548 | 1.0000 |
| ieee9-uniforme | 1 | H2-1LE | 1024 | 0.7286 | 1.0000 |
| ieee9-uniforme | 2 | H2-1LE | 1024 | 0.8197 | 1.0000 |
| ieee9-uniforme | 3 | H2-1LE | 1024 | 0.8506 | 1.0000 |

Limitación honesta: QAOA no supera a Goemans-Williamson en Max-Cut en ninguna instancia; la garantía p=1 (0.6924) es estrictamente menor que la de GW (0.878). Ver el informe para la discusión completa.
