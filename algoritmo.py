#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Importaciones
from fisotec_basedatos import FisotecBaseDatos
from fisotec_utils import FisotecUtils

def obtener_nombre_esquema(proyecto, modulo):
    """
    Devuelve el nombre del esquema dependiendo del proyecto y modulo
    """

    if modulo == 9:
        return proyecto + '_gissmart_water'
    elif modulo == 6:
        return proyecto + '_gissmart_energy'
    elif modulo == 11:
        return proyecto + '_giahsa'

print("Inicio de algoritmo")

# Conectamos la base de datos
conexion = FisotecBaseDatos.conectarBaseDatos()

# Datos de ejecución 6=ENERGY, 9=WATER, 11=GIAHSA
modulo = 9

# Datos extraccion
usuario = 'jsanchez'
fecha_inicio = '2026-02-02' # Adaptar a codificacion
fecha_final = '2026-02-06' # Adaptar a codificacion

# Obtenemos los proyecto
consulta_proyectos = u"""
        SELECT 
            id_proyecto,
            nombre,
            administracion.fisotec_formatear(nombre) as nombre_formateado,
            proyeccion
        FROM administracion.proyecto as proy
        WHERE (
            SELECT count(*)
            from administracion.proyecto_grupo as pg
            LEFT JOIN administracion.grupo as gr ON pg.grupo = gr.id_grupo
            WHERE pg.proyecto = proy.id_proyecto
            AND gr.modulo = {MODULO}
        ) > 0 
        ORDER BY nombre ASC
    """.format(MODULO=modulo)

resultado_consulta_proyectos = FisotecBaseDatos.consultaSQL(conexion, consulta_proyectos)

# Recorremos los proyectos
for proyecto in resultado_consulta_proyectos:
    print("Proyecto: {PROYECTO}".format(PROYECTO=proyecto['nombre']))

    # Definimos el nombre del proyecto dependiendo del modulo
    nombre_proyecto = obtener_nombre_esquema(proyecto['nombre_formateado'], modulo)

    print(nombre_proyecto)

    # Aquí ira todo

# Cerramos la conexion a la base de datos
FisotecBaseDatos.cerrarBaseDatos(conexion)

print("Terminamos el algoritmo")