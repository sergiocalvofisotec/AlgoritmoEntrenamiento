# Algoritmo de Balanceo de Datasets para Entrenamiento ML

## Descripción del proyecto

Algoritmo que clasifica y balancea imágenes de señales verticales de tráfico para generar datasets equilibrados de entrenamiento de modelos de Machine Learning. Consulta una base de datos PostgreSQL que almacena imágenes etiquetadas por tipo de señal (`clase`), proyecto geográfico y dimensiones, y produce un dataset balanceado por clase, grupo de tamaño y proyecto.

El objetivo es evitar el sesgo de entrenamiento causado por clases con muchas más imágenes que otras, o por proyectos que dominan cierto rango de tamaño.

### Pipeline de 5 fases

```
Fase 1: Recopilar datos ─── Consulta BD, filtra clases válidas (≥50 imgs)
Fase 1.5: Separar train/val/test ─── Split estratificado por clase y proyecto (70/15/15)
Fase 2: Calcular objetivo ─── Determina imágenes por clase (modo independiente o estricto)
Fases 3-4: Clasificar + balancear ─── 4 grupos de tamaño × balanceo por proyecto (solo train)
Fase 5: Augmentation + weights ─── Augmentation adaptativo + class weights (solo train)
```

## Estructura de carpetas y ficheros

```
AlgoritmoEntrenamiento/
├── algoritmo.py                          # Algoritmo principal: configuración, clasificación, balanceo, augmentation
├── fisotec_basedatos.py                  # Clase FisotecBaseDatos — conexión y operaciones PostgreSQL
├── fisotec_utils.py                      # Clase FisotecUtils — utilidades generales (originaria del plugin QGIS)
├── credenciales.py                       # Constantes de conexión a BD (excluido de git)
├── test_algoritmo.py                     # 100 tests unitarios (20 clases de test)
├── test_mejoras_dataset.py               # 26 tests de mejoras del dataset (6 clases de test)
├── informe_mejoras_dataset.txt           # Análisis de 5 mejoras identificadas para el dataset
├── diagrama_flujo.html                   # Diagrama de flujo interactivo del algoritmo (Mermaid)
├── resultados_clases_proporcional.txt    # Fichero de salida de la última ejecución
├── CLAUDE.md                             # Guía para Claude Code
└── .gitignore                            # Excluye __pycache__/, *.pyc, .claude/, credenciales.py
```

### Qué hace cada fichero

| Fichero | Descripción |
|---|---|
| `algoritmo.py` | Lógica completa del balanceo: configuración (`CONFIG`), funciones puras de clasificación y balanceo, funciones de acceso a BD, orquestación por fases y generación de resultados. Punto de entrada: `python algoritmo.py` |
| `fisotec_basedatos.py` | Clase `FisotecBaseDatos` con métodos estáticos para conectar, consultar, insertar, modificar y eliminar datos en PostgreSQL vía `psycopg2`. Originaria del framework Fisotec |
| `fisotec_utils.py` | Clase `FisotecUtils` con utilidades generales: formateo de datos para SQL, validaciones, manejo de fechas, colores aleatorios. Originaria del plugin QGIS de Fisotec |
| `credenciales.py` | Define constantes `DBHOST`, `DBNAME`, `DBPORT`, `DBUSER`, `DBPASSWORD` para la conexión a PostgreSQL local |
| `test_algoritmo.py` | Suite de 100 tests unitarios que validan todas las funciones puras del algoritmo sin necesidad de conexión a BD |
| `test_mejoras_dataset.py` | Suite de 26 tests que validan las mejoras del dataset: sesgo de selección, split train/val/test, granularidad de grupos y filtros de calidad |
| `informe_mejoras_dataset.txt` | Informe con 5 mejoras identificadas para optimizar la calidad del dataset, con análisis de impacto y prioridad |
| `diagrama_flujo.html` | Diagrama de flujo interactivo con Mermaid que visualiza las 5 fases del algoritmo |
| `resultados_clases_proporcional.txt` | Salida generada por el algoritmo: resumen del split train/val/test, distribución por grupos, plan de augmentation y class weights |

## Clases principales

### `FisotecBaseDatos` (fisotec_basedatos.py)

Controlador de base de datos PostgreSQL. Todos sus métodos son `@staticmethod`.

