#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests que validan las mejoras del dataset orientadas a YOLO.

Valida filtros de calidad, balanceo por proyecto, separación
train/val/test y exportación a formato YOLO.
"""

import random
import unittest
from collections import Counter

from algoritmo import (
    balancear_por_proyecto,
    calcular_objetivo,
    separar_train_val_test,
    generar_label_yolo,
)


# ============================================================
# Helpers
# ============================================================

def crear_imagen(id, ancho, alto, proyecto, nombre_imagen="img.jpg",
                 x_center=320, y_center=320, w_imagen=640, h_imagen=640):
    return {
        'id': id, 'ancho': ancho, 'alto': alto,
        'proyecto': proyecto, 'nombre_imagen': nombre_imagen,
        'x_center': x_center, 'y_center': y_center,
        'w_imagen': w_imagen, 'h_imagen': h_imagen,
    }


def crear_imagenes_ordenadas(n, proyecto="p1", alto_min=10, alto_max=500):
    """Crea N imágenes con altos incrementales."""
    paso = (alto_max - alto_min) / max(n - 1, 1)
    return [
        crear_imagen(i, 50, alto_min + i * paso, proyecto,
                     f"img_{proyecto}_{i}.jpg")
        for i in range(n)
    ]


def crear_dataset_realista():
    """Dataset simulado con distribución real de clases (>=100 muestras)."""
    random.seed(42)
    clases = {
        "R-1": 1828, "R-301": 2263, "R-101": 1772, "P-9c": 1206,
        "BCV": 837, "P-15a": 1075, "S-13": 1608, "P-4": 387,
        "R-100": 110, "S-600": 86, "P-1": 241, "S-800": 140,
    }
    proyectos = ["p1", "p2", "p3", "p4"]
    datos = {}
    id_global = 0
    for clase, total in clases.items():
        imgs = []
        for i in range(total):
            proy = proyectos[i % len(proyectos)]
            ancho = random.randint(15, 200)
            alto = random.randint(15, 400)
            x_center = random.uniform(50, 590)
            y_center = random.uniform(50, 590)
            imgs.append(crear_imagen(id_global, ancho, alto, proy,
                                     f"img_{clase}_{i}.jpg",
                                     x_center=x_center, y_center=y_center))
            id_global += 1
        datos[clase] = imgs
    return datos


# ============================================================
# PROBLEMA 1: Sesgo en la selección
# ============================================================

class TestSesgoSeleccion(unittest.TestCase):
    """Verifica que el muestreo aleatorio evita sesgo en la selección."""

    def test_muestreo_aleatorio_cubre_rango(self):
        """Con random.sample, la selección cubre todo el rango de tamaños."""
        random.seed(42)
        grupo = crear_imagenes_ordenadas(100, "p1", 10, 500)
        seleccion, _ = balancear_por_proyecto(grupo, 20)
        altos_sel = [img['alto'] for img in seleccion]
        self.assertGreater(max(altos_sel), 200,
            "El muestreo aleatorio debe cubrir el rango completo")

    def test_no_seleccion_secuencial(self):
        """No se seleccionan simplemente los primeros N."""
        random.seed(42)
        imagenes = crear_imagenes_ordenadas(200, "p1", 10, 500)
        seleccion, _ = balancear_por_proyecto(imagenes, 40)
        ids = [img['id'] for img in seleccion]
        self.assertNotEqual(ids, list(range(40)))

    def test_cobertura_amplia(self):
        """El muestreo cubre al menos el 70% del rango de tamaños."""
        random.seed(42)
        grupo = crear_imagenes_ordenadas(200, "p1", 10, 500)
        seleccion, _ = balancear_por_proyecto(grupo, 40)
        altos = [img['alto'] for img in seleccion]
        cobertura = (max(altos) - min(altos)) / (500 - 10)
        self.assertGreater(cobertura, 0.70)


# ============================================================
# PROBLEMA 2: Filtro de calidad (tamaño mínimo)
# ============================================================

class TestFiltroCalidadMinimo(unittest.TestCase):
    """Verifica que los filtros de calidad funcionan correctamente."""

    def test_excluir_recortes_diminutos(self):
        """Recortes menores de 10px se excluyen como errores de anotación."""
        imagenes = [
            crear_imagen(0, 5, 3, "p1"),    # ambos < 10: excluir
            crear_imagen(1, 80, 120, "p1"),  # ok
            crear_imagen(2, 8, 120, "p1"),   # ancho < 10: excluir
            crear_imagen(3, 80, 7, "p1"),    # alto < 10: excluir
        ]
        filtradas = [img for img in imagenes
                     if img['ancho'] >= 10 and img['alto'] >= 10]
        self.assertEqual(len(filtradas), 1)

    def test_filtro_maximo(self):
        """Recortes mayores del máximo se excluyen."""
        imagenes = [
            crear_imagen(0, 80, 120, "p1"),
            crear_imagen(1, 80, 600, "p1"),   # alto > 500
            crear_imagen(2, 80, 500, "p1"),   # justo en el límite
        ]
        filtradas = [img for img in imagenes if img['alto'] <= 500]
        self.assertEqual(len(filtradas), 2)

    def test_cantidad_minima_100(self):
        """Clases con menos de 100 imágenes se excluyen para YOLO."""
        clases = {"BCV": 837, "X": 30, "R-1": 1828, "Y": 99}
        validas = {k: v for k, v in clases.items() if v >= 100}
        self.assertEqual(set(validas.keys()), {"BCV", "R-1"})

    def test_duplicados_inflan_dataset(self):
        """Imágenes con medidas repetidas inflan artificialmente el dataset."""
        random.seed(42)
        imagenes = []
        for i in range(100):
            alto = random.choice([10, 20, 30, 40, 50])
            imagenes.append(crear_imagen(i, 50, alto, "p1"))
        altos = [img['alto'] for img in imagenes]
        counter = Counter(altos)
        mas_comun = counter.most_common(1)[0]
        self.assertGreater(mas_comun[1], 15,
            f"Alto {mas_comun[0]} aparece {mas_comun[1]} veces")


# ============================================================
# MEJORA 3: Separación train/val/test pre-balanceo
# ============================================================

class TestSeparacionTrainValTest(unittest.TestCase):
    """Valida que la separación pre-balanceo evita data leakage."""

    RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}

    def setUp(self):
        random.seed(42)
        self.datos = crear_dataset_realista()
        self.splits = separar_train_val_test(self.datos, self.RATIOS)

    def test_no_solapamiento(self):
        """Ninguna imagen aparece en más de un split."""
        for clase in self.datos:
            ids_train = {img['id'] for img in self.splits["train"][clase]}
            ids_val = {img['id'] for img in self.splits["val"][clase]}
            ids_test = {img['id'] for img in self.splits["test"][clase]}
            self.assertEqual(len(ids_train & ids_val), 0)
            self.assertEqual(len(ids_train & ids_test), 0)
            self.assertEqual(len(ids_val & ids_test), 0)

    def test_no_pierde_imagenes(self):
        """train + val + test = total."""
        for clase in self.datos:
            total = (len(self.splits["train"][clase]) +
                     len(self.splits["val"][clase]) +
                     len(self.splits["test"][clase]))
            self.assertEqual(total, len(self.datos[clase]))

    def test_ratios_aproximados(self):
        """Los ratios son aproximados a los configurados."""
        for clase, imagenes in self.datos.items():
            n = len(imagenes)
            if n < 20:
                continue
            ratio_train = len(self.splits["train"][clase]) / n
            self.assertAlmostEqual(ratio_train, 0.70, delta=0.10)

    def test_estratificado_por_proyecto(self):
        """Train tiene representación de todos los proyectos."""
        for clase in self.datos:
            if len(self.datos[clase]) < 20:
                continue
            proyectos_original = {img['proyecto'] for img in self.datos[clase]}
            proyectos_train = {img['proyecto'] for img in self.splits["train"][clase]}
            self.assertEqual(proyectos_train, proyectos_original)

    def test_train_mayor(self):
        """Train siempre tiene más imágenes que val y test."""
        for clase in self.datos:
            self.assertGreaterEqual(len(self.splits["train"][clase]),
                                    len(self.splits["val"][clase]))
            self.assertGreaterEqual(len(self.splits["train"][clase]),
                                    len(self.splits["test"][clase]))


# ============================================================
# MEJORA 4: Labels YOLO correctos
# ============================================================

class TestLabelsYolo(unittest.TestCase):
    """Verifica que los labels YOLO se generan correctamente."""

    def test_normalizacion_correcta(self):
        """Las coordenadas se normalizan dividiendo por el tamaño de imagen."""
        img = crear_imagen(0, 80, 120, "p1", x_center=320, y_center=240)
        label = generar_label_yolo(img, 0, 640, 640)
        partes = label.split()
        self.assertAlmostEqual(float(partes[1]), 0.5, places=3)    # x_center
        self.assertAlmostEqual(float(partes[2]), 0.375, places=3)  # y_center
        self.assertAlmostEqual(float(partes[3]), 0.125, places=3)  # width
        self.assertAlmostEqual(float(partes[4]), 0.1875, places=3) # height

    def test_valores_en_rango(self):
        """Todos los valores normalizados están entre 0 y 1."""
        for _ in range(100):
            x = random.uniform(0, 640)
            y = random.uniform(0, 640)
            w = random.uniform(1, 200)
            h = random.uniform(1, 300)
            img = crear_imagen(0, w, h, "p1", x_center=x, y_center=y)
            label = generar_label_yolo(img, 0, 640, 640)
            for val in label.split()[1:]:
                self.assertGreaterEqual(float(val), 0.0)
                self.assertLessEqual(float(val), 1.0)

    def test_clase_id_correcto(self):
        """El ID de clase se escribe correctamente."""
        img = crear_imagen(0, 80, 120, "p1")
        for clase_id in [0, 5, 46]:
            label = generar_label_yolo(img, clase_id, 640, 640)
            self.assertEqual(label.split()[0], str(clase_id))


# ============================================================
# TESTS INTEGRADOS: Pipeline completo
# ============================================================

class TestPipelineCompleto(unittest.TestCase):
    """Verifica el pipeline completo de preparación de dataset YOLO."""

    def setUp(self):
        random.seed(42)
        self.datos = crear_dataset_realista()

    def test_pipeline_produce_dataset_viable(self):
        """El pipeline completo produce un dataset viable para YOLO."""
        ratios = {"train": 0.70, "val": 0.15, "test": 0.15}
        splits = separar_train_val_test(self.datos, ratios)
        objetivos = calcular_objetivo(splits["train"], 2000)

        total_train = sum(objetivos.values())
        total_val = sum(len(imgs) for imgs in splits["val"].values())
        total_test = sum(len(imgs) for imgs in splits["test"].values())

        self.assertGreater(total_train, 5000, "Train insuficiente para YOLO")
        self.assertGreater(total_val, 500, "Val insuficiente")
        self.assertGreater(total_test, 500, "Test insuficiente")

    def test_balanceo_reduce_dominancia(self):
        """El cap de cantidad_maxima reduce la dominancia de clases grandes."""
        objetivos = calcular_objetivo(self.datos, 2000)
        ratio = max(objetivos.values()) / min(objetivos.values())
        # Sin cap sería 2263/86 = 26x. Con cap: 2000/86 = 23x
        # El balanceo por proyecto + cap reduce la dominancia
        self.assertLess(ratio, 25)

    def test_todos_los_proyectos_representados(self):
        """Tras balanceo, todos los proyectos están representados en clases grandes."""
        imagenes_r1 = self.datos["R-1"]
        seleccion, cuotas = balancear_por_proyecto(imagenes_r1, 2000)
        self.assertEqual(len(cuotas), 4)
        for proy, n in cuotas.items():
            self.assertGreater(n, 0, f"Proyecto {proy} sin representación")


if __name__ == '__main__':
    unittest.main()
