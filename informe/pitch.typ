// Pitch deck — Quantathon CR 2026, Challenge 1
// Compilar:  uv run python scripts/build_informe.py --pitch
//
// Sistema de diseño heredado de docs/index.html (tokens Blite / Chimera Studio
// DESIGN.md v3), tema claro — las figuras de matplotlib tienen fondo blanco.
// Los tokens OKLCH del front se convirtieron a sus equivalentes sRGB:
//   brand oklch(0.6 0.118 184.704) -> #0d9488   chart-2 oklch(0.541 .281 293) -> #7c3aed
//   chart-3 oklch(0.588 .158 242)  -> #0284c7   chart-4 oklch(0.666 .179 58)  -> #d97706

#let C = (
  bg: rgb("#ffffff"),
  fg: rgb("#0a0a0a"),
  mut: rgb("#555555"),
  bord: rgb("#e5e5e5"),
  soft: rgb("#f5f5f5"),
  brand: rgb("#0d9488"), // --brand / --chart-1  (Zona A)
  c2: rgb("#7c3aed"), // --chart-2            (Zona B)
  c3: rgb("#0284c7"), // --chart-3
  c4: rgb("#d97706"), // --chart-4 / --status-warning
  ok: rgb("#059669"), // --status-success
  ink: rgb("#0a0a0a"), // fondo de portada/cierre (tema oscuro del front)
  inkfg: rgb("#fafafa"),
  inkbrand: rgb("#2dd4bf"), // --brand en tema oscuro
  inkmut: rgb("#a3a3a3"),
)

#set page(
  paper: "presentation-16-9",
  margin: (x: 1.5cm, top: 1.15cm, bottom: 1.15cm),
  fill: C.bg,
  footer: context {
    set text(size: 8.5pt, fill: C.mut)
    grid(
      columns: (1fr, auto),
      align(left)[#text(fill: C.brand, weight: 700)[blite] · Reto 1 — Quantathon CR 2026],
      align(right)[#counter(page).display()],
    )
  },
  footer-descent: 0.55cm,
)

#set text(font: ("Lato", "DejaVu Sans"), size: 14pt, lang: "es", fill: C.fg)
#set par(spacing: 0.72em, leading: 0.62em)
#show raw: set text(font: "DejaVu Sans Mono", size: 0.86em, fill: C.brand)
#set list(marker: text(fill: C.brand)[•], indent: 2pt, body-indent: 6pt, spacing: 0.78em)

// ── Componentes (espejo del CSS del front) ──────────────────────────────────
#let panel(body, bg: C.bg, edge: C.bord, inset: (x: 11pt, y: 9pt)) = block(
  width: 100%,
  fill: bg,
  stroke: 0.6pt + edge,
  radius: 4.5pt,
  inset: inset,
  body,
)

#let statcard(key, val, sub: none) = panel[
  #text(size: 8pt, fill: C.mut, weight: 600, tracking: 0.9pt)[#upper(key)]
  #v(-2.4mm)
  #text(size: 18pt, weight: 700)[#val]
  #if sub != none [ #text(size: 9pt, fill: C.mut)[#sub] ]
]

#let inkstat(key, val, sub: none) = block(
  width: 100%,
  stroke: 0.6pt + rgb("#ffffff26"),
  radius: 4.5pt,
  inset: (x: 10pt, y: 8pt),
)[
  #text(size: 8pt, fill: C.inkmut, weight: 600, tracking: 0.9pt)[#upper(key)]
  #v(-2.4mm)
  #text(size: 17pt, weight: 700, fill: C.inkfg)[#val]
  #if sub != none [ #text(size: 9pt, fill: C.inkmut)[#sub] ]
]

#let pill(t) = box(
  fill: rgb("#ecfdf5"),
  stroke: 0.5pt + rgb("#a7f3d0"),
  radius: 999pt,
  inset: (x: 5.5pt, y: 1.6pt),
)[#text(size: 8pt, fill: C.ok, weight: 600)[#t]]

#let warn(body) = block(
  width: 100%,
  fill: rgb("#fffbeb"),
  stroke: 0.7pt + rgb("#fcd34d"),
  radius: 4.5pt,
  inset: (x: 12pt, y: 10pt),
  body,
)

#let dtable(..args) = table(
  stroke: (_, y) => (bottom: if y == 0 { 0.9pt + C.mut } else { 0.5pt + C.bord }),
  inset: (x: 7pt, y: 5.2pt),
  fill: (_, y) => if y == 0 { none } else { none },
  ..args,
)

#let th(t) = text(size: 8.5pt, fill: C.mut, weight: 600, tracking: 0.6pt)[#upper(t)]

