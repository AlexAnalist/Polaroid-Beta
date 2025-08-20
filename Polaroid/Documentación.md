
Flask es un microframework de Python para crear aplicaciones web. Lo llaman “micro” no porque sea limitado, sino porque es ligero, flexible y minimalista. Solo te da lo esencial para que puedas agregar lo que necesites, sin imponer muchas reglas.

from flask import request, redirect, flash, render_template

request: da accesep a los datos enviados por el navegador (como formularios)
redirect: permite redirigir al usuario a otra página
flash: envía mensajes temporales a la interfaz (por ejemplo. "contraseña incorrecta")
render_template: mostrar HTML dinámico usando Jinja 2 

from  flask_sqlalchemy import SQAlchemy 

Importa la clase que te permite trabajar con bases de datos usando el ORM de SQLAlchemy. 

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user 

LoginManager: Administra el sistemana de login de usuarios. 

UserMixin: Se herada de tu clase User, agrega funcionalidad para manejar usuarios facilmente. 

login_required: Protege rutas para que solo usuarios autenticados puedan acceder 

login_user: Inicia la sesion de un usuario 

logout_user: Finaliza la sesión actual 

current_user: Te da acceso al usuario que está actualmente logueado. 

app = Flask(__name__)

__name__ le dice a Flask donde se encuentra el archivo principal, lo cual ayuda a encontrar rutas, templates, etc. 

A partir de aqui puedes definir rutas, configurar extensiones y lanzar el servidor. 

basedir = os.path.abspath(os.path.dirname(__file__))

Obtiene la ruta absoluta del directorio donde esta tu archivo .py 
Esto te permite construir rutas seguras y compatibles con cualquier sistema operativo. 

db_path = os.path.join(basedir,'database','instagram.db')
Une la ruta base con los subdirectorios y archivo que necesitas. 
Resultado: una ruta completa hacia tu base de datos instagram.db dentro de la carpeta database. 

app.config['SQLALCHEMY_DATABASE_URI'] = F'sqlite:///{db_path}'

Configura la direccion URI que SQLAlchemy usará para conectarse a la base de datos. 

En este estás usando SQLite en una ruta local. 

app.config['SECRET_KEY'] = 'clave-secreta'

Esta clave es vital para proteger sesiones de usuario, formlarios, cookies y tokens- 

cambiar la clave secreta //

db = SQLAlchemy(app)
Esto inicializa la extension SQAlchemu con tu aplicacion Flask
Te permite trabjar con bases de datos de forma sencilla usando un modelo de objetos. 
Con esto, puedes definir tus tablas como clases Python y realizar operaciones como insertar, consultar, actualizar y eliminar datos. 

login_manager = LoginManager(app)
aqui estas configurando Flask-Login, una extension que maneja la autenticacion de usuarios.

LoginManager se asocia con tu app Flask para controlar inicios de sesion, cerrar sesion y proteger rutas que requieren auteticacion. 

login_manager.login_view = 'login'
Si un usuario intenta acceder a la pagina protegida sin estar autenticado, Flask lo redigira automaticamente a esa ruta. 

class User(UserMixin, db.Model): 
Define la clase User, que representa una tabla en la base de datos. 
Hereda de db.Model, lo cual convierte esta clase en un modelo de SQLAlchemy. 
hereda de UserMixin, lo que añade funcionalidades necesarias para que Flask-Login pueda usar este modelo como usuario autenticable (como is:autheticated, is_active)

id = db.Column(db.Integer, primary_key=True)
Crea la columna id como un entero único que funciona como clave primaria 
Esto identifica a cada usuario de forma individual en la base de datos. 

mail = db.Column(db.String(80), unique=True, nullable=False)
Crea una columan mail (correo electronico)
Tipo: cadena de texto de máximo 80 caracteres. 
unique = True: no puede haber 2 usuarios on el mismo correo 
null = False; obligatorio; no puede dejarse vacío. 

username = db.Column(db.String(80), unique=True, nullable=False)
lo mismo 

password = db.Column(db.String(100), nullable=False)
Crea una columna Password, obligatoria. 
falta aumentar la seguridad////

class Post(db.Model): 
#Define una clase Post que hereda de db.Model, lo que indica que es un modelo de SQLAlchemy. 
Representa una tabla en la base de datos para almacenar publicaciones. 

id = db.Column(db.Integer, primary_key=True) 
Columna id que es la clave primaria de la tabla. 
Es un identificador único para cada publicación. 

image = db.Column(db.String(255)) description = db.Column(db.Text)
Columna que guarda la ruta o URL  de una imagen asociada a la publicacion 
Es una cadena de máximo 255 caracteres. 

description = db.Column(db.text)
Aqui se guarda el testo descriptivo o contenido del post 
Tipo Text, ideal para textos largos sin limite de caracteres. 

user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
Relaciona cada publicacion con un usuario 
user_id guarda el ID del usuaeio autor de ese post. 
ForeignKey('user.id') indica que este valor debe coincidi con un ode de la tabla user. 
Esto establece una relacion uno a muchos: un usuario puede tener muchos posts, pero cada post pertenece a un solo usuario. 

@login_maneger.user_loader
Es un decorador que registra la funcion que se encargara de cargar el usuario desde la base de datos. 
Flask-Login la llama automaticamente cuando necesita recuperar informacion del usuario actual (por ejemplo, para validar sesiones)

def load_user(user_id): 
Define la funcion load_user que recibe el user_id como parámetro 
Este user_id se guarda en la sesión cuando el usuario inicia sesión. 

return User.query.get(int(user_id))
Busca al usuario en la base de datos usando SQLAlchemy 
User.query.get(...) recupera la instancia del usuario con ese ID. 
Se usa int(user_id) para asegurarse de que se trata de un número entero. 

Es importante pq esto permite que el Flask-Login sepa quien es el usuario que está autenticado en cada request. 

from flask_login import current_user

@app.route('/')
Es un decorador de Flask que indica que esta funcion(index) se ejecuta cuando el usuario visita la raíz del sitio web 
Define la ruta principal de la aplicacion

def index():
Define la funcion llamada index que sera la encargada de manejar esa ruta
Es comun nombrar esta funcion igual que la vista principal o la plantilla HTML que se va a renderizar. 

posts = Post.query.all()

Recupera tods los registros de la tabla Post usando SQLAlchemy 
Post.query.all() devuelve una lista con todas las publicaciones guardadas en la base de datos. 

return render_template('index.html', post=posts)
Renderiza el archivo HTML llamado index.html desde la carpeta templates. 
Le pasa la variable posts al template, para que puedas recorrerla en HTML y mostrar cada una- 

Ruta registro 
@app.route('/register', methods=['GET', 'POST'])
def register():
Define una ruta accesible con métodos GET (para mostrar el formulario) y POST (para recibir los datos)

username = request.form['username']
password = request.form['password']
Extrae el nombre de usuario y la contraseña del formulario enviado. 

if User.query.filter_by(username=username).first(): 
flash('Usuario ya existe')
return redirect(url_for('register'))
Verifica si el usuario ya está registrado en la base de datos- 
Si existe, muestra un mensaje y redirige nuevamente al formulario- 

user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
Crea una instancia del usuario, la guarda en la base de datos y confirma el registro. 

        flash('Registro exitoso. Inicia sesión.')
        return redirect(url_for('login'))
        Muestra un mensaje de exito y redirige 
        return render_template('register.html') Muestra el formulario de registro. 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Credenciales incorrectas')
    return render_template('login.html')












