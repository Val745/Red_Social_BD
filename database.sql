-- Creación de la base de datos
DROP DATABASE IF EXISTS red_social;
CREATE DATABASE red_social;
USE red_social;

-- Tabla de usuarios
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    ubicacion VARCHAR(100),
    biografia TEXT,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    ultimo_login DATETIME,
    activo BOOLEAN DEFAULT TRUE,
    foto_perfil VARCHAR(255) DEFAULT 'default.jpg'
);

-- Tabla de publicaciones
CREATE TABLE publicaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    contenido TEXT NOT NULL,
    fecha_publicacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    privacidad ENUM('publico', 'amigos', 'privado') DEFAULT 'publico',
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Tabla de comentarios
CREATE TABLE comentarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    publicacion_id INT NOT NULL,
    usuario_id INT NOT NULL,
    contenido TEXT NOT NULL,
    fecha_publicacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (publicacion_id) REFERENCES publicaciones(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Tabla de me gusta
CREATE TABLE me_gusta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    publicacion_id INT NOT NULL,
    usuario_id INT NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (publicacion_id) REFERENCES publicaciones(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY (publicacion_id, usuario_id)
);

-- Tabla de amistades
CREATE TABLE amistades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario1_id INT NOT NULL,
    usuario2_id INT NOT NULL,
    fecha_amistad DATETIME DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('pendiente', 'aceptada', 'rechazada') DEFAULT 'pendiente',
    FOREIGN KEY (usuario1_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario2_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    CHECK (usuario1_id < usuario2_id)
);

-- Tabla de mensajes
CREATE TABLE mensajes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    emisor_id INT NOT NULL,
    receptor_id INT NOT NULL,
    contenido TEXT NOT NULL,
    fecha_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
    leido BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (emisor_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (receptor_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Tabla de notificaciones
CREATE TABLE notificaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    tipo ENUM('amistad', 'me_gusta', 'comentario', 'mensaje') NOT NULL,
    contenido TEXT NOT NULL,
    fecha_notificacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    leida BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Índices para optimización
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_publicaciones_usuario ON publicaciones(usuario_id);
CREATE INDEX idx_comentarios_publicacion ON comentarios(publicacion_id);
CREATE INDEX idx_me_gusta_publicacion ON me_gusta(publicacion_id);
CREATE INDEX idx_amistades_usuario1 ON amistades(usuario1_id);
CREATE INDEX idx_amistades_usuario2 ON amistades(usuario2_id);
CREATE INDEX idx_mensajes_emisor_receptor ON mensajes(emisor_id, receptor_id);

-- Datos de ejemplo
-- Insertar usuarios
INSERT INTO usuarios (nombre, apellido, email, password_hash, fecha_nacimiento, ubicacion, biografia) VALUES
('Juan', 'Pérez', 'juan@example.com', SHA2('password123', 256), '1990-05-15', 'Ciudad de México', 'Desarrollador web y amante de la tecnología'),
('María', 'Gómez', 'maria@example.com', SHA2('securepass', 256), '1988-11-22', 'Bogotá', 'Diseñadora gráfica y fotógrafa amateur'),
('Carlos', 'Rodríguez', 'carlos@example.com', SHA2('mypassword', 256), '1995-03-10', 'Madrid', 'Estudiante de ingeniería informática'),
('Ana', 'López', 'ana@example.com', SHA2('anapass123', 256), '1992-07-30', 'Buenos Aires', 'Chef profesional y food blogger'),
('Luis', 'Martínez', 'luis@example.com', SHA2('luispass', 256), '1985-09-18', 'Santiago', 'Ingeniero civil especializado en puentes'),
('Laura', 'Hernández', 'laura@example.com', SHA2('laurapass', 256), '1993-12-05', 'Lima', 'Psicóloga clínica con enfoque cognitivo');

-- Insertar publicaciones
INSERT INTO publicaciones (usuario_id, contenido) VALUES
(1, 'Hoy es un gran día para aprender sobre bases de datos!'),
(2, 'Acabo de terminar mi proyecto final, qué alivio!'),
(3, 'Alguien quiere reunirse para estudiar para el examen?'),
(4, 'Nueva receta en mi blog: Pastel de chocolate sin harina!'),
(1, 'Recomendaciones de libros sobre programación?'),
(3, 'Alguien sabe de buenos cursos online para aprender Python?'),
(5, 'Acabo de publicar un artículo sobre estructuras de acero en mi blog'),
(6, 'Taller gratuito de manejo de ansiedad este fin de semana'),
(2, 'Fotos de mi último viaje a la playa ahora en mi perfil!'),
(4, 'Consejos para mantener una alimentación saludable durante la cuarentena');

-- Insertar amistades
INSERT INTO amistades (usuario1_id, usuario2_id, estado) VALUES
(1, 2, 'aceptada'),
(1, 3, 'aceptada'),
(2, 4, 'aceptada'),
(3, 4, 'pendiente'),
(1, 5, 'aceptada'),
(2, 6, 'aceptada'),
(3, 5, 'pendiente');

-- Insertar me gusta
INSERT INTO me_gusta (publicacion_id, usuario_id) VALUES
(1, 2),
(1, 3),
(2, 1),
(2, 4),
(3, 2),
(4, 1),
(4, 2),
(5, 3),
(6, 1),
(6, 4),
(7, 1),
(7, 3),
(8, 2),
(8, 4),
(9, 1),
(9, 3),
(10, 2),
(10, 5);

-- Insertar comentarios
INSERT INTO comentarios (publicacion_id, usuario_id, contenido) VALUES
(1, 2, 'Totalmente de acuerdo, Juan!'),
(1, 3, 'Qué interesante tema!'),
(2, 1, 'Felicidades María!'),
(2, 4, 'Qué bien, a celebrar!'),
(3, 2, 'Yo puedo el fin de semana'),
(4, 1, 'Se ve delicioso!'),
(5, 3, 'Clean Code de Robert Martin es excelente'),
(6, 2, 'En Coursera hay buenos cursos'),
(7, 4, 'Muy interesante tu artículo'),
(8, 1, 'Dónde será el taller?'),
(9, 3, 'Hermosas fotos!'),
(10, 5, 'Excelentes consejos, gracias');

-- Insertar mensajes
INSERT INTO mensajes (emisor_id, receptor_id, contenido) VALUES
(1, 2, 'Hola María, cómo estás?'),
(2, 1, 'Hola Juan! Todo bien, gracias por preguntar'),
(1, 3, 'Carlos, qué tal el estudio?'),
(3, 1, 'Bien, pero necesito repasar algunos temas'),
(4, 2, 'María, te gustaría colaborar en un proyecto?'),
(2, 4, 'Claro Ana, cuéntame más'),
(5, 1, 'Juan, viste mi último artículo?'),
(6, 2, 'María, te envié información sobre el taller');

-- Insertar notificaciones
INSERT INTO notificaciones (usuario_id, tipo, contenido) VALUES
(2, 'amistad', 'Juan Pérez te ha enviado una solicitud de amistad'),
(3, 'me_gusta', 'A María Gómez le gustó tu publicación'),
(1, 'comentario', 'Carlos Rodríguez ha comentado en tu publicación'),
(4, 'mensaje', 'Tienes un nuevo mensaje de Ana López');

-- Vistas
-- Vista de perfil de usuario resumido
CREATE VIEW vista_perfil_usuario AS
SELECT u.id, u.nombre, u.apellido, u.email, u.biografia, u.ubicacion, 
       TIMESTAMPDIFF(YEAR, u.fecha_nacimiento, CURDATE()) AS edad,
       (SELECT COUNT(*) FROM publicaciones WHERE usuario_id = u.id) AS total_publicaciones,
       (SELECT COUNT(*) FROM (
           SELECT usuario2_id FROM amistades WHERE usuario1_id = u.id AND estado = 'aceptada'
           UNION
           SELECT usuario1_id FROM amistades WHERE usuario2_id = u.id AND estado = 'aceptada'
       ) AS amigos) AS total_amigos
FROM usuarios u;

-- Vista de muro de noticias de un usuario
CREATE VIEW vista_muro_noticias AS
SELECT p.id, p.contenido, p.fecha_publicacion, u.nombre, u.apellido, u.id AS usuario_id
FROM publicaciones p
JOIN usuarios u ON p.usuario_id = u.id
WHERE p.usuario_id IN (
    SELECT usuario2_id FROM amistades WHERE usuario1_id = 1 AND estado = 'aceptada'
    UNION
    SELECT usuario1_id FROM amistades WHERE usuario2_id = 1 AND estado = 'aceptada'
) OR p.usuario_id = 1
ORDER BY p.fecha_publicacion DESC;

-- Vista de estadísticas de la red social
CREATE VIEW vista_estadisticas AS
SELECT 
    (SELECT COUNT(*) FROM usuarios) AS total_usuarios,
    (SELECT COUNT(*) FROM publicaciones) AS total_publicaciones,
    (SELECT COUNT(*) FROM comentarios) AS total_comentarios,
    (SELECT COUNT(*) FROM me_gusta) AS total_me_gusta,
    (SELECT COUNT(*) FROM amistades WHERE estado = 'aceptada') AS total_amistades,
    (SELECT COUNT(*) FROM mensajes) AS total_mensajes,
    (SELECT COUNT(*) FROM usuarios WHERE ultimo_login >= DATE_SUB(NOW(), INTERVAL 7 DAY)) AS usuarios_activos_7dias;

-- Procedimientos almacenados
DELIMITER //

-- Procedimiento para insertar un nuevo usuario
CREATE PROCEDURE insertar_usuario(
    IN p_nombre VARCHAR(50),
    IN p_apellido VARCHAR(50),
    IN p_email VARCHAR(100),
    IN p_password VARCHAR(255),
    IN p_fecha_nacimiento DATE,
    IN p_ubicacion VARCHAR(100),
    IN p_biografia TEXT
)
BEGIN
    INSERT INTO usuarios (nombre, apellido, email, password_hash, fecha_nacimiento, ubicacion, biografia)
    VALUES (p_nombre, p_apellido, p_email, SHA2(p_password, 256), p_fecha_nacimiento, p_ubicacion, p_biografia);
END //

-- Procedimiento para eliminar una publicación
CREATE PROCEDURE eliminar_publicacion(
    IN p_publicacion_id INT,
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_es_propietario INT;
    
    SELECT COUNT(*) INTO v_es_propietario
    FROM publicaciones
    WHERE id = p_publicacion_id AND usuario_id = p_usuario_id;
    
    IF v_es_propietario > 0 THEN
        DELETE FROM publicaciones WHERE id = p_publicacion_id;
        SELECT 'Publicación eliminada correctamente' AS mensaje;
    ELSE
        SELECT 'No tienes permiso para eliminar esta publicación' AS mensaje;
    END IF;
END //

-- Procedimiento para enviar notificación a amigos
CREATE PROCEDURE notificar_amigos(
    IN p_usuario_id INT,
    IN p_tipo ENUM('amistad', 'me_gusta', 'comentario', 'mensaje'),
    IN p_contenido TEXT
)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_amigo_id INT;
    DECLARE cur CURSOR FOR 
        SELECT usuario2_id FROM amistades WHERE usuario1_id = p_usuario_id AND estado = 'aceptada'
        UNION
        SELECT usuario1_id FROM amistades WHERE usuario2_id = p_usuario_id AND estado = 'aceptada';
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN cur;
    
    read_loop: LOOP
        FETCH cur INTO v_amigo_id;
        IF done THEN
            LEAVE read_loop;
        END IF;
        
        INSERT INTO notificaciones (usuario_id, tipo, contenido)
        VALUES (v_amigo_id, p_tipo, p_contenido);
    END LOOP;
    
    CLOSE cur;
END //

DELIMITER ;