# Algoritmo de Balanceo de Datasets para Entrenamiento

## Descripcion

Algoritmo de balanceo y clasificacion de imagenes de seniales verticales de trafico para preparar datasets equilibrados de entrenamiento de modelos de Machine Learning. Consulta una base de datos PostgreSQL con imagenes clasificadas por tipo de senal, proyecto geografico y tamanio, y genera un dataset balanceado por clase, grupo de tamanio y proyecto.

## Estructura del Proyecto

```
AlgoritmoEntrenamiento/
  algoritmo.py                          # Algoritmo principal (modular, importable)
  fisotec_basedatos.py                  # Conexion y operaciones con PostgreSQL
  fisotec_utils.py                      # Utilidades generales (QGIS plugin)
  credenciales.py                       # Credenciales de BD (NO subir a repositorio)
  test_algoritmo.py                     # Tests unitarios (52 tests)
  resultados_clases_proporcional.txt    # Resultados de la ultima ejecucion
```

## Ejecucion

```bash
# Ejecutar el algoritmo
python algoritmo.py

# Ejecutar los tests (no requiere BD)
python -m unittest test_algoritmo -v
```

## Como funciona el algoritmo

### Fase 1: Recopilacion de datos (`recopilar_datos`)
1. Conecta a PostgreSQL y obtiene todas las clases de seniales
2. Filtra por proyectos configurados, excluye clases no deseadas
3. Descarta clases con menos de `cantidad_minima` imagenes
4. Excluye imagenes que superen `tamanio_maximo`

### Fase 2: Calculo del objetivo (`calcular_objetivo`)
- Identifica la clase con menos imagenes
- El objetivo por clase = `min(cantidad_maxima, clase_mas_pequena)`
- Esto garantiza que todas las clases queden equilibradas

### Fase 3: Clasificacion en grupos de tamanio
Cada clase se divide en 4 grupos con nomenclatura unificada:
- **muy_pequeno** (1er cuartil)
- **pequeno** (2do cuartil)
- **medio** (3er cuartil)
- **grande** (4to cuartil)

Dos metodos disponibles:
- `clasificar_por_rango()`: Divide por intervalos iguales de tamanio
- `clasificar_proporcional()`: Divide por cantidad igual de imagenes (cuartiles)

### Fase 4: Balanceo por proyecto (`balancear_por_proyecto`)
Dentro de cada grupo de tamanio, las imagenes se distribuyen equitativamente entre los proyectos geograficos. Si un proyecto no tiene suficientes imagenes, su cuota se redistribuye a los demas.

### Fase 5: Data augmentation (`calcular_augmentation`)
Calcula cuantas imagenes augmentadas se necesitan por clase y grupo para multiplicar el dataset por el factor configurado (por defecto x5).

### Fase 6: Resultados (`generar_fichero_resultados`)
- Actualiza la columna `tamanio` en la BD con el grupo asignado
- Genera un fichero `.txt` con el resumen y plan de augmentation

## Configuracion

Parametros en el dict `CONFIG` de `algoritmo.py`:

| Parametro | Valor actual | Descripcion |
|---|---|---|
| `tipo_clasificacion` | `"proporcional"` | Metodo de division en grupos |
| `criterio_tamanio` | `"altura"` | Medida usada (altura o diagonal) |
| `proyectos` | 4 proyectos | Lista de proyectos a incluir |
| `clases_excluidas` | ST_C, ST_R, ST_S, ST_T | Clases ignoradas |
| `cantidad_minima` | 50 | Minimo de imagenes por clase |
| `cantidad_maxima` | 1000 | Maximo de imagenes por clase |
| `tamanio_maximo` | 500 | Tamanio maximo permitido (px) |
| `augmentation_factor` | 5 | Multiplicador de data augmentation |

## Arquitectura del codigo

El algoritmo esta estructurado en funciones puras importables, separando logica de negocio y acceso a BD:

