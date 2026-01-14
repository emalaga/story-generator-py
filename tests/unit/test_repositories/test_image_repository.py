"""
Unit tests for Image Repository.
Write these tests BEFORE implementing the repository (TDD approach).
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import base64


class TestImageRepository:
    """Test ImageRepository for managing image file persistence"""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def image_repo(self, temp_storage_dir):
        """Create an ImageRepository instance for testing"""
        from src.repositories.image_repository import ImageRepository
        return ImageRepository(storage_dir=temp_storage_dir)

    @pytest.fixture
    def sample_image_data(self):
        """Create sample image data (small PNG)"""
        # Minimal 1x1 red PNG
        png_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=='
        )
        return png_data

    def test_image_repository_initialization(self, temp_storage_dir):
        """Test creating ImageRepository with custom storage directory"""
        from src.repositories.image_repository import ImageRepository

        repo = ImageRepository(storage_dir=temp_storage_dir)

        assert repo.storage_dir == temp_storage_dir
        assert repo.storage_dir.exists()

    def test_image_repository_creates_storage_dir_if_not_exists(self, temp_storage_dir):
        """Test that ImageRepository creates storage directory if it doesn't exist"""
        from src.repositories.image_repository import ImageRepository

        non_existent_dir = temp_storage_dir / "new_dir"
        assert not non_existent_dir.exists()

        repo = ImageRepository(storage_dir=non_existent_dir)

        assert repo.storage_dir.exists()

    def test_save_image(self, image_repo, sample_image_data, temp_storage_dir):
        """Test saving an image"""
        project_id = "project-123"
        page_number = 1

        image_path = image_repo.save(project_id, page_number, sample_image_data)

        assert image_path is not None
        assert isinstance(image_path, Path)
        assert image_path.exists()
        assert image_path.suffix == ".png"

    def test_save_image_creates_project_directory(self, image_repo, sample_image_data, temp_storage_dir):
        """Test that saving image creates project-specific directory"""
        project_id = "project-456"
        page_number = 1

        image_path = image_repo.save(project_id, page_number, sample_image_data)

        project_dir = temp_storage_dir / "images" / project_id
        assert project_dir.exists()
        assert image_path.parent == project_dir

    def test_save_image_filename_format(self, image_repo, sample_image_data):
        """Test that saved image has correct filename format"""
        project_id = "project-789"
        page_number = 3

        image_path = image_repo.save(project_id, page_number, sample_image_data)

        assert image_path.name == "page_3.png"

    def test_get_image(self, image_repo, sample_image_data):
        """Test retrieving an image by project ID and page number"""
        project_id = "project-abc"
        page_number = 2

        # Save image first
        image_repo.save(project_id, page_number, sample_image_data)

        # Retrieve image
        retrieved_data = image_repo.get(project_id, page_number)

        assert retrieved_data is not None
        assert retrieved_data == sample_image_data

    def test_get_nonexistent_image_returns_none(self, image_repo):
        """Test that getting a non-existent image returns None"""
        result = image_repo.get("nonexistent-project", 1)
        assert result is None

    def test_get_image_path(self, image_repo, sample_image_data):
        """Test getting the path to an image"""
        project_id = "project-def"
        page_number = 5

        # Save image first
        saved_path = image_repo.save(project_id, page_number, sample_image_data)

        # Get path
        retrieved_path = image_repo.get_path(project_id, page_number)

        assert retrieved_path is not None
        assert retrieved_path == saved_path
        assert retrieved_path.exists()

    def test_get_path_nonexistent_image_returns_none(self, image_repo):
        """Test that getting path for non-existent image returns None"""
        result = image_repo.get_path("nonexistent-project", 1)
        assert result is None

    def test_delete_image(self, image_repo, sample_image_data):
        """Test deleting an image"""
        project_id = "project-ghi"
        page_number = 1

        # Save image first
        image_path = image_repo.save(project_id, page_number, sample_image_data)
        assert image_path.exists()

        # Delete image
        image_repo.delete(project_id, page_number)

        assert not image_path.exists()
        assert image_repo.get(project_id, page_number) is None

    def test_delete_nonexistent_image_raises_error(self, image_repo):
        """Test that deleting non-existent image raises ValueError"""
        with pytest.raises(ValueError, match="Image .* not found"):
            image_repo.delete("nonexistent-project", 1)

    def test_delete_all_project_images(self, image_repo, sample_image_data):
        """Test deleting all images for a project"""
        project_id = "project-jkl"

        # Save multiple images
        image_repo.save(project_id, 1, sample_image_data)
        image_repo.save(project_id, 2, sample_image_data)
        image_repo.save(project_id, 3, sample_image_data)

        # Verify they exist
        assert image_repo.get(project_id, 1) is not None
        assert image_repo.get(project_id, 2) is not None
        assert image_repo.get(project_id, 3) is not None

        # Delete all
        image_repo.delete_all(project_id)

        # Verify all deleted
        assert image_repo.get(project_id, 1) is None
        assert image_repo.get(project_id, 2) is None
        assert image_repo.get(project_id, 3) is None

    def test_delete_all_nonexistent_project_succeeds(self, image_repo):
        """Test that deleting all images for non-existent project succeeds silently"""
        # Should not raise an error
        image_repo.delete_all("nonexistent-project")

    def test_list_project_images(self, image_repo, sample_image_data):
        """Test listing all images for a project"""
        project_id = "project-mno"

        # Save multiple images
        image_repo.save(project_id, 1, sample_image_data)
        image_repo.save(project_id, 3, sample_image_data)
        image_repo.save(project_id, 5, sample_image_data)

        # List images
        images = image_repo.list_images(project_id)

        assert len(images) == 3
        assert 1 in images
        assert 3 in images
        assert 5 in images

    def test_list_images_empty_project(self, image_repo):
        """Test listing images for project with no images"""
        images = image_repo.list_images("nonexistent-project")
        assert images == []

    def test_save_multiple_images_same_project(self, image_repo, sample_image_data):
        """Test saving multiple images for the same project"""
        project_id = "project-pqr"

        path1 = image_repo.save(project_id, 1, sample_image_data)
        path2 = image_repo.save(project_id, 2, sample_image_data)
        path3 = image_repo.save(project_id, 3, sample_image_data)

        # All should exist
        assert path1.exists()
        assert path2.exists()
        assert path3.exists()

        # All should be in same project directory
        assert path1.parent == path2.parent == path3.parent

        # Should have different filenames
        assert path1.name == "page_1.png"
        assert path2.name == "page_2.png"
        assert path3.name == "page_3.png"

    def test_overwrite_existing_image(self, image_repo):
        """Test that saving to existing page number overwrites"""
        project_id = "project-stu"
        page_number = 1

        # Create two different image data sets
        image_data_1 = b"fake image data 1"
        image_data_2 = b"fake image data 2"

        # Save first image
        image_repo.save(project_id, page_number, image_data_1)
        retrieved_1 = image_repo.get(project_id, page_number)
        assert retrieved_1 == image_data_1

        # Overwrite with second image
        image_repo.save(project_id, page_number, image_data_2)
        retrieved_2 = image_repo.get(project_id, page_number)
        assert retrieved_2 == image_data_2

    def test_multiple_projects_independent(self, image_repo, sample_image_data):
        """Test that images from different projects are stored independently"""
        project_id_1 = "project-vwx"
        project_id_2 = "project-yz"

        # Save images with same page number for different projects
        path1 = image_repo.save(project_id_1, 1, sample_image_data)
        path2 = image_repo.save(project_id_2, 1, sample_image_data)

        # Should be in different directories
        assert path1.parent != path2.parent

        # Both should exist
        assert path1.exists()
        assert path2.exists()

        # Should be retrievable independently
        assert image_repo.get(project_id_1, 1) == sample_image_data
        assert image_repo.get(project_id_2, 1) == sample_image_data

    def test_image_persistence_across_instances(self, temp_storage_dir, sample_image_data):
        """Test that images persist across repository instances"""
        from src.repositories.image_repository import ImageRepository

        project_id = "project-persist"
        page_number = 1

        # Create first instance and save image
        repo1 = ImageRepository(storage_dir=temp_storage_dir)
        repo1.save(project_id, page_number, sample_image_data)

        # Create second instance and retrieve image
        repo2 = ImageRepository(storage_dir=temp_storage_dir)
        retrieved = repo2.get(project_id, page_number)

        assert retrieved is not None
        assert retrieved == sample_image_data

    def test_save_large_image(self, image_repo):
        """Test saving a larger image (simulated)"""
        project_id = "project-large"
        page_number = 1

        # Create larger fake image data (1KB)
        large_image_data = b"x" * 1024

        image_path = image_repo.save(project_id, page_number, large_image_data)

        assert image_path.exists()

        retrieved = image_repo.get(project_id, page_number)
        assert len(retrieved) == 1024
        assert retrieved == large_image_data

    def test_image_directory_structure(self, image_repo, sample_image_data, temp_storage_dir):
        """Test that correct directory structure is created"""
        project_id = "project-structure"
        page_number = 1

        image_repo.save(project_id, page_number, sample_image_data)

        # Verify directory structure: storage_dir/images/project_id/page_X.png
        expected_path = temp_storage_dir / "images" / project_id / "page_1.png"
        assert expected_path.exists()

    def test_delete_updates_list(self, image_repo, sample_image_data):
        """Test that deleting an image updates the list"""
        project_id = "project-list"

        # Save three images
        image_repo.save(project_id, 1, sample_image_data)
        image_repo.save(project_id, 2, sample_image_data)
        image_repo.save(project_id, 3, sample_image_data)

        assert len(image_repo.list_images(project_id)) == 3

        # Delete one
        image_repo.delete(project_id, 2)

        # List should update
        images = image_repo.list_images(project_id)
        assert len(images) == 2
        assert 1 in images
        assert 2 not in images
        assert 3 in images

    def test_page_number_zero(self, image_repo, sample_image_data):
        """Test that page number 0 is handled correctly"""
        project_id = "project-zero"
        page_number = 0

        image_path = image_repo.save(project_id, page_number, sample_image_data)

        assert image_path.name == "page_0.png"
        assert image_repo.get(project_id, page_number) == sample_image_data

    def test_large_page_number(self, image_repo, sample_image_data):
        """Test that large page numbers are handled correctly"""
        project_id = "project-large-page"
        page_number = 999

        image_path = image_repo.save(project_id, page_number, sample_image_data)

        assert image_path.name == "page_999.png"
        assert image_repo.get(project_id, page_number) == sample_image_data
