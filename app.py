from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = '754008b5554056dc63cc680d6075df88e40cafe380c1fa105a13e2ac6f91307f'

# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'red_social'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error de conexión: {err}")
        raise  # Re-lanza la excepción para manejarla en el llamador

from contextlib import contextmanager

@contextmanager
def get_db_cursor():
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        yield cursor
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Rutas de la aplicación
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        with get_db_cursor() as cursor:
            # Obtener información del usuario
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (session['user_id'],))
            usuario = cursor.fetchone()
            
            # Obtener publicaciones del muro
            cursor.execute("""
                SELECT p.id, p.contenido, p.fecha_publicacion, u.nombre, u.apellido, 
                       (SELECT COUNT(*) FROM me_gusta WHERE publicacion_id = p.id) AS likes,
                       u.id AS usuario_id
                FROM publicaciones p
                JOIN usuarios u ON p.usuario_id = u.id
                WHERE p.usuario_id IN (
                    SELECT usuario2_id FROM amistades WHERE usuario1_id = %s AND estado = 'aceptada'
                    UNION
                    SELECT usuario1_id FROM amistades WHERE usuario2_id = %s AND estado = 'aceptada'
                ) OR p.usuario_id = %s
                ORDER BY p.fecha_publicacion DESC
                LIMIT 20
            """, (session['user_id'], session['user_id'], session['user_id']))
            publicaciones = cursor.fetchall()
            
            # Obtener comentarios para cada publicación (versión corregida)
            for pub in publicaciones:
                cursor.execute("""
                    SELECT c.id, c.contenido, c.fecha_publicacion, 
                           u.id AS usuario_id, u.nombre, u.apellido
                    FROM comentarios c
                    JOIN usuarios u ON c.usuario_id = u.id
                    WHERE c.publicacion_id = %s
                    ORDER BY c.fecha_publicacion
                """, (pub['id'],))
                pub['comentarios'] = cursor.fetchall()

            # Obtener amigos
            cursor.execute("""
                SELECT u.id, u.nombre, u.apellido 
                FROM usuarios u
                JOIN (
                    SELECT usuario2_id AS amigo_id FROM amistades WHERE usuario1_id = %s AND estado = 'aceptada'
                    UNION
                    SELECT usuario1_id AS amigo_id FROM amistades WHERE usuario2_id = %s AND estado = 'aceptada'
                ) a ON u.id = a.amigo_id
                LIMIT 10
            """, (session['user_id'], session['user_id']))
            amigos = cursor.fetchall()
            
            # Contar mensajes no leídos (versión corregida)
            cursor.execute("""
                SELECT COUNT(*) AS unread_count FROM mensajes 
                WHERE receptor_id = %s AND leido = FALSE
            """, (session['user_id'],))
            result = cursor.fetchone()
            unread_count = result['unread_count'] if result else 0
            
            print("Estructura de comentarios:")
            for pub in publicaciones:
                print(f"Publicación {pub['id']} tiene {len(pub['comentarios'])} comentarios")
                for comentario in pub['comentarios']:
                    print(comentario)  # Verifica las claves disponibles
        return render_template('index.html', 
                            usuario=usuario, 
                            publicaciones=publicaciones,
                            amigos=amigos,
                            unread_count=unread_count)
            
    except mysql.connector.Error as err:
        flash('Error de base de datos. Por favor intenta nuevamente.', 'error')
        print(f"Database error: {err}")
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Buscar usuario por email
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            usuario = cursor.fetchone()
            
            if usuario:
                # Verificar contraseña (usando SHA2 que es lo que usaste en los inserts)
                cursor.execute("SELECT SHA2(%s, 256) AS hash", (password,))
                password_hash = cursor.fetchone()['hash']
                
                if usuario['password_hash'] == password_hash:
                    session['user_id'] = usuario['id']
                    session['nombre'] = usuario['nombre']
                    
                    # Actualizar último login
                    cursor.execute("UPDATE usuarios SET ultimo_login = NOW() WHERE id = %s", (usuario['id'],))
                    conn.commit()
                    
                    flash('Has iniciado sesión correctamente', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Contraseña incorrecta', 'error')
            else:
                flash('Usuario no encontrado', 'error')
                
        except Exception as e:
            print(f"Error en login: {e}")
            flash('Error al iniciar sesión', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        fecha_nacimiento = request.form['fecha_nacimiento']
        ubicacion = request.form['ubicacion']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO usuarios (nombre, apellido, email, password_hash, fecha_nacimiento, ubicacion)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (nombre, apellido, email, password, fecha_nacimiento, ubicacion))
            conn.commit()
            
            cursor.execute("SELECT LAST_INSERT_ID() AS id")
            user_id = cursor.fetchone()[0]
            
            session['user_id'] = user_id
            session['nombre'] = nombre
            flash('Registro exitoso! Bienvenido a nuestra red social', 'success')
            return redirect(url_for('index'))
        except mysql.connector.IntegrityError:
            flash('El email ya está registrado', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('registro.html')

@app.route('/publicar', methods=['POST'])
def publicar():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    contenido = request.form['contenido']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO publicaciones (usuario_id, contenido)
            VALUES (%s, %s)
        """, (session['user_id'], contenido))
        conn.commit()
        flash('Publicación creada exitosamente!', 'success')
    except Exception as e:
        flash('Error al publicar', 'error')
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/comentar', methods=['POST'])
def comentar():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    publicacion_id = request.form['publicacion_id']
    contenido = request.form['contenido']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO comentarios (publicacion_id, usuario_id, contenido)
            VALUES (%s, %s, %s)
        """, (publicacion_id, session['user_id'], contenido))
        conn.commit()
        flash('Comentario agregado!', 'success')
    except Exception as e:
        flash('Error al comentar', 'error')
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/like/<int:publicacion_id>')
def like(publicacion_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar si ya dio like
        cursor.execute("""
            SELECT id FROM me_gusta 
            WHERE publicacion_id = %s AND usuario_id = %s
        """, (publicacion_id, session['user_id']))
        
        if cursor.fetchone():
            # Quitar like
            cursor.execute("""
                DELETE FROM me_gusta 
                WHERE publicacion_id = %s AND usuario_id = %s
            """, (publicacion_id, session['user_id']))
            flash('Like removido', 'info')
        else:
            # Dar like
            cursor.execute("""
                INSERT INTO me_gusta (publicacion_id, usuario_id)
                VALUES (%s, %s)
            """, (publicacion_id, session['user_id']))
            flash('Like agregado!', 'success')
        
        conn.commit()
    except Exception as e:
        flash('Error al procesar like', 'error')
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('index'))


@app.route('/mensajes')
def mensajes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Obtener conversaciones
    cursor.execute("""
        SELECT u.id, u.nombre, u.apellido, 
               (SELECT contenido FROM mensajes 
                WHERE (emisor_id = %s AND receptor_id = u.id) 
                   OR (emisor_id = u.id AND receptor_id = %s)
                ORDER BY fecha_envio DESC LIMIT 1) AS ultimo_mensaje,
               (SELECT fecha_envio FROM mensajes 
                WHERE (emisor_id = %s AND receptor_id = u.id) 
                   OR (emisor_id = u.id AND receptor_id = %s)
                ORDER BY fecha_envio DESC LIMIT 1) AS fecha_ultimo_mensaje,
               (SELECT COUNT(*) FROM mensajes 
                WHERE receptor_id = %s AND emisor_id = u.id AND leido = FALSE) AS no_leidos
        FROM usuarios u
        WHERE u.id IN (
            SELECT emisor_id FROM mensajes WHERE receptor_id = %s
            UNION
            SELECT receptor_id FROM mensajes WHERE emisor_id = %s
        )
        ORDER BY fecha_ultimo_mensaje DESC
    """, (session['user_id'], session['user_id'], session['user_id'], session['user_id'], session['user_id'], session['user_id'], session['user_id']))
    
    conversaciones = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('mensajes.html', conversaciones=conversaciones)

@app.route('/mensajes/<int:usuario_id>', methods=['GET', 'POST'])
def conversacion(usuario_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Obtener información del otro usuario
    cursor.execute("SELECT id, nombre, apellido FROM usuarios WHERE id = %s", (usuario_id,))
    otro_usuario = cursor.fetchone()
    
    if not otro_usuario:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('mensajes'))
    
    # Si es un POST, enviar mensaje
    if request.method == 'POST':
        contenido = request.form.get('contenido', '').strip()
        if contenido:
            try:
                cursor.execute("""
                    INSERT INTO mensajes (emisor_id, receptor_id, contenido)
                    VALUES (%s, %s, %s)
                """, (session['user_id'], usuario_id, contenido))
                conn.commit()
                flash('Mensaje enviado!', 'success')
            except Exception as e:
                conn.rollback()
                flash('Error al enviar el mensaje', 'error')
                print(f"Error al enviar mensaje: {e}")
    
    # Marcar mensajes como leídos
    cursor.execute("""
        UPDATE mensajes SET leido = TRUE 
        WHERE emisor_id = %s AND receptor_id = %s AND leido = FALSE
    """, (usuario_id, session['user_id']))
    conn.commit()
    
    # Obtener la conversación
    cursor.execute("""
        SELECT m.*, u.nombre, u.apellido 
        FROM mensajes m
        JOIN usuarios u ON m.emisor_id = u.id
        WHERE (m.emisor_id = %s AND m.receptor_id = %s) 
           OR (m.emisor_id = %s AND m.receptor_id = %s)
        ORDER BY m.fecha_envio
    """, (session['user_id'], usuario_id, usuario_id, session['user_id']))
    
    mensajes = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('conversacion.html', 
                         otro_usuario=otro_usuario, 
                         mensajes=mensajes)

@app.route('/enviar_mensaje', methods=['POST'])
def enviar_mensaje():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        receptor_id = int(request.form['receptor_id'])
        contenido = request.form['contenido'].strip()
        
        if not contenido:
            flash('El mensaje no puede estar vacío', 'error')
            return redirect(url_for('conversacion', usuario_id=receptor_id))
        
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO mensajes (emisor_id, receptor_id, contenido)
                VALUES (%s, %s, %s)
            """, (session['user_id'], receptor_id, contenido))
            
            # Crear notificación
            cursor.execute("""
                INSERT INTO notificaciones (usuario_id, tipo, contenido)
                VALUES (%s, 'mensaje', %s)
            """, (receptor_id, f"Nuevo mensaje de {session['nombre']}"))
            
        flash('Mensaje enviado correctamente', 'success')
        return redirect(url_for('conversacion', usuario_id=receptor_id))
        
    except Exception as e:
        flash('Error al enviar el mensaje', 'error')
        print(f"Error al enviar mensaje: {e}")
        return redirect(url_for('mensajes'))
    
@app.route('/amistad/<int:amigo_id>/<action>')
def gestion_amistad(amigo_id, action):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        usuario_id = session['user_id']
        
        if action == 'enviar':
            # Asegurarse de que usuario1_id es siempre el menor para evitar duplicados
            usuario1_id, usuario2_id = sorted([usuario_id, amigo_id])
            
            cursor.execute("""
                INSERT INTO amistades (usuario1_id, usuario2_id, estado)
                VALUES (%s, %s, 'pendiente')
                ON DUPLICATE KEY UPDATE estado='pendiente'
            """, (usuario1_id, usuario2_id))
            flash('Solicitud de amistad enviada', 'success')
            
        elif action == 'aceptar':
            cursor.execute("""
                UPDATE amistades 
                SET estado = 'aceptada' 
                WHERE ((usuario1_id = %s AND usuario2_id = %s) OR (usuario1_id = %s AND usuario2_id = %s))
                AND estado = 'pendiente'
            """, (amigo_id, usuario_id, usuario_id, amigo_id))
            flash('Solicitud de amistad aceptada', 'success')
            
        elif action == 'rechazar':
            cursor.execute("""
                DELETE FROM amistades 
                WHERE ((usuario1_id = %s AND usuario2_id = %s) OR (usuario1_id = %s AND usuario2_id = %s))
                AND estado = 'pendiente'
            """, (amigo_id, usuario_id, usuario_id, amigo_id))
            flash('Solicitud de amistad rechazada', 'info')
            
        elif action == 'eliminar':
            cursor.execute("""
                DELETE FROM amistades 
                WHERE (usuario1_id = %s AND usuario2_id = %s) OR (usuario1_id = %s AND usuario2_id = %s)
            """, (usuario_id, amigo_id, amigo_id, usuario_id))
            flash('Amistad eliminada', 'info')
            
        conn.commit()
    except Exception as e:
        flash('Error al procesar la solicitud', 'error')
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('index'))
@app.route('/manejar_amistad', methods=['POST'])
def manejar_amistad():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        amigo_id = int(request.form['amigo_id'])
        accion = request.form['accion']
        
        with get_db_cursor() as cursor:
            # Asegurarse de que usuario1_id es siempre el menor
            usuario1_id, usuario2_id = sorted([session['user_id'], amigo_id])
            
            if accion == 'enviar':
                cursor.execute("""
                    INSERT INTO amistades (usuario1_id, usuario2_id, estado)
                    VALUES (%s, %s, 'pendiente')
                    ON DUPLICATE KEY UPDATE estado='pendiente'
                """, (usuario1_id, usuario2_id))
                
                # Crear notificación
                cursor.execute("""
                    SELECT nombre FROM usuarios WHERE id = %s
                """, (session['user_id'],))
                nombre = cursor.fetchone()['nombre']
                
                cursor.execute("""
                    INSERT INTO notificaciones (usuario_id, tipo, contenido)
                    VALUES (%s, 'amistad', %s)
                """, (amigo_id, f"Solicitud de amistad de {nombre}"))
                
                flash('Solicitud enviada', 'success')
                
            elif accion == 'aceptar':
                cursor.execute("""
                    UPDATE amistades 
                    SET estado = 'aceptada'
                    WHERE usuario1_id = %s AND usuario2_id = %s
                """, (usuario1_id, usuario2_id))
                flash('Solicitud aceptada', 'success')
                
            elif accion == 'rechazar':
                cursor.execute("""
                    DELETE FROM amistades
                    WHERE usuario1_id = %s AND usuario2_id = %s
                """, (usuario1_id, usuario2_id))
                flash('Solicitud rechazada', 'info')
                
            elif accion == 'cancelar':
                cursor.execute("""
                    DELETE FROM amistades
                    WHERE usuario1_id = %s AND usuario2_id = %s
                """, (usuario1_id, usuario2_id))
                flash('Solicitud cancelada', 'info')
                
        return redirect(request.referrer or url_for('index'))
        
    except Exception as e:
        flash('Error al procesar la solicitud', 'error')
        print(f"Error en manejar_amistad: {e}")
        return redirect(url_for('index'))
    
@app.route('/buscar', methods=['GET'])
def buscar():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    query = request.args.get('q', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT id, nombre, apellido, email 
        FROM usuarios 
        WHERE nombre LIKE %s OR apellido LIKE %s
        LIMIT 20
    """, (f'%{query}%', f'%{query}%'))
    
    resultados = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('buscar.html', resultados=resultados, query=query)

