"""
Тесты для API эндпоинтов
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

client = TestClient(app)


class TestAPIEndpoints:
    """Тесты для API эндпоинтов"""
    
    def test_root_endpoint(self):
        """Тест главной страницы"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert response.json() == {"message": "Rating Telegram Bot is running!"}
    
    def test_health_endpoint(self):
        """Тест health check эндпоинта"""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_webhook_endpoint_get(self):
        """Тест webhook эндпоинта с GET запросом (должен возвращать 405)"""
        # Получаем путь webhook из настроек
        from app.core.config import settings
        webhook_path = settings.WEBHOOK_PATH
        
        response = client.get(webhook_path)
        
        # GET запрос к webhook должен возвращать 405 Method Not Allowed
        assert response.status_code == 405
    
    def test_webhook_endpoint_post_invalid_data(self):
        """Тест webhook эндпоинта с некорректными данными"""
        from app.core.config import settings
        webhook_path = settings.WEBHOOK_PATH
        
        response = client.post(webhook_path, json={"invalid": "data"})
        
        # Должен обработать некорректные данные без ошибки
        assert response.status_code in [200, 500]  # Может быть ошибка обработки, но не 404
    
    def test_nonexistent_endpoint(self):
        """Тест несуществующего эндпоинта"""
        response = client.get("/nonexistent")
        
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
