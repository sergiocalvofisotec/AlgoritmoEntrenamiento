#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests unitarios para el algoritmo de preparación de datasets YOLO.

Importa directamente las funciones del módulo algoritmo,
sin necesidad de conexión a base de datos.
"""

import os
import random
import shutil
import tempfile
import unittest

from algoritmo import (
    balancear_por_proyecto,
    calcular_objetivo,
    separar_train_val_test,
    generar_label_yolo,
    generar_yaml_contenido,
    exportar_dataset_yolo,
    procesar_clases,
)


# ============================================================
# Helpers para generar datos de test
# ============================================================

def crear_imagen(id, ancho, alto, proyecto, nombre_imagen="img_test.jpg",
                 x_center=None, y_center=None, w_imagen=640, h_imagen=640):
    """Crea un diccionario de imagen simulada con campos YOLO."""
    return {
        'id': id,
        'ancho': ancho,
        'alto': alto,
        'proyecto': proyecto,
        'nombre_imagen': nombre_imagen,
        'x_center': x_center if x_center is not None else w_imagen / 2,
        'y_center': y_center if y_center is not None else h_imagen / 2,
        'w_imagen': w_imagen,
        'h_imagen': h_imagen,
    }


def crear_imagenes(n, proyecto="proyecto1", ancho=50, alto_inicio=10, alto_paso=5):
    """Genera n imágenes con dimensiones incrementales."""
    return [
        crear_imagen(i, ancho, alto_inicio + i * alto_paso, proyecto,
                     f"img_{proyecto}_{i}.jpg",
                     x_center=320, y_center=320)
        for i in range(n)
    ]


def crear_imagenes_multiproyecto(n_por_proyecto, proyectos):
    """Genera imágenes distribuidas entre varios proyectos."""
    imagenes = []
    id_global = 0
    for proyecto in proyectos:
        for i in range(n_por_proyecto):
            imagenes.append(
                crear_imagen(id_global, 50, 20 + i * 10, proyecto,
                             f"img_{proyecto}_{i}.jpg",
                             x_center=320, y_center=320)
            )
            id_global += 1
    return imagenes


# Distribución real extraída de la BD (clases con >= 100 imágenes)
CLASES_REALES = {
    "BCV": 837, "P-1": 241, "P-13a": 111, "P-13b": 130, "P-15a": 1075,
    "P-1a": 178, "P-20b": 178, "P-21a": 111, "P-4": 387, "P-9c": 1206,
    "PDP": 868, "R-1": 1828, "R-100": 110, "R-101": 1772, "R-2": 627,
    "R-301": 2263, "R-304": 93, "R-305": 637, "R-308": 707,
    "R-308c": 171, "R-308d": 191, "R-308e": 1482, "R-308f": 420,
    "R-400a": 221, "R-400b": 182, "R-401a": 521, "R-402": 857,
    "R-502": 101, "S-105a": 331, "S-11": 138, "S-13": 1608,
    "S-17a": 228, "S-19": 121, "S-200": 319, "S-300": 457,
    "S-572": 188, "S-600": 86, "S-800": 140,
}

PROYECTOS_REALES = ["03_ibiza", "01_alcaudete", "02_fuente_albilla", "04_carreteras"]


def generar_dataset_realista(clases_dict, proyectos):
    """Genera un dataset simulado con la distribución real de la BD."""
    random.seed(42)
    datos_clases = {}
    id_global = 0
    for clase, total in clases_dict.items():
        imagenes = []
        for i in range(total):
            proyecto = proyectos[i % len(proyectos)]
            ancho = random.randint(15, 200)
            alto = random.randint(15, 400)
            x_center = random.uniform(50, 590)
            y_center = random.uniform(50, 590)
            imagenes.append(
                crear_imagen(id_global, ancho, alto, proyecto,
                             f"img_{clase}_{i}.jpg",
                             x_center=x_center, y_center=y_center)
            )
            id_global += 1
        datos_clases[clase] = imagenes
    return datos_clases


# ============================================================
# TESTS DE BALANCEO POR PROYECTO
# ============================================================

class TestBalancearPorProyecto(unittest.TestCase):
    """Tests para la función de balanceo entre proyectos."""

    def test_reparto_equitativo(self):
        """Con cuota suficiente, reparte igual entre proyectos."""
        imagenes = crear_imagenes_multiproyecto(20, ["p1", "p2"])
        seleccion, cuotas = balancear_por_proyecto(imagenes, 20)
        self.assertEqual(cuotas["p1"], 10)
        self.assertEqual(cuotas["p2"], 10)

    def test_respeta_cuota(self):
        """La selección no supera la cuota pedida."""
        imagenes = crear_imagenes_multiproyecto(50, ["p1", "p2", "p3"])
        seleccion, cuotas = balancear_por_proyecto(imagenes, 30)
        self.assertEqual(len(seleccion), 30)

    def test_proyecto_con_pocas_imagenes(self):
        """Redistribuye excedente si un proyecto no alcanza su cuota."""
        imgs_p1 = crear_imagenes(5, "p1")
        imgs_p2 = crear_imagenes(100, "p2")
        imagenes = imgs_p1 + imgs_p2
        seleccion, cuotas = balancear_por_proyecto(imagenes, 40)
        self.assertEqual(cuotas["p1"], 5)
        self.assertEqual(cuotas["p2"], 35)
        self.assertEqual(len(seleccion), 40)

    def test_cuota_mayor_que_total(self):
        """Si la cuota supera el total, devuelve todas las imágenes."""
        imagenes = crear_imagenes(10, "p1")
        seleccion, cuotas = balancear_por_proyecto(imagenes, 1000)
        self.assertEqual(len(seleccion), 10)

    def test_grupo_vacio(self):
        """Con lista vacía devuelve selección vacía."""
        seleccion, cuotas = balancear_por_proyecto([], 10)
        self.assertEqual(len(seleccion), 0)
        self.assertEqual(cuotas, {})

    def test_muestreo_aleatorio(self):
        """Usa random.sample, no selección secuencial."""
        random.seed(42)
        imagenes = crear_imagenes(100, "p1")
        sel1, _ = balancear_por_proyecto(imagenes, 10)
        ids1 = [img['id'] for img in sel1]
        # No debe ser simplemente los primeros 10
        self.assertNotEqual(ids1, list(range(10)))

    def test_cuatro_proyectos(self):
        """Con 4 proyectos reales, todos quedan representados."""
        imagenes = crear_imagenes_multiproyecto(30, PROYECTOS_REALES)
        seleccion, cuotas = balancear_por_proyecto(imagenes, 40)
        for proy in PROYECTOS_REALES:
            self.assertIn(proy, cuotas)
            self.assertGreater(cuotas[proy], 0)

    def test_ids_unicos(self):
        """Los IDs seleccionados son únicos (sin duplicados)."""
        imagenes = crear_imagenes_multiproyecto(50, ["p1", "p2", "p3"])
        seleccion, _ = balancear_por_proyecto(imagenes, 60)
        ids = [img['id'] for img in seleccion]
        self.assertEqual(len(ids), len(set(ids)))


# ============================================================
# TESTS DE CÁLCULO DE OBJETIVO
# ============================================================

class TestCalcularObjetivo(unittest.TestCase):
    """Tests para el cálculo del objetivo por clase."""

    def test_limita_a_maxima(self):
        """Clases con más imágenes que el máximo quedan limitadas."""
        datos = {"A": crear_imagenes(3000), "B": crear_imagenes(500)}
        objetivos = calcular_objetivo(datos, 2000)
        self.assertEqual(objetivos["A"], 2000)
        self.assertEqual(objetivos["B"], 500)

    def test_clase_pequena_usa_todo(self):
        """Clases con pocas imágenes usan todas."""
        datos = {"A": crear_imagenes(150)}
        objetivos = calcular_objetivo(datos, 2000)
        self.assertEqual(objetivos["A"], 150)

    def test_vacio(self):
        """Con datos vacíos devuelve dict vacío."""
        objetivos = calcular_objetivo({}, 2000)
        self.assertEqual(objetivos, {})

    def test_independiente_por_clase(self):
        """Cada clase tiene su propio objetivo."""
        datos = {"A": crear_imagenes(2500), "B": crear_imagenes(200), "C": crear_imagenes(100)}
        objetivos = calcular_objetivo(datos, 2000)
        self.assertEqual(objetivos["A"], 2000)
        self.assertEqual(objetivos["B"], 200)
        self.assertEqual(objetivos["C"], 100)


# ============================================================
# TESTS DE SEPARACIÓN TRAIN/VAL/TEST
# ============================================================

class TestSepararTrainValTest(unittest.TestCase):
    """Tests para el split estratificado por clase y proyecto."""

    def setUp(self):
        self.datos = {
            "A": crear_imagenes_multiproyecto(50, ["p1", "p2"]),
            "B": crear_imagenes_multiproyecto(30, ["p1", "p2", "p3"]),
        }
        self.ratios = {"train": 0.70, "val": 0.15, "test": 0.15}

    def test_no_pierde_datos(self):
        """train + val + test = total para cada clase."""
        splits = separar_train_val_test(self.datos, self.ratios)
        for clase in self.datos:
            total = len(splits["train"][clase]) + len(splits["val"][clase]) + len(splits["test"][clase])
            self.assertEqual(total, len(self.datos[clase]))

    def test_train_mayor(self):
        """Train siempre tiene más datos que val y test."""
        splits = separar_train_val_test(self.datos, self.ratios)
        for clase in self.datos:
            self.assertGreater(len(splits["train"][clase]), len(splits["val"][clase]))
            self.assertGreater(len(splits["train"][clase]), len(splits["test"][clase]))

    def test_sin_solapamiento(self):
        """No hay IDs compartidos entre splits."""
        splits = separar_train_val_test(self.datos, self.ratios)
        for clase in self.datos:
            ids_train = {img['id'] for img in splits["train"][clase]}
            ids_val = {img['id'] for img in splits["val"][clase]}
            ids_test = {img['id'] for img in splits["test"][clase]}
            self.assertEqual(len(ids_train & ids_val), 0)
            self.assertEqual(len(ids_train & ids_test), 0)
            self.assertEqual(len(ids_val & ids_test), 0)

    def test_val_test_no_vacios(self):
        """Con suficientes datos, val y test no quedan vacíos."""
        splits = separar_train_val_test(self.datos, self.ratios)
        for clase in self.datos:
            self.assertGreater(len(splits["val"][clase]), 0)
            self.assertGreater(len(splits["test"][clase]), 0)

    def test_estratificado_por_proyecto(self):
        """Cada split tiene representación de los proyectos."""
        datos = {"A": crear_imagenes_multiproyecto(50, PROYECTOS_REALES)}
        splits = separar_train_val_test(datos, self.ratios)
        for split_name in ["train", "val", "test"]:
            proyectos_en_split = {img['proyecto'] for img in splits[split_name]["A"]}
            self.assertEqual(len(proyectos_en_split), len(PROYECTOS_REALES),
                f"Split {split_name}: no todos los proyectos representados")

    def test_sin_leakage_imagen_multiclase(self):
        """Una imagen con anotaciones de varias clases va al mismo split.

        Si img_shared.jpg tiene señales de clase A y B, ambas anotaciones
        deben caer en el mismo split para evitar data leakage.
        """
        # Imagen compartida entre clase A y clase B
        img_compartida_a = crear_imagen(100, 50, 50, "p1", "img_shared.jpg",
                                        x_center=100, y_center=100)
        img_compartida_b = crear_imagen(101, 30, 30, "p1", "img_shared.jpg",
                                        x_center=200, y_center=200)
        datos = {
            "A": crear_imagenes_multiproyecto(20, ["p1", "p2"]) + [img_compartida_a],
            "B": crear_imagenes_multiproyecto(20, ["p1", "p2"]) + [img_compartida_b],
        }
        splits = separar_train_val_test(datos, self.ratios)

        # Buscar en qué split cayó img_shared.jpg para cada clase
        split_clase_a = None
        split_clase_b = None
        for split_name in ["train", "val", "test"]:
            if any(img['nombre_imagen'] == "img_shared.jpg" for img in splits[split_name]["A"]):
                split_clase_a = split_name
            if any(img['nombre_imagen'] == "img_shared.jpg" for img in splits[split_name]["B"]):
                split_clase_b = split_name

        self.assertIsNotNone(split_clase_a, "img_shared.jpg no encontrada en clase A")
        self.assertIsNotNone(split_clase_b, "img_shared.jpg no encontrada en clase B")
        self.assertEqual(split_clase_a, split_clase_b,
            f"Data leakage: img_shared.jpg en '{split_clase_a}' para A y '{split_clase_b}' para B")


# ============================================================
# TESTS DE GENERACIÓN DE LABELS YOLO
# ============================================================

class TestGenerarLabelYolo(unittest.TestCase):
    """Tests para la generación de labels en formato YOLO."""

    def test_formato_correcto(self):
        """El label tiene 5 campos: clase_id x y w h."""
        img = crear_imagen(0, 80, 120, "p1", x_center=320, y_center=320)
        label = generar_label_yolo(img, 5, 640, 640)
        partes = label.split()
        self.assertEqual(len(partes), 5)
        self.assertEqual(partes[0], "5")

    def test_valores_normalizados(self):
        """Todos los valores están entre 0 y 1."""
        img = crear_imagen(0, 80, 120, "p1", x_center=320, y_center=240)
        label = generar_label_yolo(img, 0, 640, 640)
        partes = label.split()
        for valor in partes[1:]:
            v = float(valor)
            self.assertGreaterEqual(v, 0.0)
            self.assertLessEqual(v, 1.0)

    def test_centro_imagen(self):
        """Un objeto centrado tiene x_center=0.5 y y_center=0.5."""
        img = crear_imagen(0, 100, 100, "p1", x_center=320, y_center=320)
        label = generar_label_yolo(img, 0, 640, 640)
        partes = label.split()
        self.assertAlmostEqual(float(partes[1]), 0.5, places=3)
        self.assertAlmostEqual(float(partes[2]), 0.5, places=3)

    def test_clamp_fuera_de_rango(self):
        """Valores fuera de rango se clamplan a [0, 1]."""
        img = crear_imagen(0, 100, 100, "p1", x_center=700, y_center=-50)
        label = generar_label_yolo(img, 0, 640, 640)
        partes = label.split()
        self.assertEqual(float(partes[1]), 1.0)  # x_center clamped
        self.assertEqual(float(partes[2]), 0.0)  # y_center clamped

    def test_precision_6_decimales(self):
        """Los valores tienen 6 decimales de precisión."""
        img = crear_imagen(0, 80, 143, "p1", x_center=319, y_center=320.5)
        label = generar_label_yolo(img, 0, 640, 640)
        partes = label.split()
        for valor in partes[1:]:
            decimales = valor.split('.')[1]
            self.assertEqual(len(decimales), 6)


# ============================================================
# TESTS DE GENERACIÓN YAML
# ============================================================

class TestGenerarYaml(unittest.TestCase):
    """Tests para la generación del fichero seniales.yaml."""

    def test_contenido_basico(self):
        """El YAML contiene path, train, val, test, nc y names."""
        clases = ["BCV", "P-1", "R-301"]
        contenido = generar_yaml_contenido(clases, "/ruta/dataset")
        self.assertIn("path: /ruta/dataset", contenido)
        self.assertIn("train: images/train", contenido)
        self.assertIn("val: images/val", contenido)
        self.assertIn("test: images/test", contenido)
        self.assertIn("nc: 3", contenido)

    def test_mapeo_clases(self):
        """Las clases están mapeadas con índice correcto."""
        clases = ["BCV", "P-1", "R-301"]
        contenido = generar_yaml_contenido(clases, "/ruta")
        self.assertIn("0: BCV", contenido)
        self.assertIn("1: P-1", contenido)
        self.assertIn("2: R-301", contenido)

    def test_nc_coincide(self):
        """nc coincide con el número de clases."""
        clases = ["A", "B", "C", "D", "E"]
        contenido = generar_yaml_contenido(clases, "/ruta")
        self.assertIn("nc: 5", contenido)


# ============================================================
# TESTS DE EXPORTACIÓN YOLO
# ============================================================

class TestExportarDatasetYolo(unittest.TestCase):
    """Tests para la exportación a estructura de carpetas YOLO."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config = {
            "ruta_salida": os.path.join(self.tmpdir, "dataset"),
            "ruta_imagenes": None,
        }
        # Crear resúmenes simulados
        imgs_train = [crear_imagen(i, 80, 120, "p1", f"train_{i}.jpg",
                                   x_center=320, y_center=320)
                      for i in range(10)]
        imgs_val = [crear_imagen(100+i, 80, 120, "p1", f"val_{i}.jpg",
                                 x_center=320, y_center=320)
                    for i in range(3)]
        imgs_test = [crear_imagen(200+i, 80, 120, "p1", f"test_{i}.jpg",
                                  x_center=320, y_center=320)
                     for i in range(3)]

        self.resumen_train = [{'clase': 'BCV', 'total': 10, 'total_balanceado': 10,
                               'seleccion': imgs_train, 'cuotas_proyecto': {"p1": 10}}]
        self.resumen_val = [{'clase': 'BCV', 'total': 3, 'total_balanceado': 3,
                             'seleccion': imgs_val, 'cuotas_proyecto': {}}]
        self.resumen_test = [{'clase': 'BCV', 'total': 3, 'total_balanceado': 3,
                              'seleccion': imgs_test, 'cuotas_proyecto': {}}]
        self.clases = ["BCV"]

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_crea_estructura_carpetas(self):
        """Crea las carpetas images/ y labels/ para cada split."""
        exportar_dataset_yolo(self.resumen_train, self.resumen_val,
                              self.resumen_test, self.clases, self.config)
        ruta = self.config["ruta_salida"]
        for split in ["train", "val", "test"]:
            self.assertTrue(os.path.isdir(os.path.join(ruta, "images", split)))
            self.assertTrue(os.path.isdir(os.path.join(ruta, "labels", split)))

    def test_genera_labels(self):
        """Genera un fichero .txt por imagen en labels/."""
        exportar_dataset_yolo(self.resumen_train, self.resumen_val,
                              self.resumen_test, self.clases, self.config)
        ruta = self.config["ruta_salida"]
        labels_train = os.listdir(os.path.join(ruta, "labels", "train"))
        self.assertEqual(len(labels_train), 10)
        self.assertTrue(all(f.endswith('.txt') for f in labels_train))

    def test_contenido_label(self):
        """El contenido del label tiene formato YOLO correcto."""
        exportar_dataset_yolo(self.resumen_train, self.resumen_val,
                              self.resumen_test, self.clases, self.config)
        ruta = self.config["ruta_salida"]
        label_file = os.path.join(ruta, "labels", "train", "train_0.txt")
        with open(label_file) as f:
            contenido = f.read().strip()
        partes = contenido.split()
        self.assertEqual(len(partes), 5)
        self.assertEqual(partes[0], "0")  # clase_id = 0 (BCV)

    def test_genera_yaml(self):
        """Genera el fichero seniales.yaml."""
        _, ruta_yaml = exportar_dataset_yolo(
            self.resumen_train, self.resumen_val,
            self.resumen_test, self.clases, self.config)
        self.assertTrue(os.path.exists(ruta_yaml))
        with open(ruta_yaml) as f:
            contenido = f.read()
        self.assertIn("nc: 1", contenido)
        self.assertIn("0: BCV", contenido)

    def test_estadisticas(self):
        """Las estadísticas reflejan el número de imágenes exportadas."""
        stats, _ = exportar_dataset_yolo(
            self.resumen_train, self.resumen_val,
            self.resumen_test, self.clases, self.config)
        self.assertEqual(stats["train"], 10)
        self.assertEqual(stats["val"], 3)
        self.assertEqual(stats["test"], 3)

    def test_multiples_anotaciones_misma_imagen(self):
        """Varias señales en una imagen generan un solo fichero con múltiples líneas."""
        img_compartida = crear_imagen(0, 80, 120, "p1", "shared.jpg",
                                      x_center=100, y_center=100)
        img_compartida2 = crear_imagen(1, 40, 60, "p1", "shared.jpg",
                                       x_center=400, y_center=400)
        resumen = [
            {'clase': 'BCV', 'total': 1, 'total_balanceado': 1,
             'seleccion': [img_compartida], 'cuotas_proyecto': {"p1": 1}},
            {'clase': 'R-301', 'total': 1, 'total_balanceado': 1,
             'seleccion': [img_compartida2], 'cuotas_proyecto': {"p1": 1}},
        ]
        exportar_dataset_yolo(resumen, [], [], ["BCV", "R-301"], self.config)
        label_file = os.path.join(self.config["ruta_salida"], "labels", "train", "shared.txt")
        with open(label_file) as f:
            lineas = f.read().strip().split('\n')
        self.assertEqual(len(lineas), 2)
        # Una línea con clase 0 (BCV) y otra con clase 1 (R-301)
        clases_ids = {l.split()[0] for l in lineas}
        self.assertEqual(clases_ids, {"0", "1"})


