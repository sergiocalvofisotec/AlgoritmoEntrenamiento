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
usuario = 'jluque'
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


# Cerramos la conexion a la base de datos
FisotecBaseDatos.cerrarBaseDatos(conexion)

print("Terminamos el algoritmo")
