from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'hospitalizacion_db'

mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/lista_pacientes')
def lista_pacientes():
    cursor = mysql.connection.cursor()
    #el LEFT JOIN nos permite traer el nombre del tipo de diagnóstico aunque el paciente no tenga uno asignado (NULL)
    query_pacientes = """
        SELECT p.id, p.nombre, p.apellido, t.nombre AS tipo_diagnostico, p.tipo_diagnostico_id
        FROM paciente p
        LEFT JOIN tipo_diagnostico t ON p.tipo_diagnostico_id = t.id
    """
    cursor.execute(query_pacientes)
    datos_pacientes = cursor.fetchall()
    
    cursor.execute("SELECT * FROM tipo_diagnostico")
    tipos_diagnostico = cursor.fetchall()
    cursor.close()

    return render_template('pacientes.html', pacientes=datos_pacientes, tipos=tipos_diagnostico)

# Guardar Nuevo Paciente (POST)
@app.route('/lista_pacientes/crear', methods=['POST'])
def crear_paciente():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        tipo_diagnostico_id = request.form['tipo_diagnostico_id']
        
        # Si no seleccionó un diagnóstico en el select, guardamos NULL en la BD
        if tipo_diagnostico_id == "":
            tipo_diagnostico_id = None

        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO paciente (nombre, apellido, tipo_diagnostico_id) 
            VALUES (%s, %s, %s)
        """, (nombre, apellido, tipo_diagnostico_id))
        mysql.connection.commit()
        cursor.close()
        
        return redirect(url_for('lista_pacientes'))

# EDITAR
@app.route('/lista_pacientes/editar/<int:id>', methods=['POST'])
def editar_paciente(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        tipo_diagnostico_id = request.form['tipo_diagnostico_id']
        
        if tipo_diagnostico_id == "":
            tipo_diagnostico_id = None

        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE paciente 
            SET nombre = %s, apellido = %s, tipo_diagnostico_id = %s 
            WHERE id = %s
        """, (nombre, apellido, tipo_diagnostico_id, id))
        mysql.connection.commit()
        cursor.close()
        
        return redirect(url_for('lista_pacientes'))

# Eliminar Paciente
@app.route('/lista_pacientes/eliminar/<int:id>')
def eliminar_paciente(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM hospitalizacion WHERE paciente_id = %s", (id,))
    cursor.execute("DELETE FROM paciente WHERE id = %s", (id,))
    mysql.connection.commit()
    cursor.close()
    
    return redirect(url_for('lista_pacientes'))
#HOSPITALIZACIONES
@app.route('/hospitalizaciones')
def listar_hospitalizaciones():
    # Creamos el cursor especificando que queremos los resultados como Diccionarios
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT h.id, h.paciente_id, h.fecha_ingreso, h.fecha_alta, h.sala_id,
        p.nombre AS nombre_paciente, p.apellido AS apellido_paciente,
        s.nombre AS nombre_sala
        FROM hospitalizacion h
        INNER JOIN paciente p ON h.paciente_id = p.id
        INNER JOIN sala s ON h.sala_id = s.id
    """)
    lista_hospitalizaciones = cursor.fetchall()
    cursor.execute("SELECT id, nombre, apellido FROM paciente")
    lista_pacientes = cursor.fetchall()
    
    # 3. Traer todas las salas para los select de los formularios (Crear/Editar)
    cursor.execute("SELECT id, nombre FROM sala")
    lista_salas = cursor.fetchall()
    
    cursor.close()
    
    return render_template('hospitalizaciones.html', 
        hospitalizaciones=lista_hospitalizaciones, 
        pacientes=lista_pacientes, 
        salas=lista_salas)

@app.route('/hospitalizaciones/crear', methods=['POST'])
def crear_hospitalizacion():
    paciente_id = request.form.get('paciente_id')
    fecha_ingreso = request.form.get('fecha_ingreso')
    fecha_alta = request.form.get('fecha_alta')
    sala_id = request.form.get('sala_id')
    
    # Si la fecha de alta está vacía en el formulario, guardamos NULL en la base de datos
    if not fecha_alta:
        fecha_alta = None

    cursor = mysql.connection.cursor()
    query = """
        INSERT INTO hospitalizacion (paciente_id, fecha_ingreso, fecha_alta, sala_id) 
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (paciente_id, fecha_ingreso, fecha_alta, sala_id))
    mysql.connection.commit() # Confirmamos los cambios en la BD
    cursor.close()
    
    return redirect(url_for('listar_hospitalizaciones'))

@app.route('/hospitalizaciones/modificar/<int:id>', methods=['POST'])
def modificar_hospitalizacion(id):
    paciente_id = request.form.get('paciente_id')
    fecha_ingreso = request.form.get('fecha_ingreso')
    fecha_alta = request.form.get('fecha_alta')
    sala_id = request.form.get('sala_id')
    
    if not fecha_alta:
        fecha_alta = None

    cursor = mysql.connection.cursor()
    query = """
        UPDATE hospitalizacion 
        SET paciente_id = %s, fecha_ingreso = %s, fecha_alta = %s, sala_id = %s 
        WHERE id = %s
    """
    cursor.execute(query, (paciente_id, fecha_ingreso, fecha_alta, sala_id, id))
    mysql.connection.commit()
    cursor.close()
    
    return redirect(url_for('listar_hospitalizaciones'))

