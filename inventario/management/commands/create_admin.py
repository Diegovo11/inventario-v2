from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create superuser for production'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Solo crear si no existe ya un superusuario
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@inventario.com',
                password='admin123'  # Cambia esta contraseña después
            )
            self.stdout.write(
                self.style.SUCCESS('Superuser created successfully!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Superuser already exists')
            )