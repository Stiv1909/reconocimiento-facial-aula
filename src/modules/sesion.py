# modules/sesion.py
class Sesion:
    # Variable de clase que almacena la información del usuario actual
    _usuario = None

    @classmethod
    def iniciar_sesion(cls, datos_usuario: dict):
        """
        Inicia la sesión del usuario.
        Recibe un diccionario con los datos del usuario (por ejemplo: id, nombres, apellidos, rol, foto, etc.)
        y lo guarda en la variable de clase _usuario.
        """
        cls._usuario = datos_usuario

    @classmethod
    def obtener_usuario(cls):
        """
        Retorna la información del usuario actualmente autenticado.
        Si no hay sesión iniciada, devuelve None.
        """
        return cls._usuario

    @classmethod
    def cerrar_sesion(cls):
        """
        Cierra la sesión actual, eliminando los datos almacenados del usuario.
        """
        cls._usuario = None

    @classmethod
    def esta_autenticado(cls):
        """
        Verifica si hay una sesión activa.
        Devuelve True si _usuario contiene información, False si no hay sesión.
        """
        return cls._usuario is not None
