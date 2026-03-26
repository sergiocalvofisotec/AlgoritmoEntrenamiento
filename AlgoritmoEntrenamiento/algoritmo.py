#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Importaciones
from fisotec_basedatos import FisotecBaseDatos

# ============================================================
# CONFIGURACIÓN
# ============================================================
# Tipo de clasificación:
#   "rango"        -> Divide por rangos iguales (algoritmo 1)
#   "proporcional" -> Divide por cantidad proporcional de imágenes (algoritmo 2)
TIPO_CLASIFICACION = "proporcional"

# Criterio de tamaño:
#   "altura"   -> Clasifica por la altura de la imagen
#   "diagonal" -> Clasifica por la diagonal de la imagen
CRITERIO_TAMANIO = "altura"

# Proyectos a incluir. Lista vacía = todos los proyectos
# Ejemplo: ["proyecto1", "proyecto2"]
PROYECTOS = ["03_ibiza","01_alcaudete","02_fuente_albilla","04_carreteras"]

# Clases a excluir del algoritmo
CLASES_EXCLUIDAS = ["ST_C","ST_R","ST_S","ST_T"]

# Cantidad mínima y máxima de imágenes por clase
CANTIDAD_MINIMA = 50
CANTIDAD_MAXIMA = 1000

# Tamaño máximo de imagen (según criterio elegido). Las imágenes mayores se excluyen.
# None = sin límite
TAMANIO_MAXIMO = 500
# ============================================================

print("Inicio de algoritmo unificado")
print(f"Tipo de clasificación: {TIPO_CLASIFICACION}")
print(f"Criterio de tamaño: {CRITERIO_TAMANIO}")
print(f"Proyectos: {PROYECTOS if PROYECTOS else 'Todos'}")
print(f"Clases excluidas: {CLASES_EXCLUIDAS if CLASES_EXCLUIDAS else 'Ninguna'}")
print(f"Cantidad mínima de imágenes por clase: {CANTIDAD_MINIMA}")
print(f"Cantidad máxima de imágenes por clase: {CANTIDAD_MAXIMA}")
print(f"Tamaño máximo ({CRITERIO_TAMANIO}): {TAMANIO_MAXIMO if TAMANIO_MAXIMO else 'Sin límite'}")

# Conectamos la base de datos
conexion = FisotecBaseDatos.conectarBaseDatos()

# Crear la columna tamaño si no existe
consulta_crear_columna = u"""
    ALTER TABLE public.seniales_verticales
    ADD COLUMN IF NOT EXISTS tamaño VARCHAR(20)
"""
conexion.execute(consulta_crear_columna)

resumen = []

# Construimos el filtro de proyectos
filtro_proyectos = ""
if PROYECTOS:
    lista = ", ".join(["'{0}'".format(p) for p in PROYECTOS])
    filtro_proyectos = "AND proyecto IN ({0})".format(lista)

# Recorremos todas las clases y las guardamos en un array
consulta_clases = u"""
    SELECT clase
    FROM public.seniales_verticales
    WHERE 1=1
    {filtro_proyectos}
    GROUP BY clase
    ORDER BY clase ASC
""".format(filtro_proyectos=filtro_proyectos)

resultado_consulta_clases = FisotecBaseDatos.consultaSQL(conexion, consulta_clases)

# ============================================================
# FASE 1: Recopilar datos de todas las clases válidas
# ============================================================
# Construimos expresión SQL y filtro según el criterio de tamaño
if CRITERIO_TAMANIO == "altura":
    expresion_tamanio = "CAST(sv.height AS NUMERIC)"
else:
    expresion_tamanio = "SQRT(POW(CAST(sv.width AS NUMERIC), 2) + POW(CAST(sv.height AS NUMERIC), 2))"

filtro_tamanio = ""
if TAMANIO_MAXIMO is not None:
    filtro_tamanio = "AND {0} <= {1}".format(expresion_tamanio, TAMANIO_MAXIMO)

datos_clases = {}

