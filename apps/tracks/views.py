import os
from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import Http404
import stripe
from django.conf import settings

from .models import Track, Genre, Mood, LicenseType, Purchase
from .serializers import (
    TrackListSerializer, TrackDetailSerializer, TrackUploadSerializer,
    GenreSerializer, MoodSerializer, LicenseTypeSerializer, PurchaseSerializer
)
from .permissions import IsArtistOrReadOnly
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from .utils.license_generator import generate_license_certificate
import mimetypes



stripe.api_key = settings.STRIPE_SECRET_KEY


class TrackListView(generics.ListAPIView):
    """List all approved tracks with filtering and search"""
    queryset = Track.objects.filter(status=Track.APPROVED)
    serializer_class = TrackListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['genre', 'mood', 'is_featured']
    search_fields = ['title', 'artist__username', 'tags', 'description']
    ordering_fields = ['uploaded_at', 'play_count', 'purchase_count', 'base_price']
    ordering = ['-uploaded_at']


class TrackDetailView(generics.RetrieveAPIView):
    """Get detailed track information"""
    queryset = Track.objects.filter(status=Track.APPROVED)
    serializer_class = TrackDetailSerializer
    lookup_field = 'public_id'
    
    def get(self, request, *args, **kwargs):
        track = self.get_object()
        # Increment play count when track details are viewed
        track.increment_play_count()
        return super().get(request, *args, **kwargs)


class TrackUploadView(generics.CreateAPIView):
    """Upload new track (artists only)"""
    serializer_class = TrackUploadSerializer
    permission_classes = [permissions.IsAuthenticated, IsArtistOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    
    def perform_create(self, serializer):
        serializer.save(
            artist=self.request.user,
            status=Track.APPROVED
        )


class ArtistTracksView(generics.ListAPIView):
    """List tracks for the authenticated artist"""
    serializer_class = TrackDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Track.objects.filter(artist=self.request.user)


class GenreListView(generics.ListAPIView):
    """List all genres"""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class MoodListView(generics.ListAPIView):
    """List all moods"""
    queryset = Mood.objects.all()
    serializer_class = MoodSerializer


class LicenseTypeListView(generics.ListAPIView):
    """List all active license types"""
    queryset = LicenseType.objects.filter(is_active=True)
    serializer_class = LicenseTypeSerializer



# Add this debugging version to your views.py
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_payment_intent(request):

    try:
        # Check if data exists
        if not request.data:
            return Response(
                {'error': 'No data provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        track_id = request.data.get('track_id')
        license_type = request.data.get('license_type', 'standard')


        if not track_id:
            return Response(
                {'error': 'track_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            track = Track.objects.get(public_id=track_id, status=Track.APPROVED)
        except Track.DoesNotExist:
            return Response(
                {'error': f'Track not found: {track_id}'},
                status=status.HTTP_404_NOT_FOUND
            )

        existing_purchase = Purchase.objects.filter(
            buyer=request.user,
            track=track,
            license_type__name=license_type,
            payment_status='succeeded'
        ).exists()

        if existing_purchase:
            return Response(
                {'error': 'You already own this track with this license type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate price
        try:
            price = track.get_license_price(license_type)
        except Exception as e:
            return Response(
                {'error': f'Error calculating price: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        amount = int(price * 100)  # Stripe uses cents

        # Check Stripe configuration
        if not stripe.api_key:
            return Response(
                {'error': 'Payment system not configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency='usd',
                metadata={
                    'track_id': str(track.public_id),
                    'license_type': license_type,
                    'buyer_id': str(request.user.public_id),
                }
            )
        except Exception as e:
            return Response(
                {'error': f'Payment system error: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        response_data = {
            'client_secret': intent.client_secret,
            'amount': price,
            'track_title': track.title,
            'license_type': license_type
        }
        return Response(response_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Unexpected error: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )



@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def confirm_purchase(request):
    """Confirm purchase after successful Stripe payment"""
    try:
        payment_intent_id = request.data.get('payment_intent_id')
        
        # Retrieve payment intent from Stripe
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if intent.status == 'succeeded':
            # Create purchase record
            track = get_object_or_404(Track, public_id=intent.metadata['track_id'])
            license_type = get_object_or_404(LicenseType, name=intent.metadata['license_type'])
            
            purchase = Purchase.objects.create(
                buyer=request.user,
                track=track,
                license_type=license_type,
                stripe_payment_intent_id=payment_intent_id,
                price_paid=intent.amount / 100,  # Convert from cents
                payment_status='succeeded'
            )
            
            # Update track purchase count
            track.increment_purchase_count()
            
            return Response({
                'success': True,
                'purchase_id': purchase.public_id,
                'message': 'Purchase confirmed successfully'
            })
        else:
            return Response(
                {'error': 'Payment was not successful'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class UserPurchasesView(generics.ListAPIView):
    """List user's purchases"""
    serializer_class = PurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Purchase.objects.filter(buyer=self.request.user, payment_status='succeeded')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_purchased_track(request, purchase_id):
    """Download full quality track after purchase"""
    try:
        # Get the purchase and verify ownership
        purchase = get_object_or_404(
            Purchase,
            public_id=purchase_id,
            buyer=request.user,
            payment_status='succeeded'
        )

        # Check download limits
        if not purchase.can_download:
            return Response(
                {
                    'error': f'Download limit exceeded. You have used {purchase.download_count}/{purchase.max_downloads} downloads.'},
                status=status.HTTP_403_FORBIDDEN
            )

        track = purchase.track

        # Make sure file exists
        if not track.audio_file or not os.path.exists(track.audio_file.path):
            return Response(
                {'error': 'Audio file not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Increment download count
        purchase.increment_download_count()

        # Serve the file
        response = FileResponse(
            open(track.audio_file.path, 'rb'),
            content_type='audio/mpeg'
        )

        # Set download filename
        filename = f"{track.artist.username} - {track.title}.mp3"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
def stream_preview(request, track_id):
    """Stream preview file (no authentication required)"""
    try:
        track = get_object_or_404(Track, public_id=track_id, status=Track.APPROVED)

        # Use preview file if available, otherwise serve a snippet of main file
        if track.preview_file and os.path.exists(track.preview_file.path):
            file_path = track.preview_file.path
        elif track.audio_file and os.path.exists(track.audio_file.path):
            # Fallback to main file (you might want to generate preview on-the-fly)
            file_path = track.audio_file.path
        else:
            raise Http404("Preview not available")

        # Increment play count
        track.increment_play_count()

        # Stream the file (not download)
        response = FileResponse(
            open(file_path, 'rb'),
            content_type='audio/mpeg'
        )

        # Set headers for streaming (not download)
        response['Content-Disposition'] = 'inline'
        response['Accept-Ranges'] = 'bytes'

        return response

    except Exception as e:
        raise Http404("Preview not found")


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_license_certificate(request, purchase_id):
    """Download license certificate PDF"""
    try:
        purchase = get_object_or_404(
            Purchase,
            public_id=purchase_id,
            buyer=request.user,
            payment_status='succeeded'
        )

        # Generate license certificate if not exists
        if not purchase.license_file:
            generate_license_certificate(purchase)

        if not purchase.license_file or not os.path.exists(purchase.license_file.path):
            return Response(
                {'error': 'License certificate not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        response = FileResponse(
            open(purchase.license_file.path, 'rb'),
            content_type='application/pdf'
        )

        filename = f"License_{purchase.track.title}_{purchase.license_type.name}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
