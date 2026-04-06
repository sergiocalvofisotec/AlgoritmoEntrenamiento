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
modulo = 6

# Datos extraccion
usuario = 'aortega'
fecha_inicio = '2020-01-01' # Adaptar a codificacion
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
consulta_crear_tabla = u"""
        CREATE SCHEMA IF NOT EXISTS "0_historial";

        CREATE TABLE IF NOT EXISTS "0_historial".{USUARIO}
        (
            id bigserial,
            proyecto text COLLATE pg_catalog."default",
            capa text COLLATE pg_catalog."default",
            elemento text COLLATE pg_catalog."default",
            fecha_ult timestamp without time zone,
            usuario_evento text COLLATE pg_catalog."default",
            tipo_operacion text COLLATE pg_catalog."default",
            operacion text COLLATE pg_catalog."default",
            geom geometry,
            CONSTRAINT {USUARIO}_id_pkey PRIMARY KEY (id)
        )
        WITH (
            OIDS = FALSE
        )
        TABLESPACE pg_default;
        
        ALTER TABLE IF EXISTS "0_historial".{USUARIO}
            OWNER to postgres;
    """.format(USUARIO=usuario)

# Recorremos los proyectos
if modulo == 9:
    print("Water proyect")
    for proyecto in resultado_consulta_proyectos:
        print("Proyecto: {PROYECTO}".format(PROYECTO=proyecto['nombre']))

        # Definimos el nombre del proyecto dependiendo del modulo
        nombre_proy = obtener_nombre_esquema(proyecto['nombre_formateado'], modulo)

        print(nombre_proy)

        # Aquí ira todo

        #Se crea la tabla con el usuario


                

        FisotecBaseDatos.consultaSQL(conexion, consulta_crear_tabla)
        #Se obtienen los historiales unificados y se insertan en la tabla

        consulta_historial_agrupado = u"""
        INSERT INTO "0_historial".{USUARIO} (proyecto, capa, elemento, fecha_ult, usuario_evento, tipo_operacion, operacion, geom)
        SELECT DISTINCT
            '{NOMBRE_PROY}'::text as proyecto,
            capa,
            elemento,
            fecha_ult,
            usuario_evento,
            tipo_operacion,
            operacion,
            geom
        FROM (
            (
                SELECT 
                    'acometidas' as capa,
                    h.id_acometidas as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_acometidas h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'acometidas' as capa,
                    h.id_acometidas as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_acometidas h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'bocas_de_riego' as capa,
                    h.id_bocas_de_riego as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_bocas_de_riego h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'bocas_de_riego' as capa,
                    h.id_bocas_de_riego as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_bocas_de_riego h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'contador_red' as capa,
                    h.id_contador_red as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_contador_red h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'contador_red' as capa,
                    h.id_contador_red as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_contador_red h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'distribucion_principal' as capa,
                    h.id_distribucion_principal as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_distribucion_principal h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'distribucion_principal' as capa,
                    h.id_distribucion_principal as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_distribucion_principal h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'estructuras_red' as capa,
                    h.id_estructuras_red as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_estructuras_red h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'estructuras_red' as capa,
                    h.id_estructuras_red as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_estructuras_red h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'fuentes' as capa,
                    h.id_fuentes as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_fuentes h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'fuentes' as capa,
                    h.id_fuentes as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_fuentes h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'hidrantes' as capa,
                    h.id_hidrantes as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_hidrantes h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'hidrantes' as capa,
                    h.id_hidrantes as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_hidrantes h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'juntas' as capa,
                    h.id_juntas as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_juntas h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'juntas' as capa,
                    h.id_juntas as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_juntas h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'llaves_valvulas' as capa,
                    h.id_llaves_valvulas as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_llaves_valvulas h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'llaves_valvulas' as capa,
                    h.id_llaves_valvulas as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_llaves_valvulas h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'valvulas_control' as capa,
                    h.id_valvulas_control as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_valvulas_control h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'valvulas_control' as capa,
                    h.id_valvulas_control as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_valvulas_control h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'valvulas_sistema' as capa,
                    h.id_valvulas_sistema as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_valvulas_sistema h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'valvulas_sistema' as capa,
                    h.id_valvulas_sistema as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_abastecimiento_valvulas_sistema h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abas_adjunto' as capa,
                    h.id_adjunto as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(gh_0.geom, gh_1.geom, gh_2.geom, gh_3.geom, gh_4.geom, gh_5.geom, gh_6.geom, gh_7.geom, gh_8.geom, gh_9.geom, gh_10.geom) AS geom
                FROM {PROYECTO}.historial_abastecimiento_adjunto h
                LEFT JOIN (SELECT DISTINCT ON (id_acometidas) id_acometidas, geom FROM {PROYECTO}.historial_abastecimiento_acometidas WHERE geom IS NOT NULL ORDER BY id_acometidas, fecha_modificado DESC NULLS LAST) gh_0 ON h.tipo = 'acometidas' AND h.elemento = gh_0.id_acometidas
                LEFT JOIN (SELECT DISTINCT ON (id_bocas_de_riego) id_bocas_de_riego, geom FROM {PROYECTO}.historial_abastecimiento_bocas_de_riego WHERE geom IS NOT NULL ORDER BY id_bocas_de_riego, fecha_modificado DESC NULLS LAST) gh_1 ON h.tipo = 'bocas_de_riego' AND h.elemento = gh_1.id_bocas_de_riego
                LEFT JOIN (SELECT DISTINCT ON (id_contador_red) id_contador_red, geom FROM {PROYECTO}.historial_abastecimiento_contador_red WHERE geom IS NOT NULL ORDER BY id_contador_red, fecha_modificado DESC NULLS LAST) gh_2 ON h.tipo = 'contador_red' AND h.elemento = gh_2.id_contador_red
                LEFT JOIN (SELECT DISTINCT ON (id_distribucion_principal) id_distribucion_principal, geom FROM {PROYECTO}.historial_abastecimiento_distribucion_principal WHERE geom IS NOT NULL ORDER BY id_distribucion_principal, fecha_modificado DESC NULLS LAST) gh_3 ON h.tipo = 'distribucion_principal' AND h.elemento = gh_3.id_distribucion_principal
                LEFT JOIN (SELECT DISTINCT ON (id_estructuras_red) id_estructuras_red, geom FROM {PROYECTO}.historial_abastecimiento_estructuras_red WHERE geom IS NOT NULL ORDER BY id_estructuras_red, fecha_modificado DESC NULLS LAST) gh_4 ON h.tipo = 'estructuras_red' AND h.elemento = gh_4.id_estructuras_red
                LEFT JOIN (SELECT DISTINCT ON (id_fuentes) id_fuentes, geom FROM {PROYECTO}.historial_abastecimiento_fuentes WHERE geom IS NOT NULL ORDER BY id_fuentes, fecha_modificado DESC NULLS LAST) gh_5 ON h.tipo = 'fuentes' AND h.elemento = gh_5.id_fuentes
                LEFT JOIN (SELECT DISTINCT ON (id_hidrantes) id_hidrantes, geom FROM {PROYECTO}.historial_abastecimiento_hidrantes WHERE geom IS NOT NULL ORDER BY id_hidrantes, fecha_modificado DESC NULLS LAST) gh_6 ON h.tipo = 'hidrantes' AND h.elemento = gh_6.id_hidrantes
                LEFT JOIN (SELECT DISTINCT ON (id_juntas) id_juntas, geom FROM {PROYECTO}.historial_abastecimiento_juntas WHERE geom IS NOT NULL ORDER BY id_juntas, fecha_modificado DESC NULLS LAST) gh_7 ON h.tipo = 'juntas' AND h.elemento = gh_7.id_juntas
                LEFT JOIN (SELECT DISTINCT ON (id_llaves_valvulas) id_llaves_valvulas, geom FROM {PROYECTO}.historial_abastecimiento_llaves_valvulas WHERE geom IS NOT NULL ORDER BY id_llaves_valvulas, fecha_modificado DESC NULLS LAST) gh_8 ON h.tipo = 'llaves_valvulas' AND h.elemento = gh_8.id_llaves_valvulas
                LEFT JOIN (SELECT DISTINCT ON (id_valvulas_control) id_valvulas_control, geom FROM {PROYECTO}.historial_abastecimiento_valvulas_control WHERE geom IS NOT NULL ORDER BY id_valvulas_control, fecha_modificado DESC NULLS LAST) gh_9 ON h.tipo = 'valvulas_control' AND h.elemento = gh_9.id_valvulas_control
                LEFT JOIN (SELECT DISTINCT ON (id_valvulas_sistema) id_valvulas_sistema, geom FROM {PROYECTO}.historial_abastecimiento_valvulas_sistema WHERE geom IS NOT NULL ORDER BY id_valvulas_sistema, fecha_modificado DESC NULLS LAST) gh_10 ON h.tipo = 'valvulas_sistema' AND h.elemento = gh_10.id_valvulas_sistema
                WHERE h.fecha_modificado IS NOT NULL
            )
            UNION ALL
            (
                SELECT 
                    'abas_adjunto' as capa,
                    h.id_adjunto as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(gh_0.geom, gh_1.geom, gh_2.geom, gh_3.geom, gh_4.geom, gh_5.geom, gh_6.geom, gh_7.geom, gh_8.geom, gh_9.geom, gh_10.geom) AS geom
                FROM {PROYECTO}.historial_abastecimiento_adjunto h
                LEFT JOIN (SELECT DISTINCT ON (id_acometidas) id_acometidas, geom FROM {PROYECTO}.historial_abastecimiento_acometidas WHERE geom IS NOT NULL ORDER BY id_acometidas, fecha_modificado DESC NULLS LAST) gh_0 ON h.tipo = 'acometidas' AND h.elemento = gh_0.id_acometidas
                LEFT JOIN (SELECT DISTINCT ON (id_bocas_de_riego) id_bocas_de_riego, geom FROM {PROYECTO}.historial_abastecimiento_bocas_de_riego WHERE geom IS NOT NULL ORDER BY id_bocas_de_riego, fecha_modificado DESC NULLS LAST) gh_1 ON h.tipo = 'bocas_de_riego' AND h.elemento = gh_1.id_bocas_de_riego
                LEFT JOIN (SELECT DISTINCT ON (id_contador_red) id_contador_red, geom FROM {PROYECTO}.historial_abastecimiento_contador_red WHERE geom IS NOT NULL ORDER BY id_contador_red, fecha_modificado DESC NULLS LAST) gh_2 ON h.tipo = 'contador_red' AND h.elemento = gh_2.id_contador_red
                LEFT JOIN (SELECT DISTINCT ON (id_distribucion_principal) id_distribucion_principal, geom FROM {PROYECTO}.historial_abastecimiento_distribucion_principal WHERE geom IS NOT NULL ORDER BY id_distribucion_principal, fecha_modificado DESC NULLS LAST) gh_3 ON h.tipo = 'distribucion_principal' AND h.elemento = gh_3.id_distribucion_principal
                LEFT JOIN (SELECT DISTINCT ON (id_estructuras_red) id_estructuras_red, geom FROM {PROYECTO}.historial_abastecimiento_estructuras_red WHERE geom IS NOT NULL ORDER BY id_estructuras_red, fecha_modificado DESC NULLS LAST) gh_4 ON h.tipo = 'estructuras_red' AND h.elemento = gh_4.id_estructuras_red
                LEFT JOIN (SELECT DISTINCT ON (id_fuentes) id_fuentes, geom FROM {PROYECTO}.historial_abastecimiento_fuentes WHERE geom IS NOT NULL ORDER BY id_fuentes, fecha_modificado DESC NULLS LAST) gh_5 ON h.tipo = 'fuentes' AND h.elemento = gh_5.id_fuentes
                LEFT JOIN (SELECT DISTINCT ON (id_hidrantes) id_hidrantes, geom FROM {PROYECTO}.historial_abastecimiento_hidrantes WHERE geom IS NOT NULL ORDER BY id_hidrantes, fecha_modificado DESC NULLS LAST) gh_6 ON h.tipo = 'hidrantes' AND h.elemento = gh_6.id_hidrantes
                LEFT JOIN (SELECT DISTINCT ON (id_juntas) id_juntas, geom FROM {PROYECTO}.historial_abastecimiento_juntas WHERE geom IS NOT NULL ORDER BY id_juntas, fecha_modificado DESC NULLS LAST) gh_7 ON h.tipo = 'juntas' AND h.elemento = gh_7.id_juntas
                LEFT JOIN (SELECT DISTINCT ON (id_llaves_valvulas) id_llaves_valvulas, geom FROM {PROYECTO}.historial_abastecimiento_llaves_valvulas WHERE geom IS NOT NULL ORDER BY id_llaves_valvulas, fecha_modificado DESC NULLS LAST) gh_8 ON h.tipo = 'llaves_valvulas' AND h.elemento = gh_8.id_llaves_valvulas
                LEFT JOIN (SELECT DISTINCT ON (id_valvulas_control) id_valvulas_control, geom FROM {PROYECTO}.historial_abastecimiento_valvulas_control WHERE geom IS NOT NULL ORDER BY id_valvulas_control, fecha_modificado DESC NULLS LAST) gh_9 ON h.tipo = 'valvulas_control' AND h.elemento = gh_9.id_valvulas_control
                LEFT JOIN (SELECT DISTINCT ON (id_valvulas_sistema) id_valvulas_sistema, geom FROM {PROYECTO}.historial_abastecimiento_valvulas_sistema WHERE geom IS NOT NULL ORDER BY id_valvulas_sistema, fecha_modificado DESC NULLS LAST) gh_10 ON h.tipo = 'valvulas_sistema' AND h.elemento = gh_10.id_valvulas_sistema
                WHERE h.fecha_alta IS NOT NULL
            )
            UNION ALL
            (
                SELECT 
                    'acometida_saneamiento' as capa,
                    h.id_acometida_saneamiento as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_acometida_saneamiento h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'acometida_saneamiento' as capa,
                    h.id_acometida_saneamiento as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_acometida_saneamiento h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'estructuras_red_saneamiento' as capa,
                    h.id_estructuras_red_saneamiento as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_estructuras_red_saneamiento h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'estructuras_red_saneamiento' as capa,
                    h.id_estructuras_red_saneamiento as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_estructuras_red_saneamiento h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'imbornal' as capa,
                    h.id_imbornal as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_imbornal h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'imbornal' as capa,
                    h.id_imbornal as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_imbornal h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'juntas_saneamiento' as capa,
                    h.id_juntas_saneamiento as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_juntas_saneamiento h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'juntas_saneamiento' as capa,
                    h.id_juntas_saneamiento as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_juntas_saneamiento h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'pozos' as capa,
                    h.id_pozos as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_pozos h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'pozos' as capa,
                    h.id_pozos as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_pozos h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'ramal_de_pozo' as capa,
                    h.id_ramal_de_pozo as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_ramal_de_pozo h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'ramal_de_pozo' as capa,
                    h.id_ramal_de_pozo as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_ramal_de_pozo h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'registro_acometida' as capa,
                    h.id_registro_acometida as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_registro_acometida h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'registro_acometida' as capa,
                    h.id_registro_acometida as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_registro_acometida h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'servicio_saneamiento' as capa,
                    h.id_servicio_saneamiento as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_servicio_saneamiento h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'servicio_saneamiento' as capa,
                    h.id_servicio_saneamiento as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_servicio_saneamiento h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'tuberia_gravedad_saneamiento' as capa,
                    h.id_tuberia_gravedad_saneamiento as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_tuberia_gravedad_saneamiento h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'tuberia_gravedad_saneamiento' as capa,
                    h.id_tuberia_gravedad_saneamiento as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_saneamiento_tuberia_gravedad_saneamiento h
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'san_adjunto' as capa,
                    h.id_adjunto as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(gh_0.geom, gh_1.geom, gh_2.geom, gh_3.geom, gh_4.geom, gh_5.geom, gh_6.geom, gh_7.geom, gh_8.geom) AS geom
                FROM {PROYECTO}.historial_saneamiento_adjunto h
                LEFT JOIN (SELECT DISTINCT ON (id_acometida_saneamiento) id_acometida_saneamiento, geom FROM {PROYECTO}.historial_saneamiento_acometida_saneamiento WHERE geom IS NOT NULL ORDER BY id_acometida_saneamiento, fecha_modificado DESC NULLS LAST) gh_0 ON h.tipo = 'acometida_saneamiento' AND h.elemento = gh_0.id_acometida_saneamiento
                LEFT JOIN (SELECT DISTINCT ON (id_estructuras_red_saneamiento) id_estructuras_red_saneamiento, geom FROM {PROYECTO}.historial_saneamiento_estructuras_red_saneamiento WHERE geom IS NOT NULL ORDER BY id_estructuras_red_saneamiento, fecha_modificado DESC NULLS LAST) gh_1 ON h.tipo = 'estructuras_red_saneamiento' AND h.elemento = gh_1.id_estructuras_red_saneamiento
                LEFT JOIN (SELECT DISTINCT ON (id_imbornal) id_imbornal, geom FROM {PROYECTO}.historial_saneamiento_imbornal WHERE geom IS NOT NULL ORDER BY id_imbornal, fecha_modificado DESC NULLS LAST) gh_2 ON h.tipo = 'imbornal' AND h.elemento = gh_2.id_imbornal
                LEFT JOIN (SELECT DISTINCT ON (id_juntas_saneamiento) id_juntas_saneamiento, geom FROM {PROYECTO}.historial_saneamiento_juntas_saneamiento WHERE geom IS NOT NULL ORDER BY id_juntas_saneamiento, fecha_modificado DESC NULLS LAST) gh_3 ON h.tipo = 'juntas_saneamiento' AND h.elemento = gh_3.id_juntas_saneamiento
                LEFT JOIN (SELECT DISTINCT ON (id_pozos) id_pozos, geom FROM {PROYECTO}.historial_saneamiento_pozos WHERE geom IS NOT NULL ORDER BY id_pozos, fecha_modificado DESC NULLS LAST) gh_4 ON h.tipo = 'pozos' AND h.elemento = gh_4.id_pozos
                LEFT JOIN (SELECT DISTINCT ON (id_ramal_de_pozo) id_ramal_de_pozo, geom FROM {PROYECTO}.historial_saneamiento_ramal_de_pozo WHERE geom IS NOT NULL ORDER BY id_ramal_de_pozo, fecha_modificado DESC NULLS LAST) gh_5 ON h.tipo = 'ramal_de_pozo' AND h.elemento = gh_5.id_ramal_de_pozo
                LEFT JOIN (SELECT DISTINCT ON (id_registro_acometida) id_registro_acometida, geom FROM {PROYECTO}.historial_saneamiento_registro_acometida WHERE geom IS NOT NULL ORDER BY id_registro_acometida, fecha_modificado DESC NULLS LAST) gh_6 ON h.tipo = 'registro_acometida' AND h.elemento = gh_6.id_registro_acometida
                LEFT JOIN (SELECT DISTINCT ON (id_servicio_saneamiento) id_servicio_saneamiento, geom FROM {PROYECTO}.historial_saneamiento_servicio_saneamiento WHERE geom IS NOT NULL ORDER BY id_servicio_saneamiento, fecha_modificado DESC NULLS LAST) gh_7 ON h.tipo = 'servicio_saneamiento' AND h.elemento = gh_7.id_servicio_saneamiento
                LEFT JOIN (SELECT DISTINCT ON (id_tuberia_gravedad_saneamiento) id_tuberia_gravedad_saneamiento, geom FROM {PROYECTO}.historial_saneamiento_tuberia_gravedad_saneamiento WHERE geom IS NOT NULL ORDER BY id_tuberia_gravedad_saneamiento, fecha_modificado DESC NULLS LAST) gh_8 ON h.tipo = 'tuberia_gravedad_saneamiento' AND h.elemento = gh_8.id_tuberia_gravedad_saneamiento
                WHERE h.fecha_modificado IS NOT NULL
            )
            UNION ALL
            (
                SELECT 
                    'san_adjunto' as capa,
                    h.id_adjunto as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(gh_0.geom, gh_1.geom, gh_2.geom, gh_3.geom, gh_4.geom, gh_5.geom, gh_6.geom, gh_7.geom, gh_8.geom) AS geom
                FROM {PROYECTO}.historial_saneamiento_adjunto h
                LEFT JOIN (SELECT DISTINCT ON (id_acometida_saneamiento) id_acometida_saneamiento, geom FROM {PROYECTO}.historial_saneamiento_acometida_saneamiento WHERE geom IS NOT NULL ORDER BY id_acometida_saneamiento, fecha_modificado DESC NULLS LAST) gh_0 ON h.tipo = 'acometida_saneamiento' AND h.elemento = gh_0.id_acometida_saneamiento
                LEFT JOIN (SELECT DISTINCT ON (id_estructuras_red_saneamiento) id_estructuras_red_saneamiento, geom FROM {PROYECTO}.historial_saneamiento_estructuras_red_saneamiento WHERE geom IS NOT NULL ORDER BY id_estructuras_red_saneamiento, fecha_modificado DESC NULLS LAST) gh_1 ON h.tipo = 'estructuras_red_saneamiento' AND h.elemento = gh_1.id_estructuras_red_saneamiento
                LEFT JOIN (SELECT DISTINCT ON (id_imbornal) id_imbornal, geom FROM {PROYECTO}.historial_saneamiento_imbornal WHERE geom IS NOT NULL ORDER BY id_imbornal, fecha_modificado DESC NULLS LAST) gh_2 ON h.tipo = 'imbornal' AND h.elemento = gh_2.id_imbornal
                LEFT JOIN (SELECT DISTINCT ON (id_juntas_saneamiento) id_juntas_saneamiento, geom FROM {PROYECTO}.historial_saneamiento_juntas_saneamiento WHERE geom IS NOT NULL ORDER BY id_juntas_saneamiento, fecha_modificado DESC NULLS LAST) gh_3 ON h.tipo = 'juntas_saneamiento' AND h.elemento = gh_3.id_juntas_saneamiento
                LEFT JOIN (SELECT DISTINCT ON (id_pozos) id_pozos, geom FROM {PROYECTO}.historial_saneamiento_pozos WHERE geom IS NOT NULL ORDER BY id_pozos, fecha_modificado DESC NULLS LAST) gh_4 ON h.tipo = 'pozos' AND h.elemento = gh_4.id_pozos
                LEFT JOIN (SELECT DISTINCT ON (id_ramal_de_pozo) id_ramal_de_pozo, geom FROM {PROYECTO}.historial_saneamiento_ramal_de_pozo WHERE geom IS NOT NULL ORDER BY id_ramal_de_pozo, fecha_modificado DESC NULLS LAST) gh_5 ON h.tipo = 'ramal_de_pozo' AND h.elemento = gh_5.id_ramal_de_pozo
                LEFT JOIN (SELECT DISTINCT ON (id_registro_acometida) id_registro_acometida, geom FROM {PROYECTO}.historial_saneamiento_registro_acometida WHERE geom IS NOT NULL ORDER BY id_registro_acometida, fecha_modificado DESC NULLS LAST) gh_6 ON h.tipo = 'registro_acometida' AND h.elemento = gh_6.id_registro_acometida
                LEFT JOIN (SELECT DISTINCT ON (id_servicio_saneamiento) id_servicio_saneamiento, geom FROM {PROYECTO}.historial_saneamiento_servicio_saneamiento WHERE geom IS NOT NULL ORDER BY id_servicio_saneamiento, fecha_modificado DESC NULLS LAST) gh_7 ON h.tipo = 'servicio_saneamiento' AND h.elemento = gh_7.id_servicio_saneamiento
                LEFT JOIN (SELECT DISTINCT ON (id_tuberia_gravedad_saneamiento) id_tuberia_gravedad_saneamiento, geom FROM {PROYECTO}.historial_saneamiento_tuberia_gravedad_saneamiento WHERE geom IS NOT NULL ORDER BY id_tuberia_gravedad_saneamiento, fecha_modificado DESC NULLS LAST) gh_8 ON h.tipo = 'tuberia_gravedad_saneamiento' AND h.elemento = gh_8.id_tuberia_gravedad_saneamiento
                WHERE h.fecha_alta IS NOT NULL
            )    ) AS eventos
        WHERE usuario_evento = '{USUARIO}'
        AND fecha_ult BETWEEN '{FECHA_INICIO}' AND '{FECHA_FINAL}'
        GROUP BY capa, elemento, fecha_ult, usuario_evento, tipo_operacion, operacion, geom
        ORDER BY fecha_ult DESC;
        """.format(PROYECTO=nombre_proy, USUARIO=usuario, FECHA_INICIO=fecha_inicio, FECHA_FINAL=fecha_final, NOMBRE_PROY=proyecto['nombre'])

        # Ejecutamos la insercion directa
        FisotecBaseDatos.consultaSQL(conexion, consulta_historial_agrupado)
        print("Datos insertados para " + proyecto['nombre'])
