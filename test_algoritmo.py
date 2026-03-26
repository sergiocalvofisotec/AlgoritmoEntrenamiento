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


class TestCalcularAugmentation(unittest.TestCase):
    """Tests para el cálculo de data augmentation."""

    def test_factor_5(self):
        resumen = [{
            'clase': 'R-1',
            'total': 1000,
            'total_balanceado': 50,
            'grupos': {
                'muy_pequeño': {'count': 13, 'rango': (1, 10)},
                'pequeño': {'count': 13, 'rango': (11, 20)},
                'medio': {'count': 12, 'rango': (21, 30)},
                'grande': {'count': 12, 'rango': (31, 40)},
            },
            'grupo_minimo': 'medio',
        }]
        result = calcular_augmentation(resumen, 5)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['imagenes_originales'], 50)
        self.assertEqual(result[0]['imagenes_objetivo'], 250)
        self.assertEqual(result[0]['augmentaciones_necesarias'], 200)

    def test_factor_1_sin_augmentation(self):
        resumen = [{
            'clase': 'P-1',
            'total': 100,
            'total_balanceado': 50,
            'grupos': {
                'muy_pequeño': {'count': 13, 'rango': (1, 10)},
                'pequeño': {'count': 13, 'rango': (11, 20)},
                'medio': {'count': 12, 'rango': (21, 30)},
                'grande': {'count': 12, 'rango': (31, 40)},
            },
            'grupo_minimo': 'medio',
        }]
        result = calcular_augmentation(resumen, 1)
        self.assertEqual(result[0]['augmentaciones_necesarias'], 0)

    def test_augmentation_por_grupo(self):
        resumen = [{
            'clase': 'S-13',
            'total': 500,
            'total_balanceado': 40,
            'grupos': {
                'muy_pequeño': {'count': 10, 'rango': (1, 10)},
                'pequeño': {'count': 10, 'rango': (11, 20)},
                'medio': {'count': 10, 'rango': (21, 30)},
                'grande': {'count': 10, 'rango': (31, 40)},
            },
            'grupo_minimo': 'muy_pequeño',
        }]
        result = calcular_augmentation(resumen, 3)
        for nombre_grupo, datos in result[0]['por_grupo'].items():
            self.assertEqual(datos['originales'], 10)
            self.assertEqual(datos['objetivo'], 30)
            self.assertEqual(datos['a_generar'], 20)


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


if __name__ == '__main__':
    unittest.main()