// ── Plantillas de diapositiva ───────────────────────────────────────────────
// `size` sube el cuerpo en las diapositivas de puro texto para que llenen el
// 16:9 y se lean proyectadas; las que llevan figura o tabla se quedan en 14pt.
#let slide(title, body, kicker: none, size: 14pt) = page[
  #if kicker != none {
    text(size: 9pt, weight: 700, fill: C.brand, tracking: 1.3pt)[#upper(kicker)]
    v(-3.2mm)
  }
  #text(size: 23pt, weight: 700, tracking: -0.4pt)[#title]
  #v(0.4fr)
  #set text(size: size)
  #body
  #v(1fr)
]

#let inkslide(body) = page(fill: C.ink, footer: none)[
  #set text(fill: C.inkfg)
  #set list(marker: text(fill: C.inkbrand)[•], indent: 2pt, body-indent: 6pt, spacing: 0.78em)
  #body
]

// ── Mini-motor de dibujo para el grafo cr8 ──────────────────────────────────
// Coordenadas idénticas al SVG de docs/index.html (viewBox 760 x 430),
// reencuadradas al bounding box real del grafo (XOFF/YOFF) para no dejar aire.
#let K = 0.027cm
#let XOFF = 60
#let YOFF = 45
#let gx(u) = (u - XOFF) * K
#let gy(u) = (u - YOFF) * K

#let gedge(a, b, col, dashed) = place(
  top + left,
  line(
    start: (gx(a.at(0)), gy(a.at(1))),
    end: (gx(b.at(0)), gy(b.at(1))),
    stroke: (paint: col, thickness: 2.4pt, dash: if dashed { (3pt, 3pt) } else { none }, cap: "round"),
  ),
)

#let gnode(p, r, col) = place(
  top + left,
  dx: gx(p.at(0)) - r,
  dy: gy(p.at(1)) - r,
  circle(radius: r, fill: col, stroke: none),
)

#let glabel(p, off, txt, w: 3.4cm, weight: 400) = place(
  top + left,
  dx: gx(p.at(0)) - w / 2,
  dy: gy(p.at(1)) + off,
  box(width: w)[#align(center)[#text(size: 11.5pt, weight: weight)[#txt]]],
)

#let swatch(col, t, dashed: false) = box(baseline: 1.5pt)[
  #if dashed [
    #box(width: 15pt, height: 0pt, stroke: (paint: col, thickness: 2pt, dash: (3pt, 3pt)))
  ] else [
    #box(width: 9pt, height: 9pt, fill: col, radius: 2pt)
  ]
  #h(4pt)#text(size: 10pt, fill: C.mut)[#t]
]

// ── Mini-motor de barras para r vs p ────────────────────────────────────────
#let CH = (w: 21.4cm, h: 8.5cm, base: 7.5cm, top: 1.0cm, x0: 2.2cm)
#let yfor(v) = CH.base - (v - 0.5) / 0.5 * (CH.base - CH.top)

#let gridline(v, col: C.bord, dashed: false, lbl: none, lblcol: C.mut) = {
  place(
    top + left,
    dy: yfor(v),
    line(
      start: (CH.x0, 0pt),
      end: (CH.w, 0pt),
      stroke: (paint: col, thickness: 0.7pt, dash: if dashed { (4pt, 4pt) } else { none }),
    ),
  )
  place(top + left, dx: 0cm, dy: yfor(v) - 0.24cm, box(width: CH.x0 - 0.22cm)[
    #align(right)[#text(size: 9pt, fill: C.mut, font: "DejaVu Sans Mono")[#lbl]]
  ])
}

#let bar(x, v, col) = {
  let bw = 1.5cm
  place(top + left, dx: x, dy: yfor(v), rect(
    width: bw,
    height: CH.base - yfor(v),
    fill: col,
    stroke: none,
    radius: (top: 2.5pt),
  ))
  place(top + left, dx: x - 0.3cm, dy: yfor(v) - 0.56cm, box(width: bw + 0.6cm)[
    #align(center)[#text(size: 9.5pt, font: "DejaVu Sans Mono", weight: 600)[#v]]
  ])
}

#let bargroup(center, vals) = {
  let xs = (center - 2.45cm, center - 0.75cm, center + 0.95cm)
  let cols = (C.brand, C.c3, C.c4)
  for i in range(3) { bar(xs.at(i), vals.at(i), cols.at(i)) }
}

