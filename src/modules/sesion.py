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
        # Guarda la información del usuario autenticado en la variable compartida de clase
        cls._usuario = datos_usuario


    @classmethod
    def obtener_usuario(cls):
        """
        Retorna la información del usuario actualmente autenticado.
        Si no hay sesión iniciada, devuelve None.
        """
        # Retorna los datos del usuario almacenados en la sesión actual
        return cls._usuario


    @classmethod
    def cerrar_sesion(cls):
        """
        Cierra la sesión actual, eliminando los datos almacenados del usuario.
        """
        # Elimina la información del usuario actualmente autenticado
        cls._usuario = None


    @classmethod
    def esta_autenticado(cls):
        """
        Verifica si hay una sesión activa.
        Devuelve True si _usuario contiene información, False si no hay sesión.
        """
        # Comprueba si existe un usuario almacenado en la sesión
        return cls._usuario is not None
