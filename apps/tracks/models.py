import uuid
import os
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
from django.core.files.base import ContentFile
from pydub import AudioSegment
from pydub.utils import make_chunks
import tempfile


User = get_user_model()


def track_upload_path(instance, filename):
    """Generate upload path for track files"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f'tracks/{instance.artist.username}/{filename}'


def preview_upload_path(instance, filename):
    """Generate upload path for preview files"""
    ext = filename.split('.')[-1]
    filename = f"preview_{uuid.uuid4()}.{ext}"
    return f'previews/{instance.artist.username}/{filename}'


def cover_upload_path(instance, filename):
    """Generate upload path for cover images"""
    ext = filename.split('.')[-1]
    filename = f"cover_{uuid.uuid4()}.{ext}"
    return f'covers/{instance.artist.username}/{filename}'


class Genre(models.Model):
    """Music genres for categorization"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Mood(models.Model):
    """Mood tags for tracks"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class LicenseType(models.Model):
    """Different types of licenses available"""
    STANDARD = 'standard'
    EXTENDED = 'extended'
    COMMERCIAL = 'commercial'
    EXCLUSIVE = 'exclusive'

    LICENSE_CHOICES = [
        (STANDARD, 'Standard License'),
        (EXTENDED, 'Extended License'),
        (COMMERCIAL, 'Commercial License'),
        (EXCLUSIVE, 'Exclusive License'),
    ]

    name = models.CharField(max_length=20, choices=LICENSE_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField()
    price_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.00,
        help_text="Multiplier for base track price"
    )

    # License permissions
    allows_commercial_use = models.BooleanField(default=False)
    allows_modification = models.BooleanField(default=False)
    requires_attribution = models.BooleanField(default=True)
    max_copies = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum copies allowed (null = unlimited)"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['price_multiplier']

    def __str__(self):
        return self.display_name


class Track(models.Model):
    """Main track model for uploaded audio files"""

    # Status choices
    DRAFT = 'draft'
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PENDING, 'Pending Review'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]

    # Basic Information
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=200)
    artist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tracks')
    description = models.TextField(max_length=1000, blank=True)

    # Audio Files
    audio_file = models.FileField(
        upload_to=track_upload_path,
        help_text="Main audio file (MP3, WAV, FLAC)"
    )
    preview_file = models.FileField(
        upload_to=preview_upload_path,
        blank=True,
        null=True,
        help_text="30-second preview (auto-generated if not provided)"
    )
    cover_image = models.ImageField(
        upload_to=cover_upload_path,
        blank=True,
        null=True,
        help_text="Track cover art"
    )

    # Metadata
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True)
    mood = models.ForeignKey(Mood, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated tags (e.g., guitar, upbeat, summer)"
    )

    # Audio Properties (auto-filled from file)
    duration = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in seconds")
    file_size = models.PositiveIntegerField(null=True, blank=True, help_text="File size in bytes")
    bitrate = models.PositiveIntegerField(null=True, blank=True, help_text="Bitrate in kbps")
    sample_rate = models.PositiveIntegerField(null=True, blank=True, help_text="Sample rate in Hz")

    # Musical Properties
    bpm = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(60), MaxValueValidator(200)],
        help_text="Beats per minute"
    )
    key = models.CharField(max_length=10, blank=True, help_text="Musical key (e.g., Am, C, F#)")

    # Pricing
    base_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(1.00)],
        help_text="Base price for standard license"
    )

    # System Fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    rejection_reason = models.TextField(blank=True)

    # Analytics
    play_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    purchase_count = models.PositiveIntegerField(default=0)

    # SEO & Discovery
    is_featured = models.BooleanField(default=False)
    is_exclusive = models.BooleanField(default=False)

    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['genre']),
            models.Index(fields=['artist']),
            models.Index(fields=['is_featured']),
        ]

    def __str__(self):
        return f"{self.title} by {self.artist.username}"

    def save(self, *args, **kwargs):
        """Ovrride save to extract metadata and generate preview"""
        is_new = not self.pk

        """Override save to extract audio metadata"""
        if not self.pk or 'audio_file' in kwargs.get('update_fields', []):
            self._extract_audio_metadata()
        super().save(*args, **kwargs)

        if is_new or not self.preview_file:
            self._generate_preview()
            super().save(update_fields=['preview_file'])

    def _generate_preview(self):
        if not self.audio_file:
            return

        try:
            # Load the audio file
            audio = AudioSegment.from_file(self.audio_file.path)

            # Calculate preview start time (middle of track or beginning)
            duration_ms = len(audio)
            preview_duration_ms = 30 * 1000  # 30 seconds in milliseconds

            if duration_ms > preview_duration_ms:
                # Start preview from 1/4 into the track (usually where the good part is)
                start_time = duration_ms // 4
                preview = audio[start_time:start_time + preview_duration_ms]
            else:
                # If track is shorter than 30s, use the whole track
                preview = audio

            # Export preview to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                preview.export(temp_file.name, format="mp3", bitrate="128k")

                # Read the temporary file and save to preview_file field
                with open(temp_file.name, 'rb') as f:
                    preview_content = f.read()

                preview_filename = f"preview_{self.public_id}.mp3"
                self.preview_file.save(
                    preview_filename,
                    ContentFile(preview_content),
                    save=False  # Don't save the model again
                )

                # Clean up temporary file
                os.unlink(temp_file.name)

        except Exception as e:
            print(f"Error generating preview for {self.title}: {e}")

    def _extract_audio_metadata(self):
        """Extract metadata from uploaded audio file"""
        if not self.audio_file:
            return

        try:
            # Try with pydub first (more reliable)
            audio = AudioSegment.from_file(self.audio_file.path)
            self.duration = int(len(audio) / 1000)  # Convert ms to seconds
            self.file_size = self.audio_file.size

            # Try to get more detailed info with mutagen
            audio_file = MutagenFile(self.audio_file.path)
            if audio_file is not None:
                if isinstance(audio_file, (MP3, MP4)):
                    if hasattr(audio_file.info, 'bitrate'):
                        self.bitrate = audio_file.info.bitrate
                    if hasattr(audio_file.info, 'sample_rate'):
                        self.sample_rate = audio_file.info.sample_rate

        except Exception as e:
            print(f"Error extracting metadata for {self.title}: {e}")

    @property
    def duration_formatted(self):
        """Return duration in MM:SS format"""
        if not self.duration:
            return "Unknown"
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}:{seconds:02d}"

    @property
    def tag_list(self):
        """Return tags as a list"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    @property
    def is_available(self):
        """Check if track is available for purchase"""
        return self.status == self.APPROVED

    def get_license_price(self, license_type):
        """Calculate price for specific license type"""
        try:
            license_obj = LicenseType.objects.get(name=license_type, is_active=True)
            return self.base_price * license_obj.price_multiplier
        except LicenseType.DoesNotExist:
            return self.base_price

    def increment_play_count(self):
        self.play_count += 1
        self.save(update_fields=['play_count'])

    def increment_purchase_count(self):
        self.purchase_count += 1
        self.save(update_fields=['purchase_count'])


class Purchase(models.Model):
    """Track purchase records with Stripe integration"""

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='purchases')
    license_type = models.ForeignKey(LicenseType, on_delete=models.PROTECT)

    # Stripe Payment Information
    stripe_payment_intent_id = models.CharField(max_length=200, unique=True)
    stripe_customer_id = models.CharField(max_length=200, blank=True)
    price_paid = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')

    # Payment Status
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    ]
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )

    # License Information
    license_file = models.FileField(
        upload_to='licenses/',
        blank=True,
        null=True,
        help_text="Generated license certificate PDF"
    )

    # Download tracking
    download_count = models.PositiveIntegerField(default=0)
    max_downloads = models.PositiveIntegerField(default=3)  # Allow 3 downloads

    # Timestamps
    purchased_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-purchased_at']
        unique_together = ['buyer', 'track', 'license_type']

    def __str__(self):
        return f"{self.buyer.username} - {self.track.title} ({self.license_type.display_name})"

    @property
    def can_download(self):
        """Check if user can still download"""
        return self.payment_status == 'succeeded' and self.download_count < self.max_downloads

    def increment_download_count(self):
        """Increment download count"""
        if self.can_download:
            self.download_count += 1
            self.save(update_fields=['download_count'])
            return True
        return False
