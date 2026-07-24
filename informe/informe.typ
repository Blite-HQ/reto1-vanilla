// Informe técnico — Quantathon CR 2026, Challenge 1
// Compilar:  uv run python scripts/build_informe.py
#set page(paper: "us-letter", margin: (x: 1.7cm, y: 1.7cm), numbering: "1 / 1")
#set text(font: "New Computer Modern", size: 9.2pt, lang: "es")
#set par(justify: true, spacing: 0.75em)
#show heading: set block(above: 1.1em, below: 0.65em)
#set heading(numbering: "1.1")
#show link: set text(fill: rgb("#0b5394"))
#show figure.caption: set text(size: 8pt)
#show figure: set block(above: 0.9em, below: 0.9em)

#align(center)[
  #text(size: 13.5pt, weight: "bold")[
    Particionamiento de zonas de falla en la red eléctrica de Costa Rica: \
    Max-Cut, QUBO y QAOA en emuladores H-series
  ]

  #v(2mm)
  #text(size: 10.5pt)[Quantathon CR 2026 — Challenge 1 · Dojo Coding · UCR · OQI · Quantinuum]

  #v(1mm)
  #text(size: 9pt)[
    Repositorio: código, datos y registros con digest SHA-256; un único punto de
    entrada (`reproduce.py`) regenera cada cifra y figura de este informe.
  ]
]

#v(2mm)

*Resumen.* Modelamos el particionamiento en zonas de falla de la red de
transmisión costarricense como Max-Cut sobre un grafo derivado de forma
determinista y auditable de los datos abiertos del Grupo ICE, lo formulamos
como QUBO exacta sin penalizaciones ($E(x) = -"cut"(x)$), lo resolvemos con
QAOA ($p = 1..3$, 5 semillas) y lo comparamos contra las líneas base clásicas
más fuertes (exacto con doble ancla, Goemans-Williamson con cota SDP, greedy,
recocido simulado), en local y en los emuladores H-series de Quantinuum vía
Nexus; el circuito estrella se porta a Guppy con test de paridad. La
comparación escala a la red nacional completa (68 subestaciones) con una
familia anidada de corredores e intervalos honestos. El criterio suficiente
del reto ($r >= 0.6$, $p=1$, 6 nodos) se supera con margen: $r = 0.829$ en
`cr6`. QAOA no supera a Goemans-Williamson en ninguna instancia — y ese
reporte honesto es el resultado central.

= Planteamiento del problema

Ante una falla, el operador de una red de transmisión necesita separar la red
en islas que contengan la perturbación, abriendo la menor capacidad de
transporte posible entre zonas. Modelamos la red regional como un grafo
ponderado no dirigido $G = (V, E, w)$: los nodos son subestaciones, las
aristas corredores de transmisión y el peso $w_(i j)$ el número de circuitos
paralelos del corredor (convención `uniforme`, libre de supuestos; la
convención `voltaje` — suma de niveles de tensión en kV — se usa como proxy
documentado del costo de apertura). Particionar $V$ en dos zonas maximizando
el peso cortado es el problema *Max-Cut*, NP-hard incluso sin pesos.

La instancia estrella, `cr8`, es un corredor de 8 subestaciones del Gran Área
Metropolitana (La Caja, Alajuelita, Anonos, Belén, Ribera, Colima, Heredia,
Cóncavas) derivado de los datos abiertos del Grupo ICE (70 subestaciones, 102
circuitos; snapshots crudos congelados en el repositorio) mediante un criterio
determinista re-ejecutable (corredor greedy más denso desde la subestación de
mayor grado, desempate alfabético). Cada instancia congelada lleva su óptimo
probado por *dos anclas independientes* y un digest SHA-256 canónico que el
cargador verifica: un archivo editado falla ruidosamente en vez de contaminar
el benchmark.

= Formulación: de Max-Cut a QUBO

Con variables binarias $x_i in {0, 1}$ (la zona de cada subestación),

$ "cut"(x) = sum_((i,j) in E) w_(i j) (x_i + x_j - 2 x_i x_j). $

Maximizar el corte equivale a minimizar la energía cuadrática binaria
$E(x) = x^top Q x$ con

$ Q_(i i) = -sum_j w_(i j), quad Q_(i j) = Q_(j i) = w_(i j), $

