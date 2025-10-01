# modules/sesion.py
class Sesion:
    _usuario = None

    @classmethod
    def iniciar_sesion(cls, datos_usuario: dict):
        """datos_usuario: dict con keys: id, nombres, apellidos, rol, foto (bytes) opcional"""
        cls._usuario = datos_usuario

    @classmethod
    def obtener_usuario(cls):
        return cls._usuario

    @classmethod
    def cerrar_sesion(cls):
        cls._usuario = None

    @classmethod
    def esta_autenticado(cls):
        return cls._usuario is not None
