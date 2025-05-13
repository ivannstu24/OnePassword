from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import psycopg2
from psycopg2 import sql
from werkzeug.utils import secure_filename
import bcrypt


app = Flask(__name__)
CORS(app)

# Конфигурация PostgreSQL
DATABASE_CONFIG = {
    'dbname': 'OneBad',
    'user': 'ivanmerzov',
    'password': 'Vania_505',
    'host': 'localhost',
    'port': '5432'
}


UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    conn = psycopg2.connect(**DATABASE_CONFIG)
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Удаляем существующие таблицы (осторожно, это удалит все данные!)
    cur.execute("DROP TABLE IF EXISTS profiles CASCADE")
    cur.execute("DROP TABLE IF EXISTS passwords CASCADE")
    cur.execute("DROP TABLE IF EXISTS users CASCADE")
    
    # Создаем таблицы с новой структурой
    cur.execute("""
        CREATE TABLE users (
            username VARCHAR(50) PRIMARY KEY,
            password_hash VARCHAR(100) NOT NULL
        )
    """)
    
    cur.execute("""
        CREATE TABLE passwords (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) REFERENCES users(username) ON DELETE CASCADE,
            service VARCHAR(100) NOT NULL,
            password_hash VARCHAR(100) NOT NULL,
            UNIQUE(username, service)
        )
    """)
    
    cur.execute("""
        CREATE TABLE profiles (
            username VARCHAR(50) PRIMARY KEY REFERENCES users(username) ON DELETE CASCADE,
            email VARCHAR(100),
            avatar_url VARCHAR(255)
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

# Инициализация базы данных при старте
init_db()

# Функции для работы с хешами паролей
def hash_password(password: str) -> str:
    """Генерация bcrypt хеша для пароля"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(hashed_password: str, user_password: str) -> bool:
    """Проверка пароля против хеша"""
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password.encode('utf-8'))

# Функции работы с пользователями
def read_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, password_hash FROM users")
    users = [{'username': row[0], 'password_hash': row[1]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return users

def write_user(username: str, password: str):
    password_hash = hash_password(password)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
        (username, password_hash)
    )
    conn.commit()
    cur.close()
    conn.close()

# Функции работы с паролями сервисов
def write_service_password(username: str, service: str, password: str):
    password_hash = hash_password(password)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO passwords (username, service, password_hash) 
           VALUES (%s, %s, %s)
           ON CONFLICT (username, service) 
           DO UPDATE SET password_hash = EXCLUDED.password_hash""",
        (username, service, password_hash)
    )
    conn.commit()
    cur.close()
    conn.close()

def verify_service_password(username: str, service: str, password: str) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT password_hash FROM passwords WHERE username = %s AND service = %s",
        (username, service)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if not result:
        return False
    
    return check_password(result[0], password)

def get_user_services(username: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT service FROM passwords WHERE username = %s",
        (username,)
    )
    services = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return services

def delete_service_password(username: str, service: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM passwords WHERE username = %s AND service = %s",
        (username, service)
    )
    conn.commit()
    deleted = cur.rowcount > 0
    cur.close()
    conn.close()
    return deleted

# Функции работы с профилями
def read_profiles():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, email, avatar_url FROM profiles")
    profiles = [{'username': row[0], 'email': row[1], 'avatarUrl': row[2]} 
               for row in cur.fetchall()]
    cur.close()
    conn.close()
    return profiles

def write_profile(username: str, email: str, avatar_url: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO profiles (username, email, avatar_url) 
           VALUES (%s, %s, %s)
           ON CONFLICT (username) 
           DO UPDATE SET email = EXCLUDED.email, avatar_url = EXCLUDED.avatar_url""",
        (username, email, avatar_url)
    )
    conn.commit()
    cur.close()
    conn.close()

# API Endpoints
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    users = read_users()
    if any(user['username'] == username for user in users):
        return jsonify({'message': 'User already exists'}), 409

    write_user(username, password)
    return jsonify({'message': 'Registration successful'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    users = read_users()
    user = next((user for user in users if user['username'] == username), None)
    
    if user and check_password(user['password_hash'], password):
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/save_password', methods=['POST'])
def save_password():
    data = request.json
    username = data.get('username')
    service = data.get('service')
    password = data.get('password')

    if not username or not service or not password:
        return jsonify({'message': 'All fields are required'}), 400

    write_service_password(username, service, password)
    return jsonify({'message': 'Password saved securely'}), 201

@app.route('/verify_password', methods=['POST'])
def verify_password():
    data = request.json
    username = data.get('username')
    service = data.get('service')
    password = data.get('password')

    if not username or not service or not password:
        return jsonify({'message': 'All fields are required'}), 400

    is_valid = verify_service_password(username, service, password)
    return jsonify({'valid': is_valid}), 200

@app.route('/get_services', methods=['GET'])
def get_services():
    username = request.args.get('username')

    if not username:
        return jsonify({'message': 'Unauthorized'}), 403

    services = get_user_services(username)
    return jsonify({'services': services}), 200

@app.route('/delete_password', methods=['POST'])
def delete_password():
    data = request.json
    username = data.get('username')
    service = data.get('service')

    if not username or not service:
        return jsonify({'message': 'Username and service are required'}), 400

    if delete_service_password(username, service):
        return jsonify({'message': 'Password deleted'}), 200
    else:
        return jsonify({'message': 'Password not found'}), 404

@app.route('/get_profile', methods=['GET'])
def get_profile():
    username = request.args.get('username')

    if not username:
        return jsonify({'message': 'Unauthorized'}), 403

    profiles = read_profiles()
    profile = next((p for p in profiles if p['username'] == username), None)
    if profile:
        return jsonify(profile), 200
    else:
        return jsonify({
            'username': username,
            'email': None,
            'avatarUrl': None
        }), 200

@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    avatar = request.files.get('avatar')

    if not username:
        return jsonify({'message': 'Unauthorized'}), 403

    avatar_url = None
    if avatar:
        filename = secure_filename(f"{username}_{avatar.filename}")
        avatar.save(os.path.join(UPLOAD_FOLDER, filename))
        avatar_url = f"http://localhost:5000/uploads/{filename}"

    write_profile(username, email, avatar_url)
    return jsonify({
        'message': 'Profile updated',
        'avatarUrl': avatar_url
    }), 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(port=5000)