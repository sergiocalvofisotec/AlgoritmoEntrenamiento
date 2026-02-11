#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Importaciones
from fisotec_basedatos import FisotecBaseDatos
from fisotec_utils import FisotecUtils

print("Inicio de algoritmo")

# Conectamos la base de datos
conexion = FisotecBaseDatos.conectarBaseDatos()

# Datos de ejecución 6=ENERGY, 9=WATER, 11=GIAHSA
modulo = 9

# Datos extraccion
usuario = 'jsanchez'
fecha_inicio = '1990-01-01' # Adaptar a codificacion
fecha_final = '2020-12-31' # Adaptar a codificacion

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

for proyecto in resultado_consulta_proyectos:
    print("Proyecto: {PROYECTO}".format(PROYECTO=proyecto['nombre']))
    print(proyecto)

    # Aquí ira todo

# Cerramos la conexion a la base de datos
FisotecBaseDatos.cerrarBaseDatos(conexion)

print("Terminamos el algoritmo")