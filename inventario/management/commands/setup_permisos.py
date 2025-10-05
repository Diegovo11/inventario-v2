from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from inventario.models import UserProfile


class Command(BaseCommand):
    help = 'Configura grupos y permisos del sistema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Configurando sistema de permisos...'))
        
        # Crear grupos
        grupo_admin, created = Group.objects.get_or_create(name='Administradores')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo "Administradores" creado'))
        
        grupo_invitado, created = Group.objects.get_or_create(name='Invitados')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo "Invitados" creado'))
        
        # Permisos para Administradores (casi todo excepto gestión de usuarios)
        permisos_admin = Permission.objects.filter(
            content_type__app_label='inventario'
        ).exclude(
            codename__in=['add_user', 'change_user', 'delete_user']
        )
        
        grupo_admin.permissions.set(permisos_admin)
        self.stdout.write(self.style.SUCCESS(f'✓ {permisos_admin.count()} permisos asignados a Administradores'))
        
        # Permisos para Invitados (solo lectura de inventario y crear listas)
        content_type_material = ContentType.objects.get(app_label='inventario', model='material')
        content_type_lista = ContentType.objects.get(app_label='inventario', model='listaproduccion')
        content_type_monos = ContentType.objects.get(app_label='inventario', model='monos')
        
        permisos_invitado = [
            Permission.objects.get(content_type=content_type_material, codename='view_material'),
            Permission.objects.get(content_type=content_type_lista, codename='add_listaproduccion'),
            Permission.objects.get(content_type=content_type_lista, codename='view_listaproduccion'),
            Permission.objects.get(content_type=content_type_monos, codename='view_monos'),
        ]
        
        grupo_invitado.permissions.set(permisos_invitado)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(permisos_invitado)} permisos asignados a Invitados'))
        
        # Crear perfiles para usuarios existentes que no tengan
        usuarios_sin_perfil = User.objects.filter(userprofile__isnull=True)
        for user in usuarios_sin_perfil:
            if user.is_superuser:
                UserProfile.objects.create(user=user, nivel='superuser')
                self.stdout.write(self.style.SUCCESS(f'✓ Perfil SUPERUSER creado para {user.username}'))
            else:
                UserProfile.objects.create(user=user, nivel='invitado')
                user.groups.add(grupo_invitado)
                self.stdout.write(self.style.SUCCESS(f'✓ Perfil INVITADO creado para {user.username}'))
        
        self.stdout.write(self.style.SUCCESS('\n¡Sistema de permisos configurado correctamente!'))
        self.stdout.write(self.style.WARNING('\nNiveles disponibles:'))
        self.stdout.write('  • SUPERUSER: Acceso total + gestión de usuarios')
        self.stdout.write('  • ADMIN: Acceso total excepto gestión de usuarios')
        self.stdout.write('  • INVITADO: Solo inventario y crear listas (sin ver precios/costos)')