| Método | Responsabilidad |
|---|---|
| `conectarBaseDatos()` | Abre conexión PostgreSQL y devuelve un cursor `RealDictCursor` con autocommit |
| `cerrarBaseDatos(conexion)` | Cierra la conexión a BD |
| `insertarElemento(conexion, tabla, columnas, valores)` | Inserta un registro en la tabla indicada |
| `borraElemento(conexion, tabla, clausula)` | Elimina registros según cláusula WHERE |
| `modificarElemento(conexion, tabla, datos, schema)` | Actualiza un registro detectando automáticamente la clave primaria |
| `consultaSQL(conexion, consulta)` | Ejecuta una consulta SQL arbitraria y devuelve resultados |
| `consultaTotal(conexion, tabla, clausula)` | SELECT * con cláusula WHERE opcional |
| `obtenerCampoElemento(conexion, nombre_campo, elemento, columna, tabla)` | Consulta un campo específico de un registro |
| `obtenerClavePrimaria(conexion, tabla, esquema)` | Obtiene las columnas de la clave primaria de una tabla |
| `compruebaValoresNoNulos(conexion, datos, esquema, tabla)` | Valida que los campos NOT NULL estén presentes |
| `crearSchema(con, nombre)` | Crea un esquema en la BD |
| `crearTabla(nombre, con, valores, schema)` | Crea una tabla con clave primaria autoincremental |
| `crear_columna(conexion, cadena, tabla)` | Añade una columna a una tabla existente |
| `eliminar_datos_tabla(tabla)` | Elimina todos los registros de una tabla |
| `comprobar_datos_tabla(tabla)` | Comprueba si una tabla tiene datos |
| `consultas_multiples(array_sentencias)` | Ejecuta sentencias SQL en lotes de 250 |

### `FisotecUtils` (fisotec_utils.py)

Utilidades generales del framework Fisotec. Todos sus métodos son `@staticmethod`.

| Método | Responsabilidad |
|---|---|
| `crearFila(d)` | Convierte un diccionario en tupla `(campos, valores)` para sentencias INSERT |
| `es_nulo(elemento)` | Comprueba si un valor es nulo, vacío o NULL |
| `formatear_fecha(valor)` | Parsea una cadena a datetime probando 13+ formatos distintos |
| `sin_espacios(cadena)` | Normaliza cadenas: minúsculas, sin espacios ni guiones |
| `transformar_valor(dato)` | Formatea un valor según su tipo para construir sentencias SQL |
| `numero_a_texto(numero, longitud)` | Rellena un número con ceros a la izquierda |
| `color_aleatorio()` | Devuelve un color aleatorio de una paleta de 32 colores |

### Funciones del algoritmo (algoritmo.py)

El algoritmo no está encapsulado en una clase, sino en funciones modulares importables. Se dividen en tres grupos:

**Funciones puras (sin BD, testeables directamente):**

| Función | Responsabilidad |
|---|---|
| `clasificar_por_rango(imagenes)` | Divide imágenes en 4 grupos por intervalos iguales de tamaño |
| `clasificar_proporcional(imagenes)` | Divide imágenes en 4 grupos con cantidad proporcional (cuartiles) |
| `calcular_cuotas_grupos(grupos, objetivo)` | Calcula cuántas imágenes tomar de cada grupo, redistribuyendo excedentes |
| `balancear_por_proyecto(grupo, cuota)` | Reparte la cuota de un grupo equitativamente entre proyectos con `random.sample()` |
| `clasificar_y_balancear_clase(imagenes, objetivo, tipo)` | Orquesta clasificación + balanceo para una clase completa |
| `calcular_objetivo(datos_clases, max, independiente)` | Calcula el objetivo de imágenes por clase según el modo de balanceo |
| `calcular_augmentation(resumen, objetivo, factor_max)` | Calcula augmentation adaptativo: factor variable por clase según necesidad |
| `calcular_class_weights(augmentation_info)` | Calcula pesos por clase para `CrossEntropyLoss`: `total / (n_clases × n_clase)` |
| `separar_train_val_test(datos_clases, ratios)` | Split estratificado por clase y proyecto antes del balanceo |

**Funciones de BD (queries parametrizadas con `%s` de psycopg2):**