```
Funciones puras (sin BD, testeables):
  clasificar_por_rango()
  clasificar_proporcional()
  calcular_cuotas_grupos()
  balancear_por_proyecto()
  clasificar_y_balancear_clase()
  calcular_objetivo()
  calcular_augmentation()

Funciones de BD (queries parametrizadas):
  crear_columna_tamanio()
  obtener_clases()
  obtener_imagenes_clase()
  actualizar_tamanio_bd()

Orquestacion:
  recopilar_datos()
  procesar_clases()
  generar_fichero_resultados()
  main()                              # Solo se ejecuta con `python algoritmo.py`
```

## Tests

52 tests unitarios organizados en 12 clases:

| Clase de test | Tests | Que valida |
|---|---|---|
| TestClasificacionProporcional | 7 | Division por cuartiles |
| TestClasificacionRango | 4 | Division por rangos iguales |
| TestBalancearPorProyecto | 10 | Redistribucion entre proyectos |
| TestCalcularCuotasGrupos | 7 | Cuotas de los 4 grupos |
| TestClasificarYBalancearClase | 3 | Funcion integrada clasificacion+balanceo |
| TestCalcularObjetivo | 3 | Calculo del objetivo balanceado |
| TestCalcularAugmentation | 3 | Calculo de data augmentation |
| TestNombresGruposUnificados | 2 | Nomenclatura consistente |
| TestFlujoCompleto | 3 | Pipeline completo sin BD |
| TestConsistenciaResultados | 3 | IDs unicos, limites respetados |
| TestCasosLimite | 5 | Edge cases (medida 0, negativos...) |
| TestFiltroConfiguracion | 2 | Filtros de clases y proyectos |

## Correcciones aplicadas

### 1. Refactorizacion en funciones (Prioridad Alta)
**Antes**: Todo el codigo se ejecutaba a nivel de modulo al importar. Imposible importar sin BD.
**Ahora**: Logica encapsulada en funciones puras. `if __name__ == '__main__'` como unico punto de entrada. Los tests importan directamente las funciones sin necesitar BD.

### 2. SQL Injection corregido (Prioridad Alta)
**Antes**: Consultas construidas con `.format()` y `%` interpolando valores directamente:
```python
# VULNERABLE
WHERE clase = '{clase}'
SET tamanio = '{tamanio}' WHERE id = {id}
```
**Ahora**: Queries parametrizadas con `%s` de psycopg2:
```python
# SEGURO
conexion.execute("WHERE clase = %s", (clase,))
conexion.execute("SET tamanio = %s WHERE id = %s", (nombre, id))
```

### 3. Data augmentation (Prioridad Alta)
**Problema**: Solo 50 imagenes por clase (12-13 por grupo) es insuficiente para ML.
**Solucion**: Funcion `calcular_augmentation()` que calcula cuantas imagenes augmentadas necesita cada clase y grupo. El fichero de resultados incluye un plan de augmentation con transformaciones recomendadas (rotacion, flip, brillo, contraste, recorte, desenfoque, ruido).

### 4. Bug `cerrarBaseDatos()` corregido
**Antes**: `conexion.close` (sin parentesis, no cerraba la conexion).
**Ahora**: `conexion.close()`.

### 5. Nomenclatura unificada
**Antes**: Variables usaban `muy_lejos/lejos/medio/cerca`, salida usaba `muy_pequeno/pequeno/medio/grande`.
**Ahora**: Todo usa `muy_pequeno/pequeno/medio/grande` de forma consistente via la constante `NOMBRES_GRUPOS`.

## Mejoras pendientes (Prioridad Media/Baja)

| Prioridad | Mejora | Impacto |
|---|---|---|
| Media | Split train/val/test (70/15/15) | Evaluacion correcta del modelo |
| Media | Exportar a formato YOLO/COCO | Integracion con frameworks de ML |
| Media | Configuracion en YAML externo | Mantenibilidad |
| Media | Manejo de transacciones en BD | Integridad de datos |
| Baja | Metricas de distribucion (Gini, CV) | Analisis de calidad del balanceo |
| Baja | Reproducibilidad (semillas fijas) | Experimentos repetibles |
