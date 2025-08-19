
-- Script SQL para el sistema de control de acceso y asignación de equipos
-- Basado en el modelo ER actualizado

CREATE DATABASE IF NOT EXISTS control_acceso;
USE control_acceso;

-- Tabla Estudiantes
CREATE TABLE Estudiantes (
    id_estudiante INT AUTO_INCREMENT PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    foto_rostro LONGBLOB
);

-- Tabla Docentes (incluye administradores con flag es_admin)
CREATE TABLE Docentes (
    id_docente INT AUTO_INCREMENT PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    es_admin BOOLEAN DEFAULT FALSE,
    foto_rostro LONGBLOB
);

-- Tabla Equipos
CREATE TABLE Equipos (
    id_equipo INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    estado ENUM('disponible', 'ocupado', 'dañado') DEFAULT 'disponible'
);

-- Tabla Historial (relaciona estudiantes, docentes y equipos)
CREATE TABLE Historial (
    id_historial INT AUTO_INCREMENT PRIMARY KEY,
    id_estudiante INT,
    id_docente INT NOT NULL,
    id_equipo INT NOT NULL,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME,
    FOREIGN KEY (id_estudiante) REFERENCES Estudiantes(id_estudiante)
        ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (id_docente) REFERENCES Docentes(id_docente)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_equipo) REFERENCES Equipos(id_equipo)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla Incidentes (reportados por docentes e involucrando estudiantes/equipos)
CREATE TABLE Incidentes (
    id_incidente INT AUTO_INCREMENT PRIMARY KEY,
    id_docente INT NOT NULL,
    id_equipo INT NOT NULL,
    id_estudiante INT,
    descripcion TEXT NOT NULL,
    fecha DATE NOT NULL,
    FOREIGN KEY (id_docente) REFERENCES Docentes(id_docente)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_equipo) REFERENCES Equipos(id_equipo)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_estudiante) REFERENCES Estudiantes(id_estudiante)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- Tabla Asistencias (solo estudiantes)
CREATE TABLE Asistencias (
    id_asistencia INT AUTO_INCREMENT PRIMARY KEY,
    id_estudiante INT NOT NULL,
    fecha DATE NOT NULL,
    estado ENUM('presente','ausente') DEFAULT 'ausente',
    FOREIGN KEY (id_estudiante) REFERENCES Estudiantes(id_estudiante)
        ON DELETE CASCADE ON UPDATE CASCADE
);
