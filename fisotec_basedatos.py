#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Controlador Base de Datos

    Archivo creado para el creacion de BD y elementos relacionados con esta

     :Copyright: 2019, FISOTEC
    :Version:   1.0

    :Director:      Jose Ruiviejo Gutiérrez
    :Jefe Proyecto: Rafael Francisco Yeguas López
    :Autores:       Sara Valverde Padilla
    :Autores:       Rafael Francisco Yeguas López

"""
# Importamos las clases de nuestro plugin

from credenciales import *

# Importamos las clases externas
import psycopg2
from psycopg2 import extras
from psycopg2 import connect
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

class FisotecBaseDatos:

    """
        Esta clase contienene métodos para la conexion con la base de datos, para crearlas, inserción.
        Además e crear la base de datos dispone de metodos para crear tablespaces y esquemas
        Y métodos para cargar un fichero sql y ejecutarlo
    """

    # CONEXION

    @staticmethod
    def conectarBaseDatos():
        """
        Abre una conexión con la base de datos y devuelve el cursor de la misma.

        Utiliza la librería psycopg2

        :return:    Conexión a la base de datos
        :type:      psycopg2.extras.RealDictCursor

        """

        # Conectamos con la base de datos
        con = connect(user=DBUSER, host=DBHOST, password=DBPASSWORD, port=DBPORT, dbname=DBNAME)

        # Fijamos el nivel de aislamiento para la transaccion de la sesión actual, fijándolo a un nivel de autocommit
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        # Devolvemos un cursor a la conexión, fijándolo como una subclase de extras.RealDictCursor para obtener los
        # resultados en forma de diccionario
        cur = con.cursor(cursor_factory=extras.RealDictCursor)

        return cur

    @staticmethod
    def cerrarBaseDatos(conexion):
        """
        Cierra la conexión a la base de datos.

        :param conexion:    Conexión abierta a la base de datos
        :type conexion:     psycopg2.extras.RealDictCursor

        :return:    None
        """
        conexion.close()

    # INSERCIONES

    @staticmethod
    def insertarElemento(conexion, tabla, columnas, valores):
        """
            Inserta un elemento en la tabla correspondiente.

            :param conexion:    Conexión a la base de datos
            :type conexion:     psycopg2.extras.RealDictCursor


            :param tabla:       Tabla de la base base de datos
            :type tabla:        str

            :param campos:      Campos que se van a insertar
            :type campos:       str

            :param valores:     Valores que se van a insertar
            :typer valores:     str

            :return:            Indicación de si se ha insertado el elemento correctamente
            :rtype:             bool
        """

        # Creamos la consulta
        consulta = u"INSERT INTO %s (%s) VALUES (%s)" % (tabla, columnas, valores)
        # print(consulta)

        try:
            conexion.execute(consulta)
            return True
        except:
            error = "Error al insertar un %s" % (tabla)
            print(error)
            # print(consulta)
            return False

    # BORRAR

    @staticmethod
    def borraElemento(conexion, tabla, clausula):
        """
            Elimina un elemento de la base de datos.

            :param conexion:    Conexión a la base de datos
            :type conexion:     psycopg2.extras.RealDictCursor

            :param tabla:       Tabla donde se eliminará el elemento
            :type tabla:        str

            :param clausula:    Cláusula WHERE de la sentencia de eliminación
            :type clausula:     str

            :return:            Indicación de si se ha podido borrar el elemento
            :rtype:             bool
        """

        # Creamos la sentencia de eliminación
        consulta = u"DELETE FROM %s WHERE %s" % (tabla, clausula)

        # Realizamos la sentencia
        try:
            conexion.execute(consulta)
            return True
        except:
            error = "No puede borrarse el elemento de la tabla %s" % (tabla)
            iface.messageBar().pushMessage("Error", error, level=Qgis.Critical)
            return False

    @staticmethod
    def eliminar_datos_tabla(tabla):
        """
            Elimina todos los datos de una tabla

            Elimina los datos contenidos en la tabla recibida por parámetro

            :param tabla: nombre de la tabla de la que se eliminarán los datos
            :type tabla: str

            :return: None
        """

        # Abrimos conexión con la base de datos
        conexion = FisotecBaseDatos.conectarBaseDatos()

        # Creamos la consulta
        consulta = "DELETE FROM %s" % (tabla)

        # Realizamos la consulta y cerramos conexion
        try:
            FisotecBaseDatos.consultaSQL(conexion, consulta)
            FisotecBaseDatos.cerrarBaseDatos(conexion)
            return True
        except:
            error = "No ha sido posible eliminar los elemetos de la tabla %s" %(tabla)
            iface.messageBar().pushMessage("Error", error, level=Qgis.Critical)
            return False

    # MODIFICACION(UPDATE)
    @staticmethod
    def modificarElemento(conexion, tabla, datos, schema='public'):
        """
            Función que modifica un elemento de la base de datos

            :param conexion:    Conexión a la base de datos
            :type conexion:     psycopg2.extras.RealDictCursor

            :param tabla:       Tabla donde se modificará el elemento
            :type tabla:        str

            :param datos:       Diccionario con el dato a modificar
            :type datos:        dict

            :return:            Referencia a si se ha modificado el elemento
            :rtype:             bool
        """
        datos_tabla = tabla.split('.')
        # Obtenemos la llave primaria
        llave = FisotecBaseDatos.obtenerClavePrimaria(conexion, datos_tabla[1], datos_tabla[0])
        if schema != 'public':
            tabla = schema + '.' + tabla

        # Inicializamos las cláusulas where y set
        clausula_where = ''
        clausula_set = ''

        # Recorremos los datos del diccionario
        for elemento in datos.keys():
            # Si el elemento forma parte de la llave primaria, se añade a la cláusula where
            if elemento in llave:
                # Si no tenemos aún clausula
                if clausula_where == '':
                    valor = datos[elemento]

                    if type(valor) is int or type(valor) is complex or type(valor) is float:
                        clausula_where = u"%s = %s" % (elemento, valor)

                    else:
                        clausula_where = u"%s = '%s'" % (elemento, valor)

                else:
                    valor = datos[elemento]

                    if type(valor) is int or type(valor) is complex or type(valor) is float:
                        clausula_where = clausula_where + u" AND %s = %s" % (elemento, valor)

                    else:
                        clausula_where = clausula_where + u" AND %s = '%s'" % (elemento, valor)

            # Si el elemento no forma parte de la llave primaria, se añade a la cláusula set
            else:
                # Si no tenemos aún clausula
                if clausula_set == '':
                    valor = datos[elemento]

                    if type(valor) is int or type(valor) is complex or type(valor) is float or type(valor) is bool:
                        clausula_set = u"%s = %s" % (elemento, valor)

                    elif type(valor) is psycopg2.extensions.Binary:
                        clausula_set = u"%s = %s" % (elemento, str(valor))

                    # Si es la parte geométrica, la añadimos a la variable
                    elif valor.find("ST_GEOMFROMTEXT") != -1:
                        clausula_set = u"%s = %s" %(elemento, str(valor))

                    else:
                        clausula_set = u"%s = '%s'" % (elemento, valor)

                else:
                    valor = datos[elemento]

                    if type(valor) is int or type(valor) is complex or type(valor) is float or type(valor) is bool:
                        clausula_set = clausula_set + u", %s = %s" % (elemento, valor)

                    elif type(valor) is psycopg2.extensions.Binary:
                        clausula_set = clausula_set + u", %s = %s" % (elemento, str(valor))

                    # Si es la parte geométrica, la añadimos a la variable
                    elif valor.find("ST_GEOMFROMTEXT") != -1:
                        clausula_set = clausula_set + u", %s = %s" %(elemento, valor)

                    else:
                        clausula_set = clausula_set + u", %s = '%s'" % (elemento, valor)

        # Creamos la consulta de modificación
        consulta = u"UPDATE %s SET %s WHERE %s" % (tabla, clausula_set, clausula_where)

        try:
            conexion.execute(consulta)
            return True

        except:
            print(consulta)
            return False

    # CONSULTAS

    @staticmethod
    def consultaSQL(conexion, consulta):

        """
        Ejecuta la consulta SQL recibida por parámetro y devuelve el resultado

        :param conexion:    Conexión a la base de datos
        :type conexion:     psycopg2.extras.RealDictCursor

        :param consulta: consulta que se debe ejecutar
        :type consulta: str

        :return: lista con los resultados de la consulta
        :rtype: list

        """

        #realiza la consulta recibida por parámetro y devuelve el resultado
        try:
            conexion.execute(consulta)
            result = conexion.fetchall()

            return result

        #si falla muestra mensaje de error y devuelve lista vacia
        except Exception as error:
            print(error)

            return []

    @staticmethod
    def consultaTotal(conexion, tabla, clausula = ''):
        """
            Realiza una consulta en la base de datos y devuelve los elementos que cumplen dicha condición con todos
            sus valores.

            :param conexion:    Conexión a la base de datos
            :type conexion:     psycopg2.extras.RealDictCursor

            :param tabla:       Tabla donde se insertará el elemento
            :type tabla:        str

            :param clausula:    Clausula de la sentencia, parte WHERE.
            :param clausula:    str

            :return:            Diccionario con los datos obtenidos. Diccionario vacío en caso de no obtener resultados.
            :rtype:             dict
        """

        # Si la cláusula tiene datos creamos la sentencia con ella. Si no sin la parte where
        if len(clausula) > 0:
            consulta = u"SELECT * from %s WHERE %s" % (tabla, clausula)
        else:
            consulta = u"SELECT * from %s" % (tabla)

        try:

            # Realizamos la consulta
            conexion.execute(consulta)
            datos = conexion.fetchall()

            # Devolvemos los datos
            return datos

        except:
            return []

    @staticmethod
    def obtenerCampoElemento(conexion, nombre_campo, elemento, columna, tabla):
        """
            Consulta el campo de la tabla indicada con la condición indicada en los parámetros de entrada.

            :param conexion:    Conexion a la base de datos
            :type conexion:     psycopg2.extras.RealDictCursor

            :param nombre_campo:       Nombre del campo que queremos hacer la consulta
            :type nombre_campo:        str

            :param elemento:    Elemento de la clausula where
            :type elemento:     str

            :param columna:     Columna sobre la que relizar la consulta, clausula where
            :type columna:      str

            :param tabla:       Tabla en la que haremos la consulta
            :type tabla:        str



            :return:            Dato que contiene dicho campo. Si no existe devuelve None
            :rtype:             str
        """

        # Creamos la consulta y la ejecutamos
        if type(elemento) is int:
            c_consulta = u"Select %s from %s where %s=%s"
        else:
            c_consulta = u"Select %s from %s where %s='%s'"

        consulta = c_consulta % (nombre_campo, tabla, columna, str(elemento))

        conexion.execute(consulta)


        # Obtenemos el contenido del campo y lo devolvemos
        datos = conexion.fetchone()

        if datos is not None:
            return datos[nombre_campo]
        else:
            return None

    #COMPROBACIONES Y CONSULTAS SOBRE COLUMNAS

    @staticmethod
    def obtenerClavePrimaria(conexion, tabla, esquema):
        """
            Obtenemos la clave primaria de la tabla indicada como parámetro

            :param conexion:    Conexión a la base de datos
            :type conexion:     psycopg2.extras.RealDictCursor

            :param tabla:       Tabla de la que obtendremos la clave primaria
            :type tabla:        str

            :return:            Clave primaria de la tabla
            :rtype:             list
        """

        # Creamos la consulta
        consulta = u"SELECT column_name as columna FROM information_schema.key_column_usage " \
                   + u"WHERE table_name = '%s' AND constraint_schema = '%s'" % (tabla, esquema) \
                   + u"AND constraint_name LIKE '%pkey'"

        # Ejecutamos la consulta y  obtenemos los datos
        conexion.execute(consulta)
        datos = conexion.fetchall()

        # Creamos una lista para almacenar los campos que forman la clave primaria
        resultado = []
        for elemento in datos:
            resultado.append(elemento["columna"])

        # Devolvemos el resultado

        return resultado

    @staticmethod
    def compruebaValoresNoNulos(conexion, datos, esquema, tabla):
        """
            Función que comprueba que todos los valores NOT NULL de la tabla están incluidos

            :param conexion:    Conexión a la base de datos
            :type conexion:     psycopg2.extras.RealDictCursor

            :param datos:       Diccionario con el dato a comprobar
            :type datos:        dict

            :param esquema:     Esquema de la base de datos donde se encuentra la tabla
            :type esquema:      str

            :param tabla:       Tabla donde se insertará el elemento
            :type tabla:        str

            :return:            Indicación sobre si los datos son válidos.
            :rtype:             bool
        """

        # Creamos la consulta para obtener aquellos elementos que no pueden ser nulos
        consulta = u"SELECT column_name as columna FROM information_schema.columns " \
                   + u"WHERE table_schema = '%s' AND table_name = '%s' AND is_nullable = 'NO'" % (esquema, tabla) \
                   + u" AND column_default IS NULL"

        # Realizamos la consulta y obtenemos los datos.
        conexion.execute(consulta)
        columnas = conexion.fetchall()

        # Comprobamos que los valores NO NULOS se hayan insertado
        # Recorremos los elementos que no pueden ser nulos
        for elemento in columnas:
            # Si no hemos insertado dicho elemento informamos de dicho error
            if not elemento["columna"] in datos.keys():
                error = u"Error: %s debe indicarse" % (elemento["columna"])
                iface.messageBar().pushMessage(str(error), '', level=Qgis.Critical)
                return False

            # Si el elemento es vacio informamos del error
            if datos[elemento["columna"]] == '':
                error = u"Error: %s debe rellenarse" % (elemento["columna"])
                iface.messageBar().pushMessage(str(error), '', level=Qgis.Critical)
                return False

            # Si el elemento es nulo informamos del error
            if datos[elemento["columna"]] is None:
                error = u"Error: %s debe rellenarse" % (elemento["columna"])
                iface.messageBar().pushMessage(str(error), '', level=Qgis.Critical)
                return False

        return True

    @staticmethod
    def comprobar_datos_tabla(tabla):
        """
            Comprueba si una tabla tiene datos

            Comprueba si la tabla recibida por parámetro tiene datos y devuelve el resultado

            :param tabla: nombre de la tabla
            :type tabla: str

            :return: Resultado de la comprobación
            :rtype: bool
        """

        # Abrimos conexion con la base de datos
        conexion = FisotecBaseDatos.conectarBaseDatos()

        # Realizamos una consulta de todos los datos de la tabla
        datos = FisotecBaseDatos.consultaTotal(conexion, tabla)

        # si tiene datos devolvemos true si no los tiene False
        if len(datos) > 0:
            FisotecBaseDatos.cerrarBaseDatos(conexion)
            return True
        else:
            FisotecBaseDatos.cerrarBaseDatos(conexion)
            return False

    #CREACION ESQUEMA


    @staticmethod
    def crearSchema(con, nombre):

        """
        Crea un esquema en la base de datos indicada


        :param nombre:  nombre del schema que creemos
        :type nombre:   str


        :return: si crea el esquema devuelve True, si la creación falla devuelve False
        :rtype:  bool

        """
        try:
            # conecta con la base de datos
            con.execute('CREATE SCHEMA "' + nombre + '"')
            return True

        except Exception as error:
            # si falla cierra muestra el error y devuelve false
            iface.messageBar().pushMessage("Error", str(error), level=Qgis.Critical)
            return False

    @staticmethod
    def concederPermisosEditorVisor(con, nombre_esquema):
        """
            Concede permiso de edicion para editor y de seleccion para visor

            :param nombre_esquema:  nombre del esquema al que concederemos permisos
            :type nombre_esquema:   str

            :return:
        """
        try:
            con.execute(u"GRANT ALL PRIVILEGES ON SCHEMA %s TO %s" % (nombre_esquema, EDITOR_USER))
            con.execute(u"GRANT USAGE ON SCHEMA %s TO %s" % (nombre_esquema, VISOR_USER))
            con.execute(u"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA %s TO %s" %(nombre_esquema, EDITOR_USER))

            return True

        except:
            return False


    @staticmethod
    def crearTabla(nombre, con, valores, schema=None ):
        """
         Crea tabla en el esquema y con el nombre pasados por parámetros.
         Crea una columna clave primaria id serial
         El resto de columnas a crear se pasan en una cadena: nombre tipo


        :param nombre: nombre con el que se creará la tabla
        :type nombre:  str

        :param con: conexion a la base de datos
        :type con: psycopg2.extensions.connection

        :param valores: cadena con columnas a crear
        :type valores: str

        :return: si la creación la tabla es correcta devuelve True, si no, devolverá False
        :rtype: bool

        """

        try:
            serial = False
            if type(con) == psycopg2.extensions.connection:

                con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                cur = con.cursor()
            else:
                cur = con

            if 'id' not in valores:
                valores = valores + ', id serial'
                serial = True

            if schema is not None:
                tabla = schema+"."+nombre
            else:
                tabla = nombre

            #creamos la sentencia para crear la tabla y la ejecutamos
            sql = "CREATE TABLE %s (%s,CONSTRAINT %s_pkey PRIMARY KEY(id))" % (tabla, valores, nombre)

            cur.execute(sql)
        except:
            return False

        finally:
            try:
                cur.execute(u"GRANT ALL PRIVILEGES ON %s TO %s" % (tabla, EDITOR_USER))
                cur.execute(u"GRANT SELECT ON %s TO %s" % (tabla, VISOR_USER))
                if serial:
                    cur.execute(u"GRANT ALL PRIVILEGES ON SEQUENCE %s_id_seq TO %s" % (tabla, EDITOR_USER))
                    cur.execute(u"GRANT SELECT ON SEQUENCE %s_id_seq TO %s" % (tabla, VISOR_USER))

                #cerramos la conexion con la base de datos y devolvemos true

                return True
            except:
                return False


    @staticmethod
    def crear_columna(conexion, cadena, tabla):
        """
            Crea una nueva columna en una tabla

            :param conexion: conexion con la base de datos
            :type conexion:  psycopg2.extras.RealDictCursor

            :param cadena: cadena que incluirá nombre del nuevo campo(tipo, defecto..)
            :type cadena: str

            :param tabla: nombre tabla en la que se añadirá la columna
            :type tabla: str

            :return: None
        """

        consulta = u"""ALTER TABLE %s ADD COLUMN %s""" % (tabla, cadena)
        try:
            FisotecBaseDatos.consultaSQL(conexion, consulta)
            return True
        except:
            return False

    @staticmethod
    def obtener_nombre_columnas(proyecto, tabla):
        """
            Consulta el nombre de las columnas del proyecto y tabla recibidos por parámetro

            El nombre del proyecto es a su vez el nombre del esquema

            :param proyecto: nombre del proyecto
            :type proyecto: str

            :param tabla: nombre de la tabla
            :type tabla: str

            :return: Diccionario con los nombres de las columnas de una tabla
            :rtype: dict
        """

        # Abrimos conexión con lo base de datos
        conexion = FisotecBaseDatos.conectarBaseDatos()

        # Creamos la consulta y devolvemos el resultado
        consulta_columnas = u"""SELECT column_name as nombre_columna, data_type as tipo 
                            FROM information_schema.columns WHERE table_name = '%s' and table_schema = '%s'""" \
                            % (tabla, proyecto)
        d_columnas = FisotecBaseDatos.consultaSQL(conexion, consulta_columnas)

        FisotecBaseDatos.cerrarBaseDatos(conexion)

        # Creamos una lista para almacenar los campos que forman la clave primaria
        dic_elemento = dict()
        for elemento in d_columnas:
            dic_elemento[elemento["nombre_columna"]] = elemento["tipo"]

        return dic_elemento


    @staticmethod
    def consultas_multiples(array_sentencias):
        """
            Lee una lista de sentencias sql y va agrupandolas en de 250 en 250 y ejecutando

            :param array_sentencias: lista con las sentencias que debe ejecutar

            :return: None
        """

        # Iniciamos variable sentencia vacia
        sentencia = ""

        # Abrimos conexión con base de datos
        cur = FisotecBaseDatos.conectarBaseDatos()

        # Recorremos el array de sentencias y vamos construyendo la sentencia general
        for numero in range(0, len(array_sentencias)):

            # Creamos la cadena
            sentencia = sentencia + array_sentencias[numero]

            # Si el número de elementos es el indicado en el fichero de configuración ejecutamos la sentencia y la limpiamos
            if numero % NUMERO_SENTENCIAS_CONJUNTAS == 0:
                cur.execute(sentencia)
                sentencia = ""

        # Si sentencia tiene datos ejecutamos
        if len(sentencia) > 0:
            cur.execute(sentencia)

        # Por último cerramos conexión con base de datos
        FisotecBaseDatos.cerrarBaseDatos(cur)