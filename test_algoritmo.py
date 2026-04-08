#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests unitarios para el algoritmo de balanceo de datasets.

Importa directamente las funciones del módulo algoritmo refactorizado,
sin necesidad de conexión a base de datos.
"""

import unittest

from algoritmo import (
    clasificar_por_rango,
    clasificar_proporcional,
    calcular_cuotas_grupos,
    balancear_por_proyecto,
    clasificar_y_balancear_clase,
    calcular_objetivo,
    calcular_augmentation,
    calcular_class_weights,
    NOMBRES_GRUPOS,
)


# ============================================================
# Helpers para generar datos de test
# ============================================================

def crear_imagen(id, ancho, alto, proyecto, medida=None):
    """Crea un diccionario de imagen simulada."""
    return {
        'id': id,
        'ancho': ancho,
        'alto': alto,
        'proyecto': proyecto,
        'medida': medida if medida is not None else alto
    }


def crear_imagenes(n, proyecto="proyecto1", medida_inicio=10, medida_paso=5):
    """Genera n imágenes con medidas incrementales."""
    return [
        crear_imagen(i, 50, medida_inicio + i * medida_paso, proyecto,
                     medida_inicio + i * medida_paso)
        for i in range(n)
    ]


def crear_imagenes_multiproyecto(n_por_proyecto, proyectos):
    """Genera imágenes distribuidas entre varios proyectos."""
    imagenes = []
    id_counter = 0
    for proy in proyectos:
        for i in range(n_por_proyecto):
            medida = 10 + id_counter * 3
            imagenes.append(crear_imagen(id_counter, 50, medida, proy, medida))
            id_counter += 1
    imagenes.sort(key=lambda x: x['medida'])
    return imagenes


# ============================================================
# TESTS
# ============================================================

class TestClasificacionProporcional(unittest.TestCase):
    """Tests para la clasificación proporcional (por cantidad)."""

    def test_distribucion_uniforme_100(self):
        """100 imágenes deben dividirse en 4 grupos de 25."""
        imagenes = crear_imagenes(100)
        grupos = clasificar_proporcional(imagenes)
        for grupo in grupos:
            self.assertEqual(len(grupo), 25)

    def test_distribucion_uniforme_50(self):
        """50 imágenes: grupos de 13, 12, 13, 12 (o similar)."""
        imagenes = crear_imagenes(50)
        grupos = clasificar_proporcional(imagenes)
        total = sum(len(g) for g in grupos)
        self.assertEqual(total, 50)
        for grupo in grupos:
            self.assertIn(len(grupo), [12, 13])

    def test_4_imagenes(self):
        """Mínimo viable: 4 imágenes, 1 por grupo."""
        imagenes = crear_imagenes(4)
        grupos = clasificar_proporcional(imagenes)
        for grupo in grupos:
            self.assertEqual(len(grupo), 1)

    def test_1_imagen(self):
        """Con 1 imagen, solo el primer grupo la contiene."""
        imagenes = crear_imagenes(1)
        grupos = clasificar_proporcional(imagenes)
        self.assertEqual(len(grupos[0]), 1)
        self.assertEqual(len(grupos[1]), 0)
        self.assertEqual(len(grupos[2]), 0)
        self.assertEqual(len(grupos[3]), 0)

    def test_orden_preservado(self):
        """Las imágenes dentro de cada grupo mantienen el orden por medida."""
        imagenes = crear_imagenes(100)
        grupos = clasificar_proporcional(imagenes)
        for grupo in grupos:
            medidas = [img['medida'] for img in grupo]
            self.assertEqual(medidas, sorted(medidas))

    def test_no_solapamiento_medidas(self):
        """El máximo de un grupo es <= mínimo del siguiente."""
        imagenes = crear_imagenes(100)
        grupos = clasificar_proporcional(imagenes)
        for i in range(len(grupos) - 1):
            if grupos[i] and grupos[i + 1]:
                max_actual = max(img['medida'] for img in grupos[i])
                min_siguiente = min(img['medida'] for img in grupos[i + 1])
                self.assertLessEqual(max_actual, min_siguiente)

    def test_5_imagenes_distribucion(self):
        """5 imágenes: total conservado."""
        imagenes = crear_imagenes(5)
        grupos = clasificar_proporcional(imagenes)
        total = sum(len(g) for g in grupos)
        self.assertEqual(total, 5)


class TestClasificacionRango(unittest.TestCase):
    """Tests para la clasificación por rangos iguales."""

    def test_distribucion_uniforme_lineal(self):
        """Imágenes con medidas equiespaciadas: todas se clasifican."""
        imagenes = [crear_imagen(i, 50, i * 10, "p1", i * 10) for i in range(1, 101)]
        grupos = clasificar_por_rango(imagenes)
        total = sum(len(g) for g in grupos)
        self.assertEqual(total, 100)

    def test_todas_misma_medida(self):
        """Si todas tienen la misma medida, todas van al último grupo."""
        imagenes = [crear_imagen(i, 50, 50, "p1", 50) for i in range(20)]
        grupos = clasificar_por_rango(imagenes)
        self.assertEqual(len(grupos[3]), 20)

    def test_rango_correcto(self):
        """Verifica que los rangos se calculan correctamente."""
        imagenes = [crear_imagen(i, 50, m, "p1", m) for i, m in enumerate([0, 25, 50, 75, 100])]
        grupos = clasificar_por_rango(imagenes)
        self.assertEqual(len(grupos[0]), 1)  # medida 0
        self.assertEqual(len(grupos[1]), 1)  # medida 25
        self.assertEqual(len(grupos[2]), 1)  # medida 50
        self.assertEqual(len(grupos[3]), 2)  # medidas 75, 100

    def test_valores_extremos_concentrados(self):
        """Mayoría de imágenes pequeñas con pocas grandes."""
        medidas = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]
        imagenes = [crear_imagen(i, 50, m, "p1", m) for i, m in enumerate(medidas)]
        grupos = clasificar_por_rango(imagenes)
        self.assertGreater(len(grupos[0]), len(grupos[3]))


class TestBalancearPorProyecto(unittest.TestCase):
    """Tests para el balanceo entre proyectos."""

    def test_grupo_vacio(self):
        seleccion, cuotas = balancear_por_proyecto([], 10)
        self.assertEqual(seleccion, [])
        self.assertEqual(cuotas, {})

    def test_un_proyecto(self):
        grupo = crear_imagenes(20, "proyecto1")
        seleccion, cuotas = balancear_por_proyecto(grupo, 10)
        self.assertEqual(len(seleccion), 10)
        self.assertEqual(cuotas["proyecto1"], 10)

    def test_dos_proyectos_equilibrados(self):
        grupo = crear_imagenes(20, "p1") + crear_imagenes(20, "p2")
        seleccion, cuotas = balancear_por_proyecto(grupo, 10)
        self.assertEqual(len(seleccion), 10)
        self.assertEqual(cuotas["p1"], 5)
        self.assertEqual(cuotas["p2"], 5)

    def test_cuota_impar_dos_proyectos(self):
        grupo = crear_imagenes(20, "p1") + crear_imagenes(20, "p2")
        seleccion, cuotas = balancear_por_proyecto(grupo, 11)
        self.assertEqual(len(seleccion), 11)
        self.assertEqual(cuotas["p1"] + cuotas["p2"], 11)

    def test_proyecto_con_pocas_imagenes(self):
        """Si un proyecto tiene menos que su cuota, se redistribuye."""
        grupo = crear_imagenes(3, "p1") + crear_imagenes(20, "p2")
        seleccion, cuotas = balancear_por_proyecto(grupo, 10)
        self.assertEqual(cuotas["p1"], 3)
        self.assertEqual(cuotas["p2"], 7)
        self.assertEqual(len(seleccion), 10)

    def test_todos_proyectos_insuficientes(self):
        grupo = crear_imagenes(3, "p1") + crear_imagenes(4, "p2")
        seleccion, cuotas = balancear_por_proyecto(grupo, 20)
        self.assertEqual(len(seleccion), 7)

    def test_cuatro_proyectos(self):
        grupo = []
        for p in ["p1", "p2", "p3", "p4"]:
            grupo.extend(crear_imagenes(20, p))
        seleccion, cuotas = balancear_por_proyecto(grupo, 20)
        self.assertEqual(len(seleccion), 20)
        for p in ["p1", "p2", "p3", "p4"]:
            self.assertEqual(cuotas[p], 5)

    def test_redistribucion_en_cascada(self):
        grupo = (crear_imagenes(2, "p1") +
                 crear_imagenes(2, "p2") +
                 crear_imagenes(50, "p3"))
        seleccion, cuotas = balancear_por_proyecto(grupo, 30)
        self.assertEqual(cuotas["p1"], 2)
        self.assertEqual(cuotas["p2"], 2)
        self.assertEqual(cuotas["p3"], 26)
        self.assertEqual(len(seleccion), 30)

    def test_cuota_cero(self):
        grupo = crear_imagenes(10, "p1")
        seleccion, cuotas = balancear_por_proyecto(grupo, 0)
        self.assertEqual(len(seleccion), 0)

    def test_no_selecciona_mas_de_lo_disponible(self):
        grupo = crear_imagenes(5, "p1")
        seleccion, cuotas = balancear_por_proyecto(grupo, 100)
        self.assertEqual(len(seleccion), 5)


class TestCalcularCuotasGrupos(unittest.TestCase):
    """Tests para el cálculo de cuotas entre los 4 grupos de tamaño."""

    def test_objetivo_divisible_por_4(self):
        grupos = [list(range(100))] * 4
        cuotas = calcular_cuotas_grupos(grupos, 100)
        self.assertEqual(cuotas, [25, 25, 25, 25])

    def test_objetivo_no_divisible(self):
        grupos = [list(range(100))] * 4
        cuotas = calcular_cuotas_grupos(grupos, 50)
        self.assertEqual(sum(cuotas), 50)
        self.assertEqual(cuotas, [13, 13, 12, 12])

    def test_grupo_pequeno_redistribuye(self):
        grupos = [list(range(5)), list(range(100)), list(range(100)), list(range(100))]
        cuotas = calcular_cuotas_grupos(grupos, 100)
        self.assertEqual(cuotas[0], 5)
        self.assertEqual(sum(cuotas), 100)
        for i in range(1, 4):
            self.assertGreater(cuotas[i], 25)

    def test_todos_grupos_pequenos(self):
        grupos = [list(range(3)), list(range(4)), list(range(2)), list(range(5))]
        cuotas = calcular_cuotas_grupos(grupos, 100)
        self.assertEqual(cuotas, [3, 4, 2, 5])

    def test_objetivo_1(self):
        grupos = [list(range(10))] * 4
        cuotas = calcular_cuotas_grupos(grupos, 1)
        self.assertEqual(sum(cuotas), 1)

    def test_objetivo_0(self):
        grupos = [list(range(10))] * 4
        cuotas = calcular_cuotas_grupos(grupos, 0)
        self.assertEqual(sum(cuotas), 0)

    def test_redistribucion_cascada(self):
        grupos = [list(range(2)), list(range(3)), list(range(4)), list(range(100))]
        cuotas = calcular_cuotas_grupos(grupos, 40)
        self.assertEqual(cuotas[0], 2)
        self.assertEqual(cuotas[1], 3)
        self.assertEqual(cuotas[2], 4)
        self.assertEqual(cuotas[3], 31)
        self.assertEqual(sum(cuotas), 40)


class TestClasificarYBalancearClase(unittest.TestCase):
    """Tests para la función integrada clasificar_y_balancear_clase."""

    def test_proporcional_basico(self):
        imagenes = crear_imagenes(200)
        seleccionados, cuotas = clasificar_y_balancear_clase(imagenes, 50, "proporcional")
        self.assertEqual(len(seleccionados), 4)
        total = sum(len(g) for g in seleccionados)
        self.assertEqual(total, 50)

    def test_rango_basico(self):
        imagenes = crear_imagenes(200)
        seleccionados, cuotas = clasificar_y_balancear_clase(imagenes, 50, "rango")
        self.assertEqual(len(seleccionados), 4)
        total = sum(len(g) for g in seleccionados)
        self.assertEqual(total, 50)

    def test_multiproyecto(self):
        imagenes = crear_imagenes_multiproyecto(50, ["p1", "p2", "p3"])
        seleccionados, cuotas_por_grupo = clasificar_y_balancear_clase(imagenes, 50, "proporcional")
        total = sum(len(g) for g in seleccionados)
        self.assertEqual(total, 50)
        for cuotas_proy in cuotas_por_grupo:
            if cuotas_proy:
                self.assertGreater(len(cuotas_proy), 0)


class TestCalcularObjetivo(unittest.TestCase):
    """Tests para el cálculo del objetivo balanceado."""

    def test_limitado_por_clase_pequena(self):
        datos = {"R-1": list(range(2000)), "P-1": list(range(60)), "S-13": list(range(500))}
        self.assertEqual(calcular_objetivo(datos, 1000), 60)

    def test_limitado_por_maxima(self):
        datos = {"R-1": list(range(2000)), "P-1": list(range(1500))}
        self.assertEqual(calcular_objetivo(datos, 1000), 1000)

    def test_sin_datos(self):
        self.assertEqual(calcular_objetivo({}, 1000), 0)

    def test_independiente_cada_clase_su_maximo(self):
        """Con balanceo_independiente=True cada clase usa sus propias imágenes."""
        datos = {"R-1": list(range(2000)), "P-1": list(range(60)), "S-13": list(range(500))}
        resultado = calcular_objetivo(datos, 1000, balanceo_independiente=True)
        self.assertEqual(resultado["R-1"], 1000)   # limitado por cantidad_maxima
        self.assertEqual(resultado["P-1"], 60)      # usa todas las que tiene
        self.assertEqual(resultado["S-13"], 500)    # usa todas las que tiene

    def test_independiente_todas_bajo_maxima(self):
        datos = {"A": list(range(100)), "B": list(range(200))}
        resultado = calcular_objetivo(datos, 1000, balanceo_independiente=True)
        self.assertEqual(resultado["A"], 100)
        self.assertEqual(resultado["B"], 200)

    def test_independiente_todas_sobre_maxima(self):
        datos = {"A": list(range(5000)), "B": list(range(3000))}
        resultado = calcular_objetivo(datos, 1000, balanceo_independiente=True)
        self.assertEqual(resultado["A"], 1000)
        self.assertEqual(resultado["B"], 1000)

    def test_independiente_sin_datos(self):
        self.assertEqual(calcular_objetivo({}, 1000, balanceo_independiente=True), {})

    def test_independiente_no_limita_a_clase_pequena(self):
        """La clase grande NO se limita por la pequeña."""
        datos = {"grande": list(range(800)), "pequena": list(range(50))}
        # Modo estricto: ambas a 50
        estricto = calcular_objetivo(datos, 1000, balanceo_independiente=False)
        self.assertEqual(estricto, 50)
        # Modo independiente: cada una su propio total
        independiente = calcular_objetivo(datos, 1000, balanceo_independiente=True)
        self.assertEqual(independiente["grande"], 800)
        self.assertEqual(independiente["pequena"], 50)


class TestCalcularAugmentation(unittest.TestCase):
    """Tests para el cálculo de data augmentation adaptativo."""

    def _resumen(self, clase, total_balanceado, counts=(13, 13, 12, 12)):
        return [{
            'clase': clase,
            'total': 1000,
            'total_balanceado': total_balanceado,
            'grupos': {
                'muy_pequeño': {'count': counts[0], 'rango': (1, 10)},
                'pequeño': {'count': counts[1], 'rango': (11, 20)},
                'medio': {'count': counts[2], 'rango': (21, 30)},
                'grande': {'count': counts[3], 'rango': (31, 40)},
            },
            'grupo_minimo': 'medio',
        }]

    def test_clase_pequena_recibe_mas_augmentation(self):
        """P-1c (50 imgs) necesita x10 para llegar a 500."""
        result = calcular_augmentation(self._resumen('P-1c', 50), 500, 20)
        self.assertEqual(result[0]['factor'], 10)
        self.assertEqual(result[0]['imagenes_objetivo'], 500)

    def test_clase_grande_recibe_poco(self):
        """R-301 (1000 imgs) solo necesita x1 (ya supera el objetivo de 500)."""
        resumen = self._resumen('R-301', 1000, (250, 250, 250, 250))
        result = calcular_augmentation(resumen, 500, 20)
        self.assertEqual(result[0]['factor'], 1)
        self.assertEqual(result[0]['augmentaciones_necesarias'], 0)

    def test_factor_max_limita(self):
        """Con 10 imgs y objetivo 500, necesitaría x50, pero el max es 20."""
        resumen = self._resumen('tiny', 10, (3, 3, 2, 2))
        result = calcular_augmentation(resumen, 500, 20)
        self.assertEqual(result[0]['factor'], 20)
        self.assertEqual(result[0]['imagenes_objetivo'], 200)

    def test_clase_justo_en_objetivo(self):
        """500 imgs con objetivo 500 -> factor 1."""
        resumen = self._resumen('exact', 500, (125, 125, 125, 125))
        result = calcular_augmentation(resumen, 500, 20)
        self.assertEqual(result[0]['factor'], 1)

    def test_augmentation_por_grupo(self):
        """Cada grupo recibe el mismo factor que la clase."""
        result = calcular_augmentation(self._resumen('P-1c', 50), 500, 20)
        factor = result[0]['factor']  # 10
        for datos in result[0]['por_grupo'].values():
            self.assertEqual(datos['objetivo'], datos['originales'] * factor)

    def test_multiple_clases_factores_distintos(self):
        """Dos clases con tamaños distintos reciben factores distintos."""
        resumen = (
            self._resumen('pequeña', 50) +
            self._resumen('grande', 1000, (250, 250, 250, 250))
        )
        result = calcular_augmentation(resumen, 500, 20)
        self.assertGreater(result[0]['factor'], result[1]['factor'])


class TestCalcularClassWeights(unittest.TestCase):
    """Tests para el cálculo de class weights."""

    def test_clases_iguales_peso_1(self):
        """Clases con mismas imágenes -> peso ~1 para todas."""
        aug_info = [
            {'clase': 'A', 'imagenes_objetivo': 500},
            {'clase': 'B', 'imagenes_objetivo': 500},
        ]
        weights = calcular_class_weights(aug_info)
        self.assertAlmostEqual(weights['A'], 1.0)
        self.assertAlmostEqual(weights['B'], 1.0)

    def test_clase_pequena_mayor_peso(self):
        aug_info = [
            {'clase': 'grande', 'imagenes_objetivo': 1000},
            {'clase': 'pequeña', 'imagenes_objetivo': 100},
        ]
        weights = calcular_class_weights(aug_info)
        self.assertGreater(weights['pequeña'], weights['grande'])

    def test_pesos_proporcionales(self):
        """El ratio de pesos es inverso al ratio de imágenes."""
        aug_info = [
            {'clase': 'A', 'imagenes_objetivo': 1000},
            {'clase': 'B', 'imagenes_objetivo': 100},
        ]
        weights = calcular_class_weights(aug_info)
        ratio = weights['B'] / weights['A']
        self.assertAlmostEqual(ratio, 10.0)

    def test_loss_compensada(self):
        """weight * n_muestras es igual para todas las clases."""
        aug_info = [
            {'clase': 'A', 'imagenes_objetivo': 800},
            {'clase': 'B', 'imagenes_objetivo': 200},
            {'clase': 'C', 'imagenes_objetivo': 500},
        ]
        weights = calcular_class_weights(aug_info)
        productos = [weights[a['clase']] * a['imagenes_objetivo'] for a in aug_info]
        for p in productos:
            self.assertAlmostEqual(p, productos[0])

    def test_sin_datos(self):
        self.assertEqual(calcular_class_weights([]), {})


class TestNombresGruposUnificados(unittest.TestCase):
    """Tests para verificar que la nomenclatura es consistente."""

    def test_nombres_grupos_definidos(self):
        self.assertEqual(len(NOMBRES_GRUPOS), 4)
        self.assertEqual(NOMBRES_GRUPOS, ["muy_pequeño", "pequeño", "medio", "grande"])

    def test_nombres_en_resumen(self):
        """Los nombres de grupo en el resumen usan la nomenclatura unificada."""
        imagenes = crear_imagenes(200)
        seleccionados, _ = clasificar_y_balancear_clase(imagenes, 50, "proporcional")

        # Simular resumen como lo hace procesar_clases
        grupos_resumen = {}
        for i, nombre in enumerate(NOMBRES_GRUPOS):
            grupo = seleccionados[i]
            grupos_resumen[nombre] = {
                'count': len(grupo),
                'rango': (grupo[0]['medida'], grupo[-1]['medida']) if grupo else None,
            }

        for clave in grupos_resumen:
            self.assertIn(clave, ["muy_pequeño", "pequeño", "medio", "grande"])


class TestFlujoCompleto(unittest.TestCase):
    """Tests de integración del flujo completo (sin BD)."""

    def test_flujo_proporcional_basico(self):
        imagenes = crear_imagenes_multiproyecto(50, ["p1", "p2", "p3"])
        self.assertEqual(len(imagenes), 150)

        seleccionados, _ = clasificar_y_balancear_clase(imagenes, 50, "proporcional")
        total = sum(len(g) for g in seleccionados)
        self.assertEqual(total, 50)

    def test_flujo_con_proyecto_dominante(self):
        imgs_p1 = [crear_imagen(i, 50, 10 + i, "p1", 10 + i) for i in range(100)]
        imgs_p2 = [crear_imagen(100 + i, 50, 10 + i, "p2", 10 + i) for i in range(5)]
        imagenes = sorted(imgs_p1 + imgs_p2, key=lambda x: x['medida'])

        seleccionados, _ = clasificar_y_balancear_clase(imagenes, 50, "proporcional")
        total = sum(len(g) for g in seleccionados)
        self.assertLessEqual(total, 50)

    def test_consistencia_rango_vs_proporcional(self):
        imagenes = crear_imagenes(100)
        total_prop = sum(len(g) for g in clasificar_proporcional(imagenes))
        total_rango = sum(len(g) for g in clasificar_por_rango(imagenes))
        self.assertEqual(total_prop, 100)
        self.assertEqual(total_rango, 100)


class TestConsistenciaResultados(unittest.TestCase):
    """Tests que verifican la consistencia de los resultados."""

    def test_resultado_nunca_excede_objetivo(self):
        for objetivo in [10, 25, 50, 100]:
            imagenes = crear_imagenes_multiproyecto(50, ["p1", "p2"])
            seleccionados, _ = clasificar_y_balancear_clase(imagenes, objetivo, "proporcional")
            total = sum(len(g) for g in seleccionados)
            self.assertLessEqual(total, objetivo)

    def test_resultado_maximiza_seleccion(self):
        imagenes = crear_imagenes(200)
        seleccionados, _ = clasificar_y_balancear_clase(imagenes, 50, "proporcional")
        total = sum(len(g) for g in seleccionados)
        self.assertEqual(total, 50)

    def test_ids_unicos_en_seleccion(self):
        imagenes = crear_imagenes_multiproyecto(30, ["p1", "p2", "p3"])
        seleccionados, _ = clasificar_y_balancear_clase(imagenes, 50, "proporcional")

        todos_ids = []
        for grupo in seleccionados:
            todos_ids.extend(img['id'] for img in grupo)
        self.assertEqual(len(todos_ids), len(set(todos_ids)))


class TestCasosLimite(unittest.TestCase):
    """Tests de casos extremos."""

    def test_imagenes_con_medida_cero(self):
        imagenes = [crear_imagen(i, 50, 0, "p1", 0) for i in range(10)]
        imagenes.append(crear_imagen(10, 50, 100, "p1", 100))
        grupos = clasificar_por_rango(imagenes)
        total = sum(len(g) for g in grupos)
        self.assertEqual(total, 11)

    def test_medidas_negativas(self):
        imagenes = [crear_imagen(i, 50, -10 + i * 5, "p1", -10 + i * 5) for i in range(10)]
        grupos = clasificar_proporcional(imagenes)
        total = sum(len(g) for g in grupos)
        self.assertEqual(total, 10)

    def test_medidas_decimales(self):
        imagenes = [crear_imagen(i, 50, 0.5 * i, "p1", 0.5 * i) for i in range(20)]
        grupos = clasificar_proporcional(imagenes)
        total = sum(len(g) for g in grupos)
        self.assertEqual(total, 20)

    def test_muchos_proyectos_pocas_imagenes(self):
        grupo = [crear_imagen(i, 50, 10 + i, f"p{i}", 10 + i) for i in range(20)]
        seleccion, cuotas = balancear_por_proyecto(grupo, 5)
        self.assertEqual(len(seleccion), 5)

    def test_cuota_mayor_que_total(self):
        grupo = crear_imagenes(5, "p1")
        seleccion, cuotas = balancear_por_proyecto(grupo, 1000)
        self.assertEqual(len(seleccion), 5)


class TestFiltroConfiguracion(unittest.TestCase):
    """Tests para la lógica de filtrado."""

    def test_filtro_clases_excluidas(self):
        CLASES_EXCLUIDAS = ["ST_C", "ST_R", "ST_S", "ST_T"]
        clases = ["BCV", "ST_C", "P-1", "ST_R", "R-301"]
        procesadas = [c for c in clases if c not in CLASES_EXCLUIDAS]
        self.assertEqual(procesadas, ["BCV", "P-1", "R-301"])

    def test_filtro_cantidad_minima(self):
        clases = {"BCV": 837, "P-X": 30, "R-1": 1828, "S-NEW": 49}
        validas = {k: v for k, v in clases.items() if v >= 50}
        self.assertEqual(set(validas.keys()), {"BCV", "R-1"})


# ============================================================
# TESTS DE SIMULACIÓN DE ENTRENAMIENTO
# Reproducen el escenario real con datos similares a la BD
# para validar que el dataset es viable para entrenar una IA
# ============================================================

# Distribución real extraída de resultados_clases_proporcional.txt
CLASES_REALES = {
    "BCV": 837, "P-1": 241, "P-13a": 111, "P-13b": 130, "P-15a": 1075,
    "P-1a": 178, "P-1b": 96, "P-1c": 50, "P-20b": 178, "P-21a": 111,
    "P-3": 67, "P-4": 387, "P-9c": 1206, "PDP": 868, "R-1": 1828,
    "R-100": 110, "R-101": 1772, "R-2": 627, "R-301": 2263, "R-302": 72,
    "R-303": 56, "R-304": 93, "R-305": 637, "R-308": 707, "R-308c": 171,
    "R-308d": 191, "R-308e": 1482, "R-308f": 420, "R-308g": 70,
    "R-308h": 79, "R-400a": 221, "R-400b": 182, "R-401a": 521,
    "R-402": 857, "R-502": 101, "S-105a": 331, "S-11": 138, "S-13": 1608,
    "S-17a": 228, "S-19": 121, "S-200": 319, "S-300": 457, "S-348a": 101,
    "S-400": 60, "S-572": 188, "S-600": 86, "S-800": 140,
}

PROYECTOS_REALES = ["03_ibiza", "01_alcaudete", "02_fuente_albilla", "04_carreteras"]


def generar_dataset_realista(clases_dict, proyectos):
    """Genera un dataset simulado con la distribución real de la BD."""
    import random
    random.seed(42)

    datos_clases = {}
    id_global = 0
    for clase, total in clases_dict.items():
        imagenes = []
        for i in range(total):
            proyecto = proyectos[i % len(proyectos)]
            medida = random.uniform(3, 500)
            imagenes.append(crear_imagen(id_global, 50, medida, proyecto, medida))
            id_global += 1
        imagenes.sort(key=lambda x: x['medida'])
        datos_clases[clase] = imagenes
    return datos_clases


class TestSimulacionEntrenamientoEstricto(unittest.TestCase):
    """Simula el entrenamiento con balanceo ESTRICTO (limitado a clase mínima).
    Este era el comportamiento original: todas las clases a 50 imágenes."""

    def setUp(self):
        self.datos = generar_dataset_realista(CLASES_REALES, PROYECTOS_REALES)
        self.objetivo = calcular_objetivo(self.datos, 1000, balanceo_independiente=False)

    def test_objetivo_es_50(self):
        """Con P-1c=50, el objetivo queda en 50 para TODAS las clases."""
        self.assertEqual(self.objetivo, 50)

    def test_total_dataset_estricto(self):
        """47 clases x 50 = 2350 imágenes totales. Muy poco para ML."""
        total = self.objetivo * len(self.datos)
        self.assertEqual(total, 2350)

    def test_desperdicio_datos(self):
        """Calcula cuántas imágenes se desperdician con balanceo estricto."""
        total_disponible = sum(len(imgs) for imgs in self.datos.values())
        total_usado = self.objetivo * len(self.datos)
        desperdicio = 1 - (total_usado / total_disponible)
        # Se desperdicia más del 85% de los datos
        self.assertGreater(desperdicio, 0.85)

    def test_balanceo_por_clase_estricto(self):
        """Todas las clases producen exactamente el mismo número de imágenes."""
        resultados = {}
        for clase, imagenes in self.datos.items():
            seleccionados, _ = clasificar_y_balancear_clase(
                imagenes, self.objetivo, "proporcional"
            )
            resultados[clase] = sum(len(g) for g in seleccionados)

        for clase, total in resultados.items():
            self.assertEqual(total, 50, f"Clase {clase} debería tener 50, tiene {total}")

    def test_imagenes_por_grupo_insuficientes(self):
        """Con 50 imgs/clase, cada grupo de tamaño solo tiene 12-13. Poco para ML."""
        for clase, imagenes in self.datos.items():
            seleccionados, _ = clasificar_y_balancear_clase(
                imagenes, self.objetivo, "proporcional"
            )
            for i, grupo in enumerate(seleccionados):
                self.assertLessEqual(len(grupo), 13,
                    f"Clase {clase}, grupo {NOMBRES_GRUPOS[i]}: máx 13 imgs")


class TestSimulacionEntrenamientoIndependiente(unittest.TestCase):
    """Simula el entrenamiento con balanceo INDEPENDIENTE.
    Cada clase usa todas sus imágenes (hasta cantidad_maxima=2000)."""

    def setUp(self):
        self.datos = generar_dataset_realista(CLASES_REALES, PROYECTOS_REALES)
        self.objetivos = calcular_objetivo(self.datos, 2000, balanceo_independiente=True)

    def test_clase_grande_usa_mas_datos(self):
        """R-301 (2263 imgs) debería usar 2000 en vez de solo 50."""
        self.assertEqual(self.objetivos["R-301"], 2000)

    def test_clase_pequena_usa_todo(self):
        """P-1c (50 imgs) usa sus 50 pero no limita a las demás."""
        self.assertEqual(self.objetivos["P-1c"], 50)

    def test_total_dataset_independiente(self):
        """El dataset independiente usa MUCHAS más imágenes que el estricto."""
        total_independiente = sum(self.objetivos.values())
        total_estricto = 50 * len(self.datos)  # 2350
        # Al menos 5x más datos
        self.assertGreater(total_independiente, total_estricto * 5)

    def test_balanceo_real_por_clase(self):
        """Cada clase produce su objetivo independiente."""
        for clase, imagenes in self.datos.items():
            objetivo = self.objetivos[clase]
            seleccionados, _ = clasificar_y_balancear_clase(
                imagenes, objetivo, "proporcional"
            )
            total = sum(len(g) for g in seleccionados)
            self.assertEqual(total, objetivo,
                f"Clase {clase}: esperado {objetivo}, obtenido {total}")

    def test_diversidad_tamanios_preservada(self):
        """Con más imágenes, cada grupo de tamaño tiene suficiente representación."""
        for clase, imagenes in self.datos.items():
            objetivo = self.objetivos[clase]
            seleccionados, _ = clasificar_y_balancear_clase(
                imagenes, objetivo, "proporcional"
            )
            for i, grupo in enumerate(seleccionados):
                # Con objetivo independiente, incluso el grupo más pequeño tiene datos
                self.assertGreater(len(grupo), 0,
                    f"Clase {clase}, grupo {NOMBRES_GRUPOS[i]}: vacío")

    def test_distribucion_proyectos_en_clase_grande(self):
        """En clases con muchos datos, los 4 proyectos están representados."""
        imagenes_r301 = self.datos["R-301"]
        objetivo = self.objetivos["R-301"]
        seleccionados, cuotas_por_grupo = clasificar_y_balancear_clase(
            imagenes_r301, objetivo, "proporcional"
        )
        for i, cuotas_proy in enumerate(cuotas_por_grupo):
            # Los 4 proyectos deben aparecer en cada grupo
            self.assertEqual(len(cuotas_proy), 4,
                f"Grupo {NOMBRES_GRUPOS[i]}: no todos los proyectos representados")


class TestSimulacionClassWeights(unittest.TestCase):
    """Simula el cálculo de class weights con augmentation adaptativo."""

    def setUp(self):
        self.datos = generar_dataset_realista(CLASES_REALES, PROYECTOS_REALES)
        self.objetivos = calcular_objetivo(self.datos, 2000, balanceo_independiente=True)
        # Simular resumen y augmentation
        self.resumen = []
        for clase, imagenes in self.datos.items():
            objetivo = self.objetivos[clase]
            seleccionados, _ = clasificar_y_balancear_clase(imagenes, objetivo, "proporcional")
            total_bal = sum(len(g) for g in seleccionados)
            self.resumen.append({
                'clase': clase, 'total': len(imagenes), 'total_balanceado': total_bal,
                'grupos': {NOMBRES_GRUPOS[i]: {'count': len(g), 'rango': None} for i, g in enumerate(seleccionados)},
                'grupo_minimo': 'muy_pequeño',
            })
        self.aug_info = calcular_augmentation(self.resumen, 500, 20)
        self.weights = calcular_class_weights(self.aug_info)

    def test_clase_pequena_tiene_mayor_peso(self):
        """P-1c debe tener mayor peso que R-301 tras augmentation."""
        self.assertGreater(self.weights["P-1c"], self.weights["R-301"])

    def test_ningun_peso_es_cero(self):
        for clase, peso in self.weights.items():
            self.assertGreater(peso, 0, f"Clase {clase} tiene peso 0")

    def test_weighted_loss_compensa_desbalance(self):
        """loss_efectiva = weight * n_muestras debería ser igual para todas."""
        muestras = {a['clase']: a['imagenes_objetivo'] for a in self.aug_info}
        total = sum(muestras.values())
        n_clases = len(muestras)
        esperado = total / n_clases

        for clase in muestras:
            loss_efectiva = self.weights[clase] * muestras[clase]
            self.assertAlmostEqual(loss_efectiva, esperado, places=1,
                msg=f"Clase {clase}: loss efectiva no compensada")


class TestSimulacionTrainValTest(unittest.TestCase):
    """Simula la separación train/val/test y valida que cada split
    tiene suficientes datos para ser útil en entrenamiento."""

    TRAIN_RATIO = 0.70
    VAL_RATIO = 0.15
    TEST_RATIO = 0.15

    def setUp(self):
        self.datos = generar_dataset_realista(CLASES_REALES, PROYECTOS_REALES)
        self.objetivos = calcular_objetivo(self.datos, 2000, balanceo_independiente=True)

    def _split_clase(self, n_imagenes):
        """Calcula cuántas imágenes van a cada split."""
        n_train = int(n_imagenes * self.TRAIN_RATIO)
        n_val = int(n_imagenes * self.VAL_RATIO)
        n_test = n_imagenes - n_train - n_val
        return n_train, n_val, n_test

    def test_split_no_pierde_datos(self):
        """train + val + test = total para cada clase."""
        for clase, objetivo in self.objetivos.items():
            n_train, n_val, n_test = self._split_clase(objetivo)
            self.assertEqual(n_train + n_val + n_test, objetivo,
                f"Clase {clase}: split pierde datos")

    def test_train_siempre_mayor(self):
        """Train siempre tiene más datos que val y test."""
        for clase, objetivo in self.objetivos.items():
            n_train, n_val, n_test = self._split_clase(objetivo)
            self.assertGreater(n_train, n_val, f"Clase {clase}")
            self.assertGreater(n_train, n_test, f"Clase {clase}")

    def test_val_test_no_vacios_modo_independiente(self):
        """Con modo independiente, todas las clases tienen val y test con datos."""
        for clase, objetivo in self.objetivos.items():
            n_train, n_val, n_test = self._split_clase(objetivo)
            self.assertGreater(n_val, 0, f"Clase {clase}: val vacío")
            self.assertGreater(n_test, 0, f"Clase {clase}: test vacío")

    def test_clase_pequena_split_viable(self):
        """Incluso P-1c (50 imgs) tiene splits mínimos viables."""
        n_train, n_val, n_test = self._split_clase(50)
        self.assertEqual(n_train, 35)  # 70% de 50
        self.assertEqual(n_val, 7)     # 15% de 50
        self.assertEqual(n_test, 8)    # el resto
        self.assertGreaterEqual(n_val, 5, "Val demasiado pequeño para evaluar")

    def test_total_train_suficiente(self):
        """El total de imágenes de train es suficiente para entrenar un modelo."""
        total_train = 0
        for clase, objetivo in self.objetivos.items():
            n_train, _, _ = self._split_clase(objetivo)
            total_train += n_train
        # Mínimo razonable: >5000 imágenes de train
        self.assertGreater(total_train, 5000,
            f"Solo {total_train} imgs de train, insuficiente para ML")


class TestSimulacionAugmentationEntrenamiento(unittest.TestCase):
    """Simula el efecto de augmentation ADAPTATIVO sobre el dataset final."""

    def setUp(self):
        self.datos = generar_dataset_realista(CLASES_REALES, PROYECTOS_REALES)
        self.objetivos = calcular_objetivo(self.datos, 2000, balanceo_independiente=True)
        self.objetivo_aug = 500
        self.factor_max = 20
        # Construir resumen real
        self.resumen = []
        for clase, imagenes in self.datos.items():
            objetivo = self.objetivos[clase]
            seleccionados, _ = clasificar_y_balancear_clase(imagenes, objetivo, "proporcional")
            total_bal = sum(len(g) for g in seleccionados)
            self.resumen.append({
                'clase': clase, 'total': len(imagenes), 'total_balanceado': total_bal,
                'grupos': {NOMBRES_GRUPOS[i]: {'count': len(g), 'rango': None} for i, g in enumerate(seleccionados)},
                'grupo_minimo': 'muy_pequeño',
            })
        self.aug_info = calcular_augmentation(self.resumen, self.objetivo_aug, self.factor_max)
        self.aug_dict = {a['clase']: a for a in self.aug_info}

    def test_clase_pequena_recibe_mas_augmentation(self):
        """P-1c (50 imgs) recibe factor x10, R-301 (2000 imgs) recibe x1."""
        self.assertGreater(self.aug_dict["P-1c"]['factor'], self.aug_dict["R-301"]['factor'])

    def test_clase_pequena_llega_al_objetivo(self):
        """P-1c con augmentation adaptativo llega a ~500 imágenes."""
        self.assertGreaterEqual(self.aug_dict["P-1c"]['imagenes_objetivo'], self.objetivo_aug)

    def test_clase_grande_no_sobre_augmenta(self):
        """R-301 ya tiene suficientes imgs, factor debe ser 1."""
        self.assertEqual(self.aug_dict["R-301"]['factor'], 1)
        self.assertEqual(self.aug_dict["R-301"]['augmentaciones_necesarias'], 0)

    def test_total_dataset_con_augmentation(self):
        """Total final debe superar 25.000 imágenes (adaptativo no sobre-augmenta)."""
        total = sum(a['imagenes_objetivo'] for a in self.aug_info)
        self.assertGreater(total, 25000, f"Dataset final: {total} imgs")

    def test_todas_clases_minimo_viable(self):
        """TODAS las 47 clases llegan al menos a 200 imágenes tras augmentation."""
        for aug in self.aug_info:
            self.assertGreaterEqual(aug['imagenes_objetivo'], 200,
                f"Clase {aug['clase']}: solo {aug['imagenes_objetivo']} imgs tras aug")

    def test_ninguna_clase_con_augmentation_excesivo(self):
        """Ninguna clase supera el factor máximo."""
        for aug in self.aug_info:
            self.assertLessEqual(aug['factor'], self.factor_max,
                f"Clase {aug['clase']}: factor {aug['factor']} > max {self.factor_max}")


class TestBatchUpdatePreparacion(unittest.TestCase):
    """Tests para validar la preparación de IDs en batch para actualizar BD.

    La función actualizar_tamanio_bd_batch recibe una lista de IDs y un grupo.
    Estos tests verifican que la extracción de IDs desde los grupos seleccionados
    produce los lotes correctos para el UPDATE batch.
    """

    def test_extraccion_ids_por_grupo(self):
        """Los IDs se extraen correctamente de cada grupo seleccionado."""
        imagenes = crear_imagenes_multiproyecto(20, ["p1", "p2"])
        seleccionados, _ = clasificar_y_balancear_clase(imagenes, 40, "proporcional")

        for i, nombre in enumerate(NOMBRES_GRUPOS):
            ids = [img['id'] for img in seleccionados[i]]
            # Cada ID es único dentro del grupo
            self.assertEqual(len(ids), len(set(ids)),
                f"Grupo {nombre}: IDs duplicados en el batch")

    def test_ids_no_se_repiten_entre_grupos(self):
        """Ningún ID aparece en más de un grupo (evita UPDATEs contradictorios)."""
        imagenes = crear_imagenes_multiproyecto(30, ["p1", "p2", "p3"])
        seleccionados, _ = clasificar_y_balancear_clase(imagenes, 60, "proporcional")

        todos_los_ids = []
        for grupo in seleccionados:
            todos_los_ids.extend(img['id'] for img in grupo)
        self.assertEqual(len(todos_los_ids), len(set(todos_los_ids)),
            "Hay IDs repetidos entre grupos distintos")

    def test_batch_vacio_no_genera_ids(self):
        """Un grupo vacío produce una lista de IDs vacía."""
        # Crear un caso con tan pocas imágenes que algún grupo quede vacío
        imagenes = [crear_imagen(0, 50, 100, "p1", 100)]
        seleccionados, _ = clasificar_y_balancear_clase(imagenes, 1, "proporcional")

        grupos_vacios = [g for g in seleccionados if len(g) == 0]
        for grupo in grupos_vacios:
            ids = [img['id'] for img in grupo]
            self.assertEqual(len(ids), 0, "Grupo vacío generó IDs")

    def test_total_ids_coincide_con_seleccionados(self):
        """El total de IDs extraídos coincide con el total de imágenes seleccionadas."""
        imagenes = crear_imagenes_multiproyecto(50, PROYECTOS_REALES)
        objetivo = 100
        seleccionados, _ = clasificar_y_balancear_clase(imagenes, objetivo, "proporcional")

        total_ids = sum(len([img['id'] for img in grupo]) for grupo in seleccionados)
        total_imgs = sum(len(grupo) for grupo in seleccionados)
        self.assertEqual(total_ids, total_imgs)

    def test_batch_con_dataset_realista(self):
        """Simula la preparación de batches con distribución real."""
        datos = generar_dataset_realista({"R-301": 2263, "P-1c": 50}, PROYECTOS_REALES)
        objetivos = calcular_objetivo(datos, 2000, balanceo_independiente=True)

        for clase, imagenes in datos.items():
            seleccionados, _ = clasificar_y_balancear_clase(
                imagenes, objetivos[clase], "proporcional")

            ids_totales = []
            for i, nombre in enumerate(NOMBRES_GRUPOS):
                ids = [img['id'] for img in seleccionados[i]]
                ids_totales.extend(ids)
                # Cada batch tiene IDs válidos (no None, no negativos)
                for id_img in ids:
                    self.assertIsNotNone(id_img, f"Clase {clase}, grupo {nombre}: ID None")
                    self.assertGreaterEqual(id_img, 0, f"Clase {clase}, grupo {nombre}: ID negativo")

            # Sin duplicados entre todos los grupos
            self.assertEqual(len(ids_totales), len(set(ids_totales)),
                f"Clase {clase}: IDs duplicados entre grupos")


class TestComparativaEstrictoVsIndependiente(unittest.TestCase):
    """Compara directamente ambos modos para demostrar el impacto
    de usar balanceo independiente en el entrenamiento."""

    def setUp(self):
        self.datos = generar_dataset_realista(CLASES_REALES, PROYECTOS_REALES)
        self.obj_estricto = calcular_objetivo(
            self.datos, 2000, balanceo_independiente=False)
        self.obj_independiente = calcular_objetivo(
            self.datos, 2000, balanceo_independiente=True)

    def test_independiente_siempre_mas_datos(self):
        """El modo independiente SIEMPRE genera >= datos que el estricto."""
        total_estricto = self.obj_estricto * len(self.datos)
        total_independiente = sum(self.obj_independiente.values())
        self.assertGreaterEqual(total_independiente, total_estricto)

    def test_ratio_mejora(self):
        """Calcula cuántas veces más datos produce el modo independiente."""
        total_estricto = self.obj_estricto * len(self.datos)
        total_independiente = sum(self.obj_independiente.values())
        ratio = total_independiente / total_estricto
        # Con los datos reales, el modo independiente da ~8x más datos
        self.assertGreater(ratio, 5, f"Solo {ratio:.1f}x más datos, esperado >5x")

    def test_clase_grande_aprovechada(self):
        """Las clases grandes (>1000) usan muchos más datos en modo independiente."""
        clases_grandes = {c: n for c, n in CLASES_REALES.items() if n > 1000}
        for clase in clases_grandes:
            ratio = self.obj_independiente[clase] / self.obj_estricto
            self.assertGreaterEqual(ratio, 10,
                f"Clase {clase}: solo {ratio:.0f}x más en independiente")

    def test_clase_pequena_igual_en_ambos(self):
        """P-1c tiene el mismo resultado en ambos modos (es el cuello de botella)."""
        self.assertEqual(self.obj_independiente["P-1c"], self.obj_estricto)

    def test_varianza_reducida_con_independiente(self):
        """En modo estricto la varianza de tamaño de dataset es 0 (todas iguales).
        En independiente hay varianza, pero más datos compensan."""
        # Estricto: 0 varianza pero pocos datos
        # Independiente: hay varianza pero con class weights se compensa
        valores = list(self.obj_independiente.values())
        media = sum(valores) / len(valores)
        # La media por clase en independiente es muy superior al estricto
        self.assertGreater(media, self.obj_estricto * 3)


if __name__ == '__main__':
    unittest.main()
