from flask import Flask, render_template, request, redirect, flash, url_for,  get_flashed_messages
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__, static_url_path='/static')

load_dotenv()

# Configuración de la base de datos MySQL
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PORT'] = 3307
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

mysql = MySQL(app)

# Configuración de Flask-Login
app.secret_key = "mysecretkey"
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor inicia sesión para acceder a esta página."

# Definición del modelo de usuario
class User(UserMixin):
    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, email, contraseña FROM usuarios WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    if user:
        return User(user[0], user[1], user[2])
    return None

# Ruta para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['contraseña']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, email, contraseña FROM usuarios WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        
        if user and check_password_hash(user[2], password):
            user_obj = User(user[0], user[1], user[2])
            login_user(user_obj)
            flash('Inicio de sesión exitoso!', 'success')
            return redirect(url_for('cargar_datos'))
        else:
            flash('Credenciales Invalidas', 'error')
    return render_template('register.html')

# Ruta para registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        print("Formulario enviado")
        email = request.form['email']
        password = request.form['contraseña']

        # Genera el hash de las contraseñas
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Insertar el nuevo usuario en la base de datos
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO usuarios (email, contraseña) VALUES (%s, %s)", (email, hashed_password))
        mysql.connection.commit()
        cur.close()
        
        flash('Registro exitoso, ahora puedes iniciar sesión', 'success')
        print("Redireccionando a login")
        # return redirect(url_for('login'))
        return render_template('login.html')

@app.route('/')
def main():
    return render_template('login.html')


#Ruta para cargar datos
@app.route('/cargar_datos')
@login_required
def cargar_datos():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM contactos')
    data = cur.fetchall()
    return render_template( 'index.html', clientes = data)

#Ruta tambien para agregar los pacientes
@app.route('/save')
@login_required
def save():
    return render_template('save.html')

# Ruta para agregar pacientes
@app.route('/add', methods=['POST'])
def add():
    if request.method == 'POST':
        print('Formulario enviado')
        nombreCompleto = request.form['NombreCompleto']
        edad = request.form['edad']
        direccion = request.form['direccion']
        telefono = request.form['telefono']
        email = request.form['email']
        grupo = request.form['grupo']
        cur = mysql.connection.cursor()
        print(f'Recibido: {nombreCompleto}, {edad}, {direccion}, {telefono}, {email}, {grupo}')
        try:
            cur = mysql.connection.cursor()
            cur.execute('''INSERT INTO contactos (NombreCompleto, edad, direccion, telefono, email, grupo)
                    VALUES (%s, %s, %s, %s, %s, %s)'''
                    , (nombreCompleto, edad, direccion, telefono, email, grupo))
            mysql.connection.commit()
            cur.close()
            print('Datos insertados correctamente, redireccionando...')
            return redirect(url_for('cargar_datos'))
        except Exception as e:
            print(f'Error al insertar los datos: {e}')
            return render_template('index.html')

# Rutas para editar pacientes
@app.route('/edit/<id>')
def get_client(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM contactos WHERE id = %s', (id,))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('editar.html',contact= data[0])

@app.route('/update/<id>', methods=['POST'])
def update_contact(id):
    if request.method == 'POST':
        nombreCompleto = request.form['NombreCompleto']
        edad = request.form['edad']
        direccion = request.form['direccion']
        telefono = request.form['telefono']
        email = request.form['email']
        grupo = request.form['grupo']
        cur = mysql.connection.cursor()
        cur.execute('''UPDATE contactos
            SET NombreCompleto = %s, edad = %s, direccion = %s, telefono = %s, email = %s, grupo = %s
            WHERE id = %s'''
                , (nombreCompleto, edad, direccion, telefono, email, grupo, id))
        mysql.connection.commit()
        return redirect(url_for('cargar_datos'))


#Ruta para eliminar pacientes
@app.route('/delete/<id>', methods=['POST'])
@login_required
def delete_contact(id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM contactos WHERE id = %s', (id,))
    mysql.connection.commit()
    cur.close()
    flash('Contacto eliminado exitosamente', 'success')
    return redirect(url_for('cargar_datos'))


# Ruta para cerrar sesion
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('has cerrado sesión')
    return render_template('login.html')


# Ruta para el grafico
class datos_grafico:
    def __init__(self, cursor):
        self.cursor = cursor

    def get_data(self):
        self.cursor.execute('SELECT grupo, COUNT(*) FROM contactos GROUP BY grupo')
        data = self.cursor.fetchall()
        labels = [row[0] for row in data]
        values = [row[1] for row in data]
        return labels, values

@app.route('/grafico')
def grafico():
    cur = mysql.connection.cursor()
    chart_data = datos_grafico(cur)
    labels, values = chart_data.get_data()
    return render_template('grafico.html', labels=labels, values=values)




if __name__ == "__main__":
    app.run(port=5020, debug=True)
