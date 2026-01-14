"""
Unit tests for Project Models.
Write these tests BEFORE implementing the models (TDD approach).
"""

import pytest
from datetime import datetime


class TestProjectStatus:
    """Test ProjectStatus enum"""

    def test_project_status_values(self):
        """Test that ProjectStatus has correct values"""
        from src.models.project import ProjectStatus

        assert ProjectStatus.DRAFT.value == "draft"
        assert ProjectStatus.STORY_GENERATED.value == "story_generated"
        assert ProjectStatus.PROMPTS_GENERATED.value == "prompts_generated"
        assert ProjectStatus.IMAGES_GENERATED.value == "images_generated"
        assert ProjectStatus.COMPLETED.value == "completed"

    def test_project_status_from_string(self):
        """Test creating ProjectStatus from string"""
        from src.models.project import ProjectStatus

        assert ProjectStatus("draft") == ProjectStatus.DRAFT
        assert ProjectStatus("story_generated") == ProjectStatus.STORY_GENERATED
        assert ProjectStatus("prompts_generated") == ProjectStatus.PROMPTS_GENERATED
        assert ProjectStatus("images_generated") == ProjectStatus.IMAGES_GENERATED
        assert ProjectStatus("completed") == ProjectStatus.COMPLETED

    def test_project_status_workflow_order(self):
        """Test that ProjectStatus values represent workflow order"""
        from src.models.project import ProjectStatus

        # These represent the typical workflow progression
        statuses = [
            ProjectStatus.DRAFT,
            ProjectStatus.STORY_GENERATED,
            ProjectStatus.PROMPTS_GENERATED,
            ProjectStatus.IMAGES_GENERATED,
            ProjectStatus.COMPLETED
        ]

        assert len(statuses) == 5
        assert statuses[0] == ProjectStatus.DRAFT
        assert statuses[-1] == ProjectStatus.COMPLETED