for clase in resultado_consulta_clases:

    if clase['clase'] in CLASES_EXCLUIDAS:
        print(f"\n--- Clase '{clase['clase']}' excluida ---")
        continue

    consulta_imagenes = u"""
            SELECT sv.id as id, sv.width as ancho, sv.height as alto, sv.proyecto as proyecto,
                   {expresion_tamanio} AS medida
            FROM public.seniales_verticales as sv
            WHERE clase = '{clase}'
            {filtro_proyectos}
            {filtro_tamanio}
            ORDER BY medida ASC
        """.format(clase=clase['clase'], filtro_proyectos=filtro_proyectos,
                   filtro_tamanio=filtro_tamanio, expresion_tamanio=expresion_tamanio)

    resultado_consulta_imagenes = FisotecBaseDatos.consultaSQL(conexion, consulta_imagenes)
    total_imagenes = len(resultado_consulta_imagenes) if resultado_consulta_imagenes else 0

    if total_imagenes < CANTIDAD_MINIMA:
        print(f"\n  Clase '{clase['clase']}': solo {total_imagenes} imágenes (mínimo: {CANTIDAD_MINIMA}). Saltando.")
        continue

    datos_clases[clase['clase']] = resultado_consulta_imagenes

# ============================================================
# FASE 2: Calcular objetivo balanceado por clase
# ============================================================
if datos_clases:
    clase_mas_pequena = min(len(imgs) for imgs in datos_clases.values())
    objetivo_por_clase = min(CANTIDAD_MAXIMA, clase_mas_pequena)
    print(f"\n{'='*60}")
    print(f"Clases válidas: {len(datos_clases)}")
    print(f"Clase más pequeña: {clase_mas_pequena} imágenes")
    print(f"Objetivo balanceado por clase: {objetivo_por_clase} imágenes")
    print(f"{'='*60}")

# ============================================================
# FASE 3: Clasificar y balancear cada clase
# ============================================================

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

