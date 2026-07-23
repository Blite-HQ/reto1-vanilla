# Instancias de Max-Cut con óptimo conocido

Cada JSON es una instancia congelada con:

- `aristas`: `[i, j, w]` con `i < j`, pesos enteros, ordenadas;
- `optimo`: valor exacto del corte máximo, probado por **dos anclas
  independientes** (los `metodos` del registro); si las anclas discrepan, el
  generador aborta sin escribir;
- `asignacion_canonica`: un testigo óptimo con `x0 = 0` (la simetría de
  complemento se rompe siempre así);
- `digest`: SHA-256 del JSON canónico (claves ordenadas, sin espacios,
  `ensure_ascii`, sin el campo `digest`). **El digest es la identidad de la
  instancia**: el loader (`src/reto1/instances.py`) rechaza archivos editados.

Verificación de una línea:

```bash
jq -cjS 'del(.digest)' data/cr8-uniforme.json | sha256sum
```

## Familias

### ieee9 / ieee14 / ieee30 (× `uniforme`, `flujo`)

Derivadas de los casos de prueba estándar IEEE 9/14/30 buses vía
`pandapower.networks` (case9/case14/case30): nodos = buses, aristas = líneas +
transformadores en servicio, ramas paralelas agregadas. `uniforme`: w = 1 por
rama. `flujo`: w = round(100·|P|) con |P| = flujo activo (MW) del caso base
(`pandapower.runpp`, resolución 0.01 MW — el redondeo es parte de la
definición de la instancia). Anclas: CP-SAT (OR-Tools, prueba de optimalidad,
parámetros deterministas) + enumeración exhaustiva (completa para n ≤ 14;
vectorizada para ieee30). Generadas y verificadas con pandapower 3.3.x,
networkx 3.6.x, ortools 9.15.

### cr8 / cr6 (× `uniforme`, `voltaje`) — red de transmisión REAL de Costa Rica

Derivadas de los datos abiertos del Grupo ICE (portal
`datos-ice-se.opendata.arcgis.com`, snapshots crudos commiteados en
`data/raw/`, descargados 2026-07-23):

- 70 subestaciones (`Subestaciones/FeatureServer`) y 102 circuitos de
  transmisión (`LineasDeTransmision/FeatureServer`, campos `Voltaje` y
  `Circuito` "A-B").
- Derivación determinista completa en `scripts/build_cr_instances.py`
  (parsing de endpoints, corredor greedy más denso desde la subestación de
  mayor grado — La Caja —, desempate alfabético). Los 8 circuitos descartados
  (interconexiones SIEPAC/frontera y clientes privados sin subestación en la
  capa) quedan listados en la salida del script.
- `uniforme`: w = número de circuitos paralelos entre el par.
  `voltaje`: w = suma de niveles de tensión (kV) — proxy documentado del
  costo de abrir el corredor (los datos abiertos no traen capacidad MVA).
- Cada registro lleva el mapeo nodo→subestación, las URLs fuente y el
  criterio del corredor (`nodos`, `fuente`, `criterio_corredor`).
- Anclas: enumeración `itertools` + espectro vectorizado numpy (código
  independiente); re-verificadas en `tests/test_cr_instances.py`.

## Regeneración

```bash
uv run python scripts/build_cr_instances.py   # cr8/cr6 desde data/raw/
```

Regla ante cualquier discrepancia: **se reporta, no se sobreescribe** — el
archivo congelado (su digest) manda.
