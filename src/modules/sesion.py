# modules/sesion.py
class Sesion:
    # Variable de clase que almacena la información del usuario actual
    _usuario = None
    _hardware_info = None  # Info del hardware para pasar a ingreso
    _menu_tipo = "docente"  # Tipo de menu actual: "docente" o "administrativo"


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


    @classmethod
    def set_hardware_info(cls, info: dict):
        """
        Guarda la información del hardware para pasarla a las ventanas de ingreso.
        """
        cls._hardware_info = info


    @classmethod
    def get_hardware_info(cls):
        """
        Retorna la información del hardware guardada en la sesión.
        """
        return cls._hardware_info


    @classmethod
    def obtener_cedula(cls):
        """
        Retorna la cédula del usuario actual.
        """
        return cls._usuario.get("cedula", "") if cls._usuario else ""


    @classmethod
    def es_admin(cls):
        """
        Retorna True si el usuario actual es administrador.
        """
        if not cls._usuario:
            return False
        u = cls._usuario
        if "es_admin" in u and u["es_admin"]:
            return bool(u["es_admin"])
        if "rol" in u and u["rol"]:
            return str(u["rol"]).lower() == "admin"
        return False


    @classmethod
    def set_menu_tipo(cls, tipo):
        """
        Cambia el tipo de menu actual (docente o administrativo).
        """
        cls._menu_tipo = tipo


    @classmethod
    def get_menu_tipo(cls):
        """
        Retorna el tipo de menu actual.
        """
        return cls._menu_tipo
