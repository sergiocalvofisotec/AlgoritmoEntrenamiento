#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Algoritmo de preparación de datasets para entrenamiento YOLO.

Selecciona, filtra, balancea y exporta imágenes de señales verticales
a formato YOLO (carpetas images/labels + seniales.yaml).
"""

import json
import logging
import os
import random
import shutil
from datetime import datetime
from fisotec_basedatos import FisotecBaseDatos

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURACIÓN
# ============================================================
CONFIG = {
    # Proyectos a incluir. Lista vacía = todos los proyectos
    "proyectos": ["03_ibiza", "01_alcaudete", "02_fuente_albilla", "04_carreteras"],

    # Clases a excluir del algoritmo
    "clases_excluidas": ["ST_C", "ST_R", "ST_S", "ST_T"],

    # Criba por número de muestras:
    #   cantidad_minima: clases con menos de 100 imágenes se excluyen
    #                    (YOLO necesita variedad para generalizar, no memorizar)
    #   cantidad_maxima: cap por clase para evitar que las mayoritarias
    #                    dominen la loss (típico: pierde 1-2% mAP en la grande,
    #                    gana 10-15% en las pequeñas)
    "cantidad_minima": 100,
    "cantidad_maxima": 2000,

    # Criba por tamaño de recorte (en píxeles):
    #   tamanio_minimo: excluir recortes < 10px (errores de anotación)
    #   tamanio_maximo: excluir recortes muy grandes. None = sin límite
    "tamanio_minimo": 10,
    "tamanio_maximo": 500,

    # Separación train/val/test:
    #   Se divide ANTES del balanceo para evitar data leakage.
    #   El balanceo solo se aplica al split de train.
    "split_ratios": {"train": 0.70, "val": 0.15, "test": 0.15},

    # Ruta base donde están las imágenes originales (por proyecto)
    # Estructura esperada: ruta_imagenes/{proyecto}/images/*.jpg
    "ruta_imagenes": None,

    # Ruta de salida del dataset YOLO exportado
    "ruta_salida": "dataset_yolo",
}

# ============================================================
# FUNCIONES PURAS (sin BD, testeables directamente)
# ============================================================

def balancear_por_proyecto(imagenes, cuota):
    """Balancea las imágenes de una clase entre proyectos.

    Reparte la cuota equitativamente entre proyectos, redistribuyendo
    el excedente de proyectos que no alcanzan su cuota.

    Args:
        imagenes: Lista de imágenes de una clase.
        cuota: Número objetivo de imágenes a seleccionar.

    Returns:
        tuple: (seleccion, cuotas_proyecto) donde seleccion es la lista
               de imágenes seleccionadas y cuotas_proyecto es un dict
               {proyecto: n_imagenes_seleccionadas}.
    """
    por_proyecto = {}
    for img in imagenes:
        proy = img['proyecto']
        if proy not in por_proyecto:
            por_proyecto[proy] = []
        por_proyecto[proy].append(img)

    num_proyectos = len(por_proyecto)
    if num_proyectos == 0:
        return [], {}

    cuota_proy = cuota // num_proyectos
    sobrante_proy = cuota % num_proyectos

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
        cuota_final = cuotas_proy[proy]
        if cuota_final >= len(imgs):
            seleccion.extend(imgs)
        else:
            seleccion.extend(random.sample(imgs, cuota_final))

    return seleccion, cuotas_proy


def calcular_objetivo(datos_clases, cantidad_maxima):
    """Calcula el objetivo de imágenes por clase (modo independiente).

    Cada clase usa todas sus imágenes hasta cantidad_maxima.

    Returns:
        Dict {clase: objetivo} con el número de imágenes por clase.
    """
    if not datos_clases:
        return {}
    return {clase: min(cantidad_maxima, len(imgs))
            for clase, imgs in datos_clases.items()}


def separar_train_val_test(datos_clases, ratios):
    """Separa las imágenes en train/val/test ANTES del balanceo.

    El split se hace a nivel de IMAGEN (no de anotación) para evitar
    data leakage: una imagen con varias señales siempre va entera
    al mismo split. Estratificado por proyecto.

    Args:
        datos_clases: Dict {clase: [imagenes]} con todas las imágenes.
        ratios: Dict {"train": 0.70, "val": 0.15, "test": 0.15}.

    Returns:
        Dict {"train": {clase: [imgs]}, "val": {clase: [imgs]}, "test": {clase: [imgs]}}
    """
    # Paso 1: Recopilar imágenes únicas y agrupar por proyecto
    imagenes_por_proyecto = {}
    for clase, imagenes in datos_clases.items():
        for img in imagenes:
            nombre = img['nombre_imagen']
            proy = img['proyecto']
            if proy not in imagenes_por_proyecto:
                imagenes_por_proyecto[proy] = set()
            imagenes_por_proyecto[proy].add(nombre)

    # Paso 2: Asignar cada imagen única a un split, estratificado por proyecto
    asignacion_imagen = {}  # nombre_imagen -> "train"/"val"/"test"
    for proy, nombres in imagenes_por_proyecto.items():
        nombres_lista = sorted(nombres)  # Ordenar para reproducibilidad
        random.shuffle(nombres_lista)
        n = len(nombres_lista)
        n_train = int(n * ratios["train"])
        n_val = int(n * ratios["val"])

        for nombre in nombres_lista[:n_train]:
            asignacion_imagen[nombre] = "train"
        for nombre in nombres_lista[n_train:n_train + n_val]:
            asignacion_imagen[nombre] = "val"
        for nombre in nombres_lista[n_train + n_val:]:
            asignacion_imagen[nombre] = "test"

    # Paso 3: Distribuir anotaciones según el split de su imagen
    splits = {"train": {}, "val": {}, "test": {}}
    for clase in datos_clases:
        splits["train"][clase] = []
        splits["val"][clase] = []
        splits["test"][clase] = []

    for clase, imagenes in datos_clases.items():
        for img in imagenes:
            split = asignacion_imagen[img['nombre_imagen']]
            splits[split][clase].append(img)

    return splits


def generar_label_yolo(imagen, clase_id, w_imagen, h_imagen):
    """Genera una línea de label YOLO normalizada para una anotación.

    Formato YOLO: clase_id x_center y_center width height (todo 0-1)

    Args:
        imagen: Dict con x_center, y_center, ancho, alto del recorte.
        clase_id: ID numérico de la clase.
        w_imagen: Ancho de la imagen completa.
        h_imagen: Alto de la imagen completa.

    Returns:
        String con la línea de label YOLO.
    """
    x_center = float(imagen['x_center']) / float(w_imagen)
    y_center = float(imagen['y_center']) / float(h_imagen)
    width = float(imagen['ancho']) / float(w_imagen)
    height = float(imagen['alto']) / float(h_imagen)

    # Clamp a [0, 1] por si hay anotaciones ligeramente fuera de rango
    x_center = max(0.0, min(1.0, x_center))
    y_center = max(0.0, min(1.0, y_center))
    width = max(0.0, min(1.0, width))
    height = max(0.0, min(1.0, height))

    return f"{clase_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"


def generar_yaml_contenido(clases_ordenadas, ruta_dataset):
    """Genera el contenido del fichero seniales.yaml para YOLO.

    Args:
        clases_ordenadas: Lista de nombres de clase ordenados (el índice es el ID).
        ruta_dataset: Ruta raíz del dataset.

    Returns:
        String con el contenido YAML.
    """
    lineas = []
    lineas.append(f"path: {ruta_dataset}")
    lineas.append("train: images/train")
    lineas.append("val: images/val")
    lineas.append("test: images/test")
    lineas.append("")
    lineas.append(f"nc: {len(clases_ordenadas)}")
    lineas.append("names:")
    for i, clase in enumerate(clases_ordenadas):
        lineas.append(f"  {i}: {clase}")
    return "\n".join(lineas) + "\n"


# ============================================================
# FUNCIONES DE BASE DE DATOS (queries parametrizadas)
# ============================================================

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


def obtener_imagenes_clase(conexion, clase, proyectos, tamanio_minimo, tamanio_maximo):
    """Obtiene las imágenes de una clase con filtros de calidad.

    Incluye los campos necesarios para generar labels YOLO:
    x_center, y_center, nombre_imagen, W_imagen, H_imagen.
    """
    condiciones = ["clase = %s"]
    params = [clase]

    if proyectos:
        condiciones.append("proyecto IN %s")
        params.append(tuple(proyectos))

    # Filtro de calidad: tamaño mínimo (excluir recortes ruidosos)
    if tamanio_minimo is not None:
        condiciones.append("CAST(width AS NUMERIC) >= %s")
        condiciones.append("CAST(height AS NUMERIC) >= %s")
        params.extend([tamanio_minimo, tamanio_minimo])

    # Filtro de tamaño máximo
    if tamanio_maximo is not None:
        condiciones.append("CAST(height AS NUMERIC) <= %s")
        params.append(tamanio_maximo)

    where = " AND ".join(condiciones)

    consulta = f"""
        SELECT sv.id as id,
               sv.nombre_imagen as nombre_imagen,
               CAST(sv.width AS NUMERIC) as ancho,
               CAST(sv.height AS NUMERIC) as alto,
               sv.proyecto as proyecto,
               CAST(sv.x_center AS NUMERIC) as x_center,
               CAST(sv.y_center AS NUMERIC) as y_center,
               sv."W_imagen" as w_imagen,
               sv."H_imagen" as h_imagen
        FROM public.seniales_verticales as sv
        WHERE {where}
        ORDER BY sv.id ASC
    """
    conexion.execute(consulta, params)
    return conexion.fetchall()


# ============================================================
# FASE 1: Recopilar datos + filtro de calidad
# ============================================================

def recopilar_datos(conexion, config):
    """Recopila y filtra los datos de todas las clases válidas.

    Aplica tres filtros:
    1. Clases excluidas manualmente
    2. Tamaño mínimo/máximo del recorte (calidad de anotación)
    3. Cantidad mínima de muestras (viabilidad para YOLO)
    """
    clases = obtener_clases(conexion, config["proyectos"])
    datos_clases = {}
    clases_excluidas_por_cantidad = {}

    for clase in clases:
        nombre_clase = clase['clase']

        if nombre_clase in config["clases_excluidas"]:
            logger.info(f"  Clase '{nombre_clase}' excluida manualmente")
            continue

        imagenes = obtener_imagenes_clase(
            conexion, nombre_clase, config["proyectos"],
            config.get("tamanio_minimo"), config.get("tamanio_maximo")
        )
        total = len(imagenes) if imagenes else 0

        if total < config["cantidad_minima"]:
            logger.info(f"  Clase '{nombre_clase}': {total} imágenes (mínimo: {config['cantidad_minima']}). Excluida.")
            clases_excluidas_por_cantidad[nombre_clase] = total
            continue

        datos_clases[nombre_clase] = imagenes

    return datos_clases, clases_excluidas_por_cantidad


# ============================================================
# FASE 2: Balancear por clase y proyecto
# ============================================================

def procesar_clases(datos_clases, objetivo_por_clase):
    """Balancea todas las clases por proyecto.

    Sin grupos de tamaño: YOLO gestiona internamente la variación
    de escalas con mosaic, multi-scale y random resize.
    """
    resumen = []

    for nombre_clase, imagenes in datos_clases.items():
        total_imagenes = len(imagenes)
        objetivo_clase = objetivo_por_clase[nombre_clase]

        seleccion, cuotas_proy = balancear_por_proyecto(imagenes, objetivo_clase)

        logger.info(f"\n  {nombre_clase}: {total_imagenes} -> {len(seleccion)} imágenes")
        for proy, cuota in cuotas_proy.items():
            logger.info(f"    {proy}: {cuota}")

        resumen.append({
            'clase': nombre_clase,
            'total': total_imagenes,
            'total_balanceado': len(seleccion),
            'seleccion': seleccion,
            'cuotas_proyecto': cuotas_proy,
        })

    return resumen


# ============================================================
# FASE 3: Exportar a formato YOLO
# ============================================================

def exportar_dataset_yolo(resumen_train, resumen_val, resumen_test,
                          clases_ordenadas, config):
    """Exporta el dataset balanceado a la estructura de carpetas YOLO.

    Genera:
    - dataset_yolo/images/{train,val,test}/ (imágenes copiadas o enlazadas)
    - dataset_yolo/labels/{train,val,test}/ (ficheros .txt con anotaciones)
    - dataset_yolo/seniales.yaml (configuración del dataset)

    Si ruta_imagenes es None, solo genera los labels y el yaml.
    """
    ruta_salida = config["ruta_salida"]
    ruta_imagenes = config.get("ruta_imagenes")
    clase_a_id = {clase: i for i, clase in enumerate(clases_ordenadas)}

    # Crear estructura de carpetas
    for split in ["train", "val", "test"]:
        os.makedirs(os.path.join(ruta_salida, "images", split), exist_ok=True)
        os.makedirs(os.path.join(ruta_salida, "labels", split), exist_ok=True)

    # Agrupar anotaciones por imagen (una imagen puede tener varias señales)
    splits_data = {
        "train": resumen_train,
        "val": resumen_val,
        "test": resumen_test,
    }

    estadisticas = {"train": 0, "val": 0, "test": 0}

    for split, resumen_list in splits_data.items():
        # Agrupar todas las anotaciones por nombre de imagen
        anotaciones_por_imagen = {}
        for entry in resumen_list:
            clase = entry['clase']
            clase_id = clase_a_id[clase]
            for img in entry['seleccion']:
                nombre = img['nombre_imagen']
                if nombre not in anotaciones_por_imagen:
                    anotaciones_por_imagen[nombre] = {
                        'labels': [],
                        'proyecto': img['proyecto'],
                    }
                label = generar_label_yolo(
                    img, clase_id,
                    img['w_imagen'], img['h_imagen']
                )
                anotaciones_por_imagen[nombre]['labels'].append(label)

        # Escribir labels y copiar imágenes
        for nombre_imagen, datos in anotaciones_por_imagen.items():
            nombre_base = os.path.splitext(nombre_imagen)[0]

            # Escribir fichero de labels
            ruta_label = os.path.join(ruta_salida, "labels", split, f"{nombre_base}.txt")
            with open(ruta_label, 'w') as f:
                f.write("\n".join(datos['labels']) + "\n")

            # Copiar imagen si tenemos la ruta base
            if ruta_imagenes:
                origen = os.path.join(ruta_imagenes, datos['proyecto'], "images", nombre_imagen)
                destino = os.path.join(ruta_salida, "images", split, nombre_imagen)
                if os.path.exists(origen) and not os.path.exists(destino):
                    shutil.copy2(origen, destino)

        estadisticas[split] = len(anotaciones_por_imagen)

    # Generar seniales.yaml
    ruta_abs = os.path.abspath(ruta_salida)
    yaml_contenido = generar_yaml_contenido(clases_ordenadas, ruta_abs)
    ruta_yaml = os.path.join(ruta_salida, "seniales.yaml")
    with open(ruta_yaml, 'w', encoding='utf-8') as f:
        f.write(yaml_contenido)

    return estadisticas, ruta_yaml


# ============================================================
# FASE 4: Trazabilidad por versión
# ============================================================

def registrar_version(config, resumen_train, split_info, clases_excluidas_cantidad,
                      estadisticas_export, clases_ordenadas):
    """Registra la configuración y asignación de imágenes de esta ejecución.

    Genera un fichero JSON con toda la información necesaria para
    reproducir exactamente este dataset en el futuro.
    """
    ruta_salida = config["ruta_salida"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # IDs seleccionados por clase en train
    asignacion_train = {}
    for entry in resumen_train:
        asignacion_train[entry['clase']] = {
            'ids': [img['id'] for img in entry['seleccion']],
            'total': entry['total_balanceado'],
            'cuotas_proyecto': entry['cuotas_proyecto'],
        }

    version = {
        'timestamp': timestamp,
        'config': {k: v for k, v in config.items()},
        'clases_activas': clases_ordenadas,
        'clases_excluidas_por_cantidad': clases_excluidas_cantidad,
        'split_info': split_info,
        'asignacion_train': asignacion_train,
        'estadisticas_export': estadisticas_export,
    }

    nombre_fichero = os.path.join(ruta_salida, f"version_{timestamp}.json")
    with open(nombre_fichero, 'w', encoding='utf-8') as f:
        json.dump(version, f, indent=2, ensure_ascii=False, default=str)

    logger.info(f"\nVersión registrada: {nombre_fichero}")
    return nombre_fichero


# ============================================================
# GENERAR FICHERO DE RESULTADOS (resumen legible)
# ============================================================

def generar_fichero_resultados(resumen_train, config, split_info,
                               clases_excluidas_cantidad, estadisticas_export,
                               clases_ordenadas):
    """Genera el fichero de resultados con el resumen del pipeline."""
    nombre_fichero = "resultados_yolo.txt"

    with open(nombre_fichero, 'w', encoding='utf-8') as f:
        f.write("RESUMEN DEL DATASET YOLO\n")
        f.write("=" * 60 + "\n\n")

        # Configuración
        f.write("CONFIGURACIÓN\n")
        f.write("-" * 40 + "\n")
        f.write(f"Proyectos: {', '.join(config['proyectos'])}\n")
        f.write(f"Cantidad mínima por clase: {config['cantidad_minima']}\n")
        f.write(f"Cantidad máxima por clase: {config['cantidad_maxima']}\n")
        f.write(f"Tamaño mínimo de recorte: {config['tamanio_minimo']}px\n")
        f.write(f"Tamaño máximo de recorte: {config['tamanio_maximo']}px\n")
        f.write(f"Split: train={config['split_ratios']['train']:.0%} / "
                f"val={config['split_ratios']['val']:.0%} / "
                f"test={config['split_ratios']['test']:.0%}\n\n")

        # Clases excluidas por cantidad
        if clases_excluidas_cantidad:
            f.write("CLASES EXCLUIDAS POR CANTIDAD INSUFICIENTE\n")
            f.write("-" * 40 + "\n")
            for clase, total in sorted(clases_excluidas_cantidad.items()):
                f.write(f"  {clase:12s}: {total:4d} imágenes (mínimo: {config['cantidad_minima']})\n")
            f.write(f"\nTotal excluidas: {len(clases_excluidas_cantidad)}\n\n")

        # Split train/val/test
        f.write("SEPARACIÓN TRAIN/VAL/TEST (pre-balanceo)\n")
        f.write("-" * 40 + "\n")
        total_t = sum(s['train'] for s in split_info.values())
        total_v = sum(s['val'] for s in split_info.values())
        total_te = sum(s['test'] for s in split_info.values())
        total_all = sum(s['total'] for s in split_info.values())
        f.write(f"  {'Clase':12s}  {'Total':>6s}  {'Train':>6s}  {'Val':>5s}  {'Test':>5s}\n")
        f.write(f"  {'-'*12}  {'-'*6}  {'-'*6}  {'-'*5}  {'-'*5}\n")
        for clase, info in sorted(split_info.items()):
            f.write(f"  {clase:12s}  {info['total']:6d}  {info['train']:6d}  {info['val']:5d}  {info['test']:5d}\n")
        f.write(f"  {'-'*12}  {'-'*6}  {'-'*6}  {'-'*5}  {'-'*5}\n")
        f.write(f"  {'TOTAL':12s}  {total_all:6d}  {total_t:6d}  {total_v:5d}  {total_te:5d}\n\n")

        # Balanceo por proyecto (solo train)
        f.write("BALANCEO POR PROYECTO (train)\n")
        f.write("=" * 60 + "\n\n")
        for entry in resumen_train:
            f.write(f"Clase: {entry['clase']}  ({entry['total']} -> {entry['total_balanceado']} imágenes)\n")
            f.write("-" * 40 + "\n")
            for proy, cuota in entry['cuotas_proyecto'].items():
                f.write(f"  {proy:20s}: {cuota:4d} imágenes\n")
            f.write("\n")

        # Exportación YOLO
        f.write("=" * 60 + "\n")
        f.write("EXPORTACIÓN YOLO\n")
        f.write("-" * 40 + "\n")
        f.write(f"Clases activas: {len(clases_ordenadas)}\n")
        f.write(f"Imágenes train: {estadisticas_export['train']}\n")
        f.write(f"Imágenes val:   {estadisticas_export['val']}\n")
        f.write(f"Imágenes test:  {estadisticas_export['test']}\n\n")

        f.write("Mapeo de clases (ID -> nombre):\n")
        for i, clase in enumerate(clases_ordenadas):
            f.write(f"  {i:3d}: {clase}\n")

    return nombre_fichero


# ============================================================
# PUNTO DE ENTRADA PRINCIPAL
# ============================================================

def main(config=None):
    """Ejecuta el pipeline completo de preparación de dataset YOLO.

    Pipeline:
    1. Recopilar datos + filtro de calidad
    2. Separar train/val/test (estratificado por clase y proyecto)
    3. Balancear por clase y proyecto (solo train)
    4. Exportar a estructura YOLO + generar yaml
    5. Registrar versión (config + asignación de imágenes)
    """
    if config is None:
        config = CONFIG

    random.seed(42)
    logger.info("Inicio del pipeline de preparación de dataset YOLO")
    logger.info(f"Proyectos: {config['proyectos'] if config['proyectos'] else 'Todos'}")
    logger.info(f"Clases excluidas: {config['clases_excluidas']}")
    logger.info(f"Cantidad mínima: {config['cantidad_minima']} | máxima: {config['cantidad_maxima']}")
    logger.info(f"Tamaño mínimo: {config['tamanio_minimo']}px | máximo: {config['tamanio_maximo']}px")

    split_ratios = config.get("split_ratios")
    if split_ratios:
        logger.info(f"Split: {split_ratios['train']:.0%} / {split_ratios['val']:.0%} / {split_ratios['test']:.0%}")

    conexion = FisotecBaseDatos.conectarBaseDatos()

    # Fase 1: Recopilar datos + filtro de calidad
    logger.info(f"\n{'='*60}")
    logger.info("FASE 1: Recopilar datos + filtro de calidad")
    logger.info(f"{'='*60}")
    datos_clases, clases_excluidas_cantidad = recopilar_datos(conexion, config)

    if not datos_clases:
        logger.info("No se encontraron clases válidas.")
        return

    total_imagenes = sum(len(imgs) for imgs in datos_clases.values())
    logger.info(f"\nClases válidas: {len(datos_clases)} ({total_imagenes} imágenes)")
    logger.info(f"Clases excluidas por cantidad: {len(clases_excluidas_cantidad)}")

    # Fase 2: Separar train/val/test
    logger.info(f"\n{'='*60}")
    logger.info("FASE 2: Separar train/val/test")
    logger.info(f"{'='*60}")
    splits = separar_train_val_test(datos_clases, split_ratios)
    split_info = {}
    for clase in datos_clases:
        split_info[clase] = {
            'total': len(datos_clases[clase]),
            'train': len(splits["train"][clase]),
            'val': len(splits["val"][clase]),
            'test': len(splits["test"][clase]),
        }
    total_train = sum(s['train'] for s in split_info.values())
    total_val = sum(s['val'] for s in split_info.values())
    total_test = sum(s['test'] for s in split_info.values())
    logger.info(f"  Train: {total_train} | Val: {total_val} | Test: {total_test}")

    # Fase 3: Balancear por clase y proyecto (solo train)
    logger.info(f"\n{'='*60}")
    logger.info("FASE 3: Balancear por clase y proyecto (solo train)")
    logger.info(f"{'='*60}")
    objetivo_por_clase = calcular_objetivo(splits["train"], config["cantidad_maxima"])
    resumen_train = procesar_clases(splits["train"], objetivo_por_clase)

    # Val y test sin balancear (se usan completos para evaluación)
    resumen_val = [{'clase': c, 'total': len(imgs), 'total_balanceado': len(imgs),
                    'seleccion': imgs, 'cuotas_proyecto': {}}
                   for c, imgs in splits["val"].items()]
    resumen_test = [{'clase': c, 'total': len(imgs), 'total_balanceado': len(imgs),
                     'seleccion': imgs, 'cuotas_proyecto': {}}
                    for c, imgs in splits["test"].items()]

    # Lista de clases ordenadas (el índice es el ID para YOLO)
    clases_ordenadas = sorted(datos_clases.keys())

    # Fase 4: Exportar a formato YOLO
    logger.info(f"\n{'='*60}")
    logger.info("FASE 4: Exportar a formato YOLO")
    logger.info(f"{'='*60}")
    estadisticas_export, ruta_yaml = exportar_dataset_yolo(
        resumen_train, resumen_val, resumen_test,
        clases_ordenadas, config
    )
    logger.info(f"  Imágenes exportadas -> train: {estadisticas_export['train']} | "
                f"val: {estadisticas_export['val']} | test: {estadisticas_export['test']}")
    logger.info(f"  YAML generado: {ruta_yaml}")

    # Fase 5: Registrar versión
    logger.info(f"\n{'='*60}")
    logger.info("FASE 5: Registrar versión")
    logger.info(f"{'='*60}")
    fichero_version = registrar_version(
        config, resumen_train, split_info, clases_excluidas_cantidad,
        estadisticas_export, clases_ordenadas
    )

    # Generar fichero de resultados legible
    nombre_resultados = generar_fichero_resultados(
        resumen_train, config, split_info, clases_excluidas_cantidad,
        estadisticas_export, clases_ordenadas
    )

    logger.info(f"\nFichero de resultados: {nombre_resultados}")
    logger.info("Pipeline YOLO completado")

    return resumen_train, clases_ordenadas, estadisticas_export


if __name__ == '__main__':
    main()
