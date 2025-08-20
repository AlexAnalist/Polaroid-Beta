import os
from flask import Flask, render_template, request, redirect, url_for, flash 
from datetime import datetime
import uuid
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# Configuración
app = Flask(__name__) 


basedir = os.path.abspath(os.path.dirname(__file__)) #ruta absoluta 
db_path = os.path.join(basedir, 'database', 'polaroid.db') #para la base de datos 
app.config['AVATAR_FOLDER'] = os.path.join(app.static_folder, 'avatars') #carpeta de avatars 
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads') #carpeta para las publicaciones 
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}' #la conexion entre una base de datos SQLite utilizando SQLAlchemy 
app.config['SECRET_KEY'] = 'clave-secreta'  #debo cambiarla para mayor seguridad 

db = SQLAlchemy(app)
migrate = Migrate(app, db) 
loginm = LoginManager(app)
loginm.login_view = 'login'

#Tabla de relacion entre los usuarios. Seguidores y Siguiendo.
followers = db.Table('followers', 
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'), primary_key=True))
    #db.Column('created_at', db.DateTime, default=datetime.utcnow)) #ojo, revisar. 

post_likes = db.Table('post_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

# Modelo Usuario 
class User(UserMixin, db.Model):   
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, default="")
    avatar = db.Column(db.String(255), default='default.jpg')

    #Relaciones de seguidores 
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id ==id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id
        ).count() > 0
    
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
    
    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    posts = db.relationship('Post', backref='author', lazy=True)
    

# Modelo Post
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(255))
    post_type = db.Column(db.String(10))
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    #Interacciones
    likes = db.relationship('User', secondary=post_likes, backref='liked_posts', lazy='dynamic')
    comments = db.relationship('Comment', backref='post', cascade='all, delete-orphan', lazy='dynamic')
    #agregar más tarde guardar 

    def __repr__(self):
        return f'<Post {self.id} - {self.post_type}>'

# Modelo para comentarios   
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    author = db.relationship('User', backref='comments')

# Modelo para los mensajes directos entre solo 2 usuarios. 
class DirectMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_dms')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_dms')

"""Rutas"""

#Carga el usuario a través del usuario único 
@loginm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Carga la página principal de Polaroid 
@app.route('/')
def index():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)

