from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from enum import Enum
from decimal import Decimal


class ImageFormat(str, Enum):
    """Supported image formats for conversion"""

    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"
    WEBP = "webp"
    BMP = "bmp"
    TIFF = "tiff"
    GIF = "gif"


class ConversionStatus(str, Enum):
    """Status of image conversion job"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Persistent models (stored in database)
class User(SQLModel, table=True):
    """User model for tracking image conversion users"""

    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, max_length=255)
    name: str = Field(max_length=100)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    uploaded_images: List["UploadedImage"] = Relationship(back_populates="user")
    conversion_jobs: List["ConversionJob"] = Relationship(back_populates="user")


class UploadedImage(SQLModel, table=True):
    """Model for storing uploaded image metadata"""

    __tablename__ = "uploaded_images"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    original_filename: str = Field(max_length=255)
    stored_filename: str = Field(max_length=255)
    file_path: str = Field(max_length=500)
    file_size: int = Field(ge=0)  # File size in bytes
    mime_type: str = Field(max_length=100)
    original_format: ImageFormat
    width: Optional[int] = Field(default=None, ge=0)
    height: Optional[int] = Field(default=None, ge=0)
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = Field(default=False)

    # Relationships
    user: Optional[User] = Relationship(back_populates="uploaded_images")
    conversion_jobs: List["ConversionJob"] = Relationship(back_populates="source_image")


class ConversionJob(SQLModel, table=True):
    """Model for tracking image conversion jobs"""

    __tablename__ = "conversion_jobs"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    source_image_id: int = Field(foreign_key="uploaded_images.id")
    target_format: ImageFormat
    status: ConversionStatus = Field(default=ConversionStatus.PENDING)
    quality: Optional[int] = Field(default=None, ge=1, le=100)  # Quality setting (1-100)
    width: Optional[int] = Field(default=None, ge=1)  # Target width for resizing
    height: Optional[int] = Field(default=None, ge=1)  # Target height for resizing
    maintain_aspect_ratio: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None, max_length=1000)
    processing_time_seconds: Optional[Decimal] = Field(default=None)

    # Relationships
    user: Optional[User] = Relationship(back_populates="conversion_jobs")
    source_image: UploadedImage = Relationship(back_populates="conversion_jobs")
    converted_image: Optional["ConvertedImage"] = Relationship(back_populates="conversion_job")


class ConvertedImage(SQLModel, table=True):
    """Model for storing converted image metadata"""

    __tablename__ = "converted_images"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    conversion_job_id: int = Field(foreign_key="conversion_jobs.id", unique=True)
    filename: str = Field(max_length=255)
    file_path: str = Field(max_length=500)
    file_size: int = Field(ge=0)  # File size in bytes
    mime_type: str = Field(max_length=100)
    format: ImageFormat
    width: int = Field(ge=0)
    height: int = Field(ge=0)
    quality_used: Optional[int] = Field(default=None, ge=1, le=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    download_count: int = Field(default=0, ge=0)
    last_downloaded_at: Optional[datetime] = Field(default=None)
    expires_at: Optional[datetime] = Field(default=None)  # Optional expiration date
    is_deleted: bool = Field(default=False)

    # Relationships
    conversion_job: ConversionJob = Relationship(back_populates="converted_image")


# Non-persistent schemas (for validation, forms, API requests/responses)
class UserCreate(SQLModel, table=False):
    """Schema for creating a new user"""

    email: str = Field(max_length=255)
    name: str = Field(max_length=100)


class UserUpdate(SQLModel, table=False):
    """Schema for updating user information"""

    email: Optional[str] = Field(default=None, max_length=255)
    name: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = Field(default=None)


class ImageUploadRequest(SQLModel, table=False):
    """Schema for image upload request"""

    user_id: Optional[int] = Field(default=None)
    original_filename: str = Field(max_length=255)
    file_size: int = Field(ge=0)
    mime_type: str = Field(max_length=100)


class ConversionRequest(SQLModel, table=False):
    """Schema for requesting image conversion"""

    source_image_id: int
    target_format: ImageFormat
    user_id: Optional[int] = Field(default=None)
    quality: Optional[int] = Field(default=None, ge=1, le=100)
    width: Optional[int] = Field(default=None, ge=1)
    height: Optional[int] = Field(default=None, ge=1)
    maintain_aspect_ratio: bool = Field(default=True)


class ConversionJobUpdate(SQLModel, table=False):
    """Schema for updating conversion job status"""

    status: Optional[ConversionStatus] = Field(default=None)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None, max_length=1000)
    processing_time_seconds: Optional[Decimal] = Field(default=None)


class ConvertedImageCreate(SQLModel, table=False):
    """Schema for creating converted image record"""

    conversion_job_id: int
    filename: str = Field(max_length=255)
    file_path: str = Field(max_length=500)
    file_size: int = Field(ge=0)
    mime_type: str = Field(max_length=100)
    format: ImageFormat
    width: int = Field(ge=0)
    height: int = Field(ge=0)
    quality_used: Optional[int] = Field(default=None, ge=1, le=100)
    expires_at: Optional[datetime] = Field(default=None)


class ImageMetadata(SQLModel, table=False):
    """Schema for image metadata response"""

    id: int
    filename: str
    file_size: int
    format: ImageFormat
    width: Optional[int]
    height: Optional[int]
    upload_date: datetime
    mime_type: str

    def dict(self, **kwargs):
        """Override dict to handle datetime serialization"""
        data = super().dict(**kwargs)
        if "upload_date" in data and data["upload_date"]:
            data["upload_date"] = data["upload_date"].isoformat()
        return data


class ConversionJobResponse(SQLModel, table=False):
    """Schema for conversion job response"""

    id: int
    source_image_id: int
    target_format: ImageFormat
    status: ConversionStatus
    quality: Optional[int]
    width: Optional[int]
    height: Optional[int]
    maintain_aspect_ratio: bool
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    processing_time_seconds: Optional[Decimal]

    def dict(self, **kwargs):
        """Override dict to handle datetime serialization"""
        data = super().dict(**kwargs)
        for field in ["created_at", "started_at", "completed_at"]:
            if field in data and data[field]:
                data[field] = data[field].isoformat()
        return data


class ConvertedImageResponse(SQLModel, table=False):
    """Schema for converted image response"""

    id: int
    filename: str
    file_size: int
    format: ImageFormat
    width: int
    height: int
    quality_used: Optional[int]
    created_at: datetime
    download_count: int
    last_downloaded_at: Optional[datetime]
    expires_at: Optional[datetime]

    def dict(self, **kwargs):
        """Override dict to handle datetime serialization"""
        data = super().dict(**kwargs)
        for field in ["created_at", "last_downloaded_at", "expires_at"]:
            if field in data and data[field]:
                data[field] = data[field].isoformat()
        return data
