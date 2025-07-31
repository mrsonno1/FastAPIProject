import io
import os
from typing import Optional, Tuple
from PIL import Image
import uuid
import httpx
from services.storage_service import storage_service

class ThumbnailService:
    """Service for generating and managing image thumbnails"""
    
    THUMBNAIL_SIZE = (64, 64)
    THUMBNAIL_PREFIX = "thumbnails/"
    
    def generate_thumbnail(self, image_data: bytes, original_filename: str) -> Tuple[bytes, str]:
        """
        Generate a 64x64 thumbnail from image data
        
        Args:
            image_data: Original image data in bytes
            original_filename: Original filename to extract extension
            
        Returns:
            Tuple of (thumbnail_bytes, thumbnail_format)
        """
        # Open image from bytes
        img = Image.open(io.BytesIO(image_data))
        
        # Convert RGBA to RGB if necessary (for JPEG compatibility)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create a white background
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            # Paste the image on the white background using alpha channel as mask
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        # Create thumbnail maintaining aspect ratio
        img.thumbnail(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        
        # Create a square canvas
        thumb = Image.new('RGB', self.THUMBNAIL_SIZE, (255, 255, 255))
        
        # Calculate position to center the image
        x = (self.THUMBNAIL_SIZE[0] - img.width) // 2
        y = (self.THUMBNAIL_SIZE[1] - img.height) // 2
        
        # Paste the resized image onto the square canvas
        thumb.paste(img, (x, y))
        
        # Save thumbnail to bytes
        output = io.BytesIO()
        # Determine format based on original filename
        ext = os.path.splitext(original_filename)[1].lower()
        format = 'JPEG' if ext in ['.jpg', '.jpeg'] else 'PNG'
        thumb.save(output, format=format, quality=85, optimize=True)
        
        return output.getvalue(), ext[1:] if ext else 'jpg'
    
    def create_and_upload_thumbnail(self, image_data: bytes, original_filename: str) -> Optional[str]:
        """
        Create a thumbnail and upload it to storage
        
        Args:
            image_data: Original image data
            original_filename: Original filename
            
        Returns:
            URL of the uploaded thumbnail or None if failed
        """
        try:
            # Generate thumbnail
            thumbnail_data, extension = self.generate_thumbnail(image_data, original_filename)
            
            # Generate unique filename for thumbnail
            thumbnail_filename = f"thumbnail_{uuid.uuid4()}.{extension}"
            
            # Determine content type
            content_type = 'image/jpeg' if extension in ['jpg', 'jpeg'] else 'image/png'
            
            # Upload thumbnail to storage using existing method
            result = storage_service.upload_base64_file(
                file_data=thumbnail_data,
                filename=thumbnail_filename,
                content_type=content_type
            )
            
            return result['public_url'] if result else None
            
        except Exception as e:
            print(f"Error creating thumbnail: {str(e)}")
            return None
    
    def create_thumbnail_from_url(self, image_url: str) -> Optional[str]:
        """
        Create a thumbnail from an existing image URL
        
        Args:
            image_url: URL of the original image
            
        Returns:
            URL of the uploaded thumbnail or None if failed
        """
        try:
            # Download image from URL
            response = httpx.get(image_url)
            response.raise_for_status()
            image_data = response.content
            
            # Extract filename from URL
            filename = image_url.split('/')[-1]
            
            # Create and upload thumbnail
            return self.create_and_upload_thumbnail(image_data, filename)
            
        except Exception as e:
            print(f"Error creating thumbnail from URL: {str(e)}")
            return None

# Singleton instance
thumbnail_service = ThumbnailService()