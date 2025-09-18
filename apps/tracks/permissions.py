from rest_framework import permissions


class IsArtistOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow artists to create/edit tracks.
    """

    def has_permission(self, request, view):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed if the user is an artist.
        return request.user and request.user.is_authenticated and request.user.is_artist


