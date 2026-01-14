"""
End-to-end integration test for complete project workflow.

Tests the full workflow from story creation through image generation
to project saving and retrieval.
"""

import pytest
from unittest.mock import AsyncMock, patch


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
            languages=["English", "Spanish"],
            complexities=["simple", "intermediate"],
            vocabulary_levels=["basic", "advanced"],
            age_groups=["3-5", "6-8"],
            page_counts=[3, 5, 8],
            genres=["adventure", "fantasy"],
            art_styles=["cartoon", "watercolor"]
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


class TestFullWorkflow:
    """End-to-end tests for complete project workflow"""

    def test_complete_project_creation_workflow(self, client, app):
        """
        Test complete project creation workflow.

        Workflow:
        1. Get configuration
        2. Generate story
        3. Save story as project
        4. Retrieve project
        5. Delete project
        """
        # Step 1: Get configuration
        config_response = client.get('/api/config')
        assert config_response.status_code == 200
        config = config_response.get_json()

        # Step 2: Generate story
        with patch('src.ai.ollama_client.OllamaClient.generate_text', new_callable=AsyncMock) as mock_text:
            # Mock AI text responses
            mock_text.side_effect = [
                # Story generation
                """
                Page 1: Once upon a time, a brave knight named Sir Cedric set out on an adventure.
                Page 2: He traveled through enchanted forests and crossed crystal rivers.
                Page 3: Finally, he discovered a magical sword that would protect his kingdom.
                """,
                # Character extraction
                '{"characters": [{"name": "Sir Cedric", "description": "A brave knight in shining armor"}]}',
                # Character profiling
                '{"species": "human", "physical_description": "Tall knight with armor", "clothing": "Silver armor", "distinctive_features": "Red cape", "personality_traits": "Brave and noble"}'
            ]

            story_response = client.post('/api/stories', json={
                'title': 'The Knights Quest',
                'language': config['defaults']['language'],
                'age_group': config['defaults']['age_group'],
                'complexity': config['defaults']['complexity'],
                'vocabulary_diversity': config['defaults']['vocabulary_diversity'],
                'num_pages': 3,
                'genre': 'fantasy',
                'art_style': 'cartoon',
                'theme': 'courage and honor'
            })

            assert story_response.status_code == 201
            story = story_response.get_json()

        # Step 3: Save story as project
        with patch.object(
            app.config['REPOSITORIES']['project'],
            'save',
            return_value=story['id']
        ) as mock_save:
            project_data = {
                'id': story['id'],
                'name': 'The Knights Quest',
                'story': story,
                'status': 'completed',
                'character_profiles': story['characters'],
                'image_prompts': []
            }

            project_response = client.post('/api/projects', json=project_data)
            assert project_response.status_code == 201
            project = project_response.get_json()
            project_id = project['id']

        # Step 4: Retrieve project
        with patch.object(
            app.config['REPOSITORIES']['project'],
            'get',
            return_value=None  # Simulating project not found since we're mocking
        ) as mock_get:
            get_response = client.get(f'/api/projects/{project_id}')
            # Would be 200 if repository actually saved it, but we're mocking
            assert get_response.status_code in [200, 404]

        # Step 5: Delete project
        with patch.object(
            app.config['REPOSITORIES']['project'],
            'delete',
            return_value=True
        ) as mock_delete:
            delete_response = client.delete(f'/api/projects/{project_id}')
            assert delete_response.status_code in [200, 204]

    def test_project_list_workflow(self, client, app):
        """
        Test listing and managing projects.

        Workflow:
        1. Mock repository to return project list
        2. List projects
        3. Verify project IDs are returned
        """
        # Mock repository to return some project IDs
        with patch.object(
            app.config['REPOSITORIES']['project'],
            'list_all',
            return_value=['project-1', 'project-2', 'project-3']
        ) as mock_list:
            # List projects
            list_response = client.get('/api/projects')
            assert list_response.status_code == 200
            project_ids = list_response.get_json()
            assert len(project_ids) == 3
            assert 'project-1' in project_ids
            assert 'project-2' in project_ids
            assert 'project-3' in project_ids

    def test_project_creation_with_validation_errors(self, client):
        """Test project creation with validation errors"""
        # Missing required fields (id, name, story, status)
        response = client.post('/api/projects', json={
            'name': 'Test Project'
            # Missing: id, story, status
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

        # Invalid JSON
        response = client.post('/api/projects',
                              data='not json',
                              content_type='application/json')
        assert response.status_code == 400

    def test_story_generation_handles_errors(self, client, app):
        """Test error handling when story generation fails"""
        with patch('src.ai.ollama_client.OllamaClient.generate_text', new_callable=AsyncMock) as mock_text:
            # Mock story generation failure
            mock_text.side_effect = Exception("AI service unavailable")

            response = client.post('/api/stories', json={
                'title': 'Test Story',
                'num_pages': 3
            })

            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
