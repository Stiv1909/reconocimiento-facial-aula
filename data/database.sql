-- Script SQL para el sistema de control de acceso y asignación de equipos

CREATE DATABASE IF NOT EXISTS control_acceso;
USE control_acceso;

-- Tabla Docentes
CREATE TABLE IF NOT EXISTS Docentes (
    cedula VARCHAR(20) PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    celular VARCHAR(20),
    es_admin BOOLEAN DEFAULT FALSE,
    foto_rostro LONGBLOB
);

-- Tabla Usuarios (para login)
CREATE TABLE IF NOT EXISTS Usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(100) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL,
    cedula VARCHAR(20) NOT NULL,
    FOREIGN KEY (cedula) REFERENCES Docentes(cedula)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla Estudiantes
CREATE TABLE IF NOT EXISTS Estudiantes (
    id_estudiante INT AUTO_INCREMENT PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    grado VARCHAR(5),
    estado ENUM('Estudiante', 'Ex-Alumno') DEFAULT 'Estudiante',
    foto_rostro LONGBLOB
);

-- Tabla Equipos (con características técnicas)
CREATE TABLE IF NOT EXISTS Equipos (
    id_equipo VARCHAR(50) PRIMARY KEY,
    estado ENUM('disponible', 'dañado', 'otro') DEFAULT 'disponible',
    marca VARCHAR(50),
    modelo VARCHAR(100),
    procesador VARCHAR(100),
    ram VARCHAR(50),
    disco VARCHAR(50),
    serial VARCHAR(100),
    anio_adquisicion YEAR,
    observaciones TEXT
);

-- Tabla Matrículas
CREATE TABLE IF NOT EXISTS Matriculas (
    id_matricula VARCHAR(50) PRIMARY KEY,
    id_estudiante INT NOT NULL,
    grado VARCHAR(5) NOT NULL,
    anio YEAR NOT NULL,
    estado ENUM('Estudiante', 'Ex-Alumno') DEFAULT 'Estudiante',
    FOREIGN KEY (id_estudiante) REFERENCES Estudiantes(id_estudiante)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla Historial
CREATE TABLE IF NOT EXISTS Historial (
    id_historial INT AUTO_INCREMENT PRIMARY KEY,
    id_matricula VARCHAR(50),
    cedula VARCHAR(20) NOT NULL,
    id_equipo VARCHAR(50) NOT NULL,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME,
    FOREIGN KEY (id_matricula) REFERENCES Matriculas(id_matricula)
        ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (cedula) REFERENCES Docentes(cedula)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_equipo) REFERENCES Equipos(id_equipo)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla Incidentes
CREATE TABLE IF NOT EXISTS Incidentes (
    id_incidente INT AUTO_INCREMENT PRIMARY KEY,
    cedula VARCHAR(20) NOT NULL,
    id_equipo VARCHAR(50) NOT NULL,
    id_estudiante INT,
    id_matricula VARCHAR(50),
    descripcion TEXT NOT NULL,
    fecha DATE NOT NULL,
    FOREIGN KEY (cedula) REFERENCES Docentes(cedula)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_equipo) REFERENCES Equipos(id_equipo)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_estudiante) REFERENCES Estudiantes(id_estudiante)
        ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (id_matricula) REFERENCES Matriculas(id_matricula)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- Tabla Asistencias
CREATE TABLE IF NOT EXISTS Asistencias (
    id_asistencia INT AUTO_INCREMENT PRIMARY KEY,
    id_matricula VARCHAR(50) NOT NULL,
    fecha DATE NOT NULL,
    estado ENUM('presente','ausente') DEFAULT 'ausente',
    FOREIGN KEY (id_matricula) REFERENCES Matriculas(id_matricula)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla Historial de Equipos
CREATE TABLE IF NOT EXISTS Historial_Equipos (
    id_historial_equipo INT AUTO_INCREMENT PRIMARY KEY,
    id_equipo VARCHAR(50) NOT NULL,
    tipo_accion ENUM('alta', 'baja', 'cambio_estado') NOT NULL,
    estado_anterior VARCHAR(50),
    estado_nuevo VARCHAR(50),
    descripcion TEXT,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    cedula VARCHAR(20) NOT NULL,
    FOREIGN KEY (id_equipo) REFERENCES Equipos(id_equipo)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (cedula) REFERENCES Docentes(cedula)
        ON DELETE CASCADE ON UPDATE CASCADE
);