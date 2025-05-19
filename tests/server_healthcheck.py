import requests
import os
import psycopg2
from psycopg2 import OperationalError

BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
DB_CONFIG = {
    'dbname': os.getenv("DB_NAME", "OneBad"),
    'user': os.getenv("DB_USER", "ivanmerzov"),
    'password': os.getenv("DB_PASSWORD", "Vania_505"),
    'host': os.getenv("DB_HOST", "localhost"),
    'port': os.getenv("DB_PORT", "5432")
}

def test_server_is_alive():
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        assert response.status_code in [200, 404], "Сервер не отвечает"
    except requests.ConnectionError:
        assert False, "Сервер не запущен"

def test_api_endpoints():
    """Проверка основных API"""
    endpoints = ["/register", "/login"]
    for endpoint in endpoints:
        response = requests.head(f"{BASE_URL}{endpoint}", timeout=5)
        assert response.status_code != 500, f"Ошибка 500 на {endpoint}"

def test_database_connection():
    """Проверка подключения к базе данных"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1, "Тестовый запрос к БД не вернул ожидаемый результат"
        cursor.close()
        conn.close()
    except OperationalError as e:
        assert False, f"Ошибка подключения к БД: {e}"