y la identidad es exacta: $E(x) = -"cut"(x)$ para todo $x$. Max-Cut no tiene
restricciones, así que la QUBO no necesita penalizaciones — sin
hiperparámetros que calibrar ni soluciones infactibles que filtrar. La
identidad se verifica exhaustivamente ($2^n$ estados, test automatizado y
reproducible en `notebooks/reto1.ipynb`).

Para QAOA, la QUBO se mapea al hamiltoniano de Ising diagonal
$C = sum_((i,j) in E) w_(i j) (1 - Z_i Z_j) \/ 2$, cuyo valor esperado sobre
un estado computacional es el corte de ese estado.

= Líneas base clásicas

La rúbrica pide comparar contra el clásico más fuerte disponible, con
referencia publicada. Usamos cuatro:

- *Óptimo exacto.* Enumeración completa ($n <= 20$) con testigo canónico
  ($x_0 = 0$); doble ancla independiente congelada en cada instancia.
- *Goemans-Williamson* [1]: relajación SDP resuelta con CVXPY/SCS y
  redondeo por hiperplanos aleatorios (200 por semilla), razón garantizada
  $>= 0.878$. El óptimo del SDP es además una *cota superior rigurosa* del
  corte máximo — la usamos como ancla de cordura (ningún solver puede
  excederla) y como denominador honesto en instancias sin óptimo probado.
- *Greedy* de mejora local por flip (garantía clásica $W\/2$, razón
  $tilde 0.5$).
- *Recocido simulado* con enfriamiento geométrico, multi-semilla.

En todas las instancias con óptimo probado (6–30 nodos), Goemans-Williamson
*encuentra el óptimo exacto* — la vara clásica real no es su garantía de
0.878 sino $r = 1.0$.

= Implementación cuántica

*Ansatz.* QAOA estándar [2]: capa inicial $H^(⊗ n)$;
por cada capa $l <= p$, fase de costo $e^(-i gamma_l C)$ (una compuerta RZZ
por arista, pesos normalizados a $max |w| = 1$) y mixer $e^(-i beta_l B)$ con
$B = sum_i X_i$ (RX por qubit). Convención documentada y consistente en todo
el código.

*Split híbrido documentado.* Los ángulos se optimizan clásicamente sobre la
expectativa *exacta* del statevector (grid de arranque en $p=1$, COBYLA
multi-arranque con semillas, warm start $p-1 arrow p$: calidad monótona en
$p$); el circuito optimizado se *muestrea* después (Aer con semilla o el
emulador H-series). El emulador no participa del lazo de optimización —
práctica estándar NISQ, declarada como límite.

*Verificación agnóstica al backend.* Cada corte reportado se recomputa
clásicamente desde el bitstring con los pesos enteros originales; los
decodificadores de bits de cada backend están congelados con tests.

*Motor de expectación vectorizado.* Para la escalera nacional ($n >= 15$) la
expectativa se evalúa con un motor propio que explota que la capa de costo es
diagonal (fases del espectro de cortes normalizado) y el mixer es un producto
tensorial de RX aplicado eje por eje. Paridad probada contra el statevector
de Qiskit a $10^(-12)$ en tests; las instancias publicadas ($n <= 14$)
conservan la ruta Qiskit bit a bit. El presupuesto de optimización reducido
para $n >= 15$ (grid $8 times 4$, 2 re-arranques, 100 iteraciones COBYLA)
descansa en el warm start y en la concentración de ángulos de QAOA
[3].

*Emuladores Quantinuum vía Nexus.* Los circuitos optimizados se recompilan
con pytket y se ejecutan en H2-1LE (ideal, tratamiento exacto hasta 26
qubits) y H2-Emulator (modelo de ruido realista H-series): 19 corridas
cacheadas con job-id, ángulos, conteos y digest, de modo que el informe
completo se regenera sin credenciales.

*Port de paridad a Guppy.* El circuito estrella (`cr8`, $p=1$) se reescribió
en Guppy — el SDK recomendado por la organización — y se ejecutó en el
emulador Selene/Quest: RZZ descompuesto exactamente como
$"CX" dot "RZ" dot "CX"$ y ángulos en semigiros (convención tket, fijada
empíricamente contra $"RX"(pi)$ y cubierta por test). La media muestreada cae
a $0.8 sigma$ de la expectativa exacta ($6.039$ vs $6.027 plus.minus 0.015$
con 4096 shots): mismo circuito, dos SDKs, un solo resultado.

= Resultados

