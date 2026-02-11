#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

    Fichero en el que tendremos funciones utiles para el manejo del plugin, tendrá funciones comunes a varias clases de este y a las que accederán para
    realizar operaciones


     :Copyright: 2019, FISOTEC
    :Version:   1.0

    :Director:      Jose Ruiviejo Gutiérrez
    :Jefe Proyecto: Rafael Francisco Yeguas López
    :Autores:       Sara Valverde Padilla
    :Autores:       Rafael Francisco Yeguas López
"""

# Importamos las clases de nuestro plugin

# Importamos las clases de QGIS
# from qgis.core import NULL

# Importamos las clases de Qt5
# from PyQt5.QtCore import QDate

# Importamos las clases externas
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from datetime import *
from random import randrange
from decimal import *

import re


class FisotecUtils:
    """
        Controlador con funciones que permitirán el manejo de los datos y operaciones para agilizar y mejorar el
        rendimiento de nuestro plugin.
    """

    @staticmethod
    def crearFila(d):
        """
            Función que crea y devuelve los elementos del diccionario preparada para realizar la sentencia sql.

            Creará una cadena de texto para los campos y otra para los valores almacenados en el diccionario de entrada,
            devolviendo los mismos en una cadena de texto, ambos incluidos en una tupla de la forma (campos, valores).

            :param d:   Diccionario con los datos del elemento.
            :type d:    dict

            :return:    Tupla con las cadenas de texto de los campos y valores
            :rtype:     tuple
        """

        # Inicializamos las variables para almacenar los campos y los valores
        campos, valores = '', ''

        # Recorremos el diccionario
        for c in d.keys():
            # print (c, d[c])
            v = ''

            # Si no tiene valor continuamos sin añadir
            if d[c] is None:
                continue

            # Si es un número lo convertimos a cadena
            elif type(d[c]) is int or type(d[c]) is complex or type(d[c]) is float:
                v = str(d[c])

            #si es booleano lo convertimos a cadena
            elif type(d[c]) is bool:
                v = str(d[c])

            # Si es un archivo binario lo convertimos a texto
            elif type(d[c]) is psycopg2.extensions.Binary:
                v = str(d[c])

            # elif type(d[c]) is QDate:
            #     v = d[c].toString("yyyy/MM/dd")
            #     v = "'" + v + "'"

            # Si es la parte geométrica, la añadimos a la variable
            elif d[c].find("ST_GEOMFROMTEXT") != -1:
                v = d[c]

            elif d[c].find("SELECT") != -1:
                v = d[c]

            # Si es otro tipo (texto) lo añadimos entre comillas
            else:
                v = "'" + d[c] + "'"

            # Añadimos el campo y la información
            if len(v) > 0 and v != '':
                campos += c + ", "
                valores += v + ", "

        # Eliminamos la coma del final
        campos = campos[:-2]
        valores = valores[:-2]

        # Devolvemos la tupla de valores
        return (campos, valores)

    @staticmethod
    def es_nulo(elemento):
        """
            Comprueba si un elemento es nulo

            :param elemento: elemento a comprobar
            :type elemento: str

            :return: Resultado de la comprobación
            :rtype: bool
        """

        if elemento == '' or elemento == NULL or elemento is None or elemento == 'NULL' or elemento is NULL:
            return True
        else:
            return False

    @staticmethod
    def cambiar_conexion(signal, newhandler=None, oldhandler=None):
        """
            Función para eliminar conexiones activas o asignar una nueva conexion

            :param signal: señal en la que se conectará o desonectaran conexiones
            :type signal: signal

            :param newhandler: nueva conexion
            :param oldhandler:

            :return: None
        """

        # Iniciamos conexiones
        conexiones = True
        # Mientras haya desconexiones sigue desconectando
        while conexiones:
            try:
                if oldhandler is not None:
                    signal.disconnect(oldhandler)
                else:
                    signal.disconnect()
            except:
                conexiones = False
        # Si se le envia una nueva conexión conecta está a la señal recibida
        if newhandler is not None:
            signal.connect(newhandler)

    @staticmethod
    def formatear_fecha(valor):
        """
            Formatea un dato a a formato fecha


            Intentará realizar la transformación del dato recibido por parámetro a a formato fecha y devuelve el resultado
            :param valor:
            :return:
        """

        #Ponemos la variable a NULL
        dato = NULL

        # Creamos una lista con los formatos de fecha posibles
        formatos_fecha = ['%Y-%m-%d %H:%M:%S', '%Y%m%d%H%M%S', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d',
                          '%Y/%m/%d %H:%M:%S', '%Y/%d/%m', '%Y/%d/%m ', '%d/%m/%Y', '%d/%m/%Y %H:%M:%S',
                           '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M', '%d%m%Y%H%M%S', '%d/%m/%y', '%y/%m/%d',
                          '%y-%m-%d %H:%M:%S', '%y-%m-%d']

        # recorremos la lista de formatos e intentamos hacer la transformación
        for format in formatos_fecha:
            try:
                dato = datetime.strptime(valor, format)
                return dato
            except:
                pass

        return dato

    @staticmethod
    def cerrar_ventana(plugin):
        """
            Función encargada de cerrar las ventanas según el tipo y de mostrar el dock de menu de acceso rápido
            :param plugin:  Instancia al plugin
            :type plugin: QgisInterface

            :return: None
        """

        # Comprueba la  ventana abierta, cierra el dock correspondinte y muestra de nuevo el menú vertical

        # Depende de lo almacenado en ventana oculta uno u otro elemento y después lo elimina
        if plugin.ventana == 'informacion':
            plugin.dock_informacion.setVisible(False)
            plugin.dock_informacion.deleteLater()

        elif plugin.ventana == 'edicion':
            plugin.dock_edicion.setVisible(False)
            plugin.dock_edicion.deleteLater()

        elif plugin.ventana == 'capas':
            plugin.dock_capas.setVisible(False)
            plugin.dock_capas.deleteLater()

        elif plugin.ventana == 'asignacion':
            plugin.dock_asignacion.setVisible(False)
            plugin.dock_asignacion.deleteLater()

        elif plugin.ventana == 'exportacion':
            plugin.dock_exportacion.setVisible(False)
            plugin.dock_exportacion.deleteLater()

        elif plugin.ventana == 'revision':
            plugin.dock_revision.setVisible(False)
            plugin.dock_revision.deleteLater()

        # La variable ventana se actualiza con el valor nada y se muestra el menu de acceso rápido
        plugin.ventana = 'Nada'
        if plugin.acceso_rapido:
            plugin.menu_acceso_rapido.dock.setVisible(True)

    @staticmethod
    def cancelar_acciones(plugin):
        """
            Función para cancelar la acción activa y poder iniciar una nueva acción

            :param plugin: Instancia al plugin
            :type plugin: QgisInterface

            :return: None
        """

        # Desactiva herramienta del mapa
        plugin.iface.mapCanvas().unsetMapTool(plugin.iface.mapCanvas().mapTool())
        plugin.iface.actionPan().trigger()

        # Borramos y quitamos la selección
        capas_plugin = plugin.capas_cargadas.devuelve_capas_cargadas()

        for capa in capas_plugin.keys():
            FisotecUtils.cambiar_conexion(capas_plugin[capa].featureAdded)
            capas_plugin[capa].removeSelection()

        # Si la acción es información desactiva el botón
        if plugin.accion == 'informacion':
            plugin.menu_herramientas.estadoBoton('Informacion', False)

        # Si la acción es edicion alfanumérica desactiva botón
        elif plugin.accion == 'edicion_alfanumerica':
            plugin.menu_herramientas.estadoBoton('Edicion Alfanumérica', False)

        # Si la acción es edición geográfica desactiva botón
        elif plugin.accion == 'edicion_geografica':
            plugin.menu_herramientas.estadoBoton('Edicion Geografica', False)

        # Si la acción es guardar desactiva botón
        elif plugin.accion == 'guardar':
            plugin.menu_herramientas.estadoBoton('Guardar', False)

        # Si la acción es eliminar elemento desactiva el botón
        elif plugin.accion == 'eliminar_elemento':
            plugin.menu_herramientas.estadoBoton('Borrar', False)

        # Si la acción es nuevo elemento
        elif plugin.accion == 'nuevo':
            plugin.menu_herramientas.estadoBoton('Crear', False)

        elif plugin.accion == 'copiar':
            plugin.menu_herramientas.estadoBoton('Copiar', False)

        elif plugin.accion == 'copiar_atributos':
            plugin.menu_herramientas.estadoBoton('Copiar Atributos', False)

        elif plugin.accion == 'edicion_multiple':
            plugin.menu_herramientas.estadoBoton('Edicion Multiple', False)

        elif plugin.accion == 'edicion_atributos_multiple':
            plugin.menu_herramientas.estadoBoton('Edicion Atributos Multiple', False)

        # Si la acción es asignar puntos llama a la función salir de su clase (asignacion_
        elif plugin.accion == 'asignar_puntos':
            plugin.asignacion_puntos.salir()

        # Si la acción es exportar elementos llama a la función salir de su clase (exportar_elementos)
        elif plugin.accion == 'exportar_elementos':
            plugin.exportar_elementos.salir()

        # Si la accion es revision llama  a la opción de salir de su clase (revisar_intervencion)
        elif plugin.accion == 'modo_revision':
            plugin.revisar.salir()

        # Si la acción es editar sección llamamos a la opción de salir de su clase
        elif plugin.accion == 'editar_seccion':
            plugin.edicion_seccion.salir()

        elif plugin.accion == 'cambiar_estilo':
            plugin.cambiar_estilo.salir()

        elif plugin.accion == 'nuevo_estilo':
            plugin.nuevo_estilo.salir()

        elif plugin.accion == 'asignar_estilo':
            plugin.asignar_estilo.salir()

        elif plugin.accion == 'exportar_seccion':
            plugin.exportar_simulacion.cancelar()

        # Reiniciamos el valor de la variable acción de plugin
        plugin.accion = ''

    @staticmethod
    def sin_espacios(cadena):
        """
            Elimina los espacios, guiones y pone a minúscula la cadena recibida por parámetro
            y devuelve el resultado

            :param cadena: variable que contiene una cadena de texto
            :type cadena: str

            :return: Cadena formateada
            :rtype: str
        """

        # Pasamos a minúscula y quitamos _
        nombre = str(cadena).lower().replace("_", "")

        # Eliminamos guiones y caracteres raros
        sin_guion = nombre.replace("-", "")

        # Eliminamos espacios
        nombre_sin_espacios = sin_guion.replace(" ", "")

        return nombre_sin_espacios

    @staticmethod
    def transformar_valor(dato):
        """
            Transforma el dato recibido segun su tipo para construir sentecias

            :param dato: valor a transformar
            :type dato:

            :return: dato transformado
            :rtype:
        """
        # Comprueba el tipo del campo de actualización para construir la sentencia where
        if type(dato) is int or type(dato) is complex or type(dato) is float or dato is NULL:
            valor = dato

        elif type(dato) is bool:
            valor = str(dato)

        # Si el tipo de dato es binary guardamos transformado a str
        elif type(dato) is psycopg2.extensions.Binary:
            valor = str(dato)

        elif type(dato) is QDate:
            v = dato.toString("yyyy/MM/dd")
            valor = "'%s'" %(v)

        # Si es la parte geométrica, la añadimos a la variable
        elif dato.find("ST_GEOMFROMTEXT") != -1:
            valor = str(dato)

        else:
            valor = "'%s'" % (dato)

        return valor

    @staticmethod
    def color_aleatorio():
        """
            Selecciona un color aleatorio de una lista de colores y devuelve el color seleccionado

            :return: color seleccionado
            :rtype: str
        """

        # Lista con algunos colores
        lista_colores = ['#F0F8FF', '#E6E6FA', '#B0E0E6', '#B0E0E6', '#ADD8E6', '#87CEFA', '#00BFFF', 'FF7F50',
                         '#B0C4DE', '#1E90FF', '#6495ED', '#6495ED', '#5F9EA0', '#7B68EE', '#6A5ACD', '#483D8B',
                         '#4169E1', '#0000FF', '#0000CD', '#8A2BE2', '#4B0082', '#E0FFFF', '#00FFFF', '#AFEEEE',
                         '#DA70D6', '#DDA0DD', '#FFDAB9', '#BC8F8F', '#FF1493', '#808000', '#DC143C', '#FFCCFF']

        # Seleccionamos un color al azar
        color = lista_colores[randrange(0, len(lista_colores))]

        # Devolvemos el color obtenido
        return color

    @staticmethod
    def mensaje_error(texto, label):
        """
            Muestra el mensaje de error en el label de una ventana

            :param texto: texto que mostrará
            :type texto: str

            :return: None
        """

        # Cambioamos el color de la fuente y mostramos el texto
        label.setStyleSheet('color: red')
        label.setText(texto)

    @staticmethod
    def numero_a_texto(numero, longitud):
        """

        :param numero:
        :param longitud:
        :return:
        """

        texto = str(numero)

        while len(texto) < longitud:
            texto = '0' + texto

        return texto