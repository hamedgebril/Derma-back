"""
File management service
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional
from uuid import uuid4

import aiofiles
from PIL import Image

from app.core.config import settings
from app.core.exceptions import FileProcessingError, ValidationError

logger = logging.getLogger(__name__)


class FileService:
    """Handle file operations for uploads"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = settings.MAX_UPLOAD_SIZE
        self.allowed_extensions = set(settings.ALLOWED_EXTENSIONS)
    
    async def save_upload(
        self,
        file_content: bytes,
        filename: str,
        session_id: Optional[str] = None
    ) -> Path:
        """
        Save uploaded file with validation
        
        Args:
            file_content: File bytes
            filename: Original filename
            session_id: Optional session ID for naming
            
        Returns:
            Path to saved file
        """
        # Validate file
        self._validate_file(file_content, filename)
        
        # Generate unique filename
        file_ext = Path(filename).suffix.lower()
        unique_name = f"{session_id or uuid4()}{file_ext}"
        file_path = self.upload_dir / unique_name
        
        try:
            # Save file asynchronously
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Validate it's a real image
            await self._validate_image_content(file_path)
            
            logger.info(f"File saved: {file_path}")
            return file_path
            
        except Exception as e:
            # Cleanup on error
            if file_path.exists():
                file_path.unlink()
            logger.error(f"Error saving file: {e}")
            raise FileProcessingError(f"Failed to save file: {str(e)}")
    
    def _validate_file(self, file_content: bytes, filename: str) -> None:
        """Validate file before saving"""
        # Check size
        if len(file_content) > self.max_size:
            raise ValidationError(
                f"File too large. Maximum size: {self.max_size / 1024 / 1024:.1f}MB",
                details={"size": len(file_content), "max_size": self.max_size}
            )
        
        # Check extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            raise ValidationError(
                f"Invalid file type. Allowed: {', '.join(self.allowed_extensions)}",
                details={"extension": file_ext}
            )
    
    async def _validate_image_content(self, file_path: Path) -> None:
        """Validate that file is actually an image"""
        try:
            # Run in thread pool to avoid blocking
            await asyncio.to_thread(self._check_image, file_path)
        except Exception as e:
            raise ValidationError(
                f"Invalid image file: {str(e)}",
                details={"path": str(file_path)}
            )
    
    @staticmethod
    def _check_image(file_path: Path) -> None:
        """Check if file is valid image (runs in thread pool)"""
        with Image.open(file_path) as img:
            img.verify()
    
    async def delete_file(self, file_path: Path) -> bool:
        """
        Delete a file
        
        Args:
            file_path: Path to file
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            if file_path.exists():
                await asyncio.to_thread(file_path.unlink)
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    async def cleanup_old_files(self, days: int = 30) -> int:
        """
        Cleanup files older than specified days
        
        Args:
            days: Age threshold in days
            
        Returns:
            Number of files deleted
        """
        from datetime import datetime, timedelta
        
        threshold = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for file_path in self.upload_dir.iterdir():
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < threshold:
                    if await self.delete_file(file_path):
                        deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old files")
        return deleted_count
