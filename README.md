# Algoritmo de Balanceo de Datasets para Entrenamiento ML

## Descripcion del proyecto

Algoritmo que clasifica y balancea imagenes de seniales verticales de trafico para generar datasets equilibrados de entrenamiento de modelos de Machine Learning. Consulta una base de datos PostgreSQL que almacena imagenes etiquetadas por tipo de senal (`clase`), proyecto geografico y dimensiones, y produce un dataset balanceado por clase, grupo de tamanio y proyecto.

El objetivo es evitar el sesgo de entrenamiento causado por clases con muchas mas imagenes que otras, o por proyectos que dominan cierto rango de tamanio.

## Estructura de carpetas y ficheros

```
AlgoritmoEntrenamiento/
├── algoritmo.py                          # Algoritmo principal: clasificacion, balanceo, augmentation
├── fisotec_basedatos.py                  # Clase FisotecBaseDatos - conexion y operaciones PostgreSQL
├── fisotec_utils.py                      # Clase FisotecUtils - utilidades generales (originaria del plugin QGIS)
├── credenciales.py                       # Constantes de conexion a BD (excluido de git)
├── test_algoritmo.py                     # 95 tests unitarios (19 clases de test)
├── resultados_clases_proporcional.txt    # Fichero de salida de la ultima ejecucion
├── .gitignore                            # Excluye __pycache__/, *.pyc, .claude/, credenciales.py
└── AlgoritmoEntrenamiento/               # Copia anterior del proyecto (version previa a refactorizacion)
    ├── algoritmo.py
    ├── fisotec_basedatos.py
    ├── fisotec_utils.py
    └── credenciales.py
```

### Que hace cada fichero

| Fichero | Descripcion |
|---|---|
| `algoritmo.py` | Logica completa del balanceo: configuracion (`CONFIG`), funciones puras de clasificacion y balanceo, funciones de acceso a BD, orquestacion por fases, generacion de resultados. Punto de entrada: `python algoritmo.py` |
| `fisotec_basedatos.py` | Clase `FisotecBaseDatos` con metodos estaticos para conectar, consultar, insertar, modificar y eliminar datos en PostgreSQL via `psycopg2`. Originaria del framework Fisotec |
| `fisotec_utils.py` | Clase `FisotecUtils` con utilidades generales: formateo de datos para SQL, validaciones, manejo de fechas, colores aleatorios. Originaria del plugin QGIS de Fisotec |
| `credenciales.py` | Define constantes `DBHOST`, `DBNAME`, `DBPORT`, `DBUSER`, `DBPASSWORD` para la conexion a PostgreSQL local |
| `test_algoritmo.py` | Suite de 95 tests unitarios que validan todas las funciones puras del algoritmo sin necesidad de conexion a BD |
| `resultados_clases_proporcional.txt` | Salida generada por el algoritmo: resumen por clase con distribucion en grupos, plan de data augmentation y class weights |

## Clases principales

### `FisotecBaseDatos` (fisotec_basedatos.py)

Controlador de base de datos PostgreSQL. Todos sus metodos son `@staticmethod`.

| Metodo | Responsabilidad |
|---|---|
| `conectarBaseDatos()` | Abre conexion PostgreSQL y devuelve un cursor `RealDictCursor` con autocommit |
| `cerrarBaseDatos(conexion)` | Cierra la conexion a BD |
| `insertarElemento(conexion, tabla, columnas, valores)` | Inserta un registro en la tabla indicada |
| `borraElemento(conexion, tabla, clausula)` | Elimina registros segun clausula WHERE |
| `modificarElemento(conexion, tabla, datos, schema)` | Actualiza un registro detectando automaticamente la clave primaria |
| `consultaSQL(conexion, consulta)` | Ejecuta una consulta SQL arbitraria y devuelve resultados |
| `consultaTotal(conexion, tabla, clausula)` | SELECT * con clausula WHERE opcional |
| `obtenerClavePrimaria(conexion, tabla, esquema)` | Obtiene las columnas de la clave primaria de una tabla |
| `crearTabla(nombre, con, valores, schema)` | Crea una tabla con clave primaria autoincremental |
| `crear_columna(conexion, cadena, tabla)` | Anade una columna a una tabla existente |

