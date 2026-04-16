-- Script para agregar la tabla Historial_Equipos
-- Ejecutar solo si necesitas эту функionalità

USE control_acceso;

-- Tabla Historial de Equipos (registro de altas, bajas y cambios de estado)
CREATE TABLE IF NOT EXISTS Historial_Equipos (
    id_historial_equipo INT AUTO_INCREMENT PRIMARY KEY,
    id_equipo VARCHAR(50) NOT NULL,
    tipo_accion ENUM('alta', 'baja', 'cambio_estado') NOT NULL,
    estado_anterior VARCHAR(50),
    estado_nuevo VARCHAR(50),
    descripcion TEXT,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    id_docente INT NOT NULL,
    FOREIGN KEY (id_equipo) REFERENCES Equipos(codigo)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_docente) REFERENCES Docentes(id_docente)
        ON DELETE CASCADE ON UPDATE CASCADE
);