class TestProject:
    """Test Project dataclass"""

    def test_project_creation_minimal(self):
        """Test creating Project with minimal required fields"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata

        metadata = StoryMetadata(
            title="Test Story",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=5,
            user_prompt="A test story"
        )

        story = Story(
            id="story-123",
            metadata=metadata,
            pages=[]
        )

        project = Project(
            id="project-123",
            name="My First Story",
            story=story,
            status=ProjectStatus.DRAFT
        )

        assert project.id == "project-123"
        assert project.name == "My First Story"
        assert project.story == story
        assert project.status == ProjectStatus.DRAFT
        assert project.character_profiles == []
        assert project.image_prompts == []
        assert isinstance(project.created_at, datetime)
        assert isinstance(project.updated_at, datetime)

    def test_project_creation_full(self):
        """Test creating Project with all fields"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata, StoryPage
        from src.models.character import Character, CharacterProfile
        from src.models.image_prompt import ImagePrompt

        # Story
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
            StoryPage(page_number=1, text="Page 1 text"),
            StoryPage(page_number=2, text="Page 2 text"),
            StoryPage(page_number=3, text="Page 3 text"),
        ]

        luna = Character(name="Luna", description="A brave squirrel", role="protagonist")

        story = Story(
            id="story-456",
            metadata=metadata,
            pages=pages,
            characters=[luna]
        )

        # Character Profile
        luna_profile = CharacterProfile(
            name="Luna",
            species="squirrel",
            physical_description="small brown squirrel with bushy tail",
            clothing="tiny green backpack"
        )

        # Image Prompts
        prompt1 = ImagePrompt(
            page_number=1,
            scene_description="Luna in the forest",
            art_style="watercolor children's book illustration",
            characters=[luna_profile]
        )

        prompt2 = ImagePrompt(
            page_number=2,
            scene_description="Luna climbing a tree",
            art_style="watercolor children's book illustration",
            characters=[luna_profile]
        )

        # Project
        now = datetime.now()
        project = Project(
            id="project-456",
            name="Luna's Adventure",
            story=story,
            status=ProjectStatus.PROMPTS_GENERATED,
            character_profiles=[luna_profile],
            image_prompts=[prompt1, prompt2],
            created_at=now,
            updated_at=now
        )

        assert project.id == "project-456"
        assert project.name == "Luna's Adventure"
        assert project.story == story
        assert project.status == ProjectStatus.PROMPTS_GENERATED
        assert len(project.character_profiles) == 1
        assert project.character_profiles[0].name == "Luna"
        assert len(project.image_prompts) == 2
        assert project.image_prompts[0].page_number == 1
        assert project.created_at == now
        assert project.updated_at == now

    def test_project_status_progression(self):
        """Test Project status progression through workflow"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata

        metadata = StoryMetadata(
            title="Progressive Story",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=5,
            user_prompt="Test"
        )

        story = Story(id="story-789", metadata=metadata, pages=[])

        # Start as draft
        project = Project(
            id="project-789",
            name="Progressive Project",
            story=story,
            status=ProjectStatus.DRAFT
        )
        assert project.status == ProjectStatus.DRAFT

        # Progress through statuses (in real app, would create new instance)
        statuses = [
            ProjectStatus.STORY_GENERATED,
            ProjectStatus.PROMPTS_GENERATED,
            ProjectStatus.IMAGES_GENERATED,
            ProjectStatus.COMPLETED
        ]

        for status in statuses:
            # Simulate status update (in real app, would be a new Project instance)
            test_project = Project(
                id=project.id,
                name=project.name,
                story=project.story,
                status=status
            )
            assert test_project.status == status

    def test_project_with_multiple_character_profiles(self):
        """Test Project with multiple character profiles"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata
        from src.models.character import CharacterProfile

        metadata = StoryMetadata(
            title="Multiple Characters",
            language="English",
            complexity="intermediate",
            vocabulary_diversity="medium",
            age_group="8-12 years",
            num_pages=10,
            user_prompt="A story with many characters"
        )

        story = Story(id="story-multi", metadata=metadata, pages=[])

        hero = CharacterProfile(
            name="Hero",
            species="fox",
            physical_description="red fox with white-tipped tail"
        )

        mentor = CharacterProfile(
            name="Mentor",
            species="owl",
            physical_description="wise old owl with gray feathers"
        )

        friend = CharacterProfile(
            name="Friend",
            species="rabbit",
            physical_description="friendly white rabbit"
        )

        project = Project(
            id="project-multi",
            name="Multi-Character Story",
            story=story,
            status=ProjectStatus.DRAFT,
            character_profiles=[hero, mentor, friend]
        )

        assert len(project.character_profiles) == 3
        assert project.character_profiles[0].name == "Hero"
        assert project.character_profiles[1].name == "Mentor"
        assert project.character_profiles[2].name == "Friend"

    def test_project_with_image_prompts_for_all_pages(self):
        """Test Project with image prompts matching all story pages"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata, StoryPage
        from src.models.image_prompt import ImagePrompt

        metadata = StoryMetadata(
            title="Complete Story",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=5,
            user_prompt="Test"
        )

        pages = [StoryPage(page_number=i, text=f"Page {i}") for i in range(1, 6)]
        story = Story(id="story-complete", metadata=metadata, pages=pages)

        prompts = [
            ImagePrompt(
                page_number=i,
                scene_description=f"Scene {i}",
                art_style="watercolor children's book illustration"
            )
            for i in range(1, 6)
        ]

        project = Project(
            id="project-complete",
            name="Complete Project",
            story=story,
            status=ProjectStatus.PROMPTS_GENERATED,
            image_prompts=prompts
        )

        assert len(project.story.pages) == 5
        assert len(project.image_prompts) == 5
        assert project.story.pages[0].page_number == project.image_prompts[0].page_number

    def test_project_empty_character_profiles(self):
        """Test Project can have empty character profiles list"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata

        metadata = StoryMetadata(
            title="No Characters",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=3,
            user_prompt="A landscape story"
        )

        story = Story(id="story-no-chars", metadata=metadata, pages=[])

        project = Project(
            id="project-no-chars",
            name="Landscape Story",
            story=story,
            status=ProjectStatus.DRAFT
        )

        assert project.character_profiles == []
        assert len(project.character_profiles) == 0

    def test_project_empty_image_prompts(self):
        """Test Project can have empty image prompts list"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata

        metadata = StoryMetadata(
            title="New Story",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=5,
            user_prompt="Just starting"
        )

        story = Story(id="story-new", metadata=metadata, pages=[])

        project = Project(
            id="project-new",
            name="New Project",
            story=story,
            status=ProjectStatus.STORY_GENERATED
        )

        assert project.image_prompts == []
        assert len(project.image_prompts) == 0

    def test_project_timestamps_auto_generated(self):
        """Test that timestamps are auto-generated if not provided"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata

        metadata = StoryMetadata(
            title="Timestamp Test",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=3,
            user_prompt="Test"
        )

        story = Story(id="story-time", metadata=metadata, pages=[])

        project = Project(
            id="project-time",
            name="Timestamp Project",
            story=story,
            status=ProjectStatus.DRAFT
        )

        assert project.created_at is not None
        assert project.updated_at is not None
        assert isinstance(project.created_at, datetime)
        assert isinstance(project.updated_at, datetime)

    def test_project_name_different_from_story_title(self):
        """Test that project name can differ from story title"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryMetadata

        metadata = StoryMetadata(
            title="The Great Adventure",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=5,
            user_prompt="Test"
        )

        story = Story(id="story-diff", metadata=metadata, pages=[])

        project = Project(
            id="project-diff",
            name="My Project v2",  # Different from story title
            story=story,
            status=ProjectStatus.DRAFT
        )

        assert project.name == "My Project v2"
        assert project.story.metadata.title == "The Great Adventure"
        assert project.name != project.story.metadata.title