### `FisotecUtils` (fisotec_utils.py)

Utilidades generales del framework Fisotec. Todos sus metodos son `@staticmethod`.

| Metodo | Responsabilidad |
|---|---|
| `crearFila(d)` | Convierte un diccionario en tupla (campos, valores) para sentencias INSERT |
| `es_nulo(elemento)` | Comprueba si un valor es nulo, vacio o NULL |
| `formatear_fecha(valor)` | Parsea una cadena a datetime probando multiples formatos |
| `sin_espacios(cadena)` | Normaliza cadenas: minusculas, sin espacios ni guiones |
| `transformar_valor(dato)` | Formatea un valor segun su tipo para construir sentencias SQL |
| `numero_a_texto(numero, longitud)` | Rellena un numero con ceros a la izquierda |

### Funciones del algoritmo (algoritmo.py)

El algoritmo no esta encapsulado en una clase, sino en funciones modulares importables. Se dividen en tres grupos:

**Funciones puras (sin BD, testeables directamente):**

| Funcion | Responsabilidad |
|---|---|
| `clasificar_por_rango(imagenes)` | Divide imagenes en 4 grupos por intervalos iguales de tamanio |
| `clasificar_proporcional(imagenes)` | Divide imagenes en 4 grupos con cantidad proporcional (cuartiles) |
| `calcular_cuotas_grupos(grupos, objetivo)` | Calcula cuantas imagenes tomar de cada grupo, redistribuyendo excedentes |
| `balancear_por_proyecto(grupo, cuota)` | Reparte la cuota de un grupo equitativamente entre proyectos |
| `clasificar_y_balancear_clase(imagenes, objetivo, tipo)` | Orquesta clasificacion + balanceo para una clase completa |
| `calcular_objetivo(datos_clases, max, independiente)` | Calcula el objetivo de imagenes por clase segun el modo de balanceo |
| `calcular_augmentation(resumen, objetivo, factor_max)` | Calcula augmentation adaptativo: factor variable por clase segun necesidad |
| `calcular_class_weights(augmentation_info)` | Calcula pesos por clase para `CrossEntropyLoss` (`total / (n_clases * n_clase)`) |

**Funciones de BD (queries parametrizadas con `%s` de psycopg2):**

| Funcion | Responsabilidad |
|---|---|
| `crear_columna_tamanio(conexion)` | Anade la columna `tamanio` a la tabla si no existe |
| `obtener_clases(conexion, proyectos)` | Obtiene las clases disponibles, filtradas por proyecto |
| `obtener_imagenes_clase(conexion, clase, ...)` | Consulta imagenes de una clase con filtros de proyecto y tamanio |
| `actualizar_tamanio_bd(conexion, id, grupo)` | Escribe el grupo de tamanio asignado a cada imagen en BD |

**Orquestacion (fases del pipeline):**

| Funcion | Responsabilidad |
|---|---|
| `recopilar_datos(conexion, config)` | Fase 1: obtiene y filtra las clases validas |
| `calcular_objetivo(datos_clases, ...)` | Fase 2: determina cuantas imagenes por clase |
| `procesar_clases(conexion, datos, objetivo, config)` | Fases 3-4: clasifica, balancea y actualiza BD |
| `generar_fichero_resultados(resumen, config, ...)` | Fase 5: escribe el fichero `.txt` de resultados |
| `main(config)` | Punto de entrada: ejecuta todas las fases en orden |

## Dependencias

| Paquete | Version | Uso |
|---|---|---|
| Python | 3.14+ | Runtime (probado con CPython 3.14) |
| psycopg2 | - | Conexion a PostgreSQL |
| PostgreSQL | - | Base de datos con tabla `public.seniales_verticales` |

### Instalacion

```bash
pip install psycopg2-binary
```

La base de datos debe estar corriendo en local (o configurar `credenciales.py`) con una tabla `public.seniales_verticales` que contenga al menos las columnas: `id`, `clase`, `proyecto`, `width`, `height`.

## Como se usa el proyecto

### Ejecutar el algoritmo

```bash
python algoritmo.py
```

Esto conecta a la BD, ejecuta las 5 fases y genera el fichero `resultados_clases_proporcional.txt` (o `resultados_clases_rango.txt` segun la configuracion).

