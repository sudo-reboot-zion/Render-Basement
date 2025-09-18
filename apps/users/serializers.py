from rest_framework import serializers
from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True, format="hex")
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'email', 'username',
            'role', 'bio', 'profile_image', 'spotify_link', 'soundcloud_link',
            'instagram_link', 'is_verified', 'created_at', 'updated'
        ]
        read_only_fields = ['is_verified', 'created_at', 'updated']