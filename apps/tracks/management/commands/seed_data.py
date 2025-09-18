# apps/tracks/management/commands/seed_data.py
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.tracks.models import Genre, Mood, LicenseType
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with initial data for RiffRent'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('🗑️  Clearing existing data...')
            Genre.objects.all().delete()
            Mood.objects.all().delete()
            LicenseType.objects.all().delete()
            # Don't delete users automatically - let them decide
            self.stdout.write('  ✅ Data cleared\n')

        self.stdout.write('🎵 Starting RiffRent data seeding...\n')

        # Create Genres
        self.create_genres()

        # Create Moods
        self.create_moods()

        # Create License Types
        self.create_license_types()

        # Create sample users
        self.create_sample_users()

        self.stdout.write(
            self.style.SUCCESS('✅ Database seeding completed successfully!')
        )

    def create_genres(self):
        """Create music genres"""
        self.stdout.write('📂 Creating genres...')

        genres_data = [
            {
                'name': 'Hip Hop',
                'description': 'Urban beats, rap vocals, strong rhythmic elements'
            },
            {
                'name': 'Electronic',
                'description': 'Synthesized sounds, digital production, dance-oriented'
            },
            {
                'name': 'Rock',
                'description': 'Guitar-driven, powerful drums, energetic compositions'
            },
            {
                'name': 'Pop',
                'description': 'Catchy melodies, mainstream appeal, radio-friendly'
            },
            {
                'name': 'Jazz',
                'description': 'Improvisation, complex harmonies, swing rhythms'
            },
            {
                'name': 'R&B',
                'description': 'Smooth vocals, groove-based, soulful expressions'
            },
            {
                'name': 'Folk',
                'description': 'Acoustic instruments, storytelling, traditional roots'
            },
            {
                'name': 'Classical',
                'description': 'Orchestral arrangements, formal composition structures'
            },
            {
                'name': 'Reggae',
                'description': 'Caribbean rhythms, laid-back groove, social consciousness'
            },
            {
                'name': 'Country',
                'description': 'Guitar and fiddle, rural themes, narrative lyrics'
            },
            {
                'name': 'Blues',
                'description': 'Twelve-bar progression, emotional vocals, guitar solos'
            }
        ]

        created_count = 0
        for genre_data in genres_data:
            genre, created = Genre.objects.get_or_create(
                name=genre_data['name'],
                defaults={
                    'slug': slugify(genre_data['name']),
                    'description': genre_data['description']
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f'  ✅ Created {created_count} genres')

    def create_moods(self):
        """Create mood tags"""
        self.stdout.write('😊 Creating moods...')

        moods_data = [
            {
                'name': 'Upbeat',
                'description': 'High energy, positive vibes, motivational'
            },
            {
                'name': 'Chill',
                'description': 'Relaxed, laid-back, calm atmosphere'
            },
            {
                'name': 'Dark',
                'description': 'Mysterious, intense, dramatic undertones'
            },
            {
                'name': 'Happy',
                'description': 'Joyful, cheerful, uplifting emotions'
            },
            {
                'name': 'Sad',
                'description': 'Melancholic, emotional, introspective'
            },
            {
                'name': 'Energetic',
                'description': 'High tempo, driving force, powerful'
            },
            {
                'name': 'Romantic',
                'description': 'Love-themed, intimate, tender feelings'
            },
            {
                'name': 'Aggressive',
                'description': 'Intense, forceful, high-impact'
            },
            {
                'name': 'Peaceful',
                'description': 'Calm, serene, meditative quality'
            },
            {
                'name': 'Nostalgic',
                'description': 'Reminiscent, wistful, memory-evoking'
            },
            {
                'name': 'Motivational',
                'description': 'Inspiring, encouraging, goal-oriented'
            },
            {
                'name': 'Dreamy',
                'description': 'Ethereal, floating, imaginative atmosphere'
            },
            {
                'name': 'Funky',
                'description': 'Groovy, rhythmic, danceable swagger'
            },
            {
                'name': 'Epic',
                'description': 'Grand, cinematic, heroic scope'
            },
            {
                'name': 'Mysterious',
                'description': 'Enigmatic, suspenseful, unknown elements'
            }
        ]

        created_count = 0
        for mood_data in moods_data:
            mood, created = Mood.objects.get_or_create(
                name=mood_data['name'],
                defaults={
                    'slug': slugify(mood_data['name']),
                    'description': mood_data['description']
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f'  ✅ Created {created_count} moods')

    def create_license_types(self):
        """Create license types with pricing"""
        self.stdout.write('📜 Creating license types...')

        license_data = [
            {
                'name': LicenseType.STANDARD,
                'display_name': 'Standard License',
                'description': 'Perfect for personal projects, small businesses, and non-commercial use. Includes basic usage rights with attribution required.',
                'price_multiplier': 1.00,
                'allows_commercial_use': False,
                'allows_modification': False,
                'requires_attribution': True,
                'max_copies': 1000,
            },
            {
                'name': LicenseType.EXTENDED,
                'display_name': 'Extended License',
                'description': 'Great for larger projects and small commercial use. Allows modifications and higher distribution limits.',
                'price_multiplier': 2.50,
                'allows_commercial_use': True,
                'allows_modification': True,
                'requires_attribution': True,
                'max_copies': 10000,
            },
            {
                'name': LicenseType.COMMERCIAL,
                'display_name': 'Commercial License',
                'description': 'Full commercial rights for businesses, advertising, and professional use. No attribution required.',
                'price_multiplier': 5.00,
                'allows_commercial_use': True,
                'allows_modification': True,
                'requires_attribution': False,
                'max_copies': None,  # Unlimited
            },
            {
                'name': LicenseType.EXCLUSIVE,
                'display_name': 'Exclusive License',
                'description': 'Complete ownership and exclusive rights. Track will be removed from marketplace after purchase.',
                'price_multiplier': 10.00,
                'allows_commercial_use': True,
                'allows_modification': True,
                'requires_attribution': False,
                'max_copies': None,  # Unlimited
            }
        ]

        created_count = 0
        for license_info in license_data:
            license_type, created = LicenseType.objects.get_or_create(
                name=license_info['name'],
                defaults=license_info
            )
            if created:
                created_count += 1

        self.stdout.write(f'  ✅ Created {created_count} license types')

    def create_sample_users(self):
        """Create sample artist and buyer accounts for testing"""
        self.stdout.write('👤 Creating sample users...')

        # Sample Artists
        artists_data = [
            {
                'username': 'beatmaker_sam',
                'email': 'sam@example.com',
                'first_name': 'Sam',
                'last_name': 'Johnson',
                'role': 'artist',
                'bio': 'Hip-hop producer with 5 years experience. Specializing in trap beats and lo-fi instrumentals.',
            },
            {
                'username': 'indie_sarah',
                'email': 'sarah@example.com',
                'first_name': 'Sarah',
                'last_name': 'Williams',
                'role': 'artist',
                'bio': 'Indie folk songwriter creating acoustic melodies for films and commercials.',
            },
            {
                'username': 'dj_alex',
                'email': 'alex@example.com',
                'first_name': 'Alex',
                'last_name': 'Rodriguez',
                'role': 'artist',
                'bio': 'Electronic music producer focused on ambient and chill-out compositions.',
            }
        ]

        # Sample Buyers
        buyers_data = [
            {
                'username': 'content_creator_mike',
                'email': 'mike@example.com',
                'first_name': 'Mike',
                'last_name': 'Chen',
                'role': 'buyer',
                'bio': 'YouTube content creator always looking for fresh background music for vlogs.',
            },
            {
                'username': 'filmmaker_lisa',
                'email': 'lisa@example.com',
                'first_name': 'Lisa',
                'last_name': 'Davis',
                'role': 'buyer',
                'bio': 'Independent filmmaker seeking original soundtracks for short films.',
            }
        ]

        all_users = artists_data + buyers_data
        created_count = 0

        for user_data in all_users:
            if not User.objects.filter(email=user_data['email']).exists():
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password='testpass123',  # Simple password for demo
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    role=user_data['role'],
                    bio=user_data['bio']
                )
                created_count += 1

        self.stdout.write(f'  ✅ Created {created_count} sample users')
        self.stdout.write('  📝 Sample user credentials: password = "testpass123"')