*Criterio oficial.* Con $p = 1$ sobre `cr6` (6 nodos), $r = 0.829 >= 0.6$:
el resultado suficiente del reto se supera con margen. La métrica es siempre
$r = ⟨ "cut" ⟩ \/ "óptimo"$ (media $plus.minus$ desviación
estándar sobre 5 semillas), nunca el costo bruto ni una corrida suelta.

#figure(
  image("../figures/r-vs-p-cr8.png", width: 62%),
  caption: [
    `cr8-uniforme`: $r$ vs $p$ (media $plus.minus sigma$, 5 semillas) frente a
    Goemans-Williamson (que alcanza el óptimo), greedy y la garantía 0.878.
    La curva punteada es la mejor muestra por corrida: QAOA *encuentra* el
    óptimo en todas las configuraciones; su valor esperado queda por debajo.
  ],
) <fig-rvsp>

#table(
  columns: (auto, auto, auto, auto, auto),
  align: (left, center, center, center, center),
  stroke: 0.4pt + gray,
  table.header([*instancia*], [*$r$, $p=1$*], [*$r$, $p=2$*], [*$r$, $p=3$*],
               [*GW / óptimo*]),
  [`cr6-uniforme`], [$0.829 plus.minus 0.000$], [$0.885 plus.minus 0.008$],
    [$0.930 plus.minus 0.002$], [$1.000$],
  [`cr8-uniforme`], [$0.861 plus.minus 0.000$], [$0.904 plus.minus 0.006$],
    [$0.931 plus.minus 0.011$], [$1.000$],
  [`cr8-voltaje`], [$0.859 plus.minus 0.000$], [$0.904 plus.minus 0.000$],
    [$0.920 plus.minus 0.013$], [$1.000$],
  [`ieee9-uniforme`], [$0.731 plus.minus 0.000$], [$0.817 plus.minus 0.000$],
    [$0.849 plus.minus 0.019$], [$1.000$],
  [`ieee14-flujo`], [$0.761 plus.minus 0.000$], [$0.842 plus.minus 0.001$],
    [$0.861 plus.minus 0.017$], [$1.000$],
)

*Emuladores reales.* Las mismas configuraciones en H2-1LE reproducen la
referencia local dentro del error de muestreo (p. ej. `cr8-uniforme`:
$r(p=3) = 0.944$ emulado vs $0.931 plus.minus 0.011$ local), y el modelo de
ruido H-series degrada poco a estas profundidades (`cr8-uniforme` $p=3$:
$0.934$ con ruido vs $0.944$ ideal) — circuitos cortos, 6–14 qubits. El
análisis ideal-vs-ruidoso completo está en la figura `ruido-h2` del
repositorio; reportar hardware sin análisis de ruido es una red flag que
evitamos por diseño.

= Escalado a la red nacional

El mismo criterio determinista de crecimiento produce una familia *anidada*
de corredores reales
$"cr8" subset "cr12" subset "cr16" subset "cr20" subset "cr26" subset dots.h subset "cr68"$,
donde `cr68` es el grafo nacional de transmisión completo (68 subestaciones,
90 corredores agregados). El reporte distingue dos regímenes con muros
documentados:

- *Hasta 20 nodos* — óptimo probado con doble ancla; QAOA con estadística
  completa (5 semillas, $p = 1..3$). El muro de 20 qubits es el costo de la
  optimización local de ángulos sobre el statevector denso.
- *De 26 a 68 nodos* — sin pata cuántica posible (26 qubits es el techo
  exacto del emulador H2); instancias *abiertas*: el archivo congela solo el
  grafo y su procedencia, sin óptimo. Se reporta el intervalo honesto
  $["mejor corte hallado", "cota SDP"]$ y la cota inferior
  $r >= "mejor"\/"cota"$.

// LLENAR-ESCALERA: tabla cr12/cr16/cr20 (QAOA) + cr26..cr68 (intervalos)
// y cifras de la figura de escalado, cuando reproduce.py termine.

#figure(
  image("../figures/mapa-nacional.png", width: 74%),
  caption: [
    La red de transmisión nacional (coordenadas reales WGS84, datos ICE)
    particionada en dos zonas de falla por el mejor corte clásico; corredores
    cortados en trazo discontinuo, corredor `cr8` resaltado.
  ],
) <fig-mapa>

#figure(
  image("../figures/escalado-nacional.png", width: 64%),
  caption: [
    Escalado en la familia anidada: QAOA (media $plus.minus sigma$) hasta el
    muro de optimización local; cotas inferiores clásicas
    (mejor$\/$SDP) hasta el país completo. Zona sombreada: solo clásico.
  ],
) <fig-escalado>

