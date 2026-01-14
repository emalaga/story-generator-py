"""
Image repository for persisting image files.

This repository handles saving, loading, and deleting image files
for story projects. Images are organized by project ID.
"""

from pathlib import Path
from typing import Optional, List
import shutil


class ImageRepository:
    """
    Repository for managing image file persistence.

    Stores images as PNG files in a directory structure organized by project.
    Each project has its own subdirectory containing page images.

    Directory structure:
    storage_dir/
      images/
        project-123/
          page_1.png
          page_2.png
          ...
        project-456/
          page_1.png
          ...
    """

    def __init__(self, storage_dir: Path):
        """
        Initialize the repository with a storage directory.

        Args:
            storage_dir: Base directory where images will be stored
        """
        self.storage_dir = Path(storage_dir)
        self.images_dir = self.storage_dir / "images"

        # Create base images directory if it doesn't exist
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def save(self, project_id: str, page_number: int, image_data: bytes) -> Path:
        """
        Save an image for a specific project and page.

        Args:
            project_id: ID of the project this image belongs to
            page_number: Page number for this image
            image_data: Raw image data (PNG format)

        Returns:
            Path to the saved image file
        """
        # Create project-specific directory
        project_dir = self.images_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        # Create image file path
        image_path = project_dir / f"page_{page_number}.png"

        # Write image data
        with open(image_path, 'wb') as f:
            f.write(image_data)

        return image_path

    def get(self, project_id: str, page_number: int) -> Optional[bytes]:
        """
        Retrieve image data for a specific project and page.

        Args:
            project_id: ID of the project
            page_number: Page number

        Returns:
            Image data if found, None otherwise
        """
        image_path = self.images_dir / project_id / f"page_{page_number}.png"

        if not image_path.exists():
            return None

        with open(image_path, 'rb') as f:
            return f.read()

    def get_path(self, project_id: str, page_number: int) -> Optional[Path]:
        """
        Get the file path for a specific image.

        Args:
            project_id: ID of the project
            page_number: Page number

        Returns:
            Path to the image file if it exists, None otherwise
        """
        image_path = self.images_dir / project_id / f"page_{page_number}.png"

        if not image_path.exists():
            return None

        return image_path

    def delete(self, project_id: str, page_number: int) -> None:
        """
        Delete a specific image.

        Args:
            project_id: ID of the project
            page_number: Page number

        Raises:
            ValueError: If the image doesn't exist
        """
        image_path = self.images_dir / project_id / f"page_{page_number}.png"

        if not image_path.exists():
            raise ValueError(
                f"Image for project {project_id} page {page_number} not found"
            )

        image_path.unlink()

    def delete_all(self, project_id: str) -> None:
        """
        Delete all images for a specific project.

        Args:
            project_id: ID of the project

        Note:
            Does not raise an error if the project directory doesn't exist
        """
        project_dir = self.images_dir / project_id

        if project_dir.exists():
            shutil.rmtree(project_dir)

    def list_images(self, project_id: str) -> List[int]:
        """
        List all page numbers that have images for a project.

        Args:
            project_id: ID of the project

        Returns:
            Sorted list of page numbers
        """
        project_dir = self.images_dir / project_id

        if not project_dir.exists():
            return []

        page_numbers = []

        for image_file in project_dir.glob("page_*.png"):
            # Extract page number from filename (page_X.png)
            page_num_str = image_file.stem.split('_')[1]
            page_numbers.append(int(page_num_str))

        return sorted(page_numbers)