// ════════════════════════════════════════════════════════════════════════════
// 1 · PORTADA
// ════════════════════════════════════════════════════════════════════════════
#inkslide[
  #v(0.7cm)
  #text(size: 9.5pt, weight: 700, fill: C.inkbrand, tracking: 1.6pt)[QUANTATHON CR 2026 · RETO 1 · DOJO CODING · UCR · OQI · QUANTINUUM]
  #v(4mm)

  #text(size: 40pt, weight: 700, tracking: -1.2pt)[
    Cuando la red eléctrica falla, \ #text(fill: C.inkbrand)[¿por dónde se corta?]
  ]

  #v(4mm)
  #block(width: 68%)[
    #text(size: 14pt, fill: C.inkmut)[
      Particionamiento de zonas de falla en la red de transmisión de Costa Rica,
      modelado como *Max-Cut* y resuelto con *QAOA* en los emuladores
      *Quantinuum H2* — sobre datos abiertos reales del Grupo ICE.
    ]
  ]

  #v(1fr)

  #grid(
    columns: (1fr, 1fr, 1fr, 1fr),
    gutter: 4mm,
    inkstat("Escalera nacional", "8 → 68", sub: [ subestaciones]),
    inkstat("Óptimo probado", "hasta n = 20", sub: [ doble ancla]),
    inkstat("Mejor r en emulador H2", "0.944", sub: [ cr8, p = 3]),
    inkstat("Reproducibilidad", "61 tests", sub: [ · SHA-256]),
  )

  #v(1fr)

  #text(size: 8.5pt, fill: C.inkbrand, weight: 700, tracking: 1.2pt)[EQUIPO]
  #v(-2mm)
  // ── EDITAR: 1 a 4 integrantes ──
  #text(size: 13pt)[Dylan Chaves · #text(fill: C.inkmut)[Integrante 2 · Integrante 3 · Integrante 4]]
  #v(0.2cm)
]

// ════════════════════════════════════════════════════════════════════════════
// 2 · EL PROBLEMA
// ════════════════════════════════════════════════════════════════════════════
#slide(size: 16.5pt, kicker: "El problema", [Una falla no se apaga: se #text(fill: C.brand)[aísla]])[
  #v(2mm)
  #grid(
    columns: (1.25fr, 1fr),
    gutter: 7mm,
    [
      - Cuando una línea de transmisión falla, la perturbación *se propaga*.
        La defensa rápida del operador es abrir interruptores y partir la red
        en *islas* que contengan el daño.

      - Cada corredor que se abre es capacidad de transporte que se pierde.
        La pregunta no es *si* cortar, sino *dónde* — y esa decisión hay que
        tomarla en segundos.

      - Costa Rica opera con #sym.tilde\98% de generación renovable. Una red
        así solo se sostiene si es resiliente: el clima es la primera causa de
        fallas de transmisión del país.
    ],
    [
      #panel(bg: C.soft)[
        #text(size: 8pt, fill: C.mut, weight: 600, tracking: 0.9pt)[LA ANALOGÍA]
        #v(-1mm)
        #text(size: 13pt)[
          Como las *compuertas estancas* de un barco: ante una vía de agua se
          cierran las justas para que el daño no pase al resto del casco —
          no todas, porque el barco tiene que seguir navegando.
        ]
      ]
      #v(3mm)
      #statcard("La decisión operativa", "¿Dónde cortar?", sub: [ · sobre un grafo real])
    ],
  )
]

// ════════════════════════════════════════════════════════════════════════════
// 3 · LOS DATOS
// ════════════════════════════════════════════════════════════════════════════
#slide(size: 15pt, kicker: "Los datos", [No es un grafo de juguete: es #text(fill: C.brand)[la red del país]])[
  #v(1mm)
  #grid(
    columns: (1.35fr, 1fr),
    gutter: 7mm,
    align: horizon,
    panel(inset: 5pt)[#image("../figures/mapa-nacional.png", width: 100%)],
    [
      - *Datos abiertos del Grupo ICE*: 70 subestaciones y 102 circuitos de
        transmisión, descargados el 23 de julio de 2026.

      - Los archivos crudos quedan *congelados en el repositorio* con su URL y
        su fecha: cualquiera puede reconstruir el grafo desde cero.

      - Cada instancia lleva un *sello SHA-256*. Si alguien edita un dato, el
        programa se niega a correr en vez de contaminar el resultado en
        silencio.

      #v(1mm)
      #panel(bg: C.soft)[
        #text(size: 11.5pt)[
          Del grafo nacional salen *68 subestaciones* conectadas por
          *90 corredores* — y de ahí un corredor de 8 para la parte cuántica.
        ]
      ]
    ],
  )
]

