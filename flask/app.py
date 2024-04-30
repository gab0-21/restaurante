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

@app.route('/menu_mesero', methods=['GET', 'POST'])
def menu_mesero():
    return render_template('menu_mesero.html')

@app.route('/crear_orden', methods=['POST'])  # Solo permitir métodos POST
def crear_orden():    
    if request.method == 'POST':
        mesa = request.form.get('mesa')
        platillo = request.form.get('platillo')
        cantidad = request.form.get('cantidad')
        nota_especial = request.form.get('nota_especial')  # Obtener la nota especial del formulario
        
        precio = request.form.get('precio')  # Obtener el precio del formulario
        
        # Insertar la orden en la base de datos, incluyendo el precio
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO orden (mesa, platillo, cantidad, nota_especial, precio) VALUES (%s, %s, %s, %s, %s)",
                    (mesa, platillo, cantidad, nota_especial, precio))
        mysql.connection.commit()
        cur.close()
        
        return render_template('crear_orden.html')  # Redirige de vuelta al menú del mesero
    else:
        return redirect(url_for('menu_mesero'))  # Redirige de vuelta al menú del mesero si no se envía el formulario

@app.route('/ver_ordenes')
def ver_ordenes():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM orden")
    ordenes = cur.fetchall()
    cur.close()
    return render_template('ver_ordenes.html', ordenes=ordenes)   

@app.route('/gestionar_ordenes', methods=['GET', 'POST'])
def gestionar_ordenes():
    if request.method == 'GET':
        # Obtener todas las órdenes de la base de datos
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM orden")
        ordenes = cur.fetchall()
        cur.close()
        return render_template('gestionar_ordenes.html', ordenes=ordenes)
    elif request.method == 'POST':
        action = request.form.get('action')
        if action == 'delete':
            order_id = request.form.get('order_id')
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM orden WHERE id = %s", (order_id,))
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
                    cur.execute("UPDATE orden SET platillo = %s, cantidad = %s, mesa = %s, precio = %s WHERE id = %s", (new_platillo, new_cantidad, new_mesa, new_precio, order_id))
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