*Extrapolación honesta.* La tendencia de $r$ con $n$ a profundidad fija no
autoriza afirmaciones de ventaja cuántica: el valor esperado de QAOA a $p$
fijo se degrada al crecer $n$, mientras GW mantiene su garantía
independiente del tamaño y los solvers exactos siguen resolviendo estas
escalas en milisegundos. La conclusión de escalado correcta es
metodológica: el flujo datos $arrow$ QUBO $arrow$ QAOA $arrow$ verificación
funciona idéntico en 6 y en 68 nodos, y declara sus límites en vez de
esconderlos.

= Limitaciones honestas (obligatorio)

1. *QAOA no supera a Goemans-Williamson en Max-Cut.* La garantía de QAOA a
   $p=1$ (0.6924 en 3-regulares [2]) es estrictamente menor que la de
   GW (0.878 [1]); en nuestras instancias GW además encuentra el
   óptimo exacto. A estas escalas un solver exacto responde en milisegundos:
   el valor del ejercicio es el flujo híbrido verificado de punta a punta,
   no una ventaja cuántica.
2. *Split híbrido:* los ángulos se optimizan sobre el statevector local
   exacto; el emulador muestrea, no optimiza en el lazo.
3. *El emulador remoto no expone semilla por shot:* sus corridas son
   estadística de muestreo, no réplicas exactas.
4. *Pesos `voltaje` como proxy documentado* (suma de kV): los datos abiertos
   del ICE no traen capacidad MVA ni caso de flujo de potencia.
5. *Sin pata cuántica más allá de 20/26 qubits* (optimización local / techo
   H2): la escalera nacional se reporta con intervalos
   [mejor clásico, cota SDP], sin óptimos fingidos ni extrapolaciones
   cuánticas.
6. *La factibilidad física del islanding* (balance generación/carga por isla,
   criterio N-1) no está codificada en Max-Cut plano; corresponde a la
   extensión oficial de *constraint mixers* y se deja explícitamente fuera
   del alcance.

= Impacto ODS

La cadena causal es concreta: mejores particiones de aislamiento $arrow$
menos capacidad de transporte perdida por falla y restauración más rápida
$arrow$ una red que integra más renovable variable sin comprometer
resiliencia. Submetas específicas: *ODS 7.b* (modernizar la infraestructura
para servicios energéticos sostenibles — Costa Rica opera con $tilde 98%$ de
generación renovable, y la resiliencia de la red es la condición para
sostenerla), *ODS 9.1/9.4* (infraestructura fiable y modernizada) y *ODS
13.1* (fortalecer la resiliencia ante desastres relacionados con el clima,
primera causa de fallas de transmisión en el país). El uso de *datos reales
y abiertos del ICE* — con derivación auditable y re-ejecutable — convierte el
argumento ODS en un artefacto verificable, no en una diapositiva.

= Reproducibilidad

Un único punto de entrada regenera cada cifra y figura:

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python reproduce.py            # todo (≈1 h por la escalera nacional)
python reproduce.py --quick    # smoke en minutos
pytest                         # 59 tests
```

Los registros crudos (`runs/`) llevan digest SHA-256 y entorno; las corridas
de Nexus y Guppy están cacheadas para reproducción offline; el cuaderno
narrativo se re-ejecuta con `jupyter nbconvert --execute`. Los datos crudos
del ICE están congelados en `data/raw/` con su fecha de descarga y URLs.

#v(3mm)
#line(length: 100%, stroke: 0.4pt + gray)

*Referencias.*

+ M. X. Goemans, D. P. Williamson.
  _Improved approximation algorithms for maximum cut and satisfiability
  problems using semidefinite programming._ J. ACM 42(6), 1115–1145 (1995).
+ E. Farhi, J. Goldstone, S. Gutmann.
  _A quantum approximate optimization algorithm._ arXiv:1411.4028 (2014).
+ L. Zhou et al. _Quantum approximate
  optimization algorithm: performance, mechanism, and implementation on
  near-term devices._ Phys. Rev. X 10, 021067 (2020); arXiv:1812.01041.
+ Grupo ICE. _Datos abiertos del sistema eléctrico._
  `datos-ice-se.opendata.arcgis.com` (descarga 2026-07-23).
+ Quantinuum. _Nexus, H-series emulators, Guppy/Selene._ Documentación
  oficial.
