
CREATE DATABASE reclutamiento;

USE reclutamiento;

CREATE TABLE solicitudes_trabajo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(150) NOT NULL,
    telefono VARCHAR(20),
    experiencia TEXT,
    estado ENUM(
        'pendiente',
        'aceptada',
        'rechazada'
    ) NOT NULL DEFAULT 'pendiente',
    fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
