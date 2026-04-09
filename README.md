# Algoritmo de Preparación de Datasets para Entrenamiento YOLO

## Descripción del proyecto

Algoritmo que selecciona, filtra, balancea y exporta imágenes de señales verticales de tráfico para generar datasets equilibrados de entrenamiento con YOLO. Consulta una base de datos PostgreSQL que almacena imágenes etiquetadas por tipo de señal (`clase`), proyecto geográfico y dimensiones, y produce un dataset en formato YOLO (carpetas `images/labels` + `seniales.yaml`).

El objetivo es evitar el sesgo de entrenamiento causado por clases con muchas más imágenes que otras, o por proyectos que dominan el dataset, garantizando que YOLO aprende a generalizar entre distintas condiciones.

### Pipeline de 5 fases

```
Fase 1: Recopilar datos + filtro de calidad ─── Consulta BD, filtra por tamaño mínimo/máximo y cantidad mínima
Fase 2: Separar train/val/test ─── Split estratificado por clase y proyecto (70/15/15)
Fase 3: Balancear por clase y proyecto ─── Balanceo por proyecto con random.sample (solo train)
Fase 4: Exportar a formato YOLO ─── Genera carpetas images/labels + seniales.yaml
Fase 5: Registrar versión ─── Guarda config + asignación de imágenes en JSON
```

## Estructura de carpetas y ficheros

```
AlgoritmoEntrenamiento/
├── algoritmo.py                          # Algoritmo principal: configuración, filtrado, balanceo, exportación YOLO
├── fisotec_basedatos.py                  # Clase FisotecBaseDatos — conexión y operaciones PostgreSQL
├── fisotec_utils.py                      # Clase FisotecUtils — utilidades generales (originaria del plugin QGIS)
├── credenciales.py                       # Constantes de conexión a BD (excluido de git)
├── test_algoritmo.py                     # 51 tests unitarios (11 clases de test)
├── test_mejoras_dataset.py               # 18 tests de mejoras del dataset (6 clases de test)
├── informe_mejoras_dataset.txt           # Análisis de mejoras identificadas para el dataset
├── diagrama_flujo.html                   # Diagrama de flujo interactivo del algoritmo (Mermaid)
├── resultados_yolo.txt                   # Fichero de salida de la última ejecución
├── dataset_yolo/                         # Dataset exportado en formato YOLO (generado)
│   ├── images/{train,val,test}/          # Imágenes por split
│   ├── labels/{train,val,test}/          # Labels .txt en formato YOLO
│   ├── seniales.yaml                     # Configuración del dataset para YOLO
│   └── version_*.json                    # Trazabilidad de cada ejecución
├── CLAUDE.md                             # Guía para Claude Code
└── .gitignore                            # Excluye __pycache__/, *.pyc, .claude/, credenciales.py
```

### Qué hace cada fichero

| Fichero | Descripción |
|---|---|
| `algoritmo.py` | Pipeline completo de preparación de dataset YOLO: configuración (`CONFIG`), filtros de calidad, balanceo por proyecto, exportación a formato YOLO y registro de versión. Punto de entrada: `python algoritmo.py` |
| `fisotec_basedatos.py` | Clase `FisotecBaseDatos` con métodos estáticos para conectar, consultar, insertar, modificar y eliminar datos en PostgreSQL vía `psycopg2` |
| `fisotec_utils.py` | Clase `FisotecUtils` con utilidades generales: formateo de datos para SQL, validaciones, manejo de fechas |
| `credenciales.py` | Define constantes `DBHOST`, `DBNAME`, `DBPORT`, `DBUSER`, `DBPASSWORD` para la conexión a PostgreSQL local |
| `test_algoritmo.py` | Suite de 52 tests unitarios que validan todas las funciones puras del algoritmo sin necesidad de conexión a BD |
| `test_mejoras_dataset.py` | Suite de 18 tests que validan las mejoras del dataset: sesgo de selección, filtros de calidad, labels YOLO y pipeline completo |
| `diagrama_flujo.html` | Diagrama de flujo interactivo con Mermaid que visualiza las 5 fases del algoritmo |
| `resultados_yolo.txt` | Salida generada por el algoritmo: resumen del split, balanceo por proyecto, exportación YOLO y mapeo de clases |

## Funciones del algoritmo (algoritmo.py)

El algoritmo está organizado en funciones modulares importables, divididas en tres grupos:

**Funciones puras (sin BD, testeables directamente):**

