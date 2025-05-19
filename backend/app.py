import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import psycopg2
from psycopg2 import sql, errors as pg_errors
from werkzeug.utils import secure_filename
import bcrypt
import jwt
from datetime import datetime, timedelta
import traceback
import dotenv

# Загрузка переменных окружения
dotenv.load_dotenv()

app = Flask(__name__)
CORS(app)


# Функция для логирования действий
def log_user_action(username, action_type, status, details=None):
    try:
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO user_logs 
               (username, action_type, ip_address, user_agent, status, details) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (username, action_type, ip_address, user_agent, status, details)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        app.logger.error(f"Failed to log user action: {str(e)}")

# Настройка логирования
def setup_logging():
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

setup_logging()

# Конфигурация
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

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

# Кастомные ошибки
class APIError(Exception):
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status'] = 'error'
        return rv

# Глобальные обработчики ошибок
@app.errorhandler(APIError)
def handle_api_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'message': 'Resource not found',
        'status': 'error'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Server error: {str(error)}\n{traceback.format_exc()}")
    return jsonify({
        'message': 'Internal server error',
        'status': 'error'
    }), 500

# Декоратор для обработки ошибок БД
def handle_db_errors(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except pg_errors.UniqueViolation as e:
            app.logger.warning(f"Duplicate entry: {str(e)}")
            raise APIError('Resource already exists', 409)
        except pg_errors.ForeignKeyViolation as e:
            app.logger.warning(f"Foreign key violation: {str(e)}")
            raise APIError('Invalid reference', 400)
        except pg_errors.DatabaseError as e:
            app.logger.error(f"Database error: {str(e)}\n{traceback.format_exc()}")
            raise APIError('Database operation failed', 500)
    return decorated

def get_db_connection():
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        return conn
    except pg_errors.DatabaseError as e:
        app.logger.error(f"Database connection error: {str(e)}")
        raise APIError('Database connection failed', 500)

# Инициализация базы данных

@handle_db_errors
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # инц

    conn.commit()
    cur.close()
    conn.close()
    app.logger.info("Database initialized successfully")

init_db()


# Функции для работы с хешами паролей
def hash_password(password: str) -> str:
    try:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    except Exception as e:
        app.logger.error(f"Password hashing error: {str(e)}")
        raise APIError('Password processing failed', 500)

def check_password(hashed_password: str, user_password: str) -> bool:
    try:
        return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        app.logger.error(f"Password check error: {str(e)}")
        raise APIError('Password verification failed', 500)

# JWT Helpers
def generate_tokens(username):
    try:
        access_token = jwt.encode({
            'username': username,
            'exp': datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES']
        }, app.config['SECRET_KEY'], algorithm='HS256')

        refresh_token = jwt.encode({
            'username': username,
            'exp': datetime.utcnow() + app.config['JWT_REFRESH_TOKEN_EXPIRES']
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    except Exception as e:
        app.logger.error(f"Token generation error: {str(e)}")
        raise APIError('Token generation failed', 500)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            app.logger.warning("Attempt to access protected route without token")
            raise APIError('Token is missing', 401)
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data['username']
            app.logger.info(f"User {current_user} accessed protected route")
        except jwt.ExpiredSignatureError:
            app.logger.warning("Expired token attempt")
            raise APIError('Token has expired', 401)
        except jwt.InvalidTokenError:
            app.logger.warning("Invalid token attempt")
            raise APIError('Token is invalid', 401)
        except Exception as e:
            app.logger.error(f"Token verification error: {str(e)}")
            raise APIError('Token verification failed', 401)
        
        return f(current_user, *args, **kwargs)
    return decorated

# Функции работы с пользователями
@handle_db_errors
def read_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, password_hash FROM users")
    users = [{'username': row[0], 'password_hash': row[1]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return users

@handle_db_errors
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
    app.logger.info(f"New user created: {username}")

# Функции работы с паролями сервисов
@handle_db_errors
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
    app.logger.info(f"Password saved for service {service} by user {username}")

@handle_db_errors
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
        app.logger.warning(f"Password verification failed - no record for {username} and {service}")
        return False
    
    return check_password(result[0], password)

@handle_db_errors
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

@handle_db_errors
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
    
    if deleted:
        app.logger.info(f"Password deleted for service {service} by user {username}")
    else:
        app.logger.warning(f"Password deletion failed - no record for {username} and {service}")
    
    return deleted

# Функции работы с профилями
@handle_db_errors
def read_profiles():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, email, avatar_url FROM profiles")
    profiles = [{'username': row[0], 'email': row[1], 'avatarUrl': row[2]} 
               for row in cur.fetchall()]
    cur.close()
    conn.close()
    return profiles

@handle_db_errors
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
    app.logger.info(f"Profile updated for user {username}")

# API Endpoints
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            raise APIError('No input data provided', 400)
        
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            raise APIError('Username and password are required', 400)

        if len(username) < 4:
            raise APIError('Username must be at least 4 characters', 400)

        if len(password) < 8:
            raise APIError('Password must be at least 8 characters', 400)

        users = read_users()
        if any(user['username'] == username for user in users):
            raise APIError('User already exists', 409)

        write_user(username, password)
        log_user_action(username, 'REGISTER', 'SUCCESS')
        
        return jsonify({
            'message': 'Registration successful',
            'status': 'success'
        }), 201

    except APIError as e:
        log_user_action(data.get('username'), 'REGISTER', 'FAILED', e.message)
        raise e
    except Exception as e:
        app.logger.error(f"Registration error: {str(e)}\n{traceback.format_exc()}")
        log_user_action(data.get('username'), 'REGISTER', 'FAILED', 'Internal error')
        raise APIError('Registration failed', 500)

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            raise APIError('No input data provided', 400)
        
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            raise APIError('Username and password are required', 400)

        users = read_users()
        user = next((user for user in users if user['username'] == username), None)
        
        if not user:
            log_user_action(username, 'LOGIN', 'FAILED', 'User not found')
            raise APIError('Invalid credentials', 401)

        if not check_password(user['password_hash'], password):
            log_user_action(username, 'LOGIN', 'FAILED', 'Invalid password')
            raise APIError('Invalid credentials', 401)

        tokens = generate_tokens(username)
        log_user_action(username, 'LOGIN', 'SUCCESS')
        
        return jsonify({
            'message': 'Login successful',
            'status': 'success',
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token']
        }), 200

    except APIError as e:
        log_user_action(data.get('username'), 'LOGIN', 'FAILED', e.message)
        raise e
    except Exception as e:
        app.logger.error(f"Login error: {str(e)}\n{traceback.format_exc()}")
        log_user_action(data.get('username'), 'LOGIN', 'FAILED', 'Internal error')
        raise APIError('Login failed', 500)

@app.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    try:
        log_user_action(current_user, 'LOGOUT', 'SUCCESS')
        return jsonify({
            'message': 'Logged out successfully', 
            'status': 'success'
        }), 200
    except Exception as e:
        log_user_action(current_user, 'LOGOUT', 'FAILED', str(e))
        raise APIError('Logout failed', 500)

    
@app.route('/get_user_logs', methods=['GET'])
@token_required
def get_user_logs(current_user):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            """SELECT action_type, ip_address, user_agent, status, 
                      details, created_at 
               FROM user_logs 
               WHERE username = %s 
               ORDER BY created_at DESC 
               LIMIT 100""",
            (current_user,)
        )
        
        logs = []
        for row in cur.fetchall():
            logs.append({
                'action': row[0],
                'ip_address': row[1],
                'device': row[2],
                'status': row[3],
                'details': row[4],
                'timestamp': row[5].isoformat() if row[5] else None
            })
            
        cur.close()
        conn.close()
        
        return jsonify({
            'logs': logs,
            'status': 'success'
        }), 200
        
    except Exception as e:
        app.logger.error(f"Failed to get logs: {str(e)}")
        log_user_action(current_user, 'GET_LOGS', 'FAILED', str(e))
        raise APIError('Failed to get logs', 500)

@app.route('/refresh', methods=['POST'])
def refresh():
    try:
        data = request.get_json()
        if not data:
            raise APIError('No input data provided', 400)
        
        refresh_token = data.get('refresh_token')
        if not refresh_token:
            raise APIError('Refresh token is required', 400)
        
        try:
            data = jwt.decode(refresh_token, app.config['SECRET_KEY'], algorithms=['HS256'])
            username = data['username']
            
            users = read_users()
            if not any(user['username'] == username for user in users):
                raise APIError('User not found', 404)
                
            tokens = generate_tokens(username)
            return jsonify({
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'status': 'success'
            }), 200
        except jwt.ExpiredSignatureError:
            raise APIError('Refresh token has expired', 401)
        except jwt.InvalidTokenError:
            raise APIError('Invalid refresh token', 401)
            
    except APIError as e:
        raise e
    except Exception as e:
        app.logger.error(f"Token refresh error: {str(e)}\n{traceback.format_exc()}")
        raise APIError('Token refresh failed', 500)

@app.route('/save_password', methods=['POST'])
@token_required
def save_password(current_user):
    try:
        data = request.get_json()
        if not data:
            raise APIError('No input data provided', 400)
        
        service = data.get('service')
        password = data.get('password')

        if not service or not password:
            raise APIError('Service and password are required', 400)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT password_hash FROM passwords WHERE username = %s AND service = %s",
            (current_user, service)
        )
        existing_password = cur.fetchone()
        cur.close()
        conn.close()

        password_hash = hash_password(password)
        write_service_password(current_user, service, password_hash)

        if existing_password:
            action = 'UPDATE'
            old_hash = existing_password[0]
        else:
            action = 'CREATE'
            old_hash = None

        log_password_action(
            username=current_user,
            service=service,
            action_type=action,
            old_password_hash=old_hash,
            new_password_hash=password_hash,
            status='SUCCESS'
        )
        
        return jsonify({
            'message': 'Password saved securely',
            'status': 'success'
        }), 201

    except APIError as e:
        log_password_action(
            username=current_user,
            service=data.get('service'),
            action_type='CREATE_OR_UPDATE',
            status='FAILED',
            details=e.message
        )
        raise e
    except Exception as e:
        app.logger.error(f"Password save error: {str(e)}\n{traceback.format_exc()}")
        log_password_action(
            username=current_user,
            service=data.get('service'),
            action_type='CREATE_OR_UPDATE',
            status='FAILED',
            details='Internal error'
        )
        raise APIError('Password save failed', 500)

@app.route('/verify_password', methods=['POST'])
@token_required
def verify_password(current_user):
    try:
        data = request.get_json()
        if not data:
            raise APIError('No input data provided', 400)
        
        service = data.get('service')
        password = data.get('password')

        if not service or not password:
            raise APIError('Service and password are required', 400)

        is_valid = verify_service_password(current_user, service, password)
        return jsonify({
            'valid': is_valid,
            'status': 'success'
        }), 200

    except APIError as e:
        raise e
    except Exception as e:
        app.logger.error(f"Password verification error: {str(e)}\n{traceback.format_exc()}")
        raise APIError('Password verification failed', 500)

@app.route('/get_services', methods=['GET'])
@token_required
def get_services(current_user):
    try:
        services = get_user_services(current_user)
        return jsonify({
            'services': services,
            'status': 'success'
        }), 200
    except APIError as e:
        raise e
    except Exception as e:
        app.logger.error(f"Get services error: {str(e)}\n{traceback.format_exc()}")
        raise APIError('Failed to get services', 500)

@app.route('/delete_password', methods=['POST'])
@token_required
def delete_password(current_user):
    try:
        data = request.get_json()
        if not data:
            raise APIError('No input data provided', 400)
        
        service = data.get('service')
        if not service:
            raise APIError('Service is required', 400)

        # Получаем текущий пароль перед удалением
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT password_hash FROM passwords WHERE username = %s AND service = %s",
            (current_user, service)
        )
        existing_password = cur.fetchone()
        
        if not existing_password:
            log_password_action(
                username=current_user,
                service=service,
                action_type='DELETE',
                status='FAILED',
                details='Password not found'
            )
            raise APIError('Password not found', 404)

        deleted = delete_service_password(current_user, service)
        
        if deleted:
            log_password_action(
                username=current_user,
                service=service,
                action_type='DELETE',
                old_password_hash=existing_password[0],
                status='SUCCESS'
            )
            return jsonify({
                'message': 'Password deleted',
                'status': 'success'
            }), 200
        else:
            log_password_action(
                username=current_user,
                service=service,
                action_type='DELETE',
                status='FAILED',
                details='Deletion failed'
            )
            raise APIError('Deletion failed', 500)

    except APIError as e:
        log_password_action(
            username=current_user,
            service=data.get('service'),
            action_type='DELETE',
            status='FAILED',
            details=e.message
        )
        raise e
    except Exception as e:
        app.logger.error(f"Password deletion error: {str(e)}\n{traceback.format_exc()}")
        log_password_action(
            username=current_user,
            service=data.get('service'),
            action_type='DELETE',
            status='FAILED',
            details='Internal error'
        )
        raise APIError('Password deletion failed', 500)


def log_password_action(username, service, action_type, old_password_hash=None, 
                      new_password_hash=None, status='SUCCESS', details=None):
    try:
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO password_logs 
               (username, service, action_type, old_password_hash, 
                new_password_hash, ip_address, user_agent, status, details) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (username, service, action_type, old_password_hash, 
             new_password_hash, ip_address, user_agent, status, details)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        app.logger.error(f"Failed to log password action: {str(e)}")


@app.route('/get_password_logs', methods=['GET'])
@token_required
def get_password_logs(current_user):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Получаем логи только для текущего пользователя
        cur.execute(
            """SELECT service, action_type, created_at, status, details 
               FROM password_logs 
               WHERE username = %s 
               ORDER BY created_at DESC 
               LIMIT 100""",
            (current_user,)
        )
        
        logs = []
        for row in cur.fetchall():
            logs.append({
                'service': row[0],
                'action': row[1],
                'timestamp': row[2].isoformat() if row[2] else None,
                'status': row[3],
                'details': row[4]
            })
            
        cur.close()
        conn.close()
        
        return jsonify({
            'logs': logs,
            'status': 'success'
        }), 200
        
    except Exception as e:
        app.logger.error(f"Failed to get password logs: {str(e)}")
        log_user_action(current_user, 'GET_PASSWORD_LOGS', 'FAILED', str(e))
        raise APIError('Failed to get password logs', 500)

@app.route('/get_profile', methods=['GET'])
@token_required
def get_profile(current_user):
    try:
        profiles = read_profiles()
        profile = next((p for p in profiles if p['username'] == current_user), None)
        if profile:
            return jsonify({
                **profile,
                'status': 'success'
            }), 200
        else:
            return jsonify({
                'username': current_user,
                'email': None,
                'avatarUrl': None,
                'status': 'success'
            }), 200
    except APIError as e:
        raise e
    except Exception as e:
        app.logger.error(f"Get profile error: {str(e)}\n{traceback.format_exc()}")
        raise APIError('Failed to get profile', 500)

@app.route('/update_profile', methods=['POST'])
@token_required
def update_profile(current_user):
    try:
        email = request.form.get('email')
        avatar = request.files.get('avatar')

        avatar_url = None
        if avatar:
            filename = secure_filename(f"{current_user}_{avatar.filename}")
            avatar.save(os.path.join(UPLOAD_FOLDER, filename))
            avatar_url = f"http://localhost:5000/uploads/{filename}"

        write_profile(current_user, email, avatar_url)
        log_user_action(current_user, 'UPDATE_PROFILE', 'SUCCESS')
        
        return jsonify({
            'message': 'Profile updated',
            'avatarUrl': avatar_url,
            'status': 'success'
        }), 200

    except APIError as e:
        log_user_action(current_user, 'UPDATE_PROFILE', 'FAILED', e.message)
        raise e
    except Exception as e:
        app.logger.error(f"Profile update error: {str(e)}\n{traceback.format_exc()}")
        log_user_action(current_user, 'UPDATE_PROFILE', 'FAILED', 'Internal error')
        raise APIError('Profile update failed', 500)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        app.logger.error(f"File serve error: {str(e)}")
        raise APIError('File not found', 404)

if __name__ == '__main__':
    app.run(port=5000)