#Carga el registro de usuarios 
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Usuario ya existe')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email ya fue registrado')
            return redirect(url_for('register'))
        user = User(email=email, username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registro exitoso. Inicia sesión.')
        return redirect(url_for('login'))
    return render_template('register.html')

#Cargar el login de los usuarios 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('username', '').strip()
        password = request.form.get('password')
        user = User.query.filter(or_(User.username==identifier, User.email == identifier), User.password == password).first()
        if user:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Credenciales incorrectas')
    return render_template('login.html')

#Cargar perfil 
@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    #Publicaciones ordenadas de forma descendiente, las más recientes arriba 
    user_posts = Post.query.filter_by(user_id=user.id)\
                          .order_by(Post.created_at.desc())\
                          .all()
    
    
    return render_template('profile.html', 
                         user=user,
                         user_posts=user_posts)

#Busqueda de usuarios
@app.route('/sugerencias_usuario')
@login_required
def sugerencias_usuario():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    usuarios = User.query.filter(
        User.username.ilike(f"%{query}%"),
        User.id != current_user.id  # No see toma en cuenta el usuario con la sesion abierta 
    ).limit(10).all()
    
    sugerencias = [{
        'username': u.username,
        'avatar': u.avatar if u.avatar else 'default.jpg' 
    } for u in usuarios]
    
    return jsonify(sugerencias)


#Editar el avatar(foto de perfil)
@app.route('/edit_avatar', methods=['POST'])
@login_required
def edit_avatar():
    avatar_file = request.files.get('avatar')
    if avatar_file and avatar_file.filename:
        filename = secure_filename(avatar_file.filename)
        avatar_path = os.path.join(app.root_path, 'static/avatars', filename)
        avatar_file.save(avatar_path)
        current_user.avatar = filename

    nueva_bio = request.form.get('bio', '').strip()
    if nueva_bio != current_user.bio:
        current_user.bio = nueva_bio

    db.session.commit()
    return redirect(url_for('profile', username=current_user.username))

#Cierra sesion 
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

#Crear post
@app.route('/crear_post', methods=['POST'])
@login_required
def crear_post():
    file = request.files.get('file')
    upload_type = request.form.get('type', '')  ##
    description = request.form.get('description', '')

    if not file or upload_type not in ['polaroid', 'vhs']:
        flash('Datos incompletos o inválidos.', 'error')
        return redirect(request.referrer or url_for('index'))

    #Tipos permitidoss para las publicaciones
    if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        file_type = 'image'
    elif file.filename.lower().endswith(('.mp4', '.mov', '.avi')):
        file_type = 'video'
    else:
        flash('Formato no soportado.', 'error')
        return redirect(request.referrer or url_for('index'))

    filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    new_post = Post(
        file_path=filename,
        description=description,
        post_type=file_type,
        user_id=current_user.id
    )
    db.session.add(new_post)
    db.session.commit()

    flash('¡Publicación creada!', 'success')
    return redirect(url_for('profile', username=current_user.username))

#Redirige dependiendo de lo del usuario desea subir 
@app.route('/upload_polaroid')
@login_required
def upload_polaroid():
    return render_template('upload_polaroid.html')

@app.route('/upload_vhs')
@login_required
def upload_vhs():
    return render_template('upload_vhs.html')

#Seguir o no seguir
@app.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow(user_id):
    if not request.is_json:
        return jsonify({'success': False}), 400
        
    user_to_follow = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if data.get('action') == 'follow':
        current_user.follow(user_to_follow)
    else:
        current_user.unfollow(user_to_follow)
    
    db.session.commit()
    return jsonify({'success': True})

#Like en los post 
@app.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if current_user in post.likes:
        # Quitar like
        post.likes.remove(current_user)
        action = 'unlike'
    else:
        # Dar like
        post.likes.append(current_user)
        action = 'like'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'action': action,
        'likes_count': post.likes.count() 
    })

#Añadir comentario 
@app.route('/add_comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    text = request.form.get('text')
    
    if not text:
        return jsonify({'success': False, 'error': 'El comentario no puede estar vacío'})
    
    new_comment = Comment(
        text=text,
        user_id=current_user.id,
        post_id=post.id
    )
    
    db.session.add(new_comment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'comment': {
            'text': new_comment.text,
            'author': current_user.username
        }
    })

#Mensajeria entre dos usuarios 
@app.route('/messenger/<int:contact_id>')
@login_required
def messenger(contact_id):
    contact = User.query.get_or_404(contact_id)
    return render_template('messenger.html', contact=contact)

#Enviar Dm 
@app.route('/api/send_dm', methods=['POST'])
@login_required
def send_dm():
    data = request.json
    message = DirectMessage(
        sender_id=current_user.id,
        recipient_id=data['recipient_id'],
        content=data['content']
    )
    db.session.add(message)
    db.session.commit()
    return jsonify({'success': True})

#Cargar los DmS
@app.route('/api/get_dms/<int:contact_id>')
@login_required
def get_dms(contact_id):
    messages = DirectMessage.query.filter(
        ((DirectMessage.sender_id == current_user.id) & 
         (DirectMessage.recipient_id == contact_id)) |
        ((DirectMessage.sender_id == contact_id) & 
         (DirectMessage.recipient_id == current_user.id))
    ).order_by(DirectMessage.timestamp.asc()).all()

    return jsonify([{
        'id': msg.id,
        'content': msg.content,
        'timestamp': msg.timestamp.strftime('%H:%M'),
        'is_sender': msg.sender_id == current_user.id,
        'sender_avatar': msg.sender.avatar or 'default.jpg'
    } for msg in messages])

if __name__ == '__main__':
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('database', exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)