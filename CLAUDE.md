# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the algorithm (requires PostgreSQL connection)
python algoritmo.py

# Run all tests (no DB needed - pure functions only)
python -m unittest test_algoritmo -v       # 100 original tests
python -m unittest test_mejoras_dataset -v  # 26 improvement tests

# Run a single test class
python -m unittest test_algoritmo.TestBalancearPorProyecto -v

# Python path on this machine
C:/Users/sergi/AppData/Local/Python/bin/python.exe
```

## Architecture

The algorithm balances image datasets of traffic signals for ML training. It runs in 5 phases:

1. **Recopilar datos** - Query images from PostgreSQL (`public.seniales_verticales`), filter by class/project/size
2. **Separar train/val/test** - Stratified split by class AND project before balancing (70/15/15)
3. **Calcular objetivo** - Determine target images per class (independent or strict mode)
4. **Clasificar + balancear** - Split each class into 4 size groups, balance across projects with `random.sample()`
5. **Augmentation + weights** - Adaptive augmentation per class, class weights for loss function

Key design: pure functions (classification, balancing, augmentation, weights) are fully separated from DB functions. Tests only exercise pure functions.

### Core flow in `algoritmo.py`

```
main() -> recopilar_datos() -> separar_train_val_test() -> calcular_objetivo()
       -> procesar_clases() [only on train split]
       -> calcular_augmentation() [only on train]
       -> calcular_class_weights()
       -> generar_fichero_resultados()
```

### CONFIG dictionary

All behavior is controlled by the `CONFIG` dict at the top of `algoritmo.py`. Key options:
- `tipo_clasificacion`: "proporcional" (quartiles) or "rango" (equal ranges)
- `balanceo_independiente`: `True` = each class uses all its images; `False` = all limited to smallest class
- `split_ratios`: `None` to disable train/val/test separation
- `augmentation_objetivo`: minimum images per class after augmentation

## Git remotes

- `origin` -> sergiocalvofisotec/AlgoritmoEntrenamiento (main development)
- `practicas` -> rafayeguas/fisotec_sergio_practicas (deliverables)
- Auto-push hook configured: every Edit/Write auto-commits and pushes to `practicas`

## Language

All code comments, docstrings, reports, and communication should be in Spanish with correct orthography (tildes, eñes).