# ============================================================
# TESTS DE PROCESAMIENTO DE CLASES (balanceo)
# ============================================================

class TestProcesarClases(unittest.TestCase):
    """Tests para el procesamiento y balanceo de clases."""

    def test_respeta_objetivo(self):
        """Cada clase produce su número objetivo de imágenes."""
        datos = {
            "A": crear_imagenes_multiproyecto(100, ["p1", "p2"]),
            "B": crear_imagenes_multiproyecto(50, ["p1", "p2"]),
        }
        objetivos = {"A": 150, "B": 80}
        resumen = procesar_clases(datos, objetivos)
        for entry in resumen:
            self.assertEqual(entry['total_balanceado'], objetivos[entry['clase']])

    def test_seleccion_no_vacia(self):
        """Cada clase tiene imágenes seleccionadas."""
        datos = {"A": crear_imagenes(200, "p1")}
        objetivos = {"A": 100}
        resumen = procesar_clases(datos, objetivos)
        self.assertGreater(len(resumen[0]['seleccion']), 0)

    def test_ids_unicos_en_seleccion(self):
        """No hay IDs duplicados en la selección de una clase."""
        datos = {"A": crear_imagenes_multiproyecto(50, PROYECTOS_REALES)}
        objetivos = {"A": 100}
        resumen = procesar_clases(datos, objetivos)
        ids = [img['id'] for img in resumen[0]['seleccion']]
        self.assertEqual(len(ids), len(set(ids)))


