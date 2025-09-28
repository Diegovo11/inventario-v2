from django.core.management.base import BaseCommand
import os


class Command(BaseCommand):
    help = 'Verifica las variables de entorno en Railway'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== VERIFICACIÓN DE VARIABLES DE ENTORNO ===')
        )
        
        # Mostrar TODAS las variables de entorno para debugging
        self.stdout.write('\n🔍 TODAS LAS VARIABLES DISPONIBLES:')
        all_vars = dict(os.environ)
        for key, value in sorted(all_vars.items()):
            if any(keyword in key.upper() for keyword in ['DATABASE', 'RAILWAY', 'POSTGRES']):
                if 'PASSWORD' in key.upper() or 'SECRET' in key.upper():
                    masked_value = value[:10] + '***' if len(value) > 10 else '***'
                    self.stdout.write(f'🔑 {key}: {masked_value}')
                else:
                    self.stdout.write(f'📍 {key}: {value}')
        
        # Variables importantes
        important_vars = [
            'DATABASE_URL',
            'DATABASE_PUBLIC_URL', 
            'RAILWAY_ENVIRONMENT',
            'SECRET_KEY',
            'DEBUG'
        ]
        
        for var in important_vars:
            value = os.environ.get(var)
            if value:
                if 'SECRET' in var:
                    masked_value = value[:10] + '***' if len(value) > 10 else '***'
                    self.stdout.write(f'✅ {var}: {masked_value}')
                elif 'DATABASE' in var:
                    # Mostrar solo el host de la base de datos
                    if 'postgresql://' in value:
                        host_part = value.split('@')[-1].split('/')[0] if '@' in value else 'unknown'
                        self.stdout.write(f'✅ {var}: postgresql://...@{host_part}/...')
                    else:
                        self.stdout.write(f'✅ {var}: {value}')
                else:
                    self.stdout.write(f'✅ {var}: {value}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ {var}: NO CONFIGURADA')
                )
        
        # Verificar todas las variables de entorno que empiecen con DATABASE
        db_vars = [key for key in os.environ.keys() if 'DATABASE' in key]
        if db_vars:
            self.stdout.write(f'\n🔍 Variables de BD encontradas: {db_vars}')
        
        # Verificar configuración de Django
        from django.conf import settings
        db_config = settings.DATABASES['default']
        self.stdout.write(f'\n📊 Django está usando:')
        self.stdout.write(f'   Engine: {db_config["ENGINE"]}')
        self.stdout.write(f'   Host: {db_config.get("HOST", "N/A")}')
        self.stdout.write(f'   Name: {db_config.get("NAME", "N/A")}')
        
        if 'postgresql' in db_config["ENGINE"]:
            self.stdout.write(
                self.style.SUCCESS('✅ PostgreSQL configurado correctamente')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Usando SQLite - Los datos se perderán!')
            )