// ════════════════════════════════════════════════════════════════════════════
// 4 · EL MODELO
// ════════════════════════════════════════════════════════════════════════════
#slide(size: 15pt, kicker: "El modelo", [Partir la red es un problema clásico: #text(fill: C.brand)[Max-Cut]])[
  #v(2mm)
  #grid(
    columns: (1fr, 1fr),
    gutter: 7mm,
    [
      Pintamos cada subestación de uno de dos colores — *Zona A* o *Zona B*.
      Una línea "cuenta" si une dos colores distintos. El reto define el
      particionamiento como *maximizar lo que cuenta*: la frontera de
      separación más marcada posible.

      #v(2mm)
      #panel[
        #set align(center)
        #v(1mm)
        $ "corte"(x) = sum_((i,j) in E) w_(i j) (x_i + x_j - 2 x_i x_j) $
        #v(1mm)
      ]
      #v(-1mm)
      #text(size: 10.5pt, fill: C.mut)[
        $x_i in {0, 1}$ es la zona de cada subestación; $w_(i j)$, cuántos
        circuitos unen ese par. Es la *única* fórmula que hace falta entender.
      ]
    ],
    [
      #statcard("Por qué no basta con probar todo", "2⁶⁸ ≈ 3 × 10²⁰", sub: [ formas de repartir 68 subestaciones])
      #v(3mm)
      - Max-Cut es *NP-hard*: no se conoce ningún algoritmo eficiente que lo
        resuelva siempre.

      - A esta escala aún se puede probar todo por fuerza bruta y *demostrar*
        el óptimo — por eso sabemos exactamente qué tan bien lo hace cada
        método.

      - Ese es justo el terreno donde tiene sentido evaluar un algoritmo
        cuántico: con la respuesta correcta en la mano.
    ],
  )
]

// ════════════════════════════════════════════════════════════════════════════
// 5 · EL CASO ESTRELLA (grafo cr8 nativo)
// ════════════════════════════════════════════════════════════════════════════
#slide(kicker: "El caso estrella", [Ocho subestaciones del GAM, partidas de forma #text(fill: C.brand)[óptima]])[
  #v(-0.5mm)
  #align(center)[
    #box(width: gx(700), height: gy(398))[
      // corredores cortados (7)
      #gedge((345, 215), (490, 295), C.brand, true)
      #gedge((345, 215), (155, 275), C.brand, true)
      #gedge((345, 215), (460, 95), C.brand, true)
      #gedge((490, 295), (625, 240), C.brand, true)
      #gedge((490, 295), (635, 355), C.brand, true)
      #gedge((165, 145), (155, 275), C.brand, true)
      #gedge((310, 85), (460, 95), C.brand, true)
      // corredores internos (2)
      #gedge((345, 215), (165, 145), C.mut, false)
      #gedge((345, 215), (310, 85), C.mut, false)
      // Zona A
      #gnode((345, 215), 0.36cm, C.brand)
      #gnode((625, 240), 0.29cm, C.brand)
      #gnode((165, 145), 0.29cm, C.brand)
      #gnode((310, 85), 0.29cm, C.brand)
      #gnode((635, 355), 0.29cm, C.brand)
      // Zona B
      #gnode((490, 295), 0.29cm, C.c2)
      #gnode((155, 275), 0.29cm, C.c2)
      #gnode((460, 95), 0.29cm, C.c2)
      // etiquetas
      #glabel((345, 215), 0.46cm, "La Caja", weight: 700)
      #glabel((490, 295), 0.42cm, "Alajuelita")
      #glabel((625, 240), -1.0cm, "Anonos")
      #glabel((165, 145), -1.0cm, "Belén")
      #glabel((155, 275), 0.42cm, "Ribera")
      #glabel((310, 85), -1.0cm, "Colima")
      #glabel((460, 95), -1.0cm, "Heredia")
      #glabel((635, 355), 0.42cm, "Cóncavas")
    ]
  ]
  #v(1mm)
  #grid(
    columns: (auto, 1fr),
    gutter: 6mm,
    align: horizon,
    [
      #swatch(C.brand, "Zona A") #h(7mm)
      #swatch(C.c2, "Zona B") #h(7mm)
      #swatch(C.brand, "Corte óptimo: 7 de 9 corredores", dashed: true)
    ],
    align(right)[#text(size: 9.5pt, fill: C.mut, font: "DejaVu Sans Mono")[digest 66bb6c5a…f91392]],
  )
]

