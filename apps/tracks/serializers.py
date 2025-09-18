from rest_framework import serializers
from .models import Track, Genre, Mood, LicenseType, Purchase


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'slug', 'description']


class MoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mood
        fields = ['id', 'name', 'slug', 'description']


class LicenseTypeSerializer(serializers.ModelSerializer):
    permissions_summary = serializers.ReadOnlyField()
    
    class Meta:
        model = LicenseType
        fields = [
            'id', 'name', 'display_name', 'description', 
            'price_multiplier', 'allows_commercial_use',
            'allows_modification', 'requires_attribution',
            'max_copies', 'permissions_summary'
        ]


class TrackListSerializer(serializers.ModelSerializer):
    """Serializer for track list view (minimal data)"""
    artist_name = serializers.CharField(source='artist.username', read_only=True)
    artist_full_name = serializers.CharField(source='artist.full_name', read_only=True)
    genre_name = serializers.CharField(source='genre.name', read_only=True)
    mood_name = serializers.CharField(source='mood.name', read_only=True)
    duration_formatted = serializers.ReadOnlyField()
    tag_list = serializers.ReadOnlyField()
    
    class Meta:
        model = Track
        fields = [
            'public_id', 'title', 'artist_name', 'artist_full_name',
            'genre_name', 'mood_name', 'base_price', 'duration_formatted',
            'cover_image', 'preview_file', 'tag_list', 'play_count',
            'is_featured', 'uploaded_at'
        ]


class TrackDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed track view"""
    artist_name = serializers.CharField(source='artist.username', read_only=True)
    artist_full_name = serializers.CharField(source='artist.full_name', read_only=True)
    artist_bio = serializers.CharField(source='artist.bio', read_only=True)
    genre = GenreSerializer(read_only=True)
    mood = MoodSerializer(read_only=True)
    duration_formatted = serializers.ReadOnlyField()
    tag_list = serializers.ReadOnlyField()
    license_prices = serializers.SerializerMethodField()
    
    class Meta:
        model = Track
        fields = [
            'public_id', 'title', 'artist_name', 'artist_full_name', 'artist_bio',
            'description', 'genre', 'mood', 'tags', 'tag_list',
            'duration', 'duration_formatted', 'bitrate', 'sample_rate', 
            'bpm', 'key', 'base_price', 'license_prices',
            'cover_image', 'preview_file', 'play_count', 'purchase_count',
            'is_featured', 'is_exclusive', 'uploaded_at'
        ]
    
    def get_license_prices(self, obj):
        """Get prices for all available license types"""
        license_types = LicenseType.objects.filter(is_active=True)
        return {
            license.name: float(obj.get_license_price(license.name))
            for license in license_types
        }


class TrackUploadSerializer(serializers.ModelSerializer):
    """Serializer for track upload (artists only)"""
    
    class Meta:
        model = Track
        fields = [
            'title', 'description', 'audio_file', 'cover_image',
            'genre', 'mood', 'tags', 'bpm', 'key', 'base_price'
        ]
    
    def create(self, validated_data):
        # Set the artist to the current user
        validated_data['artist'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_audio_file(self, value):
        """Validate audio file format and size"""
        if not value.name.lower().endswith(('.mp3', '.wav', '.flac', '.m4a')):
            raise serializers.ValidationError(
                "Only MP3, WAV, FLAC, and M4A files are allowed."
            )
        
        # Check file size (50MB limit)
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError(
                "Audio file size cannot exceed 50MB."
            )
        
        return value


class PurchaseSerializer(serializers.ModelSerializer):
    """Serializer for purchase records"""
    track_title = serializers.CharField(source='track.title', read_only=True)
    track_artist = serializers.CharField(source='track.artist.username', read_only=True)
    license_name = serializers.CharField(source='license_type.display_name', read_only=True)
    can_download = serializers.ReadOnlyField()
    
    class Meta:
        model = Purchase
        fields = [
            'public_id', 'track_title', 'track_artist', 'license_name',
            'price_paid', 'currency', 'payment_status', 'can_download',
            'download_count', 'max_downloads', 'purchased_at'
        ]

