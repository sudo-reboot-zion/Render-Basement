from rest_framework import routers
from django.urls import path

from apps.auths.viewsets.login import LoginViewSet
from apps.auths.viewsets.refresh import RefreshViewSet
from apps.auths.viewsets.register import RegisterViewSet
from .tracks import views
from apps.users.viewsets import UserViewSet, CurrentUserView

router = routers.SimpleRouter()

#USER
router.register(r'user', UserViewSet, basename='user')

#AUTH
router.register(r'auth/register', RegisterViewSet, basename='auth-register')
router.register(r'auth/login', LoginViewSet, basename='auth-login')
router.register(r'auth/refresh', RefreshViewSet, basename='auth-refresh')


urlpatterns = [
    *router.urls,
    path('tracks/', views.TrackListView.as_view(), name='track-list'),
    path('tracks/<uuid:public_id>/', views.TrackDetailView.as_view(), name='track-detail'),
    path('tracks/upload/', views.TrackUploadView.as_view(), name='track-upload'),
    path('tracks/my-tracks/', views.ArtistTracksView.as_view(), name='artist-tracks'),

    # Metadata endpoints
    path('genres/', views.GenreListView.as_view(), name='genre-list'),
    path('moods/', views.MoodListView.as_view(), name='mood-list'),
    path('license-types/', views.LicenseTypeListView.as_view(), name='license-types'),

    # Payment endpoints
    path('payment/create-intent/', views.create_payment_intent, name='create-payment-intent'),
    path('payment/confirm/', views.confirm_purchase, name='confirm-purchase'),
    path('purchases/', views.UserPurchasesView.as_view(), name='user-purchases'),

    # Download endpoints
    path('download/track/<uuid:purchase_id>/', views.download_purchased_track, name='download-track'),
    path('auth/me/', CurrentUserView.as_view(), name='current-user'),
    path('download/license/<uuid:purchase_id>/', views.download_license_certificate, name='download-license'),
    path('stream/preview/<uuid:track_id>/', views.stream_preview, name='stream-preview'),
]