// ════════════════════════════════════════════════════════════════════════════
// 6 · LA TRADUCCIÓN
// ════════════════════════════════════════════════════════════════════════════
#slide(kicker: "La traducción", [Del mapa al circuito cuántico, #text(fill: C.brand)[sin trucos]])[
  #v(1.5mm)
  #grid(
    columns: (1fr, 1fr, 1fr, 1fr),
    gutter: 4mm,
    panel[#text(size: 8pt, fill: C.mut, weight: 600, tracking: 0.9pt)[PASO 1] #v(-1.5mm) #text(size: 12pt)[*Grafo* \ Subestaciones y corredores con peso]],
    panel[#text(size: 8pt, fill: C.mut, weight: 600, tracking: 0.9pt)[PASO 2] #v(-1.5mm) #text(size: 12pt)[*QUBO* \ Una función de energía sobre bits]],
    panel[#text(size: 8pt, fill: C.mut, weight: 600, tracking: 0.9pt)[PASO 3] #v(-1.5mm) #text(size: 12pt)[*Ising* \ Esa energía, escrita en qubits]],
    panel(edge: C.brand)[#text(size: 8pt, fill: C.brand, weight: 600, tracking: 0.9pt)[PASO 4] #v(-1.5mm) #text(size: 12pt)[*QAOA* \ El circuito que la minimiza]],
  )

  #v(3mm)
  #grid(
    columns: (1fr, 1fr),
    gutter: 7mm,
    [
      #panel[
        #set align(center)
        #v(0.5mm)
        $ E(x) = x^top Q x = -"corte"(x) $
        #v(1mm)
        #text(size: 10pt, fill: C.mut)[minimizar la energía #sym.equiv maximizar el corte]
        #v(0.5mm)
      ]
      #v(2mm)
      #panel[
        #set align(center)
        #v(0.5mm)
        $ C = sum_((i,j) in E) w_(i j) (1 - Z_i Z_j) / 2 $
        #v(1mm)
        #text(size: 10pt, fill: C.mut)[la misma energía, ya en lenguaje de qubits]
        #v(0.5mm)
      ]
    ],
    [
      - Max-Cut *no tiene restricciones*, así que la traducción es *exacta*:
        sin penalizaciones, sin hiperparámetros que calibrar, sin soluciones
        inválidas que filtrar después.

      - No lo afirmamos: lo *verificamos estado por estado*, los $2^n$, con un
        test automatizado. Si la identidad fallara en uno solo, el test cae.

      - Ese detalle importa: la mayoría de los fracasos en optimización
        cuántica ocurren en la traducción, no en el circuito.
    ],
  )

  #v(3mm)
  #panel(bg: C.soft)[
    #text(size: 13.5pt)[
      *En cristiano:* convertimos «¿por dónde parto la red?» en «¿qué
      combinación de ceros y unos tiene la energía más baja?» — y *esa* segunda
      pregunta es la que un computador cuántico sabe atacar.
    ]
  ]
]

// ════════════════════════════════════════════════════════════════════════════
// 7 · EL MÉTODO CUÁNTICO
// ════════════════════════════════════════════════════════════════════════════
#slide(size: 15pt, kicker: "El método cuántico", [QAOA, #text(fill: C.brand)[sin jerga]])[
  #v(2mm)
  #grid(
    columns: (1fr, 1fr, 1fr),
    gutter: 5mm,
    panel[
      #text(size: 20pt, weight: 700, fill: C.brand)[1]
      #v(-1mm)
      #text(size: 12.5pt)[*Considerar todo a la vez* \ #v(1mm) El computador arranca en superposición: las $2^n$ particiones posibles, simultáneamente.]
    ],
    panel[
      #text(size: 20pt, weight: 700, fill: C.brand)[2]
      #v(-1mm)
      #text(size: 12.5pt)[*Empujar hacia lo bueno* \ #v(1mm) Cada capa premia los cortes grandes y luego mezcla. Más capas ($p$) = mejor afinado.]
    ],
    panel[
      #text(size: 20pt, weight: 700, fill: C.brand)[3]
      #v(-1mm)
      #text(size: 12.5pt)[*Leer y verificar* \ #v(1mm) Se mide 1024 veces. Cada lectura es una partición concreta que evaluamos con matemática clásica.]
    ],
  )

  #v(4mm)
  #grid(
    columns: (1.15fr, 1fr),
    gutter: 7mm,
    panel(bg: C.soft)[
      #text(size: 8pt, fill: C.mut, weight: 600, tracking: 0.9pt)[EL REPARTO HÍBRIDO — DECLARADO, NO ESCONDIDO]
      #v(-0.5mm)
      #text(size: 12pt)[
        Los ángulos del circuito se afinan por *simulación exacta local*; el
        emulador cuántico *muestrea* con esos ángulos. Es la práctica estándar
        a escala NISQ, y la reportamos como límite del trabajo.
      ]
    ],
    [
      #statcard("La métrica, siempre la misma", [$r = ⟨"corte"⟩ \/ "óptimo"$])
      #v(2mm)
      #text(size: 11pt, fill: C.mut)[
        Nunca el costo bruto ni una corrida suelta: media #sym.plus.minus
        desviación estándar sobre 5 semillas.
      ]
    ],
  )
]

