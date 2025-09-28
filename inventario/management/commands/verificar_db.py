from django.core.management.base import BaseCommand
from inventario.models import Material, Monos, RecetaMonos, Movimiento
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Verifica el estado actual de la base de datos'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== ESTADO DE LA BASE DE DATOS ===')
        )
        
        # Verificar usuarios
        users_count = User.objects.count()
        self.stdout.write(f'👥 Usuarios registrados: {users_count}')
        if users_count > 0:
            for user in User.objects.all():
                self.stdout.write(f'   - {user.username} (admin: {user.is_superuser})')
        
        # Verificar materiales
        materiales_count = Material.objects.count()
        self.stdout.write(f'📦 Materiales: {materiales_count}')
        if materiales_count > 0:
            for material in Material.objects.all():
                self.stdout.write(f'   - {material.codigo}: {material.nombre}')
        
        # Verificar moños
        monos_count = Monos.objects.count()
        self.stdout.write(f'🎀 Moños: {monos_count}')
        if monos_count > 0:
            for mono in Monos.objects.all():
                recetas_count = RecetaMonos.objects.filter(monos=mono).count()
                self.stdout.write(f'   - {mono.codigo}: {mono.nombre} ({recetas_count} recetas)')
        
        # Verificar movimientos
        movimientos_count = Movimiento.objects.count()
        self.stdout.write(f'📊 Movimientos: {movimientos_count}')
        
        # Información de la base de datos
        from django.db import connection
        self.stdout.write(f'\n🔗 Base de datos: {connection.settings_dict["NAME"]}')
        self.stdout.write(f'🖥️  Host: {connection.settings_dict["HOST"]}')
        
        if materiales_count == 0:
            self.stdout.write(
                self.style.WARNING('\n⚠️  No hay materiales. Se crearán automáticamente al acceder al dashboard.')
            )
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Verificación completada')
        )