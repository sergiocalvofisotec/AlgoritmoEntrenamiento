# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the algorithm (requires PostgreSQL connection)
python algoritmo.py

# Run all tests (no DB needed - pure functions only)
python -m unittest test_algoritmo -v       # 51 tests
python -m unittest test_mejoras_dataset -v  # 18 tests

# Run a single test class
python -m unittest test_algoritmo.TestBalancearPorProyecto -v

# Python path on this machine
C:/Users/sergi/AppData/Local/Python/bin/python.exe
```

## Architecture

The algorithm prepares image datasets of traffic signals for YOLO training. It runs in 5 phases:

1. **Recopilar datos + filtro de calidad** - Query images from PostgreSQL, filter by min/max size (10-500px) and min samples per class (100)
2. **Separar train/val/test** - Stratified split by class AND project before balancing (70/15/15)
3. **Balancear por clase y proyecto** - Balance across projects with `random.sample()` (train only)
4. **Exportar a formato YOLO** - Generate images/labels folders + seniales.yaml
5. **Registrar versión** - Save config + image assignments in JSON for traceability

Key design: pure functions (balancing, label generation, YAML) are fully separated from DB functions. Tests only exercise pure functions.

### Core flow in `algoritmo.py`

```
main() -> recopilar_datos() -> separar_train_val_test()
       -> calcular_objetivo() -> procesar_clases() [train only]
       -> exportar_dataset_yolo() -> registrar_version()
       -> generar_fichero_resultados()
```

### CONFIG dictionary

All behavior is controlled by the `CONFIG` dict at the top of `algoritmo.py`. Key options:
- `cantidad_minima`: 100 (min images per class for YOLO viability)
- `cantidad_maxima`: 2000 (cap per class to avoid loss dominance)
- `tamanio_minimo`: 10 (exclude annotation errors < 10px)
- `tamanio_maximo`: 500 (exclude oversized crops)
- `split_ratios`: train/val/test ratios (70/15/15)
- `ruta_salida`: output path for YOLO dataset

## Git remotes

- `origin` -> sergiocalvofisotec/AlgoritmoEntrenamiento (main development)
- `practicas` -> rafayeguas/fisotec_sergio_practicas (deliverables)
- Auto-push hook configured: every Edit/Write auto-commits and pushes to `practicas`

## Language

All code comments, docstrings, reports, and communication should be in Spanish with correct orthography (tildes, eñes).