for nombre_clase, resultado_consulta_imagenes in datos_clases.items():

    print("\n")
    print("----------------------------")
    print(nombre_clase)

    medidas = [img['medida'] for img in resultado_consulta_imagenes]
    total_imagenes = len(resultado_consulta_imagenes)

    media_medida = sum(medidas) / len(medidas)
    print(f"  Total imágenes: {total_imagenes}")
    print(f"  Media {CRITERIO_TAMANIO}: {media_medida:.2f}")
    print(f"  {CRITERIO_TAMANIO.capitalize()} min: {min(medidas):.2f} | max: {max(medidas):.2f}")

    # Clasificar en 4 grupos de tamaño
    cerca = []
    medio = []
    lejos = []
    muy_lejos = []

    if TIPO_CLASIFICACION == "rango":
        min_medida = min(medidas)
        max_medida = max(medidas)
        rango = max_medida - min_medida
        cuarto = rango / 4

        for imagen in resultado_consulta_imagenes:
            if imagen['medida'] < min_medida + cuarto:
                muy_lejos.append(imagen)
            elif imagen['medida'] < min_medida + 2 * cuarto:
                lejos.append(imagen)
            elif imagen['medida'] < min_medida + 3 * cuarto:
                medio.append(imagen)
            else:
                cerca.append(imagen)

    elif TIPO_CLASIFICACION == "proporcional":
        total = len(resultado_consulta_imagenes)
        for i, imagen in enumerate(resultado_consulta_imagenes):
            if i < total / 4:
                muy_lejos.append(imagen)
            elif i < total / 2:
                lejos.append(imagen)
            elif i < total * 3 / 4:
                medio.append(imagen)
            else:
                cerca.append(imagen)

    # Balanceo por tamaño y proyecto
    grupos_lista = [muy_lejos, lejos, medio, cerca]
    nombres_grupos = ["muy_pequeño", "pequeño", "medio", "grande"]

    print(f"\n  Balanceando a {objetivo_por_clase} imágenes (tamaño + proyecto):")

    # Calcular cuotas por grupo de tamaño
    cuota_tamanio = objetivo_por_clase // 4
    sobrante_tamanio = objetivo_por_clase % 4

    cuotas = [cuota_tamanio] * 4
    for i in range(sobrante_tamanio):
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

    # Balancear por proyecto dentro de cada grupo de tamaño
    seleccionados = [[], [], [], []]
    for i, grupo in enumerate(grupos_lista):
        seleccionados[i], cuotas_proy = balancear_por_proyecto(grupo, cuotas[i])
        if cuotas_proy:
            print(f"    {nombres_grupos[i]:12s}: {len(seleccionados[i]):4d} imgs (de {len(grupo)}) | {', '.join(f'{p}={c}' for p, c in cuotas_proy.items())}")

    muy_lejos, lejos, medio, cerca = seleccionados

    # Actualizar tamaño en BD
    for grupo, nombre in zip([muy_lejos, lejos, medio, cerca], nombres_grupos):
        for imagen in grupo:
            consulta_tamano = u"""
            UPDATE public.seniales_verticales
            SET tamaño = '{tamanio}'
            WHERE id = {id}
            """.format(id=imagen['id'], tamanio=nombre)
            conexion.execute(consulta_tamano)

    total_balanceado = len(muy_lejos) + len(lejos) + len(medio) + len(cerca)
    print(f"  Total tras balanceo: {total_balanceado}")

    print(f"\n  Imágenes muy_pequeño: {len(muy_lejos)}")
    if muy_lejos:
        print(f"    {CRITERIO_TAMANIO.capitalize()}: {muy_lejos[0]['medida']:.2f} - {muy_lejos[-1]['medida']:.2f}")
    print(f"  Imágenes pequeño:     {len(lejos)}")
    if lejos:
        print(f"    {CRITERIO_TAMANIO.capitalize()}: {lejos[0]['medida']:.2f} - {lejos[-1]['medida']:.2f}")
    print(f"  Imágenes medio:       {len(medio)}")
    if medio:
        print(f"    {CRITERIO_TAMANIO.capitalize()}: {medio[0]['medida']:.2f} - {medio[-1]['medida']:.2f}")
    print(f"  Imágenes grande:      {len(cerca)}")
    if cerca:
        print(f"    {CRITERIO_TAMANIO.capitalize()}: {cerca[0]['medida']:.2f} - {cerca[-1]['medida']:.2f}")

    grupos = {
        'muy_lejos': {'count': len(muy_lejos), 'rango': (muy_lejos[0]['medida'], muy_lejos[-1]['medida']) if muy_lejos else None},
        'lejos':     {'count': len(lejos),     'rango': (lejos[0]['medida'],     lejos[-1]['medida'])     if lejos     else None},
        'medio':     {'count': len(medio),     'rango': (medio[0]['medida'],     medio[-1]['medida'])     if medio     else None},
        'cerca':     {'count': len(cerca),     'rango': (cerca[0]['medida'],     cerca[-1]['medida'])     if cerca     else None},
    }
    grupo_minimo = min(grupos, key=lambda g: grupos[g]['count'])
    resumen.append({
        'clase': nombre_clase,
        'total': total_imagenes,
        'total_balanceado': total_balanceado,
        'grupos': grupos,
        'grupo_minimo': grupo_minimo,
    })


# Generamos el fichero de resultados
nombre_fichero = f"resultados_clases_{TIPO_CLASIFICACION}.txt"

if TIPO_CLASIFICACION == "rango":
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
            marca = " <-- MENOS IMÁGENES" if nombre_grupo == grupo_minimo and TIPO_CLASIFICACION == "rango" else ""
            f.write(f"  {nombre_grupo:9s}: {datos['count']:4d} imágenes")
            if datos['rango']:
                f.write(f"  |  {CRITERIO_TAMANIO}: {datos['rango'][0]:.2f} - {datos['rango'][1]:.2f}")
            else:
                f.write("  |  sin imágenes")
            f.write(f"{marca}\n")

        f.write(f"\n  >> Clase con mayor diferencia de dimensiones: {grupo_minimo.upper()} ({grupos[grupo_minimo]['count']} imágenes)\n")
        f.write("\n")

    f.write("=" * 60 + "\n")
    f.write(f"Total de clases analizadas: {len(resumen)}\n")
    

print(f"Fichero '{nombre_fichero}' generado correctamente.")
print("Terminamos el algoritmo")