@app.route('/perfil/<int:usuario_id>')
def ver_perfil(usuario_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    

    try:
        with get_db_cursor() as cursor:
            # Obtener información del perfil
            cursor.execute("""
                SELECT u.*, 
                       TIMESTAMPDIFF(YEAR, u.fecha_nacimiento, CURDATE()) AS edad,
                       (SELECT COUNT(*) FROM publicaciones WHERE usuario_id = u.id) AS total_publicaciones,
                       (SELECT COUNT(*) FROM (
                           SELECT usuario2_id FROM amistades WHERE usuario1_id = u.id AND estado = 'aceptada'
                           UNION
                           SELECT usuario1_id FROM amistades WHERE usuario2_id = u.id AND estado = 'aceptada'
                       ) AS amigos) AS total_amigos
                FROM usuarios u
                WHERE u.id = %s
            """, (usuario_id,))
            perfil = cursor.fetchone()

            if not perfil:
                flash('Usuario no encontrado', 'error')
                return redirect(url_for('index'))

            # Obtener información completa de la amistad (esto es nuevo)
            cursor.execute("""
                SELECT * FROM amistades 
                WHERE (usuario1_id = %s AND usuario2_id = %s) 
                   OR (usuario1_id = %s AND usuario2_id = %s)
            """, (session['user_id'], usuario_id, usuario_id, session['user_id']))
            
            amistad = cursor.fetchone()
            estado_amistad = amistad['estado'] if amistad else None

            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Obtener información del perfil
            cursor.execute("""
                SELECT u.*, 
                    TIMESTAMPDIFF(YEAR, u.fecha_nacimiento, CURDATE()) AS edad,
                    (SELECT COUNT(*) FROM publicaciones WHERE usuario_id = u.id) AS total_publicaciones,
                    (SELECT COUNT(*) FROM (
                        SELECT usuario2_id FROM amistades WHERE usuario1_id = u.id AND estado = 'aceptada'
                        UNION
                        SELECT usuario1_id FROM amistades WHERE usuario2_id = u.id AND estado = 'aceptada'
                    ) AS amigos) AS total_amigos
                FROM usuarios u
                WHERE u.id = %s
            """, (usuario_id,))
            perfil = cursor.fetchone()
            
            if not perfil:
                flash('Usuario no encontrado', 'error')
                return redirect(url_for('index'))
            
            # Verificar estado de amistad
            cursor.execute("""
                SELECT estado FROM amistades 
                WHERE (usuario1_id = %s AND usuario2_id = %s) OR (usuario1_id = %s AND usuario2_id = %s)
            """, (session['user_id'], usuario_id, usuario_id, session['user_id']))
            
            amistad = cursor.fetchone()
            estado_amistad = amistad['estado'] if amistad else None
            
            # Obtener publicaciones del perfil
            cursor.execute("""
                SELECT p.id, p.contenido, p.fecha_publicacion, 
                    (SELECT COUNT(*) FROM me_gusta WHERE publicacion_id = p.id) AS likes,
                    (SELECT COUNT(*) FROM me_gusta WHERE publicacion_id = p.id AND usuario_id = %s) AS liked
                FROM publicaciones p
                WHERE p.usuario_id = %s
                ORDER BY p.fecha_publicacion DESC
                LIMIT 10
            """, (session['user_id'], usuario_id))
            publicaciones = cursor.fetchall()
            
            cursor.close()
            conn.close()
    
            return render_template('perfil.html', 
                                perfil=perfil, 
                                publicaciones=publicaciones,
                                estado_amistad=estado_amistad)
    except Exception as e:
        flash('Error al cargar el perfil', 'error')
        print(f"Error: {e}")
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)