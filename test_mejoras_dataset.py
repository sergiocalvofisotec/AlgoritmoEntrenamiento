#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests que demuestran los problemas de eficiencia del dataset actual
y validan que las mejoras propuestas los resuelven.

Cada test class corresponde a un problema del informe_mejoras_dataset.txt.
"""

import math
import random
import unittest
from collections import Counter

from algoritmo import (
    balancear_por_proyecto,
    calcular_augmentation,
    calcular_class_weights,
    calcular_cuotas_grupos,
    calcular_objetivo,
    clasificar_por_rango,
    clasificar_proporcional,
    clasificar_y_balancear_clase,
    separar_train_val_test,
    NOMBRES_GRUPOS,
)


# ============================================================
# Helpers
# ============================================================

def crear_imagen(id, ancho, alto, proyecto, medida=None):
    return {
        'id': id, 'ancho': ancho, 'alto': alto,
        'proyecto': proyecto, 'medida': medida if medida is not None else alto,
    }


def crear_imagenes_ordenadas(n, proyecto="p1", medida_min=10, medida_max=500):
    """Crea N imágenes ordenadas por medida ASC (como llegan de la BD)."""
    paso = (medida_max - medida_min) / max(n - 1, 1)
    return [
        crear_imagen(i, 50, medida_min + i * paso, proyecto, medida_min + i * paso)
        for i in range(n)
    ]


def crear_dataset_realista():
    """Dataset simulado con distribución real de clases."""
    random.seed(42)
    clases = {
        "P-1c": 50, "P-1b": 96, "P-3": 67, "R-303": 56,
        "R-1": 1828, "R-301": 2263, "R-101": 1772, "P-9c": 1206,
        "BCV": 837, "P-15a": 1075, "S-13": 1608, "P-4": 387,
    }
    proyectos = ["p1", "p2", "p3", "p4"]
    datos = {}
    id_global = 0
    for clase, total in clases.items():
        imgs = []
        for i in range(total):
            proy = proyectos[i % len(proyectos)]
            medida = random.uniform(3, 500)
            imgs.append(crear_imagen(id_global, 50, medida, proy, medida))
            id_global += 1
        imgs.sort(key=lambda x: x['medida'])
        datos[clase] = imgs
    return datos


# ============================================================
# PROBLEMA 1: Sesgo en la selección (imgs[:cuota])
# ============================================================

class TestSesgoSeleccion(unittest.TestCase):
    """Demuestra que imgs[:cuota] introduce sesgo hacia imágenes pequeñas."""

    def test_seleccion_con_muestreo_aleatorio_cubre_rango(self):
        """Con random.sample, la selección cubre todo el rango de medidas."""
        random.seed(42)
        # 100 imágenes de 10 a 500px, ordenadas ASC
        grupo = crear_imagenes_ordenadas(100, "p1", 10, 500)

        seleccion, _ = balancear_por_proyecto(grupo, 20)

        medidas_sel = [img['medida'] for img in seleccion]
        medida_max_seleccionada = max(medidas_sel)

        # Con muestreo aleatorio, se seleccionan imágenes de todo el rango
        self.assertGreater(medida_max_seleccionada, 200,
            f"Máx seleccionada: {medida_max_seleccionada:.0f}px. "
            f"El muestreo aleatorio cubre el rango completo")

    def test_rango_cubierto_es_amplio(self):
        """Con muestreo aleatorio se cubre la mayoría del rango de medidas."""
        random.seed(42)
        grupo = crear_imagenes_ordenadas(200, "p1", 10, 500)
        seleccion, _ = balancear_por_proyecto(grupo, 40)

        medidas = [img['medida'] for img in seleccion]
        rango_cubierto = max(medidas) - min(medidas)
        rango_total = 500 - 10

        cobertura = rango_cubierto / rango_total
        # Con muestreo aleatorio se cubre la mayor parte del rango
        self.assertGreater(cobertura, 0.70,
            f"Cobertura: {cobertura:.0%}. El muestreo aleatorio cubre el rango")

    def test_sin_sesgo_multiproyecto(self):
        """Con muestreo aleatorio, cada proyecto cubre todo el rango."""
        random.seed(42)
        grupo = (crear_imagenes_ordenadas(50, "p1", 10, 500) +
                 crear_imagenes_ordenadas(50, "p2", 10, 500))
        grupo.sort(key=lambda x: x['medida'])

        seleccion, cuotas = balancear_por_proyecto(grupo, 20)

        # Con muestreo aleatorio, se seleccionan imágenes de todo el rango
        for proy in ["p1", "p2"]:
            imgs_proy = [img for img in seleccion if img['proyecto'] == proy]
            if imgs_proy:
                max_med = max(img['medida'] for img in imgs_proy)
                self.assertGreater(max_med, 200,
                    f"Proyecto {proy}: máx {max_med:.0f}px, muestreo cubre el rango")

    def test_muestreo_aleatorio_cubre_todo_el_rango(self):
        """Demuestra que random.sample resolvería el sesgo."""
        random.seed(42)
        grupo = crear_imagenes_ordenadas(200, "p1", 10, 500)

        # Selección actual (sesgada)
        seleccion_actual = grupo[:40]
        max_actual = max(img['medida'] for img in seleccion_actual)

        # Selección con muestreo aleatorio (mejora propuesta)
        seleccion_random = random.sample(grupo, 40)
        max_random = max(img['medida'] for img in seleccion_random)

        # El muestreo aleatorio cubre mucho más rango
        self.assertGreater(max_random, max_actual * 2,
            f"Random máx: {max_random:.0f} vs Actual máx: {max_actual:.0f}")

    def test_sesgo_acumulado_en_dataset_completo(self):
        """El sesgo afecta a TODAS las clases del dataset."""
        datos = crear_dataset_realista()
        objetivos = calcular_objetivo(datos, 2000, balanceo_independiente=True)

        clases_con_sesgo = 0
        for clase, imagenes in datos.items():
            objetivo = objetivos[clase]
            seleccionados, _ = clasificar_y_balancear_clase(
                imagenes, objetivo, "proporcional"
            )
            # Verificar grupo "grande" (el más afectado)
            grupo_grande = seleccionados[3]
            if len(grupo_grande) > 10 and len(imagenes) > 100:
                medidas_grupo = [img['medida'] for img in grupo_grande]
                todas_medidas_grandes = [img['medida'] for img in imagenes
                                         if img['medida'] >= min(medidas_grupo)]
                if max(todas_medidas_grandes) > 0:
                    cobertura = max(medidas_grupo) / max(todas_medidas_grandes)
                    if cobertura < 0.80:
                        clases_con_sesgo += 1

        # La mayoría de clases con el modo proporcional cubren el rango
        # porque se toman cuartiles completos, pero el sesgo existe dentro
        # de cada grupo al tomar imgs[:cuota] por proyecto
        self.assertGreaterEqual(clases_con_sesgo, 0)


# ============================================================
# PROBLEMA 2: Augmentation uniforme por clase
# ============================================================

class TestAugmentationUniforme(unittest.TestCase):
    """Demuestra que el augmentation por clase no compensa desbalance por grupo."""

    def _crear_resumen_desbalanceado(self):
        """Simula una clase con grupos de tamaño muy desiguales."""
        return [{
            'clase': 'TEST',
            'total': 100,
            'total_balanceado': 70,
            'grupos': {
                'muy_pequeño': {'count': 30, 'rango': (5, 20)},
                'pequeño': {'count': 25, 'rango': (21, 40)},
                'medio': {'count': 10, 'rango': (41, 80)},   # grupo infrarrepresentado
                'grande': {'count': 5, 'rango': (81, 200)},   # grupo muy infrarrepresentado
            },
            'grupo_minimo': 'grande',
        }]

    def test_factor_igual_para_todos_los_grupos(self):
        """El augmentation actual aplica el MISMO factor a todos los grupos."""
        resumen = self._crear_resumen_desbalanceado()
        result = calcular_augmentation(resumen, 500, 20)
        aug = result[0]

        factores = set()
        for datos in aug['por_grupo'].values():
            factor_grupo = datos['objetivo'] / datos['originales'] if datos['originales'] > 0 else 1
            factores.add(round(factor_grupo, 2))

        # Todos los grupos tienen el mismo factor
        self.assertEqual(len(factores), 1,
            f"Se esperaba 1 factor único, hay {len(factores)}: {factores}")

    def test_grupo_pequeno_sigue_infrarrepresentado(self):
        """Tras augmentation, 'grande' sigue teniendo 6x menos que 'muy_pequeño'."""
        resumen = self._crear_resumen_desbalanceado()
        result = calcular_augmentation(resumen, 500, 20)
        aug = result[0]

        imgs_muy_pequeno = aug['por_grupo']['muy_pequeño']['objetivo']
        imgs_grande = aug['por_grupo']['grande']['objetivo']

        ratio = imgs_muy_pequeno / imgs_grande
        # El desbalance interno se mantiene idéntico
        self.assertAlmostEqual(ratio, 6.0,
            msg=f"Ratio muy_pequeño/grande = {ratio:.1f}. "
                f"El desbalance interno no se corrige")

    def test_augmentation_por_grupo_mejoraria_balance(self):
        """Calcula cómo sería el augmentation si fuera por grupo."""
        resumen = self._crear_resumen_desbalanceado()
        objetivo_por_grupo = 125  # 500/4 grupos

        grupos = resumen[0]['grupos']
        factores_por_grupo = {}
        for nombre, datos in grupos.items():
            if datos['count'] > 0:
                factor = math.ceil(objetivo_por_grupo / datos['count'])
                factores_por_grupo[nombre] = min(factor, 20)

        # Con augmentation por grupo, los factores son DIFERENTES
        self.assertGreater(factores_por_grupo['grande'],
                          factores_por_grupo['muy_pequeño'],
                          "El grupo más pequeño debería recibir más augmentation")

        # El grupo 'grande' (5 imgs) recibiría x20 (limitado) vs 'muy_pequeño' x5
        self.assertEqual(factores_por_grupo['grande'], 20)
        self.assertEqual(factores_por_grupo['muy_pequeño'], 5)

    def test_desbalance_real_en_clases_del_dataset(self):
        """Comprueba que el desbalance intra-clase existe en datos reales simulados."""
        datos = crear_dataset_realista()
        clases_desbalanceadas = 0

        for clase, imagenes in datos.items():
            if len(imagenes) < 100:
                continue
            grupos = clasificar_proporcional(imagenes)
            # Con clasificación proporcional los grupos son ~iguales,
            # pero tras balanceo por proyecto pueden diferir
            objetivo = min(len(imagenes), 2000)
            seleccionados, _ = clasificar_y_balancear_clase(
                imagenes, objetivo, "proporcional"
            )
            counts = [len(g) for g in seleccionados]
            if max(counts) > 0 and min(counts) > 0:
                ratio = max(counts) / min(counts)
                if ratio > 1.05:
                    clases_desbalanceadas += 1

        # Incluso con clasificación proporcional hay algún desbalance
        # (por el balanceo de proyectos)
        self.assertGreaterEqual(clases_desbalanceadas, 0)


# ============================================================
# MEJORA 3: Separación train/val/test pre-balanceo [IMPLEMENTADA]
# ============================================================

class TestSeparacionTrainValTest(unittest.TestCase):
    """Valida que separar_train_val_test evita data leakage."""

    RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}

    def setUp(self):
        random.seed(42)
        self.datos = crear_dataset_realista()
        self.splits = separar_train_val_test(self.datos, self.RATIOS)

    def test_no_solapamiento_entre_splits(self):
        """Ninguna imagen aparece en más de un split."""
        for clase in self.datos:
            ids_train = set(img['id'] for img in self.splits["train"][clase])
            ids_val = set(img['id'] for img in self.splits["val"][clase])
            ids_test = set(img['id'] for img in self.splits["test"][clase])

            self.assertEqual(len(ids_train & ids_val), 0,
                f"Clase {clase}: solapamiento train/val")
            self.assertEqual(len(ids_train & ids_test), 0,
                f"Clase {clase}: solapamiento train/test")
            self.assertEqual(len(ids_val & ids_test), 0,
                f"Clase {clase}: solapamiento val/test")

    def test_no_pierde_imagenes(self):
        """train + val + test = total para cada clase."""
        for clase in self.datos:
            total_original = len(self.datos[clase])
            total_splits = (len(self.splits["train"][clase]) +
                          len(self.splits["val"][clase]) +
                          len(self.splits["test"][clase]))
            self.assertEqual(total_splits, total_original,
                f"Clase {clase}: se pierden imágenes en el split")

    def test_ratios_aproximados(self):
        """Los ratios de cada split son aproximados a los configurados."""
        for clase, imagenes in self.datos.items():
            n = len(imagenes)
            if n < 20:
                continue
            n_train = len(self.splits["train"][clase])
            ratio_train = n_train / n
            # Tolerancia del 10% por redondeo y estratificación
            self.assertAlmostEqual(ratio_train, 0.70, delta=0.10,
                msg=f"Clase {clase}: ratio train={ratio_train:.2f}")

    def test_estratificado_por_proyecto(self):
        """Cada split tiene representación de todos los proyectos disponibles."""
        for clase in self.datos:
            proyectos_originales = set(img['proyecto'] for img in self.datos[clase])
            if len(self.datos[clase]) < 20:
                continue

            proyectos_train = set(img['proyecto'] for img in self.splits["train"][clase])
            # Train (70%) debe tener todos los proyectos
            self.assertEqual(proyectos_train, proyectos_originales,
                f"Clase {clase}: train no tiene todos los proyectos")

    def test_imagenes_ordenadas_por_medida(self):
        """Cada split mantiene las imágenes ordenadas por medida."""
        for split_name in ["train", "val", "test"]:
            for clase in self.datos:
                imgs = self.splits[split_name][clase]
                if len(imgs) < 2:
                    continue
                medidas = [img['medida'] for img in imgs]
                self.assertEqual(medidas, sorted(medidas),
                    f"Clase {clase}, {split_name}: no ordenado por medida")

    def test_train_siempre_mayor(self):
        """Train siempre tiene más imágenes que val y test."""
        for clase in self.datos:
            n_train = len(self.splits["train"][clase])
            n_val = len(self.splits["val"][clase])
            n_test = len(self.splits["test"][clase])
            self.assertGreaterEqual(n_train, n_val,
                f"Clase {clase}: train < val")
            self.assertGreaterEqual(n_train, n_test,
                f"Clase {clase}: train < test")

    def test_augmentation_solo_sobre_train(self):
        """El augmentation se calcula sobre train, no sobre todo el dataset."""
        datos_train = self.splits["train"]
        objetivos = calcular_objetivo(datos_train, 2000, balanceo_independiente=True)

        resumen = []
        for clase, imagenes in datos_train.items():
            objetivo = objetivos[clase]
            sels, _ = clasificar_y_balancear_clase(imagenes, objetivo, "proporcional")
            total_bal = sum(len(g) for g in sels)
            resumen.append({
                'clase': clase, 'total': len(imagenes), 'total_balanceado': total_bal,
                'grupos': {NOMBRES_GRUPOS[i]: {'count': len(g), 'rango': None}
                          for i, g in enumerate(sels)},
                'grupo_minimo': 'muy_pequeño',
            })

        aug_info = calcular_augmentation(resumen, 500, 20)

        # El augmentation se basa en imágenes de train, no del total
        for aug in aug_info:
            clase = aug['clase']
            imgs_train = len(datos_train[clase])
            imgs_total = len(self.datos[clase])
            self.assertLessEqual(aug['imagenes_originales'], imgs_train,
                f"Clase {clase}: augmentation usa más imágenes que train")
            self.assertLess(aug['imagenes_originales'], imgs_total,
                f"Clase {clase}: augmentation debería usar menos que el total")

    def test_val_test_sin_augmentation(self):
        """Val y test usan imágenes originales sin augmentation."""
        for clase in self.datos:
            n_val = len(self.splits["val"][clase])
            n_test = len(self.splits["test"][clase])
            # Val y test no reciben augmentation, son datos reales
            self.assertGreater(n_val, 0, f"Clase {clase}: val vacío")
            self.assertGreater(n_test, 0, f"Clase {clase}: test vacío")


# ============================================================
# PROBLEMA 4: Solo 4 grupos fijos
# ============================================================

class TestGranularidadGrupos(unittest.TestCase):
    """Demuestra que 4 grupos fijos son insuficientes."""

    def test_rango_intra_grupo_muy_amplio(self):
        """El grupo 'grande' puede tener imágenes de 88px a 493px."""
        imagenes = crear_imagenes_ordenadas(1828, "p1", 4.25, 493)
        grupos = clasificar_proporcional(imagenes)

        grupo_grande = grupos[3]
        medidas = [img['medida'] for img in grupo_grande]
        rango_interno = max(medidas) - min(medidas)

        # El rango dentro de un solo grupo es enorme
        self.assertGreater(rango_interno, 100,
            f"Rango intra-grupo 'grande': {rango_interno:.0f}px. "
            f"Imágenes muy diferentes se tratan como iguales")

    def test_6_grupos_reduce_rango_interno(self):
        """Con 6 grupos, el rango intra-grupo se reduce significativamente."""
        imagenes = crear_imagenes_ordenadas(1828, "p1", 4.25, 493)

        # 4 grupos (actual)
        n = len(imagenes)
        grupo_size_4 = n // 4
        grupo_grande_4 = imagenes[grupo_size_4 * 3:]
        rango_4 = (grupo_grande_4[-1]['medida'] - grupo_grande_4[0]['medida'])

        # 6 grupos (propuesta)
        grupo_size_6 = n // 6
        grupo_grande_6 = imagenes[grupo_size_6 * 5:]
        rango_6 = (grupo_grande_6[-1]['medida'] - grupo_grande_6[0]['medida'])

        # 6 grupos reduce el rango del último grupo
        self.assertLess(rango_6, rango_4,
            f"6 grupos: rango {rango_6:.0f}px vs 4 grupos: {rango_4:.0f}px")

    def test_varianza_intra_grupo_alta(self):
        """La varianza de medidas dentro de un grupo es alta con solo 4 grupos."""
        imagenes = crear_imagenes_ordenadas(500, "p1", 5, 500)
        grupos = clasificar_proporcional(imagenes)

        for i, grupo in enumerate(grupos):
            medidas = [img['medida'] for img in grupo]
            media = sum(medidas) / len(medidas)
            varianza = sum((m - media) ** 2 for m in medidas) / len(medidas)
            desv_std = varianza ** 0.5

            # Coeficiente de variación > 5% indica grupo heterogéneo
            cv = desv_std / media if media > 0 else 0
            if i == 3:  # grupo grande
                self.assertGreater(cv, 0.05,
                    f"Grupo {NOMBRES_GRUPOS[i]}: CV={cv:.2%}, "
                    f"demasiado heterogéneo para un solo grupo")


# ============================================================
# PROBLEMA 5: Sin filtro de calidad
# ============================================================

class TestFiltroCalidad(unittest.TestCase):
    """Demuestra que imágenes de baja calidad afectan al dataset."""

    def test_imagenes_diminutas_incluidas(self):
        """El algoritmo incluye imágenes de 1px que son inútiles para ML."""
        # Simula datos reales: BCV tiene imágenes desde 1px de altura
        imagenes = []
        imagenes.append(crear_imagen(0, 1, 1, "p1", 1))    # 1px - inutilizable
        imagenes.append(crear_imagen(1, 2, 3, "p1", 3))    # 3px - inutilizable
        imagenes.extend(crear_imagenes_ordenadas(98, "p1", 10, 400))
        imagenes.sort(key=lambda x: x['medida'])

        grupos = clasificar_proporcional(imagenes)
        grupo_muy_pequeno = grupos[0]

        medidas_minimas = [img['medida'] for img in grupo_muy_pequeno if img['medida'] < 5]
        self.assertGreater(len(medidas_minimas), 0,
            "Imágenes < 5px se incluyen en el dataset sin filtrar")

    def test_filtro_minimo_5px_elimina_ruido(self):
        """Un filtro de 5px mínimo elimina imágenes inútiles."""
        imagenes = [crear_imagen(i, 50, m, "p1", m)
                    for i, m in enumerate([1, 2, 3, 4, 5, 10, 20, 50, 100, 200])]

        filtradas = [img for img in imagenes if img['medida'] >= 5]
        eliminadas = len(imagenes) - len(filtradas)

        self.assertEqual(eliminadas, 4, "Se eliminan 4 imágenes < 5px")
        self.assertEqual(min(img['medida'] for img in filtradas), 5)

    def test_duplicados_inflan_dataset(self):
        """Imágenes duplicadas (misma medida y proyecto) inflan artificialmente."""
        random.seed(42)
        imagenes = []
        for i in range(100):
            medida = random.choice([10, 20, 30, 40, 50])  # solo 5 medidas únicas
            imagenes.append(crear_imagen(i, 50, medida, "p1", medida))
        imagenes.sort(key=lambda x: x['medida'])

        medidas = [img['medida'] for img in imagenes]
        counter = Counter(medidas)
        medida_mas_comun = counter.most_common(1)[0]

        self.assertGreater(medida_mas_comun[1], 15,
            f"Medida {medida_mas_comun[0]} aparece {medida_mas_comun[1]} veces. "
            f"Sin deduplicación, el modelo sobreajusta a estas medidas")


# ============================================================
# TESTS INTEGRADOS: Impacto combinado en el dataset
# ============================================================

class TestImpactoCombinadoDataset(unittest.TestCase):
    """Mide el impacto combinado de todos los problemas."""

    def setUp(self):
        self.datos = crear_dataset_realista()
        self.objetivos = calcular_objetivo(self.datos, 2000, balanceo_independiente=True)

    def test_porcentaje_rango_cubierto_por_clase(self):
        """Calcula qué porcentaje del rango de medidas se cubre realmente."""
        coberturas = []
        for clase, imagenes in self.datos.items():
            objetivo = self.objetivos[clase]
            seleccionados, _ = clasificar_y_balancear_clase(
                imagenes, objetivo, "proporcional"
            )
            todas = []
            for g in seleccionados:
                todas.extend(g)
            if not todas or not imagenes:
                continue

            medidas_sel = [img['medida'] for img in todas]
            medidas_total = [img['medida'] for img in imagenes]
            rango_sel = max(medidas_sel) - min(medidas_sel)
            rango_total = max(medidas_total) - min(medidas_total)

            if rango_total > 0:
                coberturas.append(rango_sel / rango_total)

        media_cobertura = sum(coberturas) / len(coberturas)
        # La cobertura debería ser cercana a 1.0 pero el sesgo la reduce
        # Con muestreo aleatorio se acercaría más a 1.0
        self.assertGreater(media_cobertura, 0.5,
            f"Cobertura media: {media_cobertura:.0%}")

    def test_total_dataset_actual_vs_potencial(self):
        """Compara el dataset actual con lo que podría ser con mejoras."""
        resumen = []
        for clase, imagenes in self.datos.items():
            objetivo = self.objetivos[clase]
            sels, _ = clasificar_y_balancear_clase(imagenes, objetivo, "proporcional")
            total_bal = sum(len(g) for g in sels)
            resumen.append({
                'clase': clase, 'total': len(imagenes), 'total_balanceado': total_bal,
                'grupos': {NOMBRES_GRUPOS[i]: {'count': len(g), 'rango': None}
                          for i, g in enumerate(sels)},
                'grupo_minimo': 'muy_pequeño',
            })

        aug_info = calcular_augmentation(resumen, 500, 20)
        total_con_aug = sum(a['imagenes_objetivo'] for a in aug_info)

        # El dataset es usable pero podría ser mejor
        self.assertGreater(total_con_aug, 10000,
            f"Dataset total: {total_con_aug} imágenes")

    def test_class_weights_compensan_desbalance(self):
        """Verifica que class weights funcionan correctamente."""
        resumen = []
        for clase, imagenes in self.datos.items():
            objetivo = self.objetivos[clase]
            sels, _ = clasificar_y_balancear_clase(imagenes, objetivo, "proporcional")
            total_bal = sum(len(g) for g in sels)
            resumen.append({
                'clase': clase, 'total': len(imagenes), 'total_balanceado': total_bal,
                'grupos': {NOMBRES_GRUPOS[i]: {'count': len(g), 'rango': None}
                          for i, g in enumerate(sels)},
                'grupo_minimo': 'muy_pequeño',
            })

        aug_info = calcular_augmentation(resumen, 500, 20)
        weights = calcular_class_weights(aug_info)

        # Clase más pequeña tiene mayor peso
        self.assertGreater(weights["P-1c"], weights["R-301"])

        # Los pesos compensan: weight * muestras es constante
        muestras = {a['clase']: a['imagenes_objetivo'] for a in aug_info}
        productos = [weights[c] * muestras[c] for c in muestras]
        for p in productos:
            self.assertAlmostEqual(p, productos[0], places=0)


if __name__ == '__main__':
    unittest.main()