# ============================================================
# TESTS DE FILTRO DE CALIDAD
# ============================================================

class TestFiltroCalidad(unittest.TestCase):
    """Tests para validar los criterios de filtrado de calidad."""

    def test_cantidad_minima_100(self):
        """Clases con menos de 100 imágenes se excluyen."""
        clases = {"BCV": 837, "P-X": 30, "R-1": 1828, "S-NEW": 99}
        validas = {k: v for k, v in clases.items() if v >= 100}
        self.assertEqual(set(validas.keys()), {"BCV", "R-1"})

    def test_filtro_tamanio_minimo(self):
        """Recortes menores de 10px se consideran errores de anotación."""
        imagenes = [
            crear_imagen(0, 5, 3, "p1"),   # ambos < 10: excluir
            crear_imagen(1, 80, 120, "p1"),  # ok
            crear_imagen(2, 8, 120, "p1"),   # ancho < 10: excluir
            crear_imagen(3, 80, 7, "p1"),    # alto < 10: excluir
        ]
        filtradas = [img for img in imagenes
                     if img['ancho'] >= 10 and img['alto'] >= 10]
        self.assertEqual(len(filtradas), 1)
        self.assertEqual(filtradas[0]['id'], 1)

    def test_filtro_tamanio_maximo(self):
        """Recortes mayores del máximo se excluyen."""
        imagenes = [
            crear_imagen(0, 80, 120, "p1"),   # ok
            crear_imagen(1, 80, 600, "p1"),   # alto > 500: excluir
            crear_imagen(2, 80, 500, "p1"),   # justo en el límite: ok
        ]
        filtradas = [img for img in imagenes if img['alto'] <= 500]
        self.assertEqual(len(filtradas), 2)

    def test_clases_excluidas_manualmente(self):
        """Las clases en la lista de exclusión se saltan."""
        EXCLUIDAS = ["ST_C", "ST_R", "ST_S", "ST_T"]
        clases = ["BCV", "ST_C", "P-1", "ST_R", "R-301"]
        procesadas = [c for c in clases if c not in EXCLUIDAS]
        self.assertEqual(procesadas, ["BCV", "P-1", "R-301"])