elif modulo == 6:
    print("Energy proyect")
    for proyecto in resultado_consulta_proyectos:


        print("Proyecto: {PROYECTO}".format(PROYECTO=proyecto['nombre']))

        # Definimos el nombre del proyecto dependiendo del modulo
        nombre_proy = obtener_nombre_esquema(proyecto['nombre_formateado'], modulo)

        print(nombre_proy)

        # Aquí ira todo

        #Se crea la tabla con el usuario


                

        FisotecBaseDatos.consultaSQL(conexion, consulta_crear_tabla)
        #Se obtienen los historiales unificados y se insertan en la tabla

        consulta_historial_agrupado = u"""
        INSERT INTO "0_historial".{USUARIO} (proyecto, capa, elemento, fecha_ult, usuario_evento, tipo_operacion, operacion, geom)
        -- CREATE TABLE {PROYECTO}.prueba_historial AS
        SELECT DISTINCT
            '{NOMBRE_PROY}'::text as proyecto,
            capa,
            elemento,
            fecha_ult,
            usuario_evento,
            tipo_operacion,
            operacion,
            geom
        FROM (
            (
                SELECT 
                    'luminaria' as capa,
                    h.id_luminaria as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_gestlighting_luminaria h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'adjunto' as capa,
                    h.id_adjunto as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(lum.geom, cm.geom, mm.geom) AS geom
                FROM {PROYECTO}.historial_gestlighting_adjunto h
                LEFT JOIN {PROYECTO}.gestlighting_luminaria lum ON h.tipo = 'luminaria' AND h.elemento = lum.id_luminaria
                LEFT JOIN {PROYECTO}.gestlighting_centro_mando cm ON h.tipo = 'centro_mando' AND h.elemento = cm.id_centro_mando
                LEFT JOIN {PROYECTO}.gestlighting_modulo_medida mm ON h.tipo = 'modulo_medida' AND h.elemento = mm.id_modulo_medida
                WHERE h.fecha_modificado IS NOT NULL
            )
            UNION ALL
            (
                SELECT 
                    'caja_proteccion' as capa,
                    h.id_caja_proteccion as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    cm.geom AS geom
                FROM {PROYECTO}.historial_gestlighting_caja_proteccion h
                LEFT JOIN {PROYECTO}.gestlighting_centro_mando cm ON h.centro_mando = cm.id_centro_mando
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'caja_proteccion' as capa,
                    h.id_caja_proteccion as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    cm.geom AS geom
                FROM {PROYECTO}.historial_gestlighting_caja_proteccion h
                LEFT JOIN {PROYECTO}.gestlighting_centro_mando cm ON h.centro_mando = cm.id_centro_mando
                WHERE (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'centro_mando' as capa,
                    h.id_centro_mando as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_gestlighting_centro_mando h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'circuito' as capa,
                    h.id_circuito as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    cm.geom AS geom
                FROM {PROYECTO}.historial_gestlighting_circuito h
                LEFT JOIN {PROYECTO}.gestlighting_centro_mando cm ON h.centro_mando = cm.id_centro_mando
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'circuito' as capa,
                    h.id_circuito as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    cm.geom AS geom
                FROM {PROYECTO}.historial_gestlighting_circuito h
                LEFT JOIN {PROYECTO}.gestlighting_centro_mando cm ON h.centro_mando = cm.id_centro_mando
                WHERE (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'estado_centro_mando' as capa,
                    h.id_estado_centro_mando as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_gestlighting_estado_centro_mando h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'estado_luminaria' as capa,
                    h.id_estado_luminaria as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_gestlighting_estado_luminaria h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'foto_alumbrado' as capa,
                    h.id_foto_alumbrado as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_gestlighting_foto_alumbrado h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'foto_alumbrado' as capa,
                    h.id_foto_alumbrado as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_gestlighting_foto_alumbrado h
                WHERE (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'medicion_centro_mando' as capa,
                    h.id_medicion_centro_mando as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    cm.geom AS geom
                FROM {PROYECTO}.historial_gestlighting_medicion_centro_mando h
                LEFT JOIN {PROYECTO}.gestlighting_centro_mando cm ON h.centro_mando = cm.id_centro_mando
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'medicion_centro_mando' as capa,
                    h.id_medicion_centro_mando as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    cm.geom AS geom
                FROM {PROYECTO}.historial_gestlighting_medicion_centro_mando h
                LEFT JOIN {PROYECTO}.gestlighting_centro_mando cm ON h.centro_mando = cm.id_centro_mando
                WHERE (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'medicion_circuito' as capa,
                    h.id_medicion_circuito as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    cm.geom AS geom
                FROM {PROYECTO}.historial_gestlighting_medicion_circuito h
                LEFT JOIN {PROYECTO}.gestlighting_circuito cir ON h.circuito = cir.id_circuito
                LEFT JOIN {PROYECTO}.gestlighting_centro_mando cm ON cir.centro_mando = cm.id_centro_mando
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'medicion_circuito' as capa,
                    h.id_medicion_circuito as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    cm.geom AS geom
                FROM {PROYECTO}.historial_gestlighting_medicion_circuito h
                LEFT JOIN {PROYECTO}.gestlighting_circuito cir ON h.circuito = cir.id_circuito
                LEFT JOIN {PROYECTO}.gestlighting_centro_mando cm ON cir.centro_mando = cm.id_centro_mando
                WHERE (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'modulo_medida' as capa,
                    h.id_modulo_medida as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_gestlighting_modulo_medida h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'modulo_medida' as capa,
                    h.id_modulo_medida as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_gestlighting_modulo_medida h
                WHERE (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'proteccion_centro_mando' as capa,
                    h.id_proteccion_centro_mando as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    cm.geom AS geom
                FROM {PROYECTO}.historial_gestlighting_proteccion_centro_mando h
                LEFT JOIN {PROYECTO}.gestlighting_centro_mando cm ON h.centro_mando = cm.id_centro_mando
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'proteccion_centro_mando' as capa,
                    h.id_proteccion_centro_mando as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    cm.geom AS geom
                FROM {PROYECTO}.historial_gestlighting_proteccion_centro_mando h
                LEFT JOIN {PROYECTO}.gestlighting_centro_mando cm ON h.centro_mando = cm.id_centro_mando
                WHERE (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'proteccion_circuito' as capa,
                    h.id_proteccion_circuito as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    cm.geom AS geom
                FROM {PROYECTO}.historial_gestlighting_proteccion_circuito h
                LEFT JOIN {PROYECTO}.gestlighting_circuito cir ON h.circuito = cir.id_circuito
                LEFT JOIN {PROYECTO}.gestlighting_centro_mando cm ON cir.centro_mando = cm.id_centro_mando
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'proteccion_circuito' as capa,
                    h.id_proteccion_circuito as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    cm.geom AS geom
                FROM {PROYECTO}.historial_gestlighting_proteccion_circuito h
                LEFT JOIN {PROYECTO}.gestlighting_circuito cir ON h.circuito = cir.id_circuito
                LEFT JOIN {PROYECTO}.gestlighting_centro_mando cm ON cir.centro_mando = cm.id_centro_mando
                WHERE (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'puesta_tierra' as capa,
                    h.id_puesta_tierra as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    cm.geom AS geom
                FROM {PROYECTO}.historial_gestlighting_puesta_tierra h
                LEFT JOIN {PROYECTO}.gestlighting_centro_mando cm ON h.centro_mando = cm.id_centro_mando
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'puesta_tierra' as capa,
                    h.id_puesta_tierra as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    cm.geom AS geom
                FROM {PROYECTO}.historial_gestlighting_puesta_tierra h
                LEFT JOIN {PROYECTO}.gestlighting_centro_mando cm ON h.centro_mando = cm.id_centro_mando
                WHERE (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'punto_luz' as capa,
                    h.id_punto_luz as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_gestlighting_punto_luz h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'punto_luz' as capa,
                    h.id_punto_luz as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_gestlighting_punto_luz h
                WHERE (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'zona' as capa,
                    h.id_zona as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_gestlighting_zona h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'zona' as capa,
                    h.id_zona as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_gestlighting_zona h
                WHERE (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'base_vial' as capa,
                    h.id_vial as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_base_vial h
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'base_vial' as capa,
                    h.id_vial as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    h.geom
                FROM {PROYECTO}.historial_base_vial h
                WHERE (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )            
        ) AS eventos
        GROUP BY capa, elemento, fecha_ult, usuario_evento, tipo_operacion, operacion, geom
        ORDER BY fecha_ult DESC;
        """.format(PROYECTO=nombre_proy, USUARIO=usuario, FECHA_INICIO=fecha_inicio, FECHA_FINAL=fecha_final, NOMBRE_PROY=proyecto['nombre'])

        # Ejecutamos la insercion directa
        FisotecBaseDatos.consultaSQL(conexion, consulta_historial_agrupado)
        print("Datos insertados para " + proyecto['nombre'])
    
