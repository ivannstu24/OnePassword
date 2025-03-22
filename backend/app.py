from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import csv
import os
import random
import string

app = Flask(__name__)
CORS(app)

USERS_CSV = 'users.csv'
PASSWORDS_CSV = 'passwords.csv'
PROFILES_CSV = 'profiles.csv'
UPLOAD_FOLDER = 'uploads'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(USERS_CSV):
    with open(USERS_CSV, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['username', 'password'])

if not os.path.exists(PASSWORDS_CSV):
    with open(PASSWORDS_CSV, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['username', 'service', 'password'])

if not os.path.exists(PROFILES_CSV):
    with open(PROFILES_CSV, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['username', 'email', 'avatarUrl'])

def read_users():
    with open(USERS_CSV, mode='r') as file:
        reader = csv.DictReader(file)
        return list(reader)

def write_user(username, password):
    with open(USERS_CSV, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([username, password])

def read_passwords(username):
    with open(PASSWORDS_CSV, mode='r') as file:
        reader = csv.DictReader(file)
        return [row for row in reader if row['username'] == username]

def write_password(username, service, password):
    with open(PASSWORDS_CSV, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([username, service, password])

def delete_password(username, service):
    passwords = []
    with open(PASSWORDS_CSV, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] != username or row['service'] != service:
                passwords.append(row)

    with open(PASSWORDS_CSV, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['username', 'service', 'password'])
        writer.writeheader()
        writer.writerows(passwords)

def update_password(username, service, new_password):
    passwords = []
    updated = False
    with open(PASSWORDS_CSV, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username and row['service'] == service:
                row['password'] = new_password  # Обновляем пароль
                updated = True
            passwords.append(row)

    if updated:
        with open(PASSWORDS_CSV, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['username', 'service', 'password'])
            writer.writeheader()
            writer.writerows(passwords)
        return True
    else:
        return False

def read_profiles():
    with open(PROFILES_CSV, mode='r') as file:
        reader = csv.DictReader(file)
        return list(reader)

def write_profile(username, email, avatarUrl):
    profiles = read_profiles()
    profile = next((profile for profile in profiles if profile['username'] == username), None)
    if profile:
        profile['email'] = email
        profile['avatarUrl'] = avatarUrl
    else:
        profiles.append({'username': username, 'email': email, 'avatarUrl': avatarUrl})

    with open(PROFILES_CSV, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['username', 'email', 'avatarUrl'])
        writer.writeheader()
        writer.writerows(profiles)


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

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
    user = next((user for user in users if user['username'] == username and user['password'] == password), None)
    if user:
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/save_password', methods=['POST'])
def save_password():
    data = request.json
    username = data.get('username')
    service = data.get('service')
    password = data.get('password')

    if not username:
        return jsonify({'message': 'Unauthorized'}), 403

    write_password(username, service, password)
    return jsonify({'message': 'Password saved'}), 201

@app.route('/get_passwords', methods=['GET'])
def get_passwords():
    username = request.args.get('username')

    if not username:
        return jsonify({'message': 'Unauthorized'}), 403

    user_passwords = read_passwords(username)
    return jsonify(user_passwords), 200

@app.route('/delete_password', methods=['POST'])
def delete_password_route():
    data = request.json
    username = data.get('username')
    service = data.get('service')

    if not username:
        return jsonify({'message': 'Unauthorized'}), 403

    delete_password(username, service)
    return jsonify({'message': 'Password deleted'}), 200

@app.route('/update_password', methods=['PUT'])
def update_password_route():
    data = request.json
    username = data.get('username')
    service = data.get('service')
    new_password = data.get('new_password')
    if not username or not service or not new_password:
        return jsonify({'message': 'Username, service, and new_password are required'}), 400
    if update_password(username, service, new_password):
        return jsonify({'message': 'Password updated'}), 200
    else:
        return jsonify({'message': 'Password not found'}), 404

@app.route('/get_profile', methods=['GET'])
def get_profile():
    username = request.args.get('username')

    if not username:
        return jsonify({'message': 'Unauthorized'}), 403

    profiles = read_profiles()
    profile = next((profile for profile in profiles if profile['username'] == username), None)
    if profile:
        return jsonify(profile), 200
    else:
        return jsonify({'message': 'Profile not found'}), 404

@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    avatar = request.files.get('avatar')

    avatarUrl = None
    if avatar:
        filename = f"{username}_{avatar.filename}"
        avatar.save(os.path.join(UPLOAD_FOLDER, filename))
        avatarUrl = f"http://localhost:5000/uploads/{filename}"

    write_profile(username, email, avatarUrl)
    return jsonify({'message': 'Profile updated', 'avatarUrl': avatarUrl}), 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(port=5000)