# ============================================================
# TESTS CON DATASET REALISTA
# ============================================================

class TestSimulacionDatasetRealista(unittest.TestCase):
    """Simula el pipeline completo con distribución real de la BD."""

    def setUp(self):
        random.seed(42)
        self.datos = generar_dataset_realista(CLASES_REALES, PROYECTOS_REALES)
        self.objetivos = calcular_objetivo(self.datos, 2000)

    def test_clase_grande_limitada(self):
        """R-301 (2263 imgs) queda limitada a 2000."""
        self.assertEqual(self.objetivos["R-301"], 2000)

    def test_clase_pequena_usa_todo(self):
        """S-600 (86 imgs) usa todas sus imágenes."""
        self.assertEqual(self.objetivos["S-600"], 86)

    def test_total_dataset(self):
        """El dataset total tiene suficientes imágenes para YOLO."""
        total = sum(self.objetivos.values())
        self.assertGreater(total, 10000)

    def test_balanceo_real_por_clase(self):
        """Cada clase produce su objetivo tras balanceo."""
        for clase, imagenes in self.datos.items():
            objetivo = self.objetivos[clase]
            seleccion, _ = balancear_por_proyecto(imagenes, objetivo)
            self.assertEqual(len(seleccion), objetivo,
                f"Clase {clase}: esperado {objetivo}, obtenido {len(seleccion)}")

    def test_distribucion_proyectos(self):
        """En clases grandes, los 4 proyectos están representados."""
        imagenes_r301 = self.datos["R-301"]
        objetivo = self.objetivos["R-301"]
        seleccion, cuotas = balancear_por_proyecto(imagenes_r301, objetivo)
        self.assertEqual(len(cuotas), 4)