elif modulo == 11:
    print("giahsa proyect")
    for proyecto in resultado_consulta_proyectos:


        print("Proyecto: {PROYECTO}".format(PROYECTO=proyecto['nombre']))

        # Definimos el nombre del proyecto dependiendo del modulo
        nombre_proy = obtener_nombre_esquema(proyecto['nombre_formateado'], modulo)

        print(nombre_proy)

        # Aquí ira todo

        #Se crea la tabla con el usuario


                

        FisotecBaseDatos.consultaSQL(conexion, consulta_crear_tabla)
        #Se obtienen los historiales unificados y se insertan en la tabla

        consulta_historial_agrupado = u"""
        INSERT INTO "0_historial".{USUARIO} (proyecto, capa, elemento, fecha_ult, usuario_evento, tipo_operacion, operacion, geom)
        -- CREATE TABLE {PROYECTO}.prueba_historial AS
        SELECT DISTINCT
            '{NOMBRE_PROY}'::text as proyecto,
            capa,
            elemento,
            fecha_ult,
            usuario_evento,
            tipo_operacion,
            operacion,
            geom
        FROM (
            (
                SELECT 
                    'abastecimiento_acometidas' as capa,
                    h.id_acometidas as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_acometidas h
                LEFT JOIN {PROYECTO}.abastecimiento_acometidas b ON h.id_acometidas = b.id_acometidas
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_acometidas' as capa,
                    h.id_acometidas as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_acometidas h
                LEFT JOIN {PROYECTO}.abastecimiento_acometidas b ON h.id_acometidas = b.id_acometidas
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_adjunto' as capa,
                    h.id_adjunto as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(b_valvulas_de_control.geom, b_hidrante.geom, b_valvulas_de_seccionamiento.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_adjunto h
                LEFT JOIN {PROYECTO}.abastecimiento_valvulas_de_control b_valvulas_de_control ON h.tipo = 'valvulas_de_control' AND h.elemento = b_valvulas_de_control.id_valvulas_de_control
                LEFT JOIN {PROYECTO}.abastecimiento_hidrante b_hidrante ON h.tipo = 'hidrante' AND h.elemento = b_hidrante.id_hidrante
                LEFT JOIN {PROYECTO}.abastecimiento_valvulas_de_seccionamiento b_valvulas_de_seccionamiento ON h.tipo = 'valvulas_de_seccionamiento' AND h.elemento = b_valvulas_de_seccionamiento.id_valvulas_de_seccionamiento
                WHERE h.fecha_modificado IS NOT NULL
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_elementos_singulares' as capa,
                    h.id_elementos_singulares as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_elementos_singulares h
                LEFT JOIN {PROYECTO}.abastecimiento_elementos_singulares b ON h.id_elementos_singulares = b.id_elementos_singulares
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_elementos_singulares' as capa,
                    h.id_elementos_singulares as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_elementos_singulares h
                LEFT JOIN {PROYECTO}.abastecimiento_elementos_singulares b ON h.id_elementos_singulares = b.id_elementos_singulares
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_estaciones_de_bombeo' as capa,
                    h.id_estaciones_de_bombeo as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_estaciones_de_bombeo h
                LEFT JOIN {PROYECTO}.abastecimiento_estaciones_de_bombeo b ON h.id_estaciones_de_bombeo = b.id_estaciones_de_bombeo
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_estaciones_de_bombeo' as capa,
                    h.id_estaciones_de_bombeo as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_estaciones_de_bombeo h
                LEFT JOIN {PROYECTO}.abastecimiento_estaciones_de_bombeo b ON h.id_estaciones_de_bombeo = b.id_estaciones_de_bombeo
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_estructuras_abastecimiento' as capa,
                    h.id_estructuras_abastecimiento as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_estructuras_abastecimiento h
                LEFT JOIN {PROYECTO}.abastecimiento_estructuras_abastecimiento b ON h.id_estructuras_abastecimiento = b.id_estructuras_abastecimiento
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_estructuras_abastecimiento' as capa,
                    h.id_estructuras_abastecimiento as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_estructuras_abastecimiento h
                LEFT JOIN {PROYECTO}.abastecimiento_estructuras_abastecimiento b ON h.id_estructuras_abastecimiento = b.id_estructuras_abastecimiento
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_hidrante' as capa,
                    h.id_hidrante as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_hidrante h
                LEFT JOIN {PROYECTO}.abastecimiento_hidrante b ON h.id_hidrante = b.id_hidrante
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_hidrante' as capa,
                    h.id_hidrante as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_hidrante h
                LEFT JOIN {PROYECTO}.abastecimiento_hidrante b ON h.id_hidrante = b.id_hidrante
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_linea_abandonada' as capa,
                    h.id_linea_abandonada as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_linea_abandonada h
                LEFT JOIN {PROYECTO}.abastecimiento_linea_abandonada b ON h.id_linea_abandonada = b.id_linea_abandonada
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_linea_abandonada' as capa,
                    h.id_linea_abandonada as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_linea_abandonada h
                LEFT JOIN {PROYECTO}.abastecimiento_linea_abandonada b ON h.id_linea_abandonada = b.id_linea_abandonada
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_llave_de_registro' as capa,
                    h.id_llave_de_registro as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_llave_de_registro h
                LEFT JOIN {PROYECTO}.abastecimiento_llave_de_registro b ON h.id_llave_de_registro = b.id_llave_de_registro
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_llave_de_registro' as capa,
                    h.id_llave_de_registro as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_llave_de_registro h
                LEFT JOIN {PROYECTO}.abastecimiento_llave_de_registro b ON h.id_llave_de_registro = b.id_llave_de_registro
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_pieza' as capa,
                    h.id_pieza as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_pieza h
                LEFT JOIN {PROYECTO}.abastecimiento_pieza b ON h.id_pieza = b.id_pieza
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_pieza' as capa,
                    h.id_pieza as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_pieza h
                LEFT JOIN {PROYECTO}.abastecimiento_pieza b ON h.id_pieza = b.id_pieza
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_punto_abandonado' as capa,
                    h.id_punto_abandonado as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_punto_abandonado h
                LEFT JOIN {PROYECTO}.abastecimiento_punto_abandonado b ON h.id_punto_abandonado = b.id_punto_abandonado
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_punto_abandonado' as capa,
                    h.id_punto_abandonado as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_punto_abandonado h
                LEFT JOIN {PROYECTO}.abastecimiento_punto_abandonado b ON h.id_punto_abandonado = b.id_punto_abandonado
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_punto_de_medida' as capa,
                    h.id_punto_de_medida as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_punto_de_medida h
                LEFT JOIN {PROYECTO}.abastecimiento_punto_de_medida b ON h.id_punto_de_medida = b.id_punto_de_medida
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_punto_de_medida' as capa,
                    h.id_punto_de_medida as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_punto_de_medida h
                LEFT JOIN {PROYECTO}.abastecimiento_punto_de_medida b ON h.id_punto_de_medida = b.id_punto_de_medida
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_puntos_de_muestreo' as capa,
                    h.id_puntos_de_muestreo as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_puntos_de_muestreo h
                LEFT JOIN {PROYECTO}.abastecimiento_puntos_de_muestreo b ON h.id_puntos_de_muestreo = b.id_puntos_de_muestreo
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_puntos_de_muestreo' as capa,
                    h.id_puntos_de_muestreo as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_puntos_de_muestreo h
                LEFT JOIN {PROYECTO}.abastecimiento_puntos_de_muestreo b ON h.id_puntos_de_muestreo = b.id_puntos_de_muestreo
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_ramal_de_abastecimiento' as capa,
                    h.id_ramal_de_abastecimiento as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_ramal_de_abastecimiento h
                LEFT JOIN {PROYECTO}.abastecimiento_ramal_de_abastecimiento b ON h.id_ramal_de_abastecimiento = b.id_ramal_de_abastecimiento
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_ramal_de_abastecimiento' as capa,
                    h.id_ramal_de_abastecimiento as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_ramal_de_abastecimiento h
                LEFT JOIN {PROYECTO}.abastecimiento_ramal_de_abastecimiento b ON h.id_ramal_de_abastecimiento = b.id_ramal_de_abastecimiento
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_resumen_de_la_red_con_trazas' as capa,
                    h.id_resumen_de_la_red_con_trazas as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_resumen_de_la_red_con_trazas h
                LEFT JOIN {PROYECTO}.abastecimiento_resumen_de_la_red_con_trazas b ON h.id_resumen_de_la_red_con_trazas = b.id_resumen_de_la_red_con_trazas
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_resumen_de_la_red_con_trazas' as capa,
                    h.id_resumen_de_la_red_con_trazas as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_resumen_de_la_red_con_trazas h
                LEFT JOIN {PROYECTO}.abastecimiento_resumen_de_la_red_con_trazas b ON h.id_resumen_de_la_red_con_trazas = b.id_resumen_de_la_red_con_trazas
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_tuberia' as capa,
                    h.id_tuberia as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_tuberia h
                LEFT JOIN {PROYECTO}.abastecimiento_tuberia b ON h.id_tuberia = b.id_tuberia
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_tuberia' as capa,
                    h.id_tuberia as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_tuberia h
                LEFT JOIN {PROYECTO}.abastecimiento_tuberia b ON h.id_tuberia = b.id_tuberia
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_tuberias_laterales' as capa,
                    h.id_tuberias_laterales as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_tuberias_laterales h
                LEFT JOIN {PROYECTO}.abastecimiento_tuberias_laterales b ON h.id_tuberias_laterales = b.id_tuberias_laterales
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_tuberias_laterales' as capa,
                    h.id_tuberias_laterales as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_tuberias_laterales h
                LEFT JOIN {PROYECTO}.abastecimiento_tuberias_laterales b ON h.id_tuberias_laterales = b.id_tuberias_laterales
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_valvulas_de_control' as capa,
                    h.id_valvulas_de_control as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_valvulas_de_control h
                LEFT JOIN {PROYECTO}.abastecimiento_valvulas_de_control b ON h.id_valvulas_de_control = b.id_valvulas_de_control
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_valvulas_de_control' as capa,
                    h.id_valvulas_de_control as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_valvulas_de_control h
                LEFT JOIN {PROYECTO}.abastecimiento_valvulas_de_control b ON h.id_valvulas_de_control = b.id_valvulas_de_control
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_valvulas_de_seccionamiento' as capa,
                    h.id_valvulas_de_seccionamiento as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_valvulas_de_seccionamiento h
                LEFT JOIN {PROYECTO}.abastecimiento_valvulas_de_seccionamiento b ON h.id_valvulas_de_seccionamiento = b.id_valvulas_de_seccionamiento
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_valvulas_de_seccionamiento' as capa,
                    h.id_valvulas_de_seccionamiento as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_valvulas_de_seccionamiento h
                LEFT JOIN {PROYECTO}.abastecimiento_valvulas_de_seccionamiento b ON h.id_valvulas_de_seccionamiento = b.id_valvulas_de_seccionamiento
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_zona_incidencia' as capa,
                    h.id_zona_incidencia as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_zona_incidencia h
                LEFT JOIN {PROYECTO}.abastecimiento_zona_incidencia b ON h.id_zona_incidencia = b.id_zona_incidencia
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_zona_incidencia' as capa,
                    h.id_zona_incidencia as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_zona_incidencia h
                LEFT JOIN {PROYECTO}.abastecimiento_zona_incidencia b ON h.id_zona_incidencia = b.id_zona_incidencia
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_zona_revision' as capa,
                    h.id_zona_revision as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_zona_revision h
                LEFT JOIN {PROYECTO}.abastecimiento_zona_revision b ON h.id_zona_revision = b.id_zona_revision
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'abastecimiento_zona_revision' as capa,
                    h.id_zona_revision as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_abastecimiento_zona_revision h
                LEFT JOIN {PROYECTO}.abastecimiento_zona_revision b ON h.id_zona_revision = b.id_zona_revision
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_acometida_saneamiento' as capa,
                    h.id_acometida_saneamiento as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_acometida_saneamiento h
                LEFT JOIN {PROYECTO}.saneamiento_acometida_saneamiento b ON h.id_acometida_saneamiento = b.id_acometida_saneamiento
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_acometida_saneamiento' as capa,
                    h.id_acometida_saneamiento as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_acometida_saneamiento h
                LEFT JOIN {PROYECTO}.saneamiento_acometida_saneamiento b ON h.id_acometida_saneamiento = b.id_acometida_saneamiento
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_adjunto' as capa,
                    h.id_adjunto as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(b_estructuras_de_red.geom, b_estacion_bombeo.geom, b_imbornal.geom, b_puntos_de_vertidos.geom, b_pozos.geom, b_acometida_saneamiento.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_adjunto h
                LEFT JOIN {PROYECTO}.saneamiento_estructuras_de_red b_estructuras_de_red ON h.tipo = 'estructuras_de_red' AND h.elemento = b_estructuras_de_red.id_estructuras_de_red
                LEFT JOIN {PROYECTO}.saneamiento_estacion_bombeo b_estacion_bombeo ON h.tipo = 'estacion_bombeo' AND h.elemento = b_estacion_bombeo.id_estacion_bombeo
                LEFT JOIN {PROYECTO}.saneamiento_imbornal b_imbornal ON h.tipo = 'imbornal' AND h.elemento = b_imbornal.id_imbornal
                LEFT JOIN {PROYECTO}.saneamiento_puntos_de_vertidos b_puntos_de_vertidos ON h.tipo = 'puntos_de_vertidos' AND h.elemento = b_puntos_de_vertidos.id_puntos_de_vertidos
                LEFT JOIN {PROYECTO}.saneamiento_pozos b_pozos ON h.tipo = 'pozos' AND h.elemento = b_pozos.id_pozos
                LEFT JOIN {PROYECTO}.saneamiento_acometida_saneamiento b_acometida_saneamiento ON h.tipo = 'acometida_saneamiento' AND h.elemento = b_acometida_saneamiento.id_acometida_saneamiento
                WHERE h.fecha_modificado IS NOT NULL
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_arqueta' as capa,
                    h.id_arqueta as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_arqueta h
                LEFT JOIN {PROYECTO}.saneamiento_arqueta b ON h.id_arqueta = b.id_arqueta
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_arqueta' as capa,
                    h.id_arqueta as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_arqueta h
                LEFT JOIN {PROYECTO}.saneamiento_arqueta b ON h.id_arqueta = b.id_arqueta
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_colector' as capa,
                    h.id_colector as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_colector h
                LEFT JOIN {PROYECTO}.saneamiento_colector b ON h.id_colector = b.id_colector
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_colector' as capa,
                    h.id_colector as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_colector h
                LEFT JOIN {PROYECTO}.saneamiento_colector b ON h.id_colector = b.id_colector
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_ebar' as capa,
                    h.id_ebar as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_ebar h
                LEFT JOIN {PROYECTO}.saneamiento_ebar b ON h.id_ebar = b.id_ebar
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_ebar' as capa,
                    h.id_ebar as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_ebar h
                LEFT JOIN {PROYECTO}.saneamiento_ebar b ON h.id_ebar = b.id_ebar
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_estacion_bombeo' as capa,
                    h.id_estacion_bombeo as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_estacion_bombeo h
                LEFT JOIN {PROYECTO}.saneamiento_estacion_bombeo b ON h.id_estacion_bombeo = b.id_estacion_bombeo
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_estacion_bombeo' as capa,
                    h.id_estacion_bombeo as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_estacion_bombeo h
                LEFT JOIN {PROYECTO}.saneamiento_estacion_bombeo b ON h.id_estacion_bombeo = b.id_estacion_bombeo
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_estacion_de_muestreo' as capa,
                    h.id_estacion_de_muestreo as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_estacion_de_muestreo h
                LEFT JOIN {PROYECTO}.saneamiento_estacion_de_muestreo b ON h.id_estacion_de_muestreo = b.id_estacion_de_muestreo
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_estacion_de_muestreo' as capa,
                    h.id_estacion_de_muestreo as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_estacion_de_muestreo h
                LEFT JOIN {PROYECTO}.saneamiento_estacion_de_muestreo b ON h.id_estacion_de_muestreo = b.id_estacion_de_muestreo
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_estructuras_de_red' as capa,
                    h.id_estructuras_de_red as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_estructuras_de_red h
                LEFT JOIN {PROYECTO}.saneamiento_estructuras_de_red b ON h.id_estructuras_de_red = b.id_estructuras_de_red
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_estructuras_de_red' as capa,
                    h.id_estructuras_de_red as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_estructuras_de_red h
                LEFT JOIN {PROYECTO}.saneamiento_estructuras_de_red b ON h.id_estructuras_de_red = b.id_estructuras_de_red
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_imbornal' as capa,
                    h.id_imbornal as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_imbornal h
                LEFT JOIN {PROYECTO}.saneamiento_imbornal b ON h.id_imbornal = b.id_imbornal
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_imbornal' as capa,
                    h.id_imbornal as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_imbornal h
                LEFT JOIN {PROYECTO}.saneamiento_imbornal b ON h.id_imbornal = b.id_imbornal
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_piezas_saneamiento' as capa,
                    h.id_piezas_saneamiento as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_piezas_saneamiento h
                LEFT JOIN {PROYECTO}.saneamiento_piezas_saneamiento b ON h.id_piezas_saneamiento = b.id_piezas_saneamiento
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_piezas_saneamiento' as capa,
                    h.id_piezas_saneamiento as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_piezas_saneamiento h
                LEFT JOIN {PROYECTO}.saneamiento_piezas_saneamiento b ON h.id_piezas_saneamiento = b.id_piezas_saneamiento
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_pozos' as capa,
                    h.id_pozos as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_pozos h
                LEFT JOIN {PROYECTO}.saneamiento_pozos b ON h.id_pozos = b.id_pozos
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_pozos' as capa,
                    h.id_pozos as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_pozos h
                LEFT JOIN {PROYECTO}.saneamiento_pozos b ON h.id_pozos = b.id_pozos
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_puntos_de_limpieza' as capa,
                    h.id_puntos_de_limpieza as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_puntos_de_limpieza h
                LEFT JOIN {PROYECTO}.saneamiento_puntos_de_limpieza b ON h.id_puntos_de_limpieza = b.id_puntos_de_limpieza
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_puntos_de_limpieza' as capa,
                    h.id_puntos_de_limpieza as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_puntos_de_limpieza h
                LEFT JOIN {PROYECTO}.saneamiento_puntos_de_limpieza b ON h.id_puntos_de_limpieza = b.id_puntos_de_limpieza
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_puntos_de_vertidos' as capa,
                    h.id_puntos_de_vertidos as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_puntos_de_vertidos h
                LEFT JOIN {PROYECTO}.saneamiento_puntos_de_vertidos b ON h.id_puntos_de_vertidos = b.id_puntos_de_vertidos
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_puntos_de_vertidos' as capa,
                    h.id_puntos_de_vertidos as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_puntos_de_vertidos h
                LEFT JOIN {PROYECTO}.saneamiento_puntos_de_vertidos b ON h.id_puntos_de_vertidos = b.id_puntos_de_vertidos
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_ramal_de_pozo' as capa,
                    h.id_ramal_de_pozo as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_ramal_de_pozo h
                LEFT JOIN {PROYECTO}.saneamiento_ramal_de_pozo b ON h.id_ramal_de_pozo = b.id_ramal_de_pozo
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_ramal_de_pozo' as capa,
                    h.id_ramal_de_pozo as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_ramal_de_pozo h
                LEFT JOIN {PROYECTO}.saneamiento_ramal_de_pozo b ON h.id_ramal_de_pozo = b.id_ramal_de_pozo
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_ramal_de_saneamiento' as capa,
                    h.id_ramal_de_saneamiento as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_ramal_de_saneamiento h
                LEFT JOIN {PROYECTO}.saneamiento_ramal_de_saneamiento b ON h.id_ramal_de_saneamiento = b.id_ramal_de_saneamiento
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_ramal_de_saneamiento' as capa,
                    h.id_ramal_de_saneamiento as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_ramal_de_saneamiento h
                LEFT JOIN {PROYECTO}.saneamiento_ramal_de_saneamiento b ON h.id_ramal_de_saneamiento = b.id_ramal_de_saneamiento
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_tramos_de_gravedad' as capa,
                    h.id_tramos_de_gravedad as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_tramos_de_gravedad h
                LEFT JOIN {PROYECTO}.saneamiento_tramos_de_gravedad b ON h.id_tramos_de_gravedad = b.id_tramos_de_gravedad
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_tramos_de_gravedad' as capa,
                    h.id_tramos_de_gravedad as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_tramos_de_gravedad h
                LEFT JOIN {PROYECTO}.saneamiento_tramos_de_gravedad b ON h.id_tramos_de_gravedad = b.id_tramos_de_gravedad
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_tramos_de_impulsion' as capa,
                    h.id_tramos_de_impulsion as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_tramos_de_impulsion h
                LEFT JOIN {PROYECTO}.saneamiento_tramos_de_impulsion b ON h.id_tramos_de_impulsion = b.id_tramos_de_impulsion
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_tramos_de_impulsion' as capa,
                    h.id_tramos_de_impulsion as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_tramos_de_impulsion h
                LEFT JOIN {PROYECTO}.saneamiento_tramos_de_impulsion b ON h.id_tramos_de_impulsion = b.id_tramos_de_impulsion
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_tramos_laterales' as capa,
                    h.id_tramos_laterales as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_tramos_laterales h
                LEFT JOIN {PROYECTO}.saneamiento_tramos_laterales b ON h.id_tramos_laterales = b.id_tramos_laterales
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_tramos_laterales' as capa,
                    h.id_tramos_laterales as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_tramos_laterales h
                LEFT JOIN {PROYECTO}.saneamiento_tramos_laterales b ON h.id_tramos_laterales = b.id_tramos_laterales
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_valvula_de_control' as capa,
                    h.id_valvula_de_control as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_valvula_de_control h
                LEFT JOIN {PROYECTO}.saneamiento_valvula_de_control b ON h.id_valvula_de_control = b.id_valvula_de_control
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_valvula_de_control' as capa,
                    h.id_valvula_de_control as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_valvula_de_control h
                LEFT JOIN {PROYECTO}.saneamiento_valvula_de_control b ON h.id_valvula_de_control = b.id_valvula_de_control
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_valvulas_de_seccionamiento' as capa,
                    h.id_valvulas_de_seccionamiento as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_valvulas_de_seccionamiento h
                LEFT JOIN {PROYECTO}.saneamiento_valvulas_de_seccionamiento b ON h.id_valvulas_de_seccionamiento = b.id_valvulas_de_seccionamiento
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_valvulas_de_seccionamiento' as capa,
                    h.id_valvulas_de_seccionamiento as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_valvulas_de_seccionamiento h
                LEFT JOIN {PROYECTO}.saneamiento_valvulas_de_seccionamiento b ON h.id_valvulas_de_seccionamiento = b.id_valvulas_de_seccionamiento
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_zona_incidencia_saneamiento' as capa,
                    h.id_zona_incidencia_saneamiento as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_zona_incidencia_saneamiento h
                LEFT JOIN {PROYECTO}.saneamiento_zona_incidencia_saneamiento b ON h.id_zona_incidencia_saneamiento = b.id_zona_incidencia_saneamiento
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_zona_incidencia_saneamiento' as capa,
                    h.id_zona_incidencia_saneamiento as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_zona_incidencia_saneamiento h
                LEFT JOIN {PROYECTO}.saneamiento_zona_incidencia_saneamiento b ON h.id_zona_incidencia_saneamiento = b.id_zona_incidencia_saneamiento
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_zona_revision_saneamiento' as capa,
                    h.id_zona_revision_saneamiento as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_zona_revision_saneamiento h
                LEFT JOIN {PROYECTO}.saneamiento_zona_revision_saneamiento b ON h.id_zona_revision_saneamiento = b.id_zona_revision_saneamiento
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'saneamiento_zona_revision_saneamiento' as capa,
                    h.id_zona_revision_saneamiento as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_saneamiento_zona_revision_saneamiento h
                LEFT JOIN {PROYECTO}.saneamiento_zona_revision_saneamiento b ON h.id_zona_revision_saneamiento = b.id_zona_revision_saneamiento
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'ubicaciones_tecnicas_adjunto' as capa,
                    h.id_adjunto as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    NULL::geometry as geom
                FROM {PROYECTO}.historial_ubicaciones_tecnicas_adjunto h
                WHERE h.fecha_modificado IS NOT NULL
            )
            UNION ALL
            (
                SELECT 
                    'ubicaciones_tecnicas_uts' as capa,
                    h.id_uts as elemento,
                    h.fecha_modificado AS fecha_ult,
                    h.usuario_modificado AS usuario_evento,
                    'modificar' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_ubicaciones_tecnicas_uts h
                LEFT JOIN {PROYECTO}.ubicaciones_tecnicas_uts b ON h.id_uts = b.id_uts
                WHERE h.fecha_modificado IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
            UNION ALL
            (
                SELECT 
                    'ubicaciones_tecnicas_uts' as capa,
                    h.id_uts as elemento,
                    h.fecha_alta AS fecha_ult,
                    h.usuario_alta AS usuario_evento,
                    'alta' as tipo_operacion,
                    h.herramienta as operacion,
                    COALESCE(h.geom, b.geom) as geom
                FROM {PROYECTO}.historial_ubicaciones_tecnicas_uts h
                LEFT JOIN {PROYECTO}.ubicaciones_tecnicas_uts b ON h.id_uts = b.id_uts
                WHERE h.fecha_alta IS NOT NULL AND (h.herramienta IS NULL OR h.herramienta <> 'fotos')
            )
        ) AS eventos

        GROUP BY capa, elemento, fecha_ult, usuario_evento, tipo_operacion, operacion, geom
        ORDER BY fecha_ult DESC;
            
        """.format(PROYECTO=nombre_proy, USUARIO=usuario, FECHA_INICIO=fecha_inicio, FECHA_FINAL=fecha_final, NOMBRE_PROY=proyecto['nombre'])

        # Ejecutamos la insercion directa
        FisotecBaseDatos.consultaSQL(conexion, consulta_historial_agrupado)
        print("Datos insertados para " + proyecto['nombre'])
# Cerramos la conexion a la base de datos
FisotecBaseDatos.cerrarBaseDatos(conexion)

print("Terminamos el algoritmo")
