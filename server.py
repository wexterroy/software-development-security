from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)

# Конфигурация для подключения к нескольким БД
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///primary.db'  # Основная БД (SQLite)
app.config['SQLALCHEMY_BINDS'] = {
    'secondary': 'sqlite:///secondary.db',  # Вторая БД (SQLite)
    # Примеры подключения к другим типам БД
    # 'postgres': 'postgresql://clientname:password@localhost/dbname',
    # 'mysql': 'mysql://clientname:password@localhost/dbname'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Модели для основной БД
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

# Модель для второй БД
class Item(db.Model):
    __bind_key__ = 'secondary'  # Указываем к какой БД привязана модель
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'stock': self.stock
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

# Счетчик запросов (middleware)
@app.before_request
def count_request():
    in_memory_data['stats']['requests'] += 1

# REST API для пользователей (основная БД)
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

# REST API для продуктов (вторая БД)
@app.route('/api/items', methods=['GET'])
def get_items():
    items = Item.query.all()
    return jsonify([item.to_dict() for item in items])

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify(item.to_dict())

@app.route('/api/items', methods=['POST'])
def create_item():
    data = request.get_json()
    
    if not data or not all(k in data for k in ('name', 'price')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    item = Item(
        name=data['name'], 
        price=data['price'],
        stock=data.get('stock', 0)
    )
    
    try:
        db.session.add(item)
        db.session.commit()
        return jsonify(item.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    data = request.get_json()
    
    if 'name' in data:
        item.name = data['name']
    if 'price' in data:
        item.price = data['price']
    if 'stock' in data:
        item.stock = data['stock']
    
    try:
        db.session.commit()
        return jsonify(item.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': f'Item {item_id} deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# API для данных в памяти
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
    <h1>Лабораторная работа по дисциплине "Безопасность разработки программного обеспечения"</h1>
    <p>Доступные конечные точки:</p>
    <ul>
        <li><a href="/api/clients">/api/clients</a> (GET, POST)</li>
        <li>/api/clients/&lt;id&gt; (GET, PUT, DELETE)</li>
        <li><a href="/api/items">/api/items</a> (GET, POST)</li>
        <li>/api/items/&lt;id&gt; (GET, PUT, DELETE)</li>
        <li><a href="/api/memory/settings">/api/memory/settings</a> (GET)</li>
        <li><a href="/api/memory/stats">/api/memory/stats</a> (GET)</li>
        <li><a href="/api/memory">/api/memory</a> (GET)</li>
    </ul>
    '''

# Инициализация БД
# Функция инициализации БД
def initialize_db():
    with app.app_context():
        db.create_all()
        
        # Добавление демонстрационных данных, если БД пустые
        if Client.query.count() == 0:
            test_clients = [
                Client(clientname='client1', email='client1@example.com'),
                Client(clientname='client2', email='client2@example.com'),
                Client(clientname='client3', email='client3@example.com'),
                Client(clientname='client4', email='client4@example.com'),
                Client(clientname='client5', email='client5@example.com')
            ]
            db.session.add_all(test_clients)
            
        if Item.query.count() == 0:
            test_items = [
                Item(name='Товар 1', price=100.0, stock=10),
                Item(name='Товар 2', price=200.0, stock=5),
                Item(name='Товар 3', price=150.0, stock=7),
                Item(name='Товар 4', price=80.0, stock=12),
                Item(name='Товар 5', price=300.0, stock=3)
            ]
            db.session.add_all(test_items)
            
        db.session.commit()

if __name__ == '__main__':
    # Создание папки для БД, если ее нет
    os.makedirs('instance', exist_ok=True)
    
    # Инициализация БД перед запуском
    initialize_db()
    
    # Запуск приложения
    app.run(host='0.0.0.0', port=5000, debug=True)