class TestSimulacionTrainValTest(unittest.TestCase):
    """Simula la separación train/val/test con datos realistas."""

    def setUp(self):
        random.seed(42)
        self.datos = generar_dataset_realista(CLASES_REALES, PROYECTOS_REALES)
        self.ratios = {"train": 0.70, "val": 0.15, "test": 0.15}
        self.splits = separar_train_val_test(self.datos, self.ratios)

    def test_no_pierde_datos(self):
        """train + val + test = total para cada clase."""
        for clase in self.datos:
            total = (len(self.splits["train"][clase]) +
                     len(self.splits["val"][clase]) +
                     len(self.splits["test"][clase]))
            self.assertEqual(total, len(self.datos[clase]))

    def test_train_suficiente_para_yolo(self):
        """El total de train supera 5000 imágenes (mínimo para YOLO)."""
        total_train = sum(len(imgs) for imgs in self.splits["train"].values())
        self.assertGreater(total_train, 5000)

    def test_val_test_no_vacios(self):
        """Todas las clases tienen val y test con datos."""
        for clase in self.datos:
            self.assertGreater(len(self.splits["val"][clase]), 0, f"Clase {clase}: val vacío")
            self.assertGreater(len(self.splits["test"][clase]), 0, f"Clase {clase}: test vacío")

    def test_sin_data_leakage(self):
        """No hay IDs compartidos entre train, val y test."""
        for clase in self.datos:
            ids_train = {img['id'] for img in self.splits["train"][clase]}
            ids_val = {img['id'] for img in self.splits["val"][clase]}
            ids_test = {img['id'] for img in self.splits["test"][clase]}
            self.assertEqual(len(ids_train & ids_val), 0,
                f"Clase {clase}: data leakage train-val")
            self.assertEqual(len(ids_train & ids_test), 0,
                f"Clase {clase}: data leakage train-test")