@app.route('/hospitalizaciones/eliminar/<int:id>')
def eliminar_hospitalizacion(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM hospitalizacion WHERE id = %s", (id,))
    mysql.connection.commit()
    cursor.close()
    
    return redirect(url_for('listar_hospitalizaciones'))

# SALAS

@app.route('/salas')
def lista_salas():
    # Usamos DictCursor para manejar los datos como diccionarios en la plantilla
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM sala")
    datos_salas = cursor.fetchall()
    cursor.close()
    return render_template('salas.html', salas=datos_salas)


@app.route('/salas/crear', methods=['POST'])
def crear_sala():
    nombre = request.form.get('nombre')
    capacidad = request.form.get('capacidad')
    
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO sala (nombre, capacidad) VALUES (%s, %s)", (nombre, capacidad))
    mysql.connection.commit()
    cursor.close()
    
    return redirect(url_for('lista_salas'))


@app.route('/salas/modificar/<int:id>', methods=['POST'])
def modificar_sala(id):
    nombre = request.form.get('nombre')
    capacidad = request.form.get('capacidad')
    
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE sala SET nombre=%s, capacidad=%s WHERE id=%s", (nombre, capacidad, id))
    mysql.connection.commit()
    cursor.close()
    
    return redirect(url_for('lista_salas'))


@app.route('/salas/eliminar/<int:id>')
def eliminar_sala(id):
    cursor = mysql.connection.cursor()
    # Opcional: Elimina primero cascadas en hospitalización si tu base de datos lo requiere
    cursor.execute("DELETE FROM hospitalizacion WHERE sala_id = %s", (id,))
    cursor.execute("DELETE FROM sala WHERE id = %s", (id,))
    mysql.connection.commit()
    cursor.close()
    
    return redirect(url_for('lista_salas'))

# TIPOS DE DIAGNÓSTICO
# --- TIPOS DE DIAGNÓSTICO ---

@app.route('/tipos-diagnostico')
def lista_tipos_diagnostico():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM tipo_diagnostico")
    datos_tipos = cursor.fetchall()
    cursor.close()
    return render_template('tipos.html', tipos=datos_tipos)


@app.route('/tipos-diagnostico/crear', methods=['POST'])
def crear_tipo_diagnostico():
    nombre = request.form.get('nombre')
    
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO tipo_diagnostico (nombre) VALUES (%s)", (nombre,))
    mysql.connection.commit()
    cursor.close()
    
    return redirect(url_for('lista_tipos_diagnostico'))


@app.route('/tipos-diagnostico/modificar/<int:id>', methods=['POST'])
def modificar_tipo_diagnostico(id):
    nombre = request.form.get('nombre')
    
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE tipo_diagnostico SET nombre=%s WHERE id=%s", (nombre, id))
    mysql.connection.commit()
    cursor.close()
    
    return redirect(url_for('lista_tipos_diagnostico'))


@app.route('/tipos-diagnostico/eliminar/<int:id>')
def eliminar_tipo_diagnostico(id):
    cursor = mysql.connection.cursor()
    try:
        # Se intenta eliminar el tipo de diagnóstico
        cursor.execute("DELETE FROM tipo_diagnostico WHERE id=%s", (id,))
        mysql.connection.commit()
    except Exception as e:
        # Si da error por llave foránea (pacientes que dependen de él), cancelamos los cambios
        mysql.connection.rollback()
        return "Error al eliminar: existen pacientes asociados a este diagnóstico.", 500
    finally:
        cursor.close()
        
    return redirect(url_for('lista_tipos_diagnostico'))

#----consultas----
# --- CONSULTA 1: PACIENTES ACTUALMENTE INTERNADOS ---
# --- CONSULTA 1: PACIENTES ACTUALMENTE INTERNADOS (SIN CONTADOR DE DÍAS) ---
@app.route('/consulta-internados')
def consulta_internados():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Buscamos únicamente hospitalizaciones activas (fecha_alta es NULL)
    query = """
        SELECT h.id, p.nombre AS nombre_paciente, p.apellido AS apellido_paciente, 
        s.nombre AS nombre_sala, h.fecha_ingreso
        FROM hospitalizacion h
        INNER JOIN paciente p ON h.paciente_id = p.id
        INNER JOIN sala s ON h.sala_id = s.id
        WHERE h.fecha_alta IS NULL
        ORDER BY h.fecha_ingreso ASC
    """
    cursor.execute(query)
    internados = cursor.fetchall()
    cursor.close()
    return render_template('consulta_internados.html', pacientes=internados)


# --- CONSULTA 2: PACIENTES FILTRADOS POR DIAGNÓSTICO ---
@app.route('/consulta-por-diagnostico', methods=['GET', 'POST'])
def consulta_por_diagnostico():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Siempre traemos la lista de diagnósticos para llenar el select del filtro
    cursor.execute("SELECT id, nombre FROM tipo_diagnostico")
    diagnosticos = cursor.fetchall()
    
    id_seleccionado = request.form.get('tipo_diagnostico_id') if request.method == 'POST' else None
    pacientes_filtrados = []
    
    if id_seleccionado:
        # Traemos los pacientes que tengan asignado ese diagnóstico y mostramos su ingreso activo o el último historial
        query = """
            SELECT p.nombre AS nombre_paciente, p.apellido AS apellido_paciente,
            h.fecha_ingreso, s.nombre AS nombre_sala, h.fecha_alta
            FROM paciente p
            INNER JOIN hospitalizacion h ON p.id = h.paciente_id
            INNER JOIN sala s ON h.sala_id = s.id
            WHERE p.tipo_diagnostico_id = %s
            ORDER BY h.fecha_ingreso DESC
        """
        cursor.execute(query, (id_seleccionado,))
        pacientes_filtrados = cursor.fetchall()
        
    cursor.close()
    return render_template('consulta_diagnostico.html', 
        diagnosticos=diagnosticos, 
        pacientes=pacientes_filtrados, 
        id_seleccionado=int(id_seleccionado) if id_seleccionado else None)

if __name__ == '__main__':
    app.run(debug=True)