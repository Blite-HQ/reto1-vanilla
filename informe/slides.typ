// Presentación 5 minutos — Quantathon CR 2026, Challenge 1
// Compilar:  uv run python scripts/build_informe.py --slides
#set page(paper: "presentation-16-9", margin: (x: 1.6cm, y: 1.4cm))
#set text(font: "New Computer Modern", size: 19pt, lang: "es")

#let slide(title, body) = page[
  #text(size: 26pt, weight: "bold", fill: rgb("#0b3d61"))[#title]
  #v(4mm)
  #body
]

// ── 1 · Gancho (30 s) ────────────────────────────────────────────────
#slide[Zonas de falla en la red eléctrica de Costa Rica][
  #grid(columns: (1.1fr, 1fr), gutter: 6mm,
    [
      - Una falla en transmisión hay que *aislarla en islas* abriendo la
        menor capacidad posible.
      - Red real: *datos abiertos del Grupo ICE* — 70 subestaciones,
        102 circuitos, congelados y auditables.
      - Particionar minimizando corredores abiertos *es Max-Cut* (NP-hard)
        → QUBO → *QAOA* en emuladores H-series.
      #v(2mm)
      *Quantathon CR 2026 · Challenge 1*
    ],
    image("../figures/mapa-nacional.png", width: 100%),
  )
]

// ── 2 · Método (60 s) ────────────────────────────────────────────────
#slide[Método: datos → QUBO → QAOA → verificación][
  - QUBO *exacta*, sin penalizaciones: $E(x) = -"cut"(x)$, verificada en los
    $2^n$ estados.
  - Óptimos *probados con doble ancla* + digest SHA-256 por instancia: un
    archivo editado falla ruidosamente.
  - QAOA $p = 1..3$, *5 semillas*, ángulos optimizados sobre el statevector
    exacto (warm start $p-1 arrow p$); muestreo en Aer y en los emuladores
    *H2 de Quantinuum vía Nexus* (ideal + modelo de ruido).
  - Cada corte se *recomputa clásicamente* del bitstring: la verificación no
    confía en ningún backend.
  - Port de paridad a *Guppy/Selene*: mismo circuito, dos SDKs, un resultado
    ($0.8 sigma$).
]

// ── 3 · Resultados (90 s) ────────────────────────────────────────────
#slide[Resultados: r vs p, con barras de error][
  #grid(columns: (1.15fr, 1fr), gutter: 6mm,
    image("../figures/r-vs-p-cr8.png", width: 100%),
    [
      - Criterio oficial: $r >= 0.6$, $p=1$, 6 nodos → *0.829* ✓
      - `cr8` real: $r(p=3) = 0.931 plus.minus 0.011$; la mejor muestra
        *encuentra el óptimo* en todas las configuraciones.
      - Emulador H2 con ruido ≈ ideal a estas profundidades (análisis
        completo en el informe).
      - Líneas base: exacto, *GW* (SDP), greedy, recocido — GW alcanza
        $r = 1.0$ en todo.
    ],
  )
]

// ── 4 · Escalado nacional (60 s) ─────────────────────────────────────
#slide[Escalado honesto: del corredor GAM al país entero][
  #grid(columns: (1.15fr, 1fr), gutter: 6mm,
    image("../figures/escalado-nacional.png", width: 100%),
    [
      - Familia *anidada* de corredores reales:
        cr8 ⊂ cr12 ⊂ … ⊂ *cr68 = red nacional*.
      - Óptimo probado hasta 20 nodos → QAOA con estadística.
      - Muros documentados: *20 qubits* (optimización local),
        *26* (techo H2).
      - Más allá: intervalos honestos [mejor clásico, cota SDP] — *sin
        óptimos fingidos*.
    ],
  )
]

// ── 5 · Honestidad + ODS + cierre (60 s) ─────────────────────────────
#slide[La limitación es el resultado][
  - *QAOA no supera a Goemans-Williamson en Max-Cut* — garantía $p=1$
    0.6924 < 0.878; GW encuentra el óptimo en nuestras instancias. Lo
    reportamos de frente: el valor está en el flujo híbrido *verificado de
    punta a punta*.
  - ODS *7.b · 9.1/9.4 · 13.1*: una red renovable ($tilde 98%$) solo se
    sostiene con resiliencia — y el argumento va sobre *datos reales*.
  - Todo reproducible: `python reproduce.py` regenera cada cifra; 66 tests;
    corridas de Nexus y Guppy cacheadas con digest.
  #v(3mm)
  #align(center)[
    #text(size: 22pt, weight: "bold")[Gracias — preguntas]
  ]
]