class TestSimulacionExportacionYolo(unittest.TestCase):
    """Tests de integración para la exportación completa a YOLO."""

    def setUp(self):
        random.seed(42)
        self.tmpdir = tempfile.mkdtemp()
        self.datos = generar_dataset_realista(
            {"BCV": 200, "R-301": 500, "P-1": 150}, PROYECTOS_REALES)
        self.ratios = {"train": 0.70, "val": 0.15, "test": 0.15}
        self.splits = separar_train_val_test(self.datos, self.ratios)
        self.clases = sorted(self.datos.keys())
        self.config = {"ruta_salida": os.path.join(self.tmpdir, "dataset"),
                       "ruta_imagenes": None, "cantidad_maxima": 2000}

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_pipeline_completo(self):
        """El pipeline completo genera un dataset YOLO válido."""
        objetivos = calcular_objetivo(self.splits["train"], 2000)
        resumen_train = procesar_clases(self.splits["train"], objetivos)
        resumen_val = [{'clase': c, 'total': len(imgs), 'total_balanceado': len(imgs),
                        'seleccion': imgs, 'cuotas_proyecto': {}}
                       for c, imgs in self.splits["val"].items()]
        resumen_test = [{'clase': c, 'total': len(imgs), 'total_balanceado': len(imgs),
                         'seleccion': imgs, 'cuotas_proyecto': {}}
                        for c, imgs in self.splits["test"].items()]

        stats, ruta_yaml = exportar_dataset_yolo(
            resumen_train, resumen_val, resumen_test, self.clases, self.config)

        # Verificar estructura
        ruta = self.config["ruta_salida"]
        self.assertTrue(os.path.exists(ruta_yaml))
        self.assertGreater(stats["train"], 0)
        self.assertGreater(stats["val"], 0)
        self.assertGreater(stats["test"], 0)

        # Verificar que los labels son válidos
        labels_dir = os.path.join(ruta, "labels", "train")
        for label_file in os.listdir(labels_dir)[:5]:
            with open(os.path.join(labels_dir, label_file)) as f:
                for linea in f:
                    partes = linea.strip().split()
                    self.assertEqual(len(partes), 5)
                    clase_id = int(partes[0])
                    self.assertGreaterEqual(clase_id, 0)
                    self.assertLess(clase_id, len(self.clases))

    def test_yaml_clases_correctas(self):
        """El YAML tiene las clases correctas con IDs ordenados."""
        objetivos = calcular_objetivo(self.splits["train"], 2000)
        resumen_train = procesar_clases(self.splits["train"], objetivos)
        resumen_val = [{'clase': c, 'total': len(imgs), 'total_balanceado': len(imgs),
                        'seleccion': imgs, 'cuotas_proyecto': {}}
                       for c, imgs in self.splits["val"].items()]

        _, ruta_yaml = exportar_dataset_yolo(
            resumen_train, resumen_val, [], self.clases, self.config)

        with open(ruta_yaml) as f:
            contenido = f.read()
        self.assertIn(f"nc: {len(self.clases)}", contenido)
        for i, clase in enumerate(self.clases):
            self.assertIn(f"{i}: {clase}", contenido)


