"""
Unit tests for Config Repository.
Write these tests BEFORE implementing the repository (TDD approach).
"""

import pytest
from pathlib import Path
import tempfile
import shutil


class TestConfigRepository:
    """Test ConfigRepository for managing StoryMetadata persistence"""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def config_repo(self, temp_storage_dir):
        """Create a ConfigRepository instance for testing"""
        from src.repositories.config_repository import ConfigRepository
        return ConfigRepository(storage_dir=temp_storage_dir)

    def test_config_repository_initialization(self, temp_storage_dir):
        """Test creating ConfigRepository with custom storage directory"""
        from src.repositories.config_repository import ConfigRepository

        repo = ConfigRepository(storage_dir=temp_storage_dir)

        assert repo.storage_dir == temp_storage_dir
        assert repo.storage_dir.exists()

    def test_config_repository_creates_storage_dir_if_not_exists(self, temp_storage_dir):
        """Test that ConfigRepository creates storage directory if it doesn't exist"""
        from src.repositories.config_repository import ConfigRepository

        non_existent_dir = temp_storage_dir / "new_dir"
        assert not non_existent_dir.exists()

        repo = ConfigRepository(storage_dir=non_existent_dir)

        assert repo.storage_dir.exists()

    def test_save_config(self, config_repo, temp_storage_dir):
        """Test saving a StoryMetadata"""
        from src.models.story import StoryMetadata

        config = StoryMetadata(
            title="The Magic Forest",
            language="Spanish",
            complexity="beginner",
            vocabulary_diversity="medium",
            age_group="4-7 years",
            num_pages=5,
            genre="Adventure",
            art_style="watercolor children's book illustration",
            user_prompt="A story about a brave squirrel"
        )

        config_id = config_repo.save(config)

        assert config_id is not None
        assert isinstance(config_id, str)

        # Verify file was created
        config_file = temp_storage_dir / "configs" / f"{config_id}.json"
        assert config_file.exists()

    def test_get_config_by_id(self, config_repo):
        """Test retrieving a StoryMetadata by ID"""
        from src.models.story import StoryMetadata

        config = StoryMetadata(
            title="Test Story",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=3,
            user_prompt="A test story"
        )

        config_id = config_repo.save(config)
        retrieved = config_repo.get(config_id)

        assert retrieved is not None
        assert retrieved.title == "Test Story"
        assert retrieved.language == "English"
        assert retrieved.complexity == "beginner"
        assert retrieved.num_pages == 3

    def test_get_nonexistent_config_returns_none(self, config_repo):
        """Test that getting a non-existent config returns None"""
        result = config_repo.get("nonexistent-id")
        assert result is None

    def test_list_all_configs(self, config_repo):
        """Test listing all saved configs"""
        from src.models.story import StoryMetadata

        config1 = StoryMetadata(
            title="Story 1",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=3,
            user_prompt="Story 1"
        )

        config2 = StoryMetadata(
            title="Story 2",
            language="Spanish",
            complexity="intermediate",
            vocabulary_diversity="medium",
            age_group="8-12 years",
            num_pages=5,
            user_prompt="Story 2"
        )

        id1 = config_repo.save(config1)
        id2 = config_repo.save(config2)

        all_configs = config_repo.list_all()

        assert len(all_configs) == 2
        assert id1 in all_configs
        assert id2 in all_configs

    def test_list_all_empty_repository(self, config_repo):
        """Test listing configs from empty repository"""
        all_configs = config_repo.list_all()
        assert all_configs == []

    def test_update_config(self, config_repo):
        """Test updating an existing config"""
        from src.models.story import StoryMetadata

        config = StoryMetadata(
            title="Original Title",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=3,
            user_prompt="Original prompt"
        )

        config_id = config_repo.save(config)

        # Create updated config
        updated_config = StoryMetadata(
            title="Updated Title",
            language="Spanish",
            complexity="intermediate",
            vocabulary_diversity="high",
            age_group="8-12 years",
            num_pages=10,
            user_prompt="Updated prompt"
        )

        config_repo.update(config_id, updated_config)

        # Retrieve and verify
        retrieved = config_repo.get(config_id)
        assert retrieved.title == "Updated Title"
        assert retrieved.language == "Spanish"
        assert retrieved.complexity == "intermediate"
        assert retrieved.num_pages == 10

    def test_update_nonexistent_config_raises_error(self, config_repo):
        """Test that updating non-existent config raises ValueError"""
        from src.models.story import StoryMetadata

        config = StoryMetadata(
            title="Test",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=3,
            user_prompt="Test"
        )

        with pytest.raises(ValueError, match="Config with id .* not found"):
            config_repo.update("nonexistent-id", config)

    def test_delete_config(self, config_repo, temp_storage_dir):
        """Test deleting a config"""
        from src.models.story import StoryMetadata

        config = StoryMetadata(
            title="To Delete",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=3,
            user_prompt="Test"
        )

        config_id = config_repo.save(config)
        config_file = temp_storage_dir / "configs" / f"{config_id}.json"

        assert config_file.exists()

        config_repo.delete(config_id)

        assert not config_file.exists()
        assert config_repo.get(config_id) is None

    def test_delete_nonexistent_config_raises_error(self, config_repo):
        """Test that deleting non-existent config raises ValueError"""
        with pytest.raises(ValueError, match="Config with id .* not found"):
            config_repo.delete("nonexistent-id")

    def test_config_persistence_across_instances(self, temp_storage_dir):
        """Test that configs persist across repository instances"""
        from src.repositories.config_repository import ConfigRepository
        from src.models.story import StoryMetadata

        # Create first instance and save config
        repo1 = ConfigRepository(storage_dir=temp_storage_dir)
        config = StoryMetadata(
            title="Persistent Story",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=3,
            user_prompt="Test"
        )
        config_id = repo1.save(config)

        # Create second instance and retrieve config
        repo2 = ConfigRepository(storage_dir=temp_storage_dir)
        retrieved = repo2.get(config_id)

        assert retrieved is not None
        assert retrieved.title == "Persistent Story"

    def test_config_serialization_includes_all_fields(self, config_repo):
        """Test that all config fields are properly serialized and deserialized"""
        from src.models.story import StoryMetadata

        config = StoryMetadata(
            title="Complete Story",
            language="French",
            complexity="advanced",
            vocabulary_diversity="high",
            age_group="13-18 years",
            num_pages=15,
            genre="Mystery",
            art_style="digital painting",
            user_prompt="A complex mystery story"
        )

        config_id = config_repo.save(config)
        retrieved = config_repo.get(config_id)

        assert retrieved.title == config.title
        assert retrieved.language == config.language
        assert retrieved.complexity == config.complexity
        assert retrieved.vocabulary_diversity == config.vocabulary_diversity
        assert retrieved.age_group == config.age_group
        assert retrieved.num_pages == config.num_pages
        assert retrieved.genre == config.genre
        assert retrieved.art_style == config.art_style
        assert retrieved.user_prompt == config.user_prompt

    def test_config_with_optional_fields_none(self, config_repo):
        """Test saving and retrieving config with None optional fields"""
        from src.models.story import StoryMetadata

        config = StoryMetadata(
            title="Minimal Story",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=3,
            genre=None,
            art_style=None,
            user_prompt=None
        )

        config_id = config_repo.save(config)
        retrieved = config_repo.get(config_id)

        assert retrieved.genre is None
        assert retrieved.art_style is None
        assert retrieved.user_prompt is None

    def test_multiple_configs_independent(self, config_repo):
        """Test that multiple configs are stored independently"""
        from src.models.story import StoryMetadata

        config1 = StoryMetadata(
            title="Story A",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=3,
            user_prompt="A"
        )

        config2 = StoryMetadata(
            title="Story B",
            language="Spanish",
            complexity="intermediate",
            vocabulary_diversity="medium",
            age_group="8-12 years",
            num_pages=7,
            user_prompt="B"
        )

        id1 = config_repo.save(config1)
        id2 = config_repo.save(config2)

        # Verify they are different IDs
        assert id1 != id2

        # Retrieve both
        retrieved1 = config_repo.get(id1)
        retrieved2 = config_repo.get(id2)

        assert retrieved1.title == "Story A"
        assert retrieved2.title == "Story B"
        assert retrieved1.num_pages == 3
        assert retrieved2.num_pages == 7

    def test_config_id_format(self, config_repo):
        """Test that generated config IDs follow expected format"""
        from src.models.story import StoryMetadata

        config = StoryMetadata(
            title="Test",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=3,
            user_prompt="Test"
        )

        config_id = config_repo.save(config)

        # Should be a non-empty string
        assert isinstance(config_id, str)
        assert len(config_id) > 0

        # Should start with "config-"
        assert config_id.startswith("config-")
