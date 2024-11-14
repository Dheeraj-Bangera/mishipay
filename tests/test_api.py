import pytest
import os
from datetime import datetime, timedelta
from flask import json
from io import BytesIO
import csv
from app import create_app  
from extensions import db, redis_client
from models import UserAnalytics
from config import Config

class TestConfig(Config):
    """Test configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI =  'postgresql://user:password@db:5432/usage_db'
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app(TestConfig)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    yield app
    
    # Clean up
    with app.app_context():
        db.session.remove()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture(autouse=True)
def clean_redis(app):
    """Clean Redis before each test"""
    redis_client.flushdb()
    yield
    redis_client.flushdb()

def sample_data(app):
    """Insert sample data for testing"""
    with app.app_context():
        # Clean existing data
        db.session.query(UserAnalytics).delete()
        db.session.commit()

        current_time = datetime.now()
        users = [
            UserAnalytics(
                username='test_user1',
                mac_address='00:11:22:33:44:55',
                start_time=current_time - timedelta(hours=1),
                usage_time=timedelta(minutes=30),
                upload=1024.0,
                download=2048.0
            ),
            UserAnalytics(
                username='test_user2',
                mac_address='66:77:88:99:AA:BB',
                start_time=current_time - timedelta(hours=2),
                usage_time=timedelta(hours=2),
                upload=2048.0,
                download=4096.0
            )
        ]

        db.session.bulk_save_objects(users)
        db.session.commit()
        return users

class TestIngestEndpoint:
    """Tests for /ingest endpoint"""

    def test_ingest_valid_csv(self, client):
        """Test successful CSV data ingestion"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        csv_data = "username,mac_address,start_time,usage_time,upload,download\n"
        csv_data += f"user1,00:11:22:33:44:55,{current_time},01:30:00,1024,2048\n"

        csv_file = BytesIO(csv_data.encode())

        response = client.post(
            '/ingest',
            data={'file': (csv_file, 'test.csv')},
            content_type='multipart/form-data'
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['ok'] is True

    def test_ingest_invalid_csv_format(self, client):
        """Test ingestion with invalid CSV format"""
        csv_data = "username,mac_address\nuser1,00:11:22:33:44:55\n"
        csv_file = BytesIO(csv_data.encode())

        response = client.post(
            '/ingest',
            data={'file': (csv_file, 'test.csv')},
            content_type='multipart/form-data'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['ok'] is False
        assert 'Missing required headers' in data['error']['message']

    def test_ingest_no_file(self, client):
        """Test ingestion with no file"""
        response = client.post('/ingest')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['ok'] is False

    def test_ingest_invalid_data_format(self, client):
        """Test ingestion with incorrect data format in CSV"""
        csv_data = "username,mac_address,start_time,usage_time,upload,download\n"
        csv_data += "user1,00:11:22:33:44:55,invalid_date,01:30:00,1024,2048\n"

        csv_file = BytesIO(csv_data.encode())

        response = client.post(
            '/ingest',
            data={'file': (csv_file, 'test.csv')},
            content_type='multipart/form-data'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['ok'] is False
        assert 'Data format issue' in data['error']['message']

class TestAnalyticsEndpoint:
    """Tests for /analytics endpoint"""

    def test_analytics_valid_request(self, client):
        """Test analytics endpoint with valid date"""
        today = datetime.now()
        date = today.strftime('%d%m%Y')

        # Cache some data
        key = f"analytics:{date}"
        cached_data = [{"username": "test_user1", "usage": 3600}]
        redis_client.setex(key, 3600, json.dumps(cached_data))
        
        response = client.get(f'/analytics?date={date}')
        assert response.status_code == 200
        print(response.data)
        data = json.loads(response.data)
        assert data['ok'] is True
        assert isinstance(data['data'], list)

    def test_analytics_pagination(self, client):
        """Test analytics endpoint pagination"""
        today = datetime.now()
        date = today.strftime('%d%m%Y')

        # Cache some data
        key = f"analytics:{date}"
        cached_data = [
            {"username": "test_user1", "usage": 3600},
            {"username": "test_user2", "usage": 7200}
        ]
        redis_client.setex(key, 3600, json.dumps(cached_data))

        response = client.get(f'/analytics?date={date}&page=1&pageSize=1')
        print(response.data)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['ok'] is True
        assert len(data['data']) == 1

    def test_analytics_invalid_date_format(self, client):
        """Test analytics endpoint with invalid date format"""
        response = client.get('/analytics?date=invalid_date')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['ok'] is False
        assert 'invalid date format' in data['error']['message']

class TestUserSearchEndpoint:
    """Tests for /user/search endpoint"""

    def test_user_search_invalid_username(self, client):
        """Test user search with invalid username format"""
        response = client.get('/user/search?username=invalid%username&datetime=20240101T1200')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['ok'] is False
        assert 'user not found' in data['error']['message']

    def test_user_search_missing_parameters(self, client):
        """Test user search with missing parameters"""
        # Missing username
        response = client.get('/user/search?datetime=20240101T1200')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['ok'] is False

        # Missing datetime
        response = client.get('/user/search?username=test_user1')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['ok'] is False

    def test_user_search_invalid_datetime_format(self, client):
        """Test user search with invalid datetime format"""
        response = client.get('/user/search?username=test_user1&datetime=invalid')
        print(response.data)
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['ok'] is False
        assert 'Invalid datetime format' in data['error']['message']