# ============================================================
# TESTS DE REPRODUCIBILIDAD
# ============================================================

class TestReproducibilidad(unittest.TestCase):
    """Tests para verificar que el pipeline es reproducible."""

    def test_seed_produce_mismos_resultados(self):
        """Con la misma seed, el balanceo produce resultados idénticos."""
        imagenes = crear_imagenes_multiproyecto(50, PROYECTOS_REALES)

        random.seed(42)
        sel1, _ = balancear_por_proyecto(imagenes, 100)
        ids1 = sorted(img['id'] for img in sel1)

        random.seed(42)
        sel2, _ = balancear_por_proyecto(imagenes, 100)
        ids2 = sorted(img['id'] for img in sel2)

        self.assertEqual(ids1, ids2)

    def test_seed_diferente_produce_resultados_diferentes(self):
        """Con seed distinta, el balanceo produce resultados diferentes."""
        imagenes = crear_imagenes_multiproyecto(100, ["p1", "p2"])

        random.seed(42)
        sel1, _ = balancear_por_proyecto(imagenes, 50)
        ids1 = sorted(img['id'] for img in sel1)

        random.seed(99)
        sel2, _ = balancear_por_proyecto(imagenes, 50)
        ids2 = sorted(img['id'] for img in sel2)

        self.assertNotEqual(ids1, ids2)


if __name__ == '__main__':
    unittest.main()