| Función | Responsabilidad |
|---|---|
| `balancear_por_proyecto(imagenes, cuota)` | Reparte la cuota equitativamente entre proyectos con `random.sample()` |
| `calcular_objetivo(datos_clases, max)` | Calcula el objetivo de imágenes por clase (cada clase usa su máximo hasta el cap) |
| `separar_train_val_test(datos_clases, ratios)` | Split a nivel de imagen (no de anotación) estratificado por proyecto, evitando data leakage |
| `generar_label_yolo(imagen, clase_id, w, h)` | Genera una línea de label YOLO normalizada (clase x_center y_center w h) |
| `generar_yaml_contenido(clases, ruta)` | Genera el contenido del fichero seniales.yaml para YOLO |

**Funciones de BD (queries parametrizadas con `%s` de psycopg2):**

| Función | Responsabilidad |
|---|---|
| `obtener_clases(conexion, proyectos)` | Obtiene las clases disponibles, filtradas por proyecto |
| `obtener_imagenes_clase(conexion, clase, ...)` | Consulta imágenes con filtros de calidad (tamaño mínimo/máximo) e incluye campos YOLO (x_center, y_center, nombre_imagen, W/H_imagen) |

**Orquestación (fases del pipeline):**

| Función | Responsabilidad |
|---|---|
| `recopilar_datos(conexion, config)` | Fase 1: obtiene y filtra clases válidas por calidad y cantidad |
| `procesar_clases(datos, objetivos)` | Fase 3: balancea cada clase por proyecto |
| `exportar_dataset_yolo(train, val, test, clases, config)` | Fase 4: genera carpetas, labels .txt y seniales.yaml |
| `registrar_version(config, resumen, ...)` | Fase 5: guarda JSON con config y asignación de imágenes |
| `generar_fichero_resultados(...)` | Genera el fichero .txt de resultados legible |
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

La base de datos debe estar corriendo en local (o configurar `credenciales.py`) con una tabla `public.seniales_verticales` que contenga al menos las columnas: `id`, `clase`, `proyecto`, `width`, `height`, `x_center`, `y_center`, `nombre_imagen`, `W_imagen`, `H_imagen`.

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

Conecta a la BD, ejecuta las 5 fases y genera:
- `dataset_yolo/` con la estructura de carpetas YOLO
- `dataset_yolo/seniales.yaml` con la configuración del dataset
- `dataset_yolo/version_*.json` con la trazabilidad
- `resultados_yolo.txt` con el resumen legible

### Entrenar YOLO con el dataset generado

```python
from ultralytics import YOLO

model = YOLO('yolov8n.pt')
model.train(data='dataset_yolo/seniales.yaml', epochs=100, imgsz=640)
```

### Configuración

Todos los parámetros se definen en el diccionario `CONFIG` al inicio de `algoritmo.py`:

| Parámetro | Valor actual | Descripción |
|---|---|---|
| `proyectos` | `["03_ibiza", "01_alcaudete", ...]` | Proyectos a incluir (vacío = todos) |
| `clases_excluidas` | `["ST_C", "ST_R", "ST_S", "ST_T"]` | Clases ignoradas manualmente |
| `cantidad_minima` | `100` | Mínimo de imágenes para que una clase sea válida (YOLO necesita variedad) |
| `cantidad_maxima` | `2000` | Cap por clase para evitar dominancia en la loss |
| `tamanio_minimo` | `10` | Tamaño mínimo de recorte en px (excluye errores de anotación) |
| `tamanio_maximo` | `500` | Tamaño máximo de recorte en px. `None` = sin límite |
| `split_ratios` | `{"train": 0.70, "val": 0.15, "test": 0.15}` | Ratios de separación train/val/test |
| `ruta_imagenes` | `None` | Ruta base de imágenes originales. `None` = solo genera labels |
| `ruta_salida` | `"dataset_yolo"` | Ruta de salida del dataset exportado |

### Ejecutar los tests

```bash
# Todos los tests (70 tests)
python -m unittest test_algoritmo test_mejoras_dataset -v

# Solo tests del algoritmo (52 tests, 11 clases)
python -m unittest test_algoritmo -v

# Solo tests de mejoras del dataset (18 tests, 6 clases)
python -m unittest test_mejoras_dataset -v

# Una clase de test específica
python -m unittest test_algoritmo.TestBalancearPorProyecto -v
```

Los tests no requieren conexión a base de datos. Importan directamente las funciones puras del módulo.

## Estado actual del desarrollo

