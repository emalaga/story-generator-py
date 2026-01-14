"""
Integration tests for Project Routes.
Write these tests BEFORE implementing the routes (TDD approach).

Tests the REST API endpoints for project management.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


@pytest.fixture
def app():
    """Create Flask app for testing"""
    from src.app import create_app
    from src.models.config import (
        AppConfig, AIProviderConfig, TextProvider, ImageProvider,
        OllamaConfig, StoryParameters, DefaultValues
    )

    # Create test config
    test_config = AppConfig(
        ai_providers=AIProviderConfig(
            text_provider=TextProvider.OLLAMA,
            image_provider=ImageProvider.DALLE3,
            ollama=OllamaConfig(
                base_url="http://localhost:11434",
                model="test-model",
                timeout=60
            )
        ),
        parameters=StoryParameters(
            languages=["English"],
            complexities=["simple"],
            vocabulary_levels=["basic"],
            age_groups=["3-5"],
            page_counts=[3, 5, 8],
            genres=["adventure"],
            art_styles=["cartoon"]
        ),
        defaults=DefaultValues(
            language="English",
            complexity="simple",
            vocabulary_diversity="basic",
            age_group="3-5",
            num_pages=5,
            genre="adventure",
            art_style="cartoon"
        )
    )

    app = create_app(config=test_config)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestProjectRoutes:
    """Integration tests for project routes"""

    def test_list_projects_empty(self, client, app):
        """Test GET /api/projects - list projects when none exist"""
        with patch.object(
            app.config['REPOSITORIES']['project'],
            'list_all',
            return_value=[]
        ) as mock_list:
            response = client.get('/api/projects')

            assert response.status_code == 200
            data = response.get_json()
            assert data == []
            mock_list.assert_called_once()

    def test_list_projects_with_data(self, client, app):
        """Test GET /api/projects - list projects with data"""
        with patch.object(
            app.config['REPOSITORIES']['project'],
            'list_all',
            return_value=["project-1", "project-2", "project-3"]
        ) as mock_list:
            response = client.get('/api/projects')

            assert response.status_code == 200
            data = response.get_json()
            assert len(data) == 3
            assert data == ["project-1", "project-2", "project-3"]

    def test_create_project(self, client, app):
        """Test POST /api/projects - save new project"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata, StoryPage

        # Create mock project data
        project_data = {
            'id': 'test-project-123',
            'name': 'Test Project',
            'story': {
                'id': 'story-123',
                'metadata': {
                    'title': 'Test Story',
                    'language': 'English',
                    'complexity': 'simple',
                    'vocabulary_diversity': 'basic',
                    'age_group': '3-5',
                    'num_pages': 3,
                    'genre': 'adventure',
                    'art_style': 'cartoon'
                },
                'pages': [
                    {'page_number': 1, 'text': 'Page 1'},
                    {'page_number': 2, 'text': 'Page 2'},
                    {'page_number': 3, 'text': 'Page 3'}
                ],
                'characters': [],
                'vocabulary': []
            },
            'status': 'completed',
            'character_profiles': [],
            'image_prompts': []
        }

        with patch.object(
            app.config['REPOSITORIES']['project'],
            'save',
            return_value='test-project-123'
        ) as mock_save:
            response = client.post('/api/projects', json=project_data)

            assert response.status_code == 201
            data = response.get_json()
            assert data['id'] == 'test-project-123'
            assert data['name'] == 'Test Project'
            mock_save.assert_called_once()

    def test_create_project_missing_required_fields(self, client):
        """Test POST /api/projects - missing required fields"""
        # Missing 'story' field
        project_data = {
            'id': 'test-project-123',
            'name': 'Test Project',
            'status': 'completed'
        }

        response = client.post('/api/projects', json=project_data)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_create_project_invalid_json(self, client):
        """Test POST /api/projects - invalid JSON"""
        response = client.post(
            '/api/projects',
            data="not json",
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_get_project_by_id(self, client, app):
        """Test GET /api/projects/:id - retrieve project"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata, StoryPage

        # Create mock project
        mock_story = Story(
            id="story-123",
            metadata=StoryMetadata(
                title="Test Story",
                language="English",
                complexity="simple",
                vocabulary_diversity="basic",
                age_group="3-5",
                num_pages=3
            ),
            pages=[
                StoryPage(page_number=1, text="Page 1"),
                StoryPage(page_number=2, text="Page 2"),
                StoryPage(page_number=3, text="Page 3")
            ],
            characters=[]
        )

        mock_project = Project(
            id="test-project-123",
            name="Test Project",
            story=mock_story,
            status=ProjectStatus.COMPLETED,
            character_profiles=[],
            image_prompts=[]
        )

        with patch.object(
            app.config['REPOSITORIES']['project'],
            'get',
            return_value=mock_project
        ) as mock_get:
            response = client.get('/api/projects/test-project-123')

            assert response.status_code == 200
            data = response.get_json()
            assert data['id'] == 'test-project-123'
            assert data['name'] == 'Test Project'
            assert data['status'] == 'completed'
            assert len(data['story']['pages']) == 3
            mock_get.assert_called_once_with('test-project-123')

    def test_get_project_not_found(self, client, app):
        """Test GET /api/projects/:id - project not found"""
        with patch.object(
            app.config['REPOSITORIES']['project'],
            'get',
            return_value=None
        ) as mock_get:
            response = client.get('/api/projects/nonexistent-id')

            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data

    def test_delete_project(self, client, app):
        """Test DELETE /api/projects/:id - delete project"""
        with patch.object(
            app.config['REPOSITORIES']['project'],
            'delete',
            return_value=None
        ) as mock_delete:
            response = client.delete('/api/projects/test-project-123')

            assert response.status_code == 204
            mock_delete.assert_called_once_with('test-project-123')

    def test_delete_project_not_found(self, client, app):
        """Test DELETE /api/projects/:id - project not found"""
        with patch.object(
            app.config['REPOSITORIES']['project'],
            'delete',
            side_effect=FileNotFoundError("Project not found")
        ) as mock_delete:
            response = client.delete('/api/projects/nonexistent-id')

            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data

    def test_create_project_repository_error(self, client, app):
        """Test POST /api/projects - repository error"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata, StoryPage

        project_data = {
            'id': 'test-project-123',
            'name': 'Test Project',
            'story': {
                'id': 'story-123',
                'metadata': {
                    'title': 'Test Story',
                    'language': 'English',
                    'complexity': 'simple',
                    'vocabulary_diversity': 'basic',
                    'age_group': '3-5',
                    'num_pages': 3
                },
                'pages': [{'page_number': 1, 'text': 'Page 1'}],
                'characters': [],
                'vocabulary': []
            },
            'status': 'completed',
            'character_profiles': [],
            'image_prompts': []
        }

        with patch.object(
            app.config['REPOSITORIES']['project'],
            'save',
            side_effect=Exception("Storage error")
        ) as mock_save:
            response = client.post('/api/projects', json=project_data)

            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
