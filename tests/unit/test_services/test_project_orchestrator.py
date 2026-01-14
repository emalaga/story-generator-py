"""
Unit tests for Project Orchestrator.
Write these tests BEFORE implementing the orchestrator (TDD approach).

The project orchestrator coordinates the complete workflow from project creation
to story generation and image generation, managing the entire pipeline.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestProjectOrchestrator:
    """Test ProjectOrchestrator for end-to-end workflow coordination"""

    @pytest.fixture
    def mock_story_generator(self):
        """Create mock StoryGeneratorService for testing"""
        mock_service = AsyncMock()
        mock_service.generate_story = AsyncMock()
        return mock_service

    @pytest.fixture
    def mock_image_generator(self):
        """Create mock ImageGeneratorService for testing"""
        mock_service = AsyncMock()
        mock_service.generate_images_for_story = AsyncMock()
        return mock_service

    @pytest.fixture
    def mock_project_repository(self):
        """Create mock ProjectRepository for testing"""
        mock_repo = AsyncMock()
        mock_repo.save_project = AsyncMock()
        mock_repo.get_project = AsyncMock()
        mock_repo.update_project = AsyncMock()
        return mock_repo

    @pytest.fixture
    def orchestrator(
        self,
        mock_story_generator,
        mock_image_generator,
        mock_project_repository
    ):
        """Create ProjectOrchestrator instance for testing"""
        from src.services.project_orchestrator import ProjectOrchestrator
        return ProjectOrchestrator(
            story_generator=mock_story_generator,
            image_generator=mock_image_generator,
            project_repository=mock_project_repository
        )

    @pytest.fixture
    def story_metadata(self):
        """Create sample story metadata for testing"""
        from src.models.story import StoryMetadata
        return StoryMetadata(
            title="Test Story",
            language="English",
            complexity="simple",
            vocabulary_diversity="basic",
            age_group="3-5",
            num_pages=3,
            genre="adventure",
            art_style="cartoon"
        )

    def test_orchestrator_initialization(
        self,
        mock_story_generator,
        mock_image_generator,
        mock_project_repository
    ):
        """Test creating ProjectOrchestrator with dependencies"""
        from src.services.project_orchestrator import ProjectOrchestrator

        orchestrator = ProjectOrchestrator(
            story_generator=mock_story_generator,
            image_generator=mock_image_generator,
            project_repository=mock_project_repository
        )

        assert orchestrator.story_generator == mock_story_generator
        assert orchestrator.image_generator == mock_image_generator
        assert orchestrator.project_repository == mock_project_repository

    @pytest.mark.asyncio
    async def test_create_project_basic(
        self,
        orchestrator,
        story_metadata,
        mock_story_generator,
        mock_image_generator,
        mock_project_repository
    ):
        """Test basic project creation workflow"""
        from src.models.story import Story, StoryPage
        from src.models.character import CharacterProfile

        # Mock story generation
        mock_story = Story(
            id="story-123",
            metadata=story_metadata,
            pages=[
                StoryPage(page_number=1, text="Test page 1"),
                StoryPage(page_number=2, text="Test page 2")
            ],
            characters=[
                CharacterProfile(
                    name="Hero",
                    species="human",
                    physical_description="Test character"
                )
            ]
        )
        mock_story_generator.generate_story.return_value = mock_story

        # Mock image generation (returns story with images added)
        mock_story_with_images = Story(
            id="story-123",
            metadata=story_metadata,
            pages=[
                StoryPage(
                    page_number=1,
                    text="Test page 1",
                    image_url="https://example.com/image1.png"
                ),
                StoryPage(
                    page_number=2,
                    text="Test page 2",
                    image_url="https://example.com/image2.png"
                )
            ],
            characters=mock_story.characters
        )
        mock_image_generator.generate_images_for_story.return_value = mock_story_with_images

        # Create project
        project = await orchestrator.create_project(story_metadata)

        # Verify story generation was called
        assert mock_story_generator.generate_story.called

        # Verify image generation was called
        assert mock_image_generator.generate_images_for_story.called

        # Verify project repository was called to save
        assert mock_project_repository.save_project.called

        # Verify project structure
        from src.models.project import Project
        assert isinstance(project, Project)
        assert project.story.id == "story-123"
        assert len(project.story.pages) == 2
        assert project.story.pages[0].image_url is not None

    @pytest.mark.asyncio
    async def test_create_project_with_theme(
        self,
        orchestrator,
        story_metadata,
        mock_story_generator,
        mock_image_generator,
        mock_project_repository
    ):
        """Test project creation with optional theme"""
        from src.models.story import Story, StoryPage

        mock_story = Story(
            id="story-123",
            metadata=story_metadata,
            pages=[StoryPage(page_number=1, text="Test")],
            characters=[]
        )
        mock_story_generator.generate_story.return_value = mock_story
        mock_image_generator.generate_images_for_story.return_value = mock_story

        await orchestrator.create_project(
            story_metadata,
            theme="courage and friendship"
        )

        # Verify theme was passed to story generator
        call_kwargs = mock_story_generator.generate_story.call_args[1]
        assert 'theme' in call_kwargs
        assert call_kwargs['theme'] == "courage and friendship"

    @pytest.mark.asyncio
    async def test_create_project_with_custom_prompt(
        self,
        orchestrator,
        story_metadata,
        mock_story_generator,
        mock_image_generator,
        mock_project_repository
    ):
        """Test project creation with custom story idea"""
        from src.models.story import Story, StoryPage

        mock_story = Story(
            id="story-123",
            metadata=story_metadata,
            pages=[StoryPage(page_number=1, text="Test")],
            characters=[]
        )
        mock_story_generator.generate_story.return_value = mock_story
        mock_image_generator.generate_images_for_story.return_value = mock_story

        custom_prompt = "A story about a dragon who learns to read"
        await orchestrator.create_project(
            story_metadata,
            custom_prompt=custom_prompt
        )

        # Verify custom prompt was passed to story generator
        call_kwargs = mock_story_generator.generate_story.call_args[1]
        assert 'custom_prompt' in call_kwargs
        assert call_kwargs['custom_prompt'] == custom_prompt

    @pytest.mark.asyncio
    async def test_create_project_saves_to_repository(
        self,
        orchestrator,
        story_metadata,
        mock_story_generator,
        mock_image_generator,
        mock_project_repository
    ):
        """Test that created project is saved to repository"""
        from src.models.story import Story, StoryPage

        mock_story = Story(
            id="story-123",
            metadata=story_metadata,
            pages=[StoryPage(page_number=1, text="Test")],
            characters=[]
        )
        mock_story_generator.generate_story.return_value = mock_story
        mock_image_generator.generate_images_for_story.return_value = mock_story

        project = await orchestrator.create_project(story_metadata)

        # Verify save was called with the project
        mock_project_repository.save_project.assert_called_once()
        saved_project = mock_project_repository.save_project.call_args[0][0]
        assert saved_project.story.id == "story-123"

    @pytest.mark.asyncio
    async def test_create_project_generates_project_id(
        self,
        orchestrator,
        story_metadata,
        mock_story_generator,
        mock_image_generator,
        mock_project_repository
    ):
        """Test that project gets a unique ID"""
        from src.models.story import Story, StoryPage

        mock_story = Story(
            id="story-123",
            metadata=story_metadata,
            pages=[StoryPage(page_number=1, text="Test")],
            characters=[]
        )
        mock_story_generator.generate_story.return_value = mock_story
        mock_image_generator.generate_images_for_story.return_value = mock_story

        project = await orchestrator.create_project(story_metadata)

        # Verify project has an ID
        assert project.id is not None
        assert len(project.id) > 0

    @pytest.mark.asyncio
    async def test_create_project_workflow_order(
        self,
        orchestrator,
        story_metadata,
        mock_story_generator,
        mock_image_generator,
        mock_project_repository
    ):
        """Test that workflow steps execute in correct order"""
        from src.models.story import Story, StoryPage

        call_order = []

        async def track_story_gen(*args, **kwargs):
            call_order.append('story')
            return Story(
                id="story-123",
                metadata=story_metadata,
                pages=[StoryPage(page_number=1, text="Test")],
                characters=[]
            )

        async def track_image_gen(story):
            call_order.append('images')
            return story

        async def track_save(project):
            call_order.append('save')

        mock_story_generator.generate_story.side_effect = track_story_gen
        mock_image_generator.generate_images_for_story.side_effect = track_image_gen
        mock_project_repository.save_project.side_effect = track_save

        await orchestrator.create_project(story_metadata)

        # Verify order: story -> images -> save
        assert call_order == ['story', 'images', 'save']

    @pytest.mark.asyncio
    async def test_create_project_handles_story_generation_error(
        self,
        orchestrator,
        story_metadata,
        mock_story_generator,
        mock_image_generator,
        mock_project_repository
    ):
        """Test handling of story generation errors"""
        mock_story_generator.generate_story.side_effect = Exception("AI service error")

        with pytest.raises(Exception) as exc_info:
            await orchestrator.create_project(story_metadata)

        assert "AI service error" in str(exc_info.value)

        # Verify image generation and save were not called
        assert not mock_image_generator.generate_images_for_story.called
        assert not mock_project_repository.save_project.called

    @pytest.mark.asyncio
    async def test_create_project_handles_image_generation_error(
        self,
        orchestrator,
        story_metadata,
        mock_story_generator,
        mock_image_generator,
        mock_project_repository
    ):
        """Test handling of image generation errors"""
        from src.models.story import Story, StoryPage

        mock_story = Story(
            id="story-123",
            metadata=story_metadata,
            pages=[StoryPage(page_number=1, text="Test")],
            characters=[]
        )
        mock_story_generator.generate_story.return_value = mock_story
        mock_image_generator.generate_images_for_story.side_effect = Exception("Image API error")

        with pytest.raises(Exception) as exc_info:
            await orchestrator.create_project(story_metadata)

        assert "Image API error" in str(exc_info.value)

        # Verify save was not called
        assert not mock_project_repository.save_project.called

    @pytest.mark.asyncio
    async def test_regenerate_story(
        self,
        orchestrator,
        story_metadata,
        mock_story_generator,
        mock_image_generator,
        mock_project_repository
    ):
        """Test regenerating story for existing project"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryPage

        # Mock existing project
        existing_project = Project(
            id="project-123",
            name="Old Project",
            story=Story(
                id="old-story-123",
                metadata=story_metadata,
                pages=[StoryPage(page_number=1, text="Old story")],
                characters=[]
            ),
            status=ProjectStatus.COMPLETED
        )
        mock_project_repository.get_project.return_value = existing_project

        # Mock new story generation
        new_story = Story(
            id="new-story-456",
            metadata=story_metadata,
            pages=[StoryPage(page_number=1, text="New story")],
            characters=[]
        )
        mock_story_generator.generate_story.return_value = new_story
        mock_image_generator.generate_images_for_story.return_value = new_story

        updated_project = await orchestrator.regenerate_story("project-123", story_metadata)

        # Verify project was retrieved
        mock_project_repository.get_project.assert_called_once_with("project-123")

        # Verify new story was generated
        assert mock_story_generator.generate_story.called

        # Verify project was updated
        assert updated_project.story.id == "new-story-456"
        assert mock_project_repository.update_project.called

    @pytest.mark.asyncio
    async def test_regenerate_images(
        self,
        orchestrator,
        mock_story_generator,
        mock_image_generator,
        mock_project_repository
    ):
        """Test regenerating images for existing story"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryPage, StoryMetadata

        # Mock existing project with story but no images
        existing_story = Story(
            id="story-123",
            metadata=StoryMetadata(
                title="Test",
                language="English",
                complexity="simple",
                vocabulary_diversity="basic",
                age_group="3-5",
                num_pages=2,
                art_style="cartoon"
            ),
            pages=[
                StoryPage(page_number=1, text="Page 1"),
                StoryPage(page_number=2, text="Page 2")
            ],
            characters=[]
        )

        existing_project = Project(
            id="project-123",
            name="Test Project",
            story=existing_story,
            status=ProjectStatus.STORY_GENERATED
        )
        mock_project_repository.get_project.return_value = existing_project

        # Mock image generation
        story_with_images = Story(
            id="story-123",
            metadata=existing_story.metadata,
            pages=[
                StoryPage(
                    page_number=1,
                    text="Page 1",
                    image_url="https://example.com/image1.png"
                ),
                StoryPage(
                    page_number=2,
                    text="Page 2",
                    image_url="https://example.com/image2.png"
                )
            ],
            characters=[]
        )
        mock_image_generator.generate_images_for_story.return_value = story_with_images

        updated_project = await orchestrator.regenerate_images("project-123")

        # Verify images were generated
        assert mock_image_generator.generate_images_for_story.called

        # Verify project was updated
        assert updated_project.story.pages[0].image_url is not None
        assert mock_project_repository.update_project.called

    @pytest.mark.asyncio
    async def test_get_project(
        self,
        orchestrator,
        mock_project_repository
    ):
        """Test retrieving existing project"""
        from src.models.project import Project, ProjectStatus
        from src.models.story import Story, StoryPage, StoryMetadata

        mock_project = Project(
            id="project-123",
            name="Test Project",
            story=Story(
                id="story-123",
                metadata=StoryMetadata(
                    title="Test",
                    language="English",
                    complexity="simple",
                    vocabulary_diversity="basic",
                    age_group="3-5",
                    num_pages=1
                ),
                pages=[StoryPage(page_number=1, text="Test")],
                characters=[]
            ),
            status=ProjectStatus.COMPLETED
        )
        mock_project_repository.get_project.return_value = mock_project

        project = await orchestrator.get_project("project-123")

        mock_project_repository.get_project.assert_called_once_with("project-123")
        assert project.id == "project-123"

    @pytest.mark.asyncio
    async def test_create_project_preserves_metadata(
        self,
        orchestrator,
        story_metadata,
        mock_story_generator,
        mock_image_generator,
        mock_project_repository
    ):
        """Test that story metadata is preserved through the workflow"""
        from src.models.story import Story, StoryPage

        mock_story = Story(
            id="story-123",
            metadata=story_metadata,
            pages=[StoryPage(page_number=1, text="Test")],
            characters=[]
        )
        mock_story_generator.generate_story.return_value = mock_story
        mock_image_generator.generate_images_for_story.return_value = mock_story

        project = await orchestrator.create_project(story_metadata)

        # Verify metadata is preserved
        assert project.story.metadata.title == "Test Story"
        assert project.story.metadata.language == "English"
        assert project.story.metadata.age_group == "3-5"
        assert project.story.metadata.art_style == "cartoon"