- **Pipeline YOLO funcional**: las 5 fases implementadas y probadas
- **70 tests unitarios** organizados en 17 clases de test, todos pasando
- **Filtro de calidad**: excluye recortes < 10px (errores de anotación) y clases < 100 imágenes
- **Split train/val/test**: separación a nivel de imagen (no de anotación), estratificada por proyecto, para evitar data leakage cuando una imagen tiene señales de varias clases
- **Balanceo por proyecto**: reparto equitativo entre proyectos con `random.sample()` para forzar generalización
- **Exportación YOLO**: genera carpetas images/labels, ficheros .txt con anotaciones normalizadas y seniales.yaml
- **Trazabilidad**: cada ejecución se registra en JSON con config, asignación de imágenes y estadísticas
- **SQL seguro**: queries parametrizadas con `%s` de psycopg2
- **Reproducibilidad**: `random.seed(42)` garantiza resultados idénticos entre ejecuciones

### Datos de la BD

- 28.762 anotaciones totales en 18.339 imágenes únicas (640x640)
- Múltiples señales por imagen (detección multi-objeto)
- 4 proyectos: Ibiza, Alcaudete, Fuente Albilla, Carreteras
- 37 clases válidas (≥100 imágenes) de 101 clases totales
- 3.401 anotaciones con recorte < 10px (filtradas)

### Tests

| Clase de test | Tests | Qué valida |
|---|---|---|
| `TestBalancearPorProyecto` | 8 | Redistribución entre proyectos |
| `TestCalcularObjetivo` | 4 | Cálculo del objetivo por clase |
| `TestSepararTrainValTest` | 6 | Split a nivel de imagen, sin solapamiento ni data leakage |
| `TestGenerarLabelYolo` | 5 | Labels YOLO normalizados |
| `TestGenerarYaml` | 3 | Fichero seniales.yaml |
| `TestExportarDatasetYolo` | 6 | Exportación a carpetas YOLO |
| `TestProcesarClases` | 3 | Procesamiento y balanceo |
| `TestFiltroCalidad` | 4 | Filtros de tamaño y cantidad |
| `TestSimulacionDatasetRealista` | 5 | Pipeline con distribución real |
| `TestSimulacionTrainValTest` | 4 | Split con datos realistas |
| `TestSimulacionExportacionYolo` | 2 | Exportación completa a YOLO |
| `TestReproducibilidad` | 2 | Misma seed = mismos resultados |
| `TestSesgoSeleccion` | 3 | Muestreo aleatorio vs secuencial |
| `TestFiltroCalidadMinimo` | 4 | Filtros de calidad (recortes, cantidad) |
| `TestSeparacionTrainValTest` | 5 | Data leakage y estratificación |
| `TestLabelsYolo` | 3 | Labels YOLO correctos |
| `TestPipelineCompleto` | 3 | Pipeline integrado de preparación |

## Decisiones de diseño para YOLO

### Por qué no hay balanceo por grupos de tamaño

YOLO gestiona internamente la variación de escalas con:
- **Mosaic augmentation**: combina 4 imágenes, mezclando tamaños naturalmente
- **Multi-scale training**: varía la resolución de entrada cada pocas épocas
- **Random resize**: redimensiona aleatoriamente durante entrenamiento

Forzar cuotas iguales entre grupos de tamaño es redundante y puede empeorar el entrenamiento.

### Por qué no hay cálculo de augmentation

YOLO/Ultralytics gestiona el augmentation nativamente y de forma más eficiente (mosaic, mixup, hsv, flip). Cada época genera variantes distintas on-the-fly, lo que es superior a pre-generar copias.

### Por qué cantidad_minima = 100

Con el split 70/15/15, una clase con 100 imágenes tiene ~70 en train. YOLO necesita ver variedad para generalizar. Con < 70 ejemplos de train, el modelo memoriza en vez de aprender y genera falsos positivos.

### Por qué tamanio_minimo = 10px

De las 28.762 anotaciones, 3.401 tienen recorte < 10px. Estas son errores de anotación o señales tan lejanas que el bbox de ~8x8px es impreciso. Incluirlas enseña ruido al modelo.

## Próximos pasos

- Configurar `ruta_imagenes` para copiar las imágenes físicas al dataset exportado
- Entrenar YOLO con el dataset generado y evaluar métricas (mAP, precision, recall)
- Experimentar con/sin imágenes del grupo "muy pequeño" y comparar resultados
- Implementar group split por proyecto (leave-one-project-out) para validar generalización