// ════════════════════════════════════════════════════════════════════════════
// 8 · RESULTADOS (gráfico nativo r vs p)
// ════════════════════════════════════════════════════════════════════════════
#slide(kicker: "Resultados", [Más capas, mejores cortes — y las tres fuentes #text(fill: C.brand)[coinciden]])[
  #v(0mm)
  #align(center)[
    #box(width: CH.w, height: CH.h)[
      #gridline(0.500, lbl: "0.500")
      #gridline(0.625, lbl: "0.625")
      #gridline(0.750, lbl: "0.750")
      #gridline(0.875, lbl: "0.875")
      #gridline(1.000, col: C.ok, dashed: true, lbl: "1.000")
      #place(top + left, dx: CH.w - 5.4cm, dy: CH.top - 0.62cm)[
        #box(width: 5.4cm)[#align(right)[#text(size: 9.5pt, fill: C.ok)[óptimo · GW también llega a 1.000]]]
      ]

      #bargroup(5.6cm, (0.861, 0.856, 0.856))
      #bargroup(12.1cm, (0.904, 0.909, 0.902))
      #bargroup(18.6cm, (0.931, 0.944, 0.934))

      #place(top + left, dy: CH.base, line(start: (CH.x0, 0pt), end: (CH.w, 0pt), stroke: 0.9pt + C.mut))
      #for (x, t) in ((5.6cm, "p = 1"), (12.1cm, "p = 2"), (18.6cm, "p = 3")) {
        place(top + left, dx: x - 2cm, dy: CH.base + 0.14cm, box(width: 4cm)[
          #align(center)[#text(size: 11.5pt, fill: C.mut)[#t]]
        ])
      }
    ]
  ]
  #v(-1mm)
  #grid(
    columns: (auto, 1fr),
    gutter: 5mm,
    align: horizon,
    [
      #swatch(C.brand, "Simulación local exacta") #h(6mm)
      #swatch(C.c3, "H2-1LE (ideal)") #h(6mm)
      #swatch(C.c4, "H2-Emulator (con ruido)")
    ],
    align(right)[
      #text(size: 11pt)[
        Criterio oficial del reto (#text(font: "DejaVu Sans Mono", size: 0.88em)[r ≥ 0.6], $p = 1$, 6 nodos): obtuvimos *0.829* #h(2mm) #pill("superado")
      ]
    ],
  )
  #v(1mm)
  #text(size: 11pt, fill: C.mut)[
    Y en las tres fuentes la *mejor lectura encuentra el óptimo exacto* ($r = 1.000$): el
    circuito sí produce la respuesta correcta — lo que queda por debajo es su valor promedio.
  ]
]

// ════════════════════════════════════════════════════════════════════════════
// 9 · HARDWARE
// ════════════════════════════════════════════════════════════════════════════
#slide(size: 15.5pt, kicker: "Hardware", [Corrió de verdad en los emuladores #text(fill: C.brand)[H2 de Quantinuum]])[
  #v(1mm)
  #grid(
    columns: (1.3fr, 1fr),
    gutter: 7mm,
    align: horizon,
    panel(inset: 5pt)[#image("../figures/ruido-h2.png", width: 100%)],
    [
      - *19 corridas* enviadas vía Nexus a H2-1LE (ideal) y H2-Emulator
        (modelo de ruido real de la familia H-series).

      - El ruido *casi no degrada* a estas profundidades: en `cr8` con $p=3$,
        0.944 ideal contra 0.934 con ruido. Circuitos cortos, 6–14 qubits.

      - Cada corte se *recomputa clásicamente* desde los bits medidos: la
        verificación no le cree a ningún backend.

      - Port de paridad a *Guppy/Selene* (el SDK recomendado): mismo circuito,
        dos SDKs, un solo resultado — dentro de #sym.tilde\0.8#sym.sigma.
    ],
  )
]

