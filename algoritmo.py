#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Algoritmo de balanceo de datasets para entrenamiento de modelos ML.

Clasifica y balancea imágenes de señales verticales por tamaño y proyecto,
generando un dataset equilibrado para entrenamiento.
"""

import logging
from fisotec_basedatos import FisotecBaseDatos

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURACIÓN
# ============================================================
CONFIG = {
    # Tipo de clasificación:
    #   "rango"        -> Divide por rangos iguales (algoritmo 1)
    #   "proporcional" -> Divide por cantidad proporcional de imágenes (algoritmo 2)
    "tipo_clasificacion": "proporcional",

    # Criterio de tamaño:
    #   "altura"   -> Clasifica por la altura de la imagen
    #   "diagonal" -> Clasifica por la diagonal de la imagen
    "criterio_tamanio": "altura",

    # Proyectos a incluir. Lista vacía = todos los proyectos
    "proyectos": ["03_ibiza", "01_alcaudete", "02_fuente_albilla", "04_carreteras"],

    # Clases a excluir del algoritmo
    "clases_excluidas": ["ST_C", "ST_R", "ST_S", "ST_T"],

    # Cantidad mínima y máxima de imágenes por clase
    "cantidad_minima": 50,
    "cantidad_maxima": 1000,

    # Tamaño máximo de imagen (según criterio elegido). None = sin límite
    "tamanio_maximo": 500,

    # Factor de data augmentation recomendado por grupo de tamaño
    # (multiplicador sobre las imágenes seleccionadas)
    "augmentation_factor": 5,
}

# Nombres unificados para los 4 grupos de tamaño
NOMBRES_GRUPOS = ["muy_pequeño", "pequeño", "medio", "grande"]


# ============================================================
# FUNCIONES DE CLASIFICACIÓN (lógica pura, sin BD)
# ============================================================

def clasificar_por_rango(imagenes):
    """Clasifica imágenes en 4 grupos por rangos iguales de tamaño."""
    medidas = [img['medida'] for img in imagenes]
    min_medida = min(medidas)
    max_medida = max(medidas)
    rango = max_medida - min_medida
    cuarto = rango / 4

    grupos = [[] for _ in range(4)]
    for imagen in imagenes:
        m = imagen['medida']
        if m < min_medida + cuarto:
            grupos[0].append(imagen)
        elif m < min_medida + 2 * cuarto:
            grupos[1].append(imagen)
        elif m < min_medida + 3 * cuarto:
            grupos[2].append(imagen)
        else:
            grupos[3].append(imagen)

    return grupos


def clasificar_proporcional(imagenes):
    """Clasifica imágenes en 4 grupos con cantidad proporcional."""
    total = len(imagenes)
    grupos = [[] for _ in range(4)]
    for i, imagen in enumerate(imagenes):
        if i < total / 4:
            grupos[0].append(imagen)
        elif i < total / 2:
            grupos[1].append(imagen)
        elif i < total * 3 / 4:
            grupos[2].append(imagen)
        else:
            grupos[3].append(imagen)

    return grupos


def calcular_cuotas_grupos(grupos_lista, objetivo_por_clase):
    """Calcula las cuotas de cada grupo redistribuyendo excedentes."""
    cuota_base = objetivo_por_clase // 4
    sobrante = objetivo_por_clase % 4

    cuotas = [cuota_base] * 4
    for i in range(sobrante):
        cuotas[i] += 1

    excedente = 0
    grupos_con_espacio = []
    for i, grupo in enumerate(grupos_lista):
        if len(grupo) <= cuotas[i]:
            excedente += cuotas[i] - len(grupo)
            cuotas[i] = len(grupo)
        else:
            grupos_con_espacio.append(i)

    while excedente > 0 and grupos_con_espacio:
        reparto = excedente // len(grupos_con_espacio)
        resto = excedente % len(grupos_con_espacio)
        excedente = 0
        nuevos_con_espacio = []
        for idx, i in enumerate(grupos_con_espacio):
            extra = reparto + (1 if idx < resto else 0)
            cuotas[i] += extra
            if cuotas[i] > len(grupos_lista[i]):
                excedente += cuotas[i] - len(grupos_lista[i])
                cuotas[i] = len(grupos_lista[i])
            else:
                nuevos_con_espacio.append(i)
        grupos_con_espacio = nuevos_con_espacio

    return cuotas


def balancear_por_proyecto(grupo, cuota_grupo):
    """Balancea las imágenes de un grupo de tamaño entre proyectos."""
    por_proyecto = {}
    for img in grupo:
        proy = img['proyecto']
        if proy not in por_proyecto:
            por_proyecto[proy] = []
        por_proyecto[proy].append(img)

    num_proyectos = len(por_proyecto)
    if num_proyectos == 0:
        return [], {}

    cuota_proy = cuota_grupo // num_proyectos
    sobrante_proy = cuota_grupo % num_proyectos

    cuotas_proy = {}
    excedente_proy = 0
    proyectos_con_espacio = []
    for idx_p, (proy, imgs) in enumerate(por_proyecto.items()):
        mi_cuota = cuota_proy + (1 if idx_p < sobrante_proy else 0)
        if len(imgs) <= mi_cuota:
            cuotas_proy[proy] = len(imgs)
            excedente_proy += mi_cuota - len(imgs)
        else:
            cuotas_proy[proy] = mi_cuota
            proyectos_con_espacio.append(proy)

    while excedente_proy > 0 and proyectos_con_espacio:
        reparto_p = excedente_proy // len(proyectos_con_espacio)
        resto_p = excedente_proy % len(proyectos_con_espacio)
        excedente_proy = 0
        nuevos_proy = []
        for idx_p, proy in enumerate(proyectos_con_espacio):
            extra_p = reparto_p + (1 if idx_p < resto_p else 0)
            cuotas_proy[proy] += extra_p
            if cuotas_proy[proy] > len(por_proyecto[proy]):
                excedente_proy += cuotas_proy[proy] - len(por_proyecto[proy])
                cuotas_proy[proy] = len(por_proyecto[proy])
            else:
                nuevos_proy.append(proy)
        proyectos_con_espacio = nuevos_proy

    seleccion = []
    for proy, imgs in por_proyecto.items():
        seleccion.extend(imgs[:cuotas_proy[proy]])

    return seleccion, cuotas_proy


def clasificar_y_balancear_clase(imagenes, objetivo_por_clase, tipo_clasificacion):
    """Clasifica una clase en grupos de tamaño y balancea por proyecto.

    Returns:
        tuple: (grupos_seleccionados, cuotas) donde grupos_seleccionados es una
               lista de 4 listas de imágenes seleccionadas por grupo.
    """
    if tipo_clasificacion == "rango":
        grupos_lista = clasificar_por_rango(imagenes)
    else:
        grupos_lista = clasificar_proporcional(imagenes)

    cuotas = calcular_cuotas_grupos(grupos_lista, objetivo_por_clase)

    seleccionados = []
    cuotas_por_grupo = []
    for i, grupo in enumerate(grupos_lista):
        sel, cuotas_proy = balancear_por_proyecto(grupo, cuotas[i])
        seleccionados.append(sel)
        cuotas_por_grupo.append(cuotas_proy)

    return seleccionados, cuotas_por_grupo


def calcular_augmentation(resumen, factor):
    """Calcula cuántas imágenes augmentadas se necesitan por clase y grupo.

    Args:
        resumen: Lista de resultados del balanceo.
        factor: Factor multiplicador de augmentation.

    Returns:
        Lista de dicts con información de augmentation por clase.
    """
    resultado = []
    for entry in resumen:
        clase_info = {
            'clase': entry['clase'],
            'imagenes_originales': entry['total_balanceado'],
            'imagenes_objetivo': entry['total_balanceado'] * factor,
            'augmentaciones_necesarias': entry['total_balanceado'] * (factor - 1),
            'por_grupo': {}
        }
        for nombre_grupo, datos in entry['grupos'].items():
            count = datos['count']
            clase_info['por_grupo'][nombre_grupo] = {
                'originales': count,
                'objetivo': count * factor,
                'a_generar': count * (factor - 1),
            }
        resultado.append(clase_info)
    return resultado


# ============================================================
# FUNCIONES DE BASE DE DATOS (queries parametrizadas)
# ============================================================

def crear_columna_tamanio(conexion):
    """Crea la columna tamaño en la tabla si no existe."""
    consulta = """
        ALTER TABLE public.seniales_verticales
        ADD COLUMN IF NOT EXISTS tamaño VARCHAR(20)
    """
    conexion.execute(consulta)


def obtener_clases(conexion, proyectos):
    """Obtiene las clases disponibles, filtradas por proyectos."""
    if proyectos:
        consulta = """
            SELECT clase
            FROM public.seniales_verticales
            WHERE proyecto IN %s
            GROUP BY clase
            ORDER BY clase ASC
        """
        conexion.execute(consulta, (tuple(proyectos),))
    else:
        consulta = """
            SELECT clase
            FROM public.seniales_verticales
            GROUP BY clase
            ORDER BY clase ASC
        """
        conexion.execute(consulta)

    return conexion.fetchall()


def obtener_imagenes_clase(conexion, clase, proyectos, criterio_tamanio, tamanio_maximo):
    """Obtiene las imágenes de una clase con queries parametrizadas."""
    if criterio_tamanio == "altura":
        expresion_tamanio = "CAST(sv.height AS NUMERIC)"
    else:
        expresion_tamanio = "SQRT(POW(CAST(sv.width AS NUMERIC), 2) + POW(CAST(sv.height AS NUMERIC), 2))"

    condiciones = ["clase = %s"]
    params = [clase]

    if proyectos:
        condiciones.append("proyecto IN %s")
        params.append(tuple(proyectos))

    if tamanio_maximo is not None:
        condiciones.append(f"{expresion_tamanio} <= %s")
        params.append(tamanio_maximo)

    where = " AND ".join(condiciones)

    consulta = f"""
        SELECT sv.id as id, sv.width as ancho, sv.height as alto,
               sv.proyecto as proyecto, {expresion_tamanio} AS medida
        FROM public.seniales_verticales as sv
        WHERE {where}
        ORDER BY medida ASC
    """
    conexion.execute(consulta, params)
    return conexion.fetchall()


def actualizar_tamanio_bd(conexion, imagen_id, nombre_grupo):
    """Actualiza el tamaño de una imagen en BD con query parametrizada."""
    consulta = """
        UPDATE public.seniales_verticales
        SET tamaño = %s
        WHERE id = %s
    """
    conexion.execute(consulta, (nombre_grupo, imagen_id))


# ============================================================
# FASE 1: Recopilar datos
# ============================================================

def recopilar_datos(conexion, config):
    """Recopila y filtra los datos de todas las clases válidas."""
    clases = obtener_clases(conexion, config["proyectos"])
    datos_clases = {}

    for clase in clases:
        nombre_clase = clase['clase']

        if nombre_clase in config["clases_excluidas"]:
            logger.info(f"\n--- Clase '{nombre_clase}' excluida ---")
            continue

        imagenes = obtener_imagenes_clase(
            conexion, nombre_clase, config["proyectos"],
            config["criterio_tamanio"], config["tamanio_maximo"]
        )
        total = len(imagenes) if imagenes else 0

        if total < config["cantidad_minima"]:
            logger.info(f"  Clase '{nombre_clase}': solo {total} imágenes (mínimo: {config['cantidad_minima']}). Saltando.")
            continue

        datos_clases[nombre_clase] = imagenes

    return datos_clases


# ============================================================
# FASE 2: Calcular objetivo
# ============================================================

def calcular_objetivo(datos_clases, cantidad_maxima):
    """Calcula el objetivo balanceado por clase."""
    if not datos_clases:
        return 0
    clase_mas_pequena = min(len(imgs) for imgs in datos_clases.values())
    return min(cantidad_maxima, clase_mas_pequena)


# ============================================================
# FASE 3-4: Clasificar, balancear y actualizar
# ============================================================

def procesar_clases(conexion, datos_clases, objetivo_por_clase, config):
    """Procesa todas las clases: clasifica, balancea y actualiza BD."""
    resumen = []
    criterio = config["criterio_tamanio"]
    tipo = config["tipo_clasificacion"]

    for nombre_clase, imagenes in datos_clases.items():
        medidas = [img['medida'] for img in imagenes]
        total_imagenes = len(imagenes)

        logger.info(f"\n----------------------------")
        logger.info(f"{nombre_clase}")
        logger.info(f"  Total imágenes: {total_imagenes}")
        logger.info(f"  Media {criterio}: {sum(medidas) / len(medidas):.2f}")
        logger.info(f"  {criterio.capitalize()} min: {min(medidas):.2f} | max: {max(medidas):.2f}")

        seleccionados, cuotas_por_grupo = clasificar_y_balancear_clase(
            imagenes, objetivo_por_clase, tipo
        )

        logger.info(f"\n  Balanceando a {objetivo_por_clase} imágenes (tamaño + proyecto):")
        for i, nombre in enumerate(NOMBRES_GRUPOS):
            if cuotas_por_grupo[i]:
                logger.info(
                    f"    {nombre:12s}: {len(seleccionados[i]):4d} imgs | "
                    f"{', '.join(f'{p}={c}' for p, c in cuotas_por_grupo[i].items())}"
                )

        # Actualizar tamaño en BD
        for i, nombre in enumerate(NOMBRES_GRUPOS):
            for imagen in seleccionados[i]:
                actualizar_tamanio_bd(conexion, imagen['id'], nombre)

        total_balanceado = sum(len(g) for g in seleccionados)
        logger.info(f"  Total tras balanceo: {total_balanceado}")

        for i, nombre in enumerate(NOMBRES_GRUPOS):
            grupo = seleccionados[i]
            logger.info(f"\n  Imágenes {nombre}: {len(grupo)}")
            if grupo:
                logger.info(f"    {criterio.capitalize()}: {grupo[0]['medida']:.2f} - {grupo[-1]['medida']:.2f}")

        # Construir resumen con nomenclatura unificada
        grupos_resumen = {}
        for i, nombre in enumerate(NOMBRES_GRUPOS):
            grupo = seleccionados[i]
            grupos_resumen[nombre] = {
                'count': len(grupo),
                'rango': (grupo[0]['medida'], grupo[-1]['medida']) if grupo else None,
            }

        grupo_minimo = min(grupos_resumen, key=lambda g: grupos_resumen[g]['count'])
        resumen.append({
            'clase': nombre_clase,
            'total': total_imagenes,
            'total_balanceado': total_balanceado,
            'grupos': grupos_resumen,
            'grupo_minimo': grupo_minimo,
        })

    return resumen


# ============================================================
# FASE 5: Generar fichero de resultados
# ============================================================

def generar_fichero_resultados(resumen, config, augmentation_info=None):
    """Genera el fichero de resultados con el resumen del balanceo."""
    tipo = config["tipo_clasificacion"]
    criterio = config["criterio_tamanio"]
    nombre_fichero = f"resultados_clases_{tipo}.txt"

    if tipo == "rango":
        titulo = "RESUMEN DE CLASES - RANGOS IGUALES DE DIAGONAL"
    else:
        titulo = "RESUMEN DE CLASES - DISTRIBUCIÓN PROPORCIONAL"

    with open(nombre_fichero, 'w', encoding='utf-8') as f:
        f.write(f"{titulo}\n")
        f.write("=" * 60 + "\n\n")

        for entry in resumen:
            nombre_clase = entry['clase']
            grupos = entry['grupos']
            grupo_minimo = entry['grupo_minimo']

            f.write(f"Clase: {nombre_clase}  (total: {entry['total']} -> balanceado: {entry['total_balanceado']} imágenes)\n")
            f.write("-" * 40 + "\n")

            for nombre_grupo, datos in grupos.items():
                marca = " <-- MENOS IMÁGENES" if nombre_grupo == grupo_minimo and tipo == "rango" else ""
                f.write(f"  {nombre_grupo:12s}: {datos['count']:4d} imágenes")
                if datos['rango']:
                    f.write(f"  |  {criterio}: {datos['rango'][0]:.2f} - {datos['rango'][1]:.2f}")
                else:
                    f.write("  |  sin imágenes")
                f.write(f"{marca}\n")

            f.write(f"\n  >> Grupo con menos imágenes: {grupo_minimo.upper()} ({grupos[grupo_minimo]['count']} imágenes)\n")
            f.write("\n")

        f.write("=" * 60 + "\n")
        f.write(f"Total de clases analizadas: {len(resumen)}\n")

        # Sección de data augmentation
        if augmentation_info:
            f.write("\n" + "=" * 60 + "\n")
            f.write("DATA AUGMENTATION RECOMENDADO\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Factor de augmentation: x{config['augmentation_factor']}\n\n")

            for aug in augmentation_info:
                f.write(f"Clase: {aug['clase']}\n")
                f.write(f"  Originales: {aug['imagenes_originales']} -> Objetivo: {aug['imagenes_objetivo']}\n")
                f.write(f"  Augmentaciones a generar: {aug['augmentaciones_necesarias']}\n")
                for nombre_grupo, datos in aug['por_grupo'].items():
                    f.write(f"    {nombre_grupo:12s}: {datos['originales']:4d} -> {datos['objetivo']:4d} ({datos['a_generar']} a generar)\n")
                f.write("\n")

            f.write("Transformaciones recomendadas:\n")
            f.write("  - Rotación: ±15°\n")
            f.write("  - Flip horizontal (solo señales simétricas)\n")
            f.write("  - Ajuste de brillo: ±20%\n")
            f.write("  - Ajuste de contraste: ±15%\n")
            f.write("  - Recorte aleatorio: 85-100% del área\n")
            f.write("  - Desenfoque gaussiano: sigma 0.5-1.5\n")
            f.write("  - Ruido gaussiano: sigma 5-15\n")

    return nombre_fichero


# ============================================================
# PUNTO DE ENTRADA PRINCIPAL
# ============================================================

def main(config=None):
    """Ejecuta el algoritmo completo de balanceo."""
    if config is None:
        config = CONFIG

    logger.info("Inicio de algoritmo unificado")
    logger.info(f"Tipo de clasificación: {config['tipo_clasificacion']}")
    logger.info(f"Criterio de tamaño: {config['criterio_tamanio']}")
    logger.info(f"Proyectos: {config['proyectos'] if config['proyectos'] else 'Todos'}")
    logger.info(f"Clases excluidas: {config['clases_excluidas'] if config['clases_excluidas'] else 'Ninguna'}")
    logger.info(f"Cantidad mínima: {config['cantidad_minima']}")
    logger.info(f"Cantidad máxima: {config['cantidad_maxima']}")
    logger.info(f"Tamaño máximo ({config['criterio_tamanio']}): {config['tamanio_maximo'] if config['tamanio_maximo'] else 'Sin límite'}")
    logger.info(f"Factor augmentation: x{config['augmentation_factor']}")

    conexion = FisotecBaseDatos.conectarBaseDatos()
    crear_columna_tamanio(conexion)

    # Fase 1: Recopilar datos
    datos_clases = recopilar_datos(conexion, config)

    if not datos_clases:
        logger.info("No se encontraron clases válidas.")
        return

    # Fase 2: Calcular objetivo
    objetivo_por_clase = calcular_objetivo(datos_clases, config["cantidad_maxima"])
    logger.info(f"\n{'='*60}")
    logger.info(f"Clases válidas: {len(datos_clases)}")
    logger.info(f"Clase más pequeña: {min(len(imgs) for imgs in datos_clases.values())} imágenes")
    logger.info(f"Objetivo balanceado por clase: {objetivo_por_clase} imágenes")
    logger.info(f"Con augmentation x{config['augmentation_factor']}: {objetivo_por_clase * config['augmentation_factor']} imágenes/clase")
    logger.info(f"{'='*60}")

    # Fase 3-4: Clasificar, balancear y actualizar BD
    resumen = procesar_clases(conexion, datos_clases, objetivo_por_clase, config)

    # Calcular data augmentation
    augmentation_info = calcular_augmentation(resumen, config['augmentation_factor'])

    # Fase 5: Generar fichero de resultados
    nombre_fichero = generar_fichero_resultados(resumen, config, augmentation_info)

    logger.info(f"\nFichero '{nombre_fichero}' generado correctamente.")
    logger.info("Terminamos el algoritmo")

    return resumen, augmentation_info


if __name__ == '__main__':
    main()