### Configuracion

Todos los parametros se definen en el diccionario `CONFIG` al inicio de `algoritmo.py`:

| Parametro | Valor actual | Descripcion |
|---|---|---|
| `tipo_clasificacion` | `"proporcional"` | `"rango"` (intervalos iguales) o `"proporcional"` (cuartiles) |
| `criterio_tamanio` | `"altura"` | `"altura"` o `"diagonal"` como medida de tamanio |
| `proyectos` | `["03_ibiza", "01_alcaudete", "02_fuente_albilla", "04_carreteras"]` | Proyectos a incluir (vacio = todos) |
| `clases_excluidas` | `["ST_C", "ST_R", "ST_S", "ST_T"]` | Clases ignoradas por el algoritmo |
| `cantidad_minima` | `50` | Minimo de imagenes para que una clase sea valida |
| `cantidad_maxima` | `2000` | Maximo de imagenes por clase |
| `tamanio_maximo` | `500` | Tamanio maximo de imagen en px (segun criterio). `None` = sin limite |
| `balanceo_independiente` | `True` | `True`: cada clase usa todas sus imagenes (hasta max). `False`: todas se limitan a la clase mas pequena |
| `augmentation_objetivo` | `500` | Minimo de imagenes por clase tras augmentation |
| `augmentation_factor_max` | `20` | Factor maximo de multiplicacion por augmentation |

### Ejecutar los tests

```bash
python -m unittest test_algoritmo -v
```

Los tests no requieren conexion a base de datos. Importan directamente las funciones puras del modulo.

## Estado actual del desarrollo

- **Algoritmo funcional**: las 5 fases del pipeline estan implementadas y probadas
- **95 tests unitarios** organizados en 19 clases de test, todos pasando
- **Dos modos de balanceo**: estricto (todas las clases al minimo) e independiente (cada clase usa su maximo)
- **Data augmentation adaptativo**: calcula factor variable por clase (las clases pequenas reciben mas augmentation)
- **Class weights**: calcula pesos para `CrossEntropyLoss` compensando el desbalance residual
- **SQL seguro**: queries parametrizadas con `%s` de psycopg2 (corregido desde la version original que usaba `.format()`)
- **Codigo modular**: funciones puras separadas de acceso a BD, importables y testeables individualmente

### Tests (19 clases)

| Clase de test | Tests | Que valida |
|---|---|---|
| `TestClasificacionProporcional` | 7 | Division por cuartiles |
| `TestClasificacionRango` | 4 | Division por rangos iguales |
| `TestBalancearPorProyecto` | 10 | Redistribucion entre proyectos |
| `TestCalcularCuotasGrupos` | 7 | Cuotas de los 4 grupos |
| `TestClasificarYBalancearClase` | 3 | Pipeline clasificacion + balanceo |
| `TestCalcularObjetivo` | 3 | Calculo del objetivo balanceado |
| `TestCalcularAugmentation` | 3 | Data augmentation adaptativo |
| `TestCalcularClassWeights` | 3 | Pesos para la loss function |
| `TestNombresGruposUnificados` | 2 | Nomenclatura consistente |
| `TestFlujoCompleto` | 3 | Pipeline completo sin BD |
| `TestConsistenciaResultados` | 3 | IDs unicos, limites respetados |
| `TestCasosLimite` | 5 | Edge cases (medida 0, negativos...) |
| `TestFiltroConfiguracion` | 2 | Filtros de clases y proyectos |
| `TestSimulacionEntrenamientoEstricto` | 6 | Simulacion entrenamiento modo estricto |
| `TestSimulacionEntrenamientoIndependiente` | 6 | Simulacion entrenamiento modo independiente |
| `TestSimulacionClassWeights` | 5 | Validacion de class weights |
| `TestSimulacionTrainValTest` | 5 | Simulacion split train/val/test |
| `TestSimulacionAugmentationEntrenamiento` | 7 | Augmentation con entrenamiento simulado |
| `TestComparativaEstrictoVsIndependiente` | 11 | Comparativa entre ambos modos |

## Proximos pasos

### Integracion con ladybug-fusion

*(Pendiente de definir)*
