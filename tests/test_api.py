import pytest
import os
from datetime import datetime, timedelta
from flask import json
from io import BytesIO
import csv
from app import create_app  
from extensions import db
from models import UserAnalytics
from config import Config

class TestConfig(Config):
    """Test configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  
    SQLALCHEMY_TRACK_MODIFICATIONS = False

@pytest.fixture
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
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def sample_data(app):
    """Insert sample data for testing"""
    with app.app_context():
        users = [
            UserAnalytics(
                username='test_user1',
                mac_address='00:11:22:33:44:55',
                start_time=datetime.now() - timedelta(hours=1),
                usage_time=timedelta(minutes=30),
                upload=1024.0,
                download=2048.0
            ),
            UserAnalytics(
                username='test_user2',
                mac_address='66:77:88:99:AA:BB',
                start_time=datetime.now() - timedelta(days=2),
                usage_time=timedelta(hours=2),
                upload=2048.0,
                download=4096.0
            )
        ]
        db.session.bulk_save_objects(users)
        db.session.commit()

class TestIngestEndpoint:
    """Tests for /ingest endpoint"""
    
    def test_ingest_valid_csv(self, client):
        """Test successful CSV data ingestion"""
        csv_data = "username,mac_address,start_time,usage_time,upload,download\n"
        csv_data += "user1,00:11:22:33:44:55,2024-01-01 10:00:00,01:30:00,1024,2048\n"
        csv_data += "user2,66:77:88:99:AA:BB,2024-01-01 11:00:00,02:00:00,2048,4096\n"
        
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
        csv_data = "username,mac_address\n"
        csv_data += "user1,00:11:22:33:44:55\n"
        
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

class TestAnalyticsEndpoint:
    """Tests for /analytics endpoint"""
    
    def test_analytics_valid_request(self, client, sample_data):
        """Test analytics endpoint with valid date"""
        date = datetime.now().strftime('%d%m%Y')
        response = client.get(f'/analytics?date={date}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['ok'] is True
        assert len(data['data']) > 0
    
    def test_analytics_pagination(self, client, sample_data):
        """Test analytics endpoint pagination"""
        date = datetime.now().strftime('%d%m%Y')
        response = client.get(f'/analytics?date={date}&page=1&pageSize=1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['ok'] is True
        assert len(data['data']) == 1
        assert data['pageSize'] == 1
    
    def test_analytics_future_date(self, client):
        """Test analytics endpoint with future date"""
        future_date = (datetime.now() + timedelta(days=1)).strftime('%d%m%Y')
        response = client.get(f'/analytics?date={future_date}')
        
        assert response.status_code == 422
        data = json.loads(response.data)
        assert data['ok'] is False

class TestUserSearchEndpoint:
    """Tests for /user/search endpoint"""
    def test_user_search_not_found(self, client):
        """Test user search with non-existent user"""
        datetime_str = datetime.now().strftime('%Y%m%dT%H%M')
        response = client.get(f'/user/search?username=nonexistent&datetime={datetime_str}')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['ok'] is False
    
    def test_user_search_invalid_params(self, client):
        """Test user search with invalid parameters"""
        # Missing username
        response = client.get('/user/search?datetime=20240101T1200')
        assert response.status_code == 400
        
        # Missing datetime
        response = client.get('/user/search?username=test_user1')
        assert response.status_code == 400
        
        # Invalid datetime format
        response = client.get('/user/search?username=test_user1&datetime=invalid')
        assert response.status_code == 400
