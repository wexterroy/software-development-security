from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)

# Конфигурация подключения к PostgreSQL из переменных окружения
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "flaskdb")

app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация SQLAlchemy
db = SQLAlchemy(app)

# Модель клиента (основная таблица)
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clientname = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'clientname': self.clientname,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

# Данные в памяти
in_memory_data = {
    'settings': {
        'app_name': 'Flask REST API',
        'version': '1.0.0',
        'debug': True
    },
    'stats': {
        'requests': 0,
        'start_time': datetime.utcnow().isoformat()
    }
}

# Middleware: счётчик запросов
@app.before_request
def count_request():
    in_memory_data['stats']['requests'] += 1

# --- API для клиентов ---
@app.route('/api/clients', methods=['GET'])
def get_clients():
    clients = Client.query.all()
    return jsonify([client.to_dict() for client in clients])

@app.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):
    client = Client.query.get_or_404(client_id)
    return jsonify(client.to_dict())

@app.route('/api/clients', methods=['POST'])
def create_client():
    data = request.get_json()
    if not data or not all(k in data for k in ('clientname', 'email')):
        return jsonify({'error': 'Missing required fields'}), 400

    client = Client(clientname=data['clientname'], email=data['email'])

    try:
        db.session.add(client)
        db.session.commit()
        return jsonify(client.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    client = Client.query.get_or_404(client_id)
    data = request.get_json()

    if 'clientname' in data:
        client.clientname = data['clientname']
    if 'email' in data:
        client.email = data['email']

    try:
        db.session.commit()
        return jsonify(client.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    try:
        db.session.delete(client)
        db.session.commit()
        return jsonify({'message': f'Client {client_id} deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# --- API для данных в памяти ---
@app.route('/api/memory/settings', methods=['GET'])
def get_settings():
    return jsonify(in_memory_data['settings'])

@app.route('/api/memory/stats', methods=['GET'])
def get_stats():
    return jsonify(in_memory_data['stats'])

@app.route('/api/memory', methods=['GET'])
def get_all_memory_data():
    return jsonify(in_memory_data)

# Главная страница
@app.route('/')
def index():
    return '''
    <h1>Лабораторная работа по дисциплине "Безопасность разработки ПО"</h1>
    <p>API:</p>
    <ul>
        <li><a href="/api/clients">/api/clients</a> (GET, POST)</li>
        <li>/api/clients/&lt;id&gt; (GET, PUT, DELETE)</li>
        <li><a href="/api/memory/settings">/api/memory/settings</a></li>
        <li><a href="/api/memory/stats">/api/memory/stats</a></li>
        <li><a href="/api/memory">/api/memory</a></li>
    </ul>
    '''

# Инициализация БД и демонстрационных данных
def initialize_db():
    with app.app_context():
        db.create_all()

        if Client.query.count() == 0:
            demo_clients = [
                Client(clientname='client1', email='client1@example.com'),
                Client(clientname='client2', email='client2@example.com'),
                Client(clientname='client3', email='client3@example.com'),
            ]
            db.session.add_all(demo_clients)
            db.session.commit()

if __name__ == '__main__':
    initialize_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
