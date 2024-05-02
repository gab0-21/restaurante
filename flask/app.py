from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Clave secreta para la sesión

# Configuración de la base de datos MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '58753822Br'
app.config['MYSQL_DB'] = 'restaurant'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Rutas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))
        user = cur.fetchone()
        cur.close()
        if user and user['password'] == password:
            session['usuario'] = user  # Almacenar el usuario en la sesión
            if user['puesto'] == 'mesero':
                return redirect(url_for('menu_mesero'))  # Redirige al menú del mesero
            elif user['puesto'] == 'cajero':
                return redirect(url_for('menu_cajero'))  # Redirige al menú del cajero
            elif user['puesto'] == 'administrador':
                return redirect(url_for('menu_admin'))  # Redirige al menú del administrador
        else:
            return "Nombre de usuario o contraseña incorrectos. Intente nuevamente."
    return render_template('index.html')

@app.route('/seleccionar_mesa', methods=['GET', 'POST'])
def seleccionar_mesa():
    if request.method == 'POST':
        mesa_seleccionada = request.form['mesa']
        session['mesa_seleccionada'] = mesa_seleccionada
        if request.referrer and 'gestionar_ordenes' in request.referrer:  # Si la página anterior fue gestionar_ordenes, redirige allí
            return redirect(url_for('gestionar_ordenes'))
        else:  # De lo contrario, redirige a crear_orden
            return redirect(url_for('crear_orden'))
    return render_template('seleccionar_mesa.html')

@app.route('/crear_orden', methods=['GET', 'POST'])
def crear_orden():
    mesa_seleccionada = session.get('mesa_seleccionada')
    if mesa_seleccionada is None:
        return redirect(url_for('seleccionar_mesa'))

    if request.method == 'POST':
        mesa = mesa_seleccionada
        platillos = request.form.getlist('platillos[]')  # Obtener una lista de platillos seleccionados
        cantidad = request.form.get('cantidad')
        nota_especial = request.form.get('nota_especial')

        # Verificar si todos los platillos seleccionados tienen precios en la base de datos
        cur = mysql.connection.cursor()
        for platillo in platillos:
            cur.execute("SELECT precio FROM platillos WHERE nombre_platillo = %s", (platillo,))
            precio_data = cur.fetchone()
            if precio_data is None or 'precio' not in precio_data:
                cur.close()
                return "Error: Algunos platillos seleccionados no tienen precio en la base de datos."
        cur.close()

        # Construir el nombre de la tabla de la orden
        tabla_orden = f"orden_mesa_{mesa}"

        # Insertar un registro en la base de datos para cada platillo seleccionado
        cur = mysql.connection.cursor()
        for platillo in platillos:
            # Obtener el precio del platillo desde la base de datos
            cur.execute("SELECT precio FROM platillos WHERE nombre_platillo = %s", (platillo,))
            precio_data = cur.fetchone()
            if precio_data is not None and 'precio' in precio_data:
                precio = precio_data['precio']  # Obtener el precio del platillo del diccionario
                # Insertar el registro en la tabla de órdenes con el precio individual del platillo
                cur.execute(f"INSERT INTO {tabla_orden} (mesa, platillo, cantidad, nota_especial, precio) VALUES (%s, %s, %s, %s, %s)",
                            (mesa, platillo, cantidad, nota_especial, precio))
        mysql.connection.commit()
        cur.close()

        # Después de crear la orden, redirige al usuario a seleccionar la mesa nuevamente
        return redirect(url_for('seleccionar_mesa'))
    
    return render_template('crear_orden.html', mesa_seleccionada=mesa_seleccionada)


@app.route('/ver_ordenes', methods=['GET', 'POST'])
def ver_ordenes():
    if request.method == 'POST':
        mesa_seleccionada = request.form['mesa']
        cur = mysql.connection.cursor()
        tabla_orden = f"orden_mesa_{mesa_seleccionada}"
        cur.execute(f"SELECT * FROM {tabla_orden}")
        ordenes = cur.fetchall()
        cur.close()
        return render_template('ver_ordenes.html', ordenes=ordenes, mesa_seleccionada=mesa_seleccionada)
    return render_template('seleccionar_mesa_ver_ordenes.html')

@app.route('/gestionar_ordenes', methods=['GET', 'POST'])
def gestionar_ordenes():
    mesa_seleccionada = session.get('mesa_seleccionada')
    if mesa_seleccionada:
        if request.method == 'GET':
            # Obtener las órdenes específicas para la mesa seleccionada
            cur = mysql.connection.cursor()
            tabla_orden = f"orden_mesa_{mesa_seleccionada}"
            cur.execute(f"SELECT * FROM {tabla_orden}")
            ordenes = cur.fetchall()
            cur.close()
            return render_template('gestionar_ordenes.html', ordenes=ordenes, mesa_seleccionada=mesa_seleccionada)
        elif request.method == 'POST':
            action = request.form.get('action')
            if action == 'delete':
                order_id = request.form.get('order_id')
                cur = mysql.connection.cursor()
                tabla_orden = f"orden_mesa_{mesa_seleccionada}"
                cur.execute(f"DELETE FROM {tabla_orden} WHERE id = %s", (order_id,))
                mysql.connection.commit()
                cur.close()
                return redirect(url_for('gestionar_ordenes'))
            elif action == 'edit':
                order_id = request.form.get('order_id')
                new_platillo = request.form.get('new_platillo')
                new_cantidad = request.form.get('new_cantidad')
                new_mesa = request.form.get('new_mesa')
                cur = mysql.connection.cursor()
                if new_platillo:
                    # Obtener el nuevo precio del platillo desde la base de datos
                    cur.execute("SELECT precio FROM orden WHERE platillo = %s", (new_platillo,))
                    new_precio_data = cur.fetchone()
                    if new_precio_data:
                        new_precio = new_precio_data['precio']
                        tabla_orden = f"orden_mesa_{mesa_seleccionada}"
                        cur.execute(f"UPDATE {tabla_orden} SET platillo = %s, cantidad = %s, mesa = %s, precio = %s WHERE id = %s", (new_platillo, new_cantidad, new_mesa, new_precio, order_id))
                        mysql.connection.commit()
                        cur.close()
                        return redirect(url_for('gestionar_ordenes'))
                    else:
                        # Manejar el caso donde no se encuentre el nuevo precio
                        cur.close()
                        return "El nuevo platillo seleccionado no tiene precio en la base de datos."
                else:
                    # No se proporcionó un nuevo platillo
                    return redirect(url_for('gestionar_ordenes'))
    else:
        return redirect(url_for('seleccionar_mesa'))  # Corrección aquí

    # Si no se cumple ninguna condición, se renderiza la plantilla de selección de mesa
    return render_template('seleccionar_mesa.html')  # Renderizar la plantilla de selección de mesa


@app.route('/menu_mesero')
def menu_mesero():
    return render_template('menu_mesero.html')

    
@app.route('/menu/cajero')
def menu_cajero():
    return render_template('menu_cajero.html')

@app.route('/menu/admin')
def menu_admin():
    return render_template('menu_admin.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        puesto = request.form['puesto']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO usuarios (usuario, puesto, password) VALUES (%s, %s, %s)", (usuario, puesto, password))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('index'))
    return render_template('registro.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)  # Eliminar el usuario de la sesión
    return redirect(url_for('login'))  # Redirige a la página de inicio de sesión

if __name__ == '__main__':
    app.run(debug=True)
