import uuid
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager,
    PermissionsMixin
)
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.http import Http404

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.http import Http404


class UserManager(BaseUserManager):
    def get_public_id(self, public_id):
        try:
            instance = self.get(public_id=public_id)
            return instance
        except (ObjectDoesNotExist, ValueError, TypeError):
            raise Http404

    def create_user(self, username, email, password=None, **kwargs):
        if username is None:
            raise TypeError('User must add username')
        if email is None:
            raise TypeError('User must add email')
        if password is None:
            raise TypeError('User must add password')

        user = self.model(username=username, email=self.normalize_email(email), **kwargs)
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_superuser(self, username, email, password=None, **kwargs):
        if username is None:
            raise TypeError('Superuser must provide the username')
        if email is None:
            raise TypeError('Superuser must have an email address')
        if password is None:
            raise TypeError('Superuser must have a password')

        user = self.create_user(username=username, email=self.normalize_email(email), password=password, **kwargs)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('artist', 'Artist'),
        ('buyer', 'Buyer'),
    ]

    public_id = models.UUIDField(db_index=True, unique=True, editable=False, default=uuid.uuid4)
    username = models.CharField(db_index=True, unique=True, max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(db_index=True, unique=True)

    # Role selection for RiffRent
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='buyer')

    # Profile fields
    bio = models.TextField(blank=True, null=True, max_length=500)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    # Social links for artists
    spotify_link = models.URLField(blank=True, null=True)
    soundcloud_link = models.URLField(blank=True, null=True)
    instagram_link = models.URLField(blank=True, null=True)

    # System fields
    is_membership = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    last_active = models.DateTimeField(auto_now=True, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_artist(self):
        return self.role == 'artist'

    @property
    def is_buyer(self):
        return self.role == 'buyer'

        try:
            instance = self.get(public_id=public_id)
            return instance
        except (ObjectDoesNotExist, ValueError, TypeError):
            raise Http404

    def create_user(self, username, email, password=None, **kwargs):
        if username is None:
            raise TypeError('User must add username')
        if email is None:
            raise TypeError('User must add email')
        if password is None:
            raise TypeError('User must add password')

        user = self.model(username=username, email=self.normalize_email(email), **kwargs)
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_superuser(self, username, email, password=None, **kwargs):
        if username is None:
            raise TypeError('Superuser must provide the username')
        if email is None:
            raise TypeError('Superuser must have an email address')
        if password is None:
            raise TypeError('Superuser must have a password')

        user = self.create_user(username=username, email=self.normalize_email(email), password=password, **kwargs)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user