// ════════════════════════════════════════════════════════════════════════════
// 10 · LA VARA
// ════════════════════════════════════════════════════════════════════════════
#slide(size: 15pt, kicker: "La vara", [Nos medimos contra lo mejor que existe, #text(fill: C.brand)[no contra un espantapájaros]])[
  #v(2mm)
  #grid(
    columns: (1.5fr, 1fr),
    gutter: 7mm,
    [
      #dtable(
        columns: (auto, auto, auto, auto, auto, auto),
        align: (left, right, right, right, right, right),
        table.header(
          th("Instancia"), th("Óptimo"), th("GW"), th("Cota SDP"), th("Greedy"), th("Recocido"),
        ),
        [cr6-uniforme], [5], [5], [5.2], [5], [5],
        [*cr8-uniforme*], [*7*], [*7*], [7.5], [7], [7],
        [cr8-voltaje], [1150], [1150], [1242.0], [1150], [1150],
        [ieee9-uniforme], [9], [9], [9.0], [9], [9],
        [ieee14-flujo], [57070], [57070], [57766.9], [56814], [57070],
        [ieee30-flujo], [32170], [32170], [33076.8], [30197], [31862],
      )
    ],
    [
      - *Goemans-Williamson* (1995) es el mejor algoritmo de aproximación
        conocido para Max-Cut: garantiza $#h(1pt) >= 0.878$ del óptimo.

      - En nuestras instancias hace algo mejor todavía: *encuentra el óptimo
        exacto*. La vara real no es 0.878, es *1.000*.

      - La *cota SDP* es un techo matemático riguroso: ningún método puede
        superarla. La usamos como ancla de cordura y como denominador honesto
        donde no hay óptimo probado.
    ],
  )
]

// ════════════════════════════════════════════════════════════════════════════
// 11 · HONESTIDAD
// ════════════════════════════════════════════════════════════════════════════
#slide(size: 15.5pt, kicker: "Honestidad", [QAOA no le gana a Goemans-Williamson. #text(fill: C.brand)[Lo decimos primero.]])[
  #v(2mm)
  #warn[
    #text(size: 13.5pt)[
      *La garantía de QAOA con $p = 1$ es 0.6924 — estrictamente menor que el
      0.878 de GW.* Y en nuestras instancias GW además encuentra el óptimo.
      No hay ventaja cuántica aquí, y presentarla sería el error.
    ]
  ]
  #v(3mm)
  #grid(
    columns: (1fr, 1fr),
    gutter: 7mm,
    [
      - A estas escalas (6–30 nodos) un solver clásico exacto responde en
        *milisegundos*.

      - Los ángulos se optimizan en simulación local; el emulador muestrea,
        no optimiza dentro del lazo.

      - Los pesos por voltaje son un *proxy documentado*: los datos abiertos
        del ICE no traen capacidad en MVA.
    ],
    [
      - La factibilidad física del aislamiento (balance generación/carga por
        isla, criterio N-1) *no está codificada* en Max-Cut plano.

      - Reportar hardware sin análisis de ruido, o un óptimo que no se puede
        probar, son *red flags*. Las evitamos por diseño.
    ],
  )
  #v(3mm)
  #panel(bg: C.soft)[
    #text(size: 13.5pt)[
      El entregable no es un speedup: es un *flujo híbrido verificado de punta
      a punta* — datos reales #sym.arrow modelo exacto #sym.arrow hardware
      #sym.arrow verificación independiente — que declara sus límites en vez
      de esconderlos.
    ]
  ]
]

// ════════════════════════════════════════════════════════════════════════════
// 12 · ESCALADO
// ════════════════════════════════════════════════════════════════════════════
#slide(size: 13.5pt, kicker: "Escalado", [Del corredor del GAM #text(fill: C.brand)[al país entero]])[
  #v(1.5mm)
  #grid(
    columns: (1.25fr, 1fr),
    gutter: 7mm,
    [
      #dtable(
        columns: (auto, auto, auto, auto, auto, auto, auto),
        align: (right, left, right, right, right, right, right),
        table.header(
          th("n"), th("Estado"), th("Mejor corte"), th("GW"), th("Recocido"),
          th("Cota SDP"), th("r ≥"),
        ),
        [8], [#pill("óptimo probado")], [7], [7], [7], [7.50], [1.0000],
        [12], [#pill("óptimo probado")], [14], [14], [14], [14.32], [1.0000],
        [16], [#pill("óptimo probado")], [22], [22], [22], [22.54], [1.0000],
        [20], [#pill("óptimo probado")], [26], [26], [26], [26.79], [1.0000],
        [26], [intervalo], [34], [34], [34], [35.07], [0.9695],
        [34], [intervalo], [44], [44], [44], [45.29], [0.9716],
        [44], [intervalo], [55], [55], [55], [57.67], [0.9538],
        [56], [intervalo], [69], [69], [68], [71.75], [0.9617],
        [*68*], [intervalo], [*83*], [82], [*83*], [86.43], [0.9603],
      )
      #v(1.5mm)
      #text(size: 10.5pt, fill: C.mut)[
        $n = 68$ es la red nacional completa. Hasta $n = 20$ el óptimo está
        *probado*; de 26 en adelante el valor verdadero vive en el intervalo
        [mejor corte, cota SDP].
      ]
    ],
    [
      - Un mismo criterio determinista hace crecer el corredor:
        `cr8 ⊂ cr12 ⊂ … ⊂ cr68`, la red nacional completa.

      - *Los muros son reales y están documentados*: 20 qubits para optimizar
        ángulos localmente, 26 como techo del emulador H2. Más allá no hay
        pata cuántica posible hoy — con ningún equipo.

      - Por eso, de 26 nodos en adelante reportamos un *intervalo*
        [mejor corte hallado, cota SDP] y no un óptimo inventado.

      #v(1mm)
      #panel(bg: C.soft)[
        #text(size: 11.5pt)[
          *Hallazgo:* con 68 subestaciones el recocido simulado supera a GW
          por primera vez en toda la escalera (83 vs 82). Ninguna heurística
          domina — justo por eso el intervalo es la respuesta correcta.
        ]
      ]
    ],
  )
]