| Función | Responsabilidad |
|---|---|
| `crear_columna_tamanio(conexion)` | Añade la columna `tamaño` a la tabla si no existe |
| `obtener_clases(conexion, proyectos)` | Obtiene las clases disponibles, filtradas por proyecto |
| `obtener_imagenes_clase(conexion, clase, ...)` | Consulta imágenes de una clase con filtros de proyecto y tamaño |
| `actualizar_tamanio_bd_batch(conexion, ids, grupo)` | Actualiza el grupo de tamaño de múltiples imágenes en una sola query batch (`WHERE id = ANY(%s)`) |

**Orquestación (fases del pipeline):**

| Función | Responsabilidad |
|---|---|
| `recopilar_datos(conexion, config)` | Fase 1: obtiene y filtra las clases válidas |
| `calcular_objetivo(datos_clases, ...)` | Fase 2: determina cuántas imágenes por clase |
| `procesar_clases(conexion, datos, objetivo, config)` | Fases 3-4: clasifica, balancea y actualiza BD |
| `generar_fichero_resultados(resumen, config, ...)` | Fase 5: escribe el fichero `.txt` de resultados |
| `main(config)` | Punto de entrada: ejecuta todas las fases en orden con `random.seed(42)` |

## Dependencias

| Paquete | Uso |
|---|---|
| Python 3.14+ | Runtime |
| psycopg2 | Conexión a PostgreSQL |
| PostgreSQL | Base de datos con tabla `public.seniales_verticales` |

### Instalación

```bash
pip install psycopg2-binary
```

La base de datos debe estar corriendo en local (o configurar `credenciales.py`) con una tabla `public.seniales_verticales` que contenga al menos las columnas: `id`, `clase`, `proyecto`, `width`, `height`.

Crear el fichero `credenciales.py` en la raíz del proyecto:

```python
DBHOST = 'localhost'
DBNAME = 'nombre_base_datos'
DBPORT = '5432'
DBUSER = 'postgres'
DBPASSWORD = 'tu_contraseña'
```

## Cómo se usa el proyecto

### Ejecutar el algoritmo

```bash
python algoritmo.py
```

Conecta a la BD, ejecuta las 5 fases y genera el fichero `resultados_clases_proporcional.txt` (o `resultados_clases_rango.txt` según la configuración).

### Configuración

Todos los parámetros se definen en el diccionario `CONFIG` al inicio de `algoritmo.py`:

| Parámetro | Valor actual | Descripción |
|---|---|---|
| `tipo_clasificacion` | `"proporcional"` | `"rango"` (intervalos iguales) o `"proporcional"` (cuartiles) |
| `criterio_tamanio` | `"altura"` | `"altura"` o `"diagonal"` como medida de tamaño |
| `proyectos` | `["03_ibiza", "01_alcaudete", ...]` | Proyectos a incluir (vacío = todos) |
| `clases_excluidas` | `["ST_C", "ST_R", "ST_S", "ST_T"]` | Clases ignoradas por el algoritmo |
| `cantidad_minima` | `50` | Mínimo de imágenes para que una clase sea válida |
| `cantidad_maxima` | `2000` | Máximo de imágenes por clase |
| `tamanio_maximo` | `500` | Tamaño máximo de imagen en px. `None` = sin límite |
| `balanceo_independiente` | `True` | `True`: cada clase usa todas sus imágenes. `False`: todas se limitan a la clase más pequeña |
| `augmentation_objetivo` | `500` | Mínimo de imágenes por clase tras augmentation |
| `augmentation_factor_max` | `20` | Factor máximo de multiplicación por augmentation |
| `split_ratios` | `{"train": 0.70, "val": 0.15, "test": 0.15}` | Ratios de separación train/val/test. `None` para desactivar |

### Ejecutar los tests

```bash
# Todos los tests (126 tests)
python -m unittest test_algoritmo test_mejoras_dataset -v

# Solo tests del algoritmo (100 tests, 20 clases)
python -m unittest test_algoritmo -v

# Solo tests de mejoras del dataset (26 tests, 6 clases)
python -m unittest test_mejoras_dataset -v

# Una clase de test específica
python -m unittest test_algoritmo.TestBalancearPorProyecto -v
```

Los tests no requieren conexión a base de datos. Importan directamente las funciones puras del módulo.

## Estado actual del desarrollo

