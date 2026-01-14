"""
Unit tests for Project Repository.
Write these tests BEFORE implementing the repository (TDD approach).
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime


class TestProjectRepository:
    """Test ProjectRepository for managing Project persistence"""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def project_repo(self, temp_storage_dir):
        """Create a ProjectRepository instance for testing"""
        from src.repositories.project_repository import ProjectRepository
        return ProjectRepository(storage_dir=temp_storage_dir)

    @pytest.fixture
    def sample_project(self):
        """Create a sample Project for testing"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata, StoryPage
        from src.models.character import Character

        metadata = StoryMetadata(
            title="The Magic Forest",
            language="Spanish",
            complexity="beginner",
            vocabulary_diversity="medium",
            age_group="4-7 years",
            num_pages=3,
            genre="Adventure",
            user_prompt="A story about a brave squirrel"
        )

        pages = [
            StoryPage(page_number=1, text="Había una vez un bosque mágico."),
            StoryPage(page_number=2, text="Una ardilla valiente vivía allí."),
            StoryPage(page_number=3, text="Ella encontró una bellota dorada."),
        ]

        luna = Character(
            name="Luna",
            description="A brave squirrel",
            role="protagonist"
        )

        story = Story(
            id="story-123",
            metadata=metadata,
            pages=pages,
            vocabulary=["bosque", "ardilla", "valiente", "bellota", "dorada"],
            characters=[luna]
        )

        project = Project(
            id="project-123",
            name="Luna's Adventure",
            story=story,
            status=ProjectStatus.STORY_GENERATED
        )

        return project

    def test_project_repository_initialization(self, temp_storage_dir):
        """Test creating ProjectRepository with custom storage directory"""
        from src.repositories.project_repository import ProjectRepository

        repo = ProjectRepository(storage_dir=temp_storage_dir)

        assert repo.storage_dir == temp_storage_dir
        assert repo.storage_dir.exists()

    def test_project_repository_creates_storage_dir_if_not_exists(self, temp_storage_dir):
        """Test that ProjectRepository creates storage directory if it doesn't exist"""
        from src.repositories.project_repository import ProjectRepository

        non_existent_dir = temp_storage_dir / "new_dir"
        assert not non_existent_dir.exists()

        repo = ProjectRepository(storage_dir=non_existent_dir)

        assert repo.storage_dir.exists()

    def test_save_project(self, project_repo, sample_project, temp_storage_dir):
        """Test saving a Project"""
        project_id = project_repo.save(sample_project)

        assert project_id is not None
        assert isinstance(project_id, str)
        assert project_id == sample_project.id

        # Verify file was created
        project_file = temp_storage_dir / "projects" / f"{project_id}.json"
        assert project_file.exists()

    def test_get_project_by_id(self, project_repo, sample_project):
        """Test retrieving a Project by ID"""
        project_id = project_repo.save(sample_project)
        retrieved = project_repo.get(project_id)

        assert retrieved is not None
        assert retrieved.id == sample_project.id
        assert retrieved.name == sample_project.name
        assert retrieved.status == sample_project.status
        assert retrieved.story.metadata.title == "The Magic Forest"
        assert len(retrieved.story.pages) == 3
        assert len(retrieved.story.vocabulary) == 5

    def test_get_nonexistent_project_returns_none(self, project_repo):
        """Test that getting a non-existent project returns None"""
        result = project_repo.get("nonexistent-id")
        assert result is None

    def test_list_all_projects(self, project_repo, sample_project):
        """Test listing all saved projects"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata

        # Save first project
        id1 = project_repo.save(sample_project)

        # Create and save second project
        metadata2 = StoryMetadata(
            title="Another Story",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=5,
            user_prompt="Test"
        )

        story2 = Story(id="story-456", metadata=metadata2, pages=[])
        project2 = Project(
            id="project-456",
            name="Second Project",
            story=story2,
            status=ProjectStatus.DRAFT
        )

        id2 = project_repo.save(project2)

        all_projects = project_repo.list_all()

        assert len(all_projects) == 2
        assert id1 in all_projects
        assert id2 in all_projects

    def test_list_all_empty_repository(self, project_repo):
        """Test listing projects from empty repository"""
        all_projects = project_repo.list_all()
        assert all_projects == []

    def test_update_project(self, project_repo, sample_project):
        """Test updating an existing project"""
        from src.models.project import ProjectStatus

        project_id = project_repo.save(sample_project)

        # Update project status
        sample_project.status = ProjectStatus.COMPLETED
        project_repo.update(project_id, sample_project)

        # Retrieve and verify
        retrieved = project_repo.get(project_id)
        assert retrieved.status == ProjectStatus.COMPLETED

    def test_update_nonexistent_project_raises_error(self, project_repo, sample_project):
        """Test that updating non-existent project raises ValueError"""
        with pytest.raises(ValueError, match="Project with id .* not found"):
            project_repo.update("nonexistent-id", sample_project)

    def test_delete_project(self, project_repo, sample_project, temp_storage_dir):
        """Test deleting a project"""
        project_id = project_repo.save(sample_project)
        project_file = temp_storage_dir / "projects" / f"{project_id}.json"

        assert project_file.exists()

        project_repo.delete(project_id)

        assert not project_file.exists()
        assert project_repo.get(project_id) is None

    def test_delete_nonexistent_project_raises_error(self, project_repo):
        """Test that deleting non-existent project raises ValueError"""
        with pytest.raises(ValueError, match="Project with id .* not found"):
            project_repo.delete("nonexistent-id")

    def test_project_persistence_across_instances(self, temp_storage_dir, sample_project):
        """Test that projects persist across repository instances"""
        from src.repositories.project_repository import ProjectRepository

        # Create first instance and save project
        repo1 = ProjectRepository(storage_dir=temp_storage_dir)
        project_id = repo1.save(sample_project)

        # Create second instance and retrieve project
        repo2 = ProjectRepository(storage_dir=temp_storage_dir)
        retrieved = repo2.get(project_id)

        assert retrieved is not None
        assert retrieved.name == sample_project.name

    def test_project_with_character_profiles(self, project_repo):
        """Test saving and retrieving project with character profiles"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata
        from src.models.character import CharacterProfile

        metadata = StoryMetadata(
            title="Character Story",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=5,
            user_prompt="Test"
        )

        story = Story(id="story-prof", metadata=metadata, pages=[])

        profile = CharacterProfile(
            name="Hero",
            species="fox",
            physical_description="red fox with white-tipped tail",
            clothing="green cape"
        )

        project = Project(
            id="project-prof",
            name="Character Project",
            story=story,
            status=ProjectStatus.DRAFT,
            character_profiles=[profile]
        )

        project_id = project_repo.save(project)
        retrieved = project_repo.get(project_id)

        assert len(retrieved.character_profiles) == 1
        assert retrieved.character_profiles[0].name == "Hero"
        assert retrieved.character_profiles[0].species == "fox"

    def test_project_with_image_prompts(self, project_repo):
        """Test saving and retrieving project with image prompts"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata
        from src.models.image_prompt import ImagePrompt

        metadata = StoryMetadata(
            title="Image Story",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=3,
            user_prompt="Test"
        )

        story = Story(id="story-img", metadata=metadata, pages=[])

        prompt = ImagePrompt(
            page_number=1,
            scene_description="A beautiful scene",
            art_style="watercolor children's book illustration"
        )

        project = Project(
            id="project-img",
            name="Image Project",
            story=story,
            status=ProjectStatus.PROMPTS_GENERATED,
            image_prompts=[prompt]
        )

        project_id = project_repo.save(project)
        retrieved = project_repo.get(project_id)

        assert len(retrieved.image_prompts) == 1
        assert retrieved.image_prompts[0].page_number == 1
        assert retrieved.image_prompts[0].scene_description == "A beautiful scene"

    def test_project_with_full_data(self, project_repo):
        """Test saving and retrieving project with all data (story, profiles, prompts)"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata, StoryPage
        from src.models.character import Character, CharacterProfile
        from src.models.image_prompt import ImagePrompt

        metadata = StoryMetadata(
            title="Complete Story",
            language="French",
            complexity="intermediate",
            vocabulary_diversity="high",
            age_group="8-12 years",
            num_pages=2,
            genre="Fantasy",
            user_prompt="A complete story"
        )

        pages = [
            StoryPage(page_number=1, text="Il était une fois..."),
            StoryPage(page_number=2, text="Et ils vécurent heureux."),
        ]

        character = Character(name="Pierre", description="Brave knight", role="protagonist")
        story = Story(
            id="story-full",
            metadata=metadata,
            pages=pages,
            vocabulary=["fois", "heureux"],
            characters=[character]
        )

        profile = CharacterProfile(
            name="Pierre",
            species="human",
            physical_description="tall knight with armor",
            clothing="silver armor"
        )

        prompt = ImagePrompt(
            page_number=1,
            scene_description="Pierre in the castle",
            art_style="oil painting style",
            characters=[profile]
        )

        project = Project(
            id="project-full",
            name="Complete Project",
            story=story,
            status=ProjectStatus.PROMPTS_GENERATED,
            character_profiles=[profile],
            image_prompts=[prompt]
        )

        project_id = project_repo.save(project)
        retrieved = project_repo.get(project_id)

        # Verify story
        assert retrieved.story.metadata.title == "Complete Story"
        assert len(retrieved.story.pages) == 2
        assert len(retrieved.story.vocabulary) == 2
        assert len(retrieved.story.characters) == 1

        # Verify character profiles
        assert len(retrieved.character_profiles) == 1
        assert retrieved.character_profiles[0].name == "Pierre"

        # Verify image prompts
        assert len(retrieved.image_prompts) == 1
        assert retrieved.image_prompts[0].page_number == 1

    def test_project_timestamps_preserved(self, project_repo, sample_project):
        """Test that project timestamps are preserved during save/load"""
        project_id = project_repo.save(sample_project)
        retrieved = project_repo.get(project_id)

        assert retrieved.created_at is not None
        assert retrieved.updated_at is not None
        assert isinstance(retrieved.created_at, datetime)
        assert isinstance(retrieved.updated_at, datetime)

    def test_project_status_workflow(self, project_repo):
        """Test project status progression through workflow"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata

        metadata = StoryMetadata(
            title="Workflow Story",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=5,
            user_prompt="Test"
        )

        story = Story(id="story-work", metadata=metadata, pages=[])

        project = Project(
            id="project-work",
            name="Workflow Project",
            story=story,
            status=ProjectStatus.DRAFT
        )

        # Save initial project
        project_id = project_repo.save(project)

        # Progress through statuses
        statuses = [
            ProjectStatus.STORY_GENERATED,
            ProjectStatus.PROMPTS_GENERATED,
            ProjectStatus.IMAGES_GENERATED,
            ProjectStatus.COMPLETED
        ]

        for status in statuses:
            project.status = status
            project_repo.update(project_id, project)
            retrieved = project_repo.get(project_id)
            assert retrieved.status == status

    def test_multiple_projects_independent(self, project_repo):
        """Test that multiple projects are stored independently"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata

        # Create first project
        metadata1 = StoryMetadata(
            title="Story A",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=3,
            user_prompt="A"
        )
        story1 = Story(id="story-a", metadata=metadata1, pages=[])
        project1 = Project(
            id="project-a",
            name="Project A",
            story=story1,
            status=ProjectStatus.DRAFT
        )

        # Create second project
        metadata2 = StoryMetadata(
            title="Story B",
            language="Spanish",
            complexity="intermediate",
            vocabulary_diversity="medium",
            age_group="8-12 years",
            num_pages=7,
            user_prompt="B"
        )
        story2 = Story(id="story-b", metadata=metadata2, pages=[])
        project2 = Project(
            id="project-b",
            name="Project B",
            story=story2,
            status=ProjectStatus.STORY_GENERATED
        )

        # Save both
        id1 = project_repo.save(project1)
        id2 = project_repo.save(project2)

        # Verify they are different
        assert id1 != id2

        # Retrieve both
        retrieved1 = project_repo.get(id1)
        retrieved2 = project_repo.get(id2)

        assert retrieved1.name == "Project A"
        assert retrieved2.name == "Project B"
        assert retrieved1.story.metadata.title == "Story A"
        assert retrieved2.story.metadata.title == "Story B"