// ════════════════════════════════════════════════════════════════════════════
// 13 · CONFIANZA
// ════════════════════════════════════════════════════════════════════════════
#slide(size: 16pt, kicker: "Confianza", [No hay que creernos: #text(fill: C.brand)[se puede volver a correr]])[
  #v(2mm)
  #grid(
    columns: (1fr, 1fr, 1fr, 1fr),
    gutter: 4mm,
    statcard("Un solo comando", "reproduce.py"),
    statcard("Suite de pruebas", "61 tests", sub: [ verdes]),
    statcard("Por instancia", "SHA-256", sub: [ digest canónico]),
    statcard("Por óptimo", "2 anclas", sub: [ independientes]),
  )

  #v(4mm)
  #grid(
    columns: (1fr, 1fr),
    gutter: 7mm,
    [
      - Cada óptimo está probado por *dos algoritmos independientes*. Si
        discrepan, el generador *aborta* en vez de escribir un número dudoso.

      - Los registros crudos guardan ángulos, conteos, entorno y digest. Las
        corridas de Nexus y de Guppy quedan *cacheadas*: el informe se
        regenera sin credenciales y sin red.
    ],
    [
      - El cuaderno narrativo se re-ejecuta de punta a punta; los datos crudos
        del ICE están congelados con su fecha de descarga.

      - Todo lo que se muestra en este pitch sale de ese pipeline. *Nada está
        escrito a mano.*
    ],
  )
]

// ════════════════════════════════════════════════════════════════════════════
// 14 · IMPACTO Y CIERRE
// ════════════════════════════════════════════════════════════════════════════
#inkslide[
  #v(0.4cm)
  #text(size: 9.5pt, weight: 700, fill: C.inkbrand, tracking: 1.6pt)[IMPACTO · ODS 7.b · 9.1 / 9.4 · 13.1]
  #v(3mm)
  #text(size: 30pt, weight: 700, tracking: -0.8pt)[
    Una red más resiliente es la condición \ para seguir siendo #text(fill: C.inkbrand)[98% renovable].
  ]

  #v(6mm)
  #grid(
    columns: (1fr, 1fr),
    gutter: 9mm,
    [
      #text(size: 8.5pt, fill: C.inkbrand, weight: 700, tracking: 1.2pt)[LA CADENA CAUSAL]
      #v(-1mm)
      #text(size: 13pt, fill: C.inkmut)[
        Mejores particiones de aislamiento #sym.arrow menos capacidad perdida
        por falla y restauración más rápida #sym.arrow una red que integra más
        renovable variable sin sacrificar resiliencia.
      ]
    ],
    [
      #text(size: 8.5pt, fill: C.inkbrand, weight: 700, tracking: 1.2pt)[QUÉ SIGUE]
      #v(-1mm)
      #text(size: 13pt, fill: C.inkmut)[
        Codificar la factibilidad física — balance generación/carga por isla y
        criterio N-1 — con *constraint mixers*, la extensión oficial del reto.
      ]
    ],
  )

  #v(1fr)
  #align(center)[
    #text(size: 26pt, weight: 700)[Gracias — #text(fill: C.inkbrand)[preguntas]]
  ]
  #v(0.6cm)
  #align(center)[#text(size: 10.5pt, fill: C.inkmut)[
    Código, datos, informe y dashboard: reproducible con `python reproduce.py`
  ]]
  #v(0.4cm)
]