- **Algoritmo funcional**: las 5 fases del pipeline implementadas y probadas
- **126 tests unitarios** organizados en 26 clases de test, todos pasando
- **Dos modos de balanceo**: estricto (todas las clases al mínimo) e independiente (cada clase usa su máximo)
- **Split train/val/test**: separación estratificada por clase y proyecto antes del balanceo para evitar data leakage
- **Data augmentation adaptativo**: calcula factor variable por clase (las clases pequeñas reciben más augmentation). Solo se aplica al split de train
- **Class weights**: calcula pesos para `CrossEntropyLoss` compensando el desbalance residual
- **Muestreo aleatorio**: usa `random.sample()` en vez de selección secuencial para evitar sesgo hacia imágenes pequeñas
- **SQL seguro**: queries parametrizadas con `%s` de psycopg2 y UPDATEs batch (`WHERE id = ANY(%s)`) para minimizar roundtrips a BD
- **Código modular**: funciones puras separadas de acceso a BD, importables y testeables individualmente
- **Reproducibilidad**: `random.seed(42)` garantiza resultados idénticos entre ejecuciones

### Resultados de la última ejecución

- 47 clases activas de un total de 71
- 21.772 imágenes totales (15.174 train / 3.199 val / 3.399 test)
- 31.660 imágenes de train tras augmentation adaptativo
- Clase más grande: R-301 (2.263 imágenes, limitada a 2.000)
- Clase más pequeña: P-1c (50 imágenes, augmentation x15)

### Tests

| Clase de test | Tests | Qué valida |
|---|---|---|
| `TestClasificacionProporcional` | 7 | División por cuartiles |
| `TestClasificacionRango` | 4 | División por rangos iguales |
| `TestBalancearPorProyecto` | 10 | Redistribución entre proyectos |
| `TestCalcularCuotasGrupos` | 7 | Cuotas de los 4 grupos |
| `TestClasificarYBalancearClase` | 3 | Pipeline clasificación + balanceo |
| `TestCalcularObjetivo` | 9 | Cálculo del objetivo balanceado |
| `TestCalcularAugmentation` | 6 | Data augmentation adaptativo |
| `TestCalcularClassWeights` | 5 | Pesos para la loss function |
| `TestNombresGruposUnificados` | 2 | Nomenclatura consistente |
| `TestFlujoCompleto` | 3 | Pipeline completo sin BD |
| `TestConsistenciaResultados` | 3 | IDs únicos, límites respetados |
| `TestCasosLimite` | 5 | Edge cases (medida 0, negativos...) |
| `TestFiltroConfiguracion` | 2 | Filtros de clases y proyectos |
| `TestSimulacionEntrenamientoEstricto` | 5 | Simulación entrenamiento modo estricto |
| `TestSimulacionEntrenamientoIndependiente` | 6 | Simulación entrenamiento modo independiente |
| `TestSimulacionClassWeights` | 5 | Validación de class weights |
| `TestSimulacionTrainValTest` | 5 | Simulación split train/val/test |
| `TestSimulacionAugmentationEntrenamiento` | 6 | Augmentation con entrenamiento simulado |
| `TestBatchUpdatePreparacion` | 5 | Preparación de IDs para UPDATE batch en BD |
| `TestComparativaEstrictoVsIndependiente` | 11 | Comparativa entre ambos modos |
| `TestSesgoSeleccion` | 5 | Validación de sesgo por muestreo secuencial |
| `TestAugmentationUniforme` | 4 | Identifica problemas del augmentation uniforme |
| `TestSeparacionTrainValTest` | 7 | Split estratificado sin solapamiento ni data leakage |
| `TestGranularidadGrupos` | 3 | Detecta rangos internos excesivos con 4 grupos |
| `TestFiltroCalidad` | 3 | Identifica imágenes diminutas (<5px) y duplicados |
| `TestImpactoCombinadoDataset` | 5 | Impacto combinado de todas las mejoras |

### Mejoras identificadas

| # | Mejora | Estado | Impacto |
|---|---|---|---|
| 1 | Muestreo aleatorio en selección | Implementada | Crítico |
| 2 | Augmentation adaptativo por clase | Implementada | Alto |
| 3 | Split train/val/test pre-balanceo | Implementada | Alto |
| 4 | Grupos dinámicos con cuantiles | Pendiente | Medio |
| 5 | Filtro de calidad + deduplicación | Pendiente | Bajo |

## Próximos pasos

### Integración con ladybug-fusion

*(Pendiente de definir)*
