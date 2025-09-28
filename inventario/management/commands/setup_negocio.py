from django.core.management.base import BaseCommand
from inventario.models import Material, Monos, RecetaMonos
from django.contrib.auth.models import User
from decimal import Decimal
import json


class Command(BaseCommand):
    help = 'Crea datos de ejemplo persistentes para el sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar creación aunque ya existan datos',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        # Verificar si ya hay datos
        if Material.objects.exists() and not force:
            self.stdout.write(
                self.style.WARNING('Ya existen datos. Use --force para recrear.')
            )
            return
        
        # Crear usuario admin si no existe
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@inventario.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('✅ Usuario admin creado'))
        
        # Materiales completos para un negocio de moños
        materiales_data = [
            {
                'codigo': 'LR001',
                'nombre': 'Listón Rojo Premium',
                'descripcion': 'Listón de satén rojo brillante 2cm ancho',
                'tipo_material': 'liston',
                'unidad_base': 'metros',
                'factor_conversion': 20,
                'cantidad_disponible': Decimal('100.00'),
                'precio_compra': Decimal('35.00'),
                'categoria': 'listón'
            },
            {
                'codigo': 'LA002',
                'nombre': 'Listón Azul Marino',
                'descripcion': 'Listón de terciopelo azul marino 1.5cm',
                'tipo_material': 'liston',
                'unidad_base': 'metros',
                'factor_conversion': 15,
                'cantidad_disponible': Decimal('75.00'),
                'precio_compra': Decimal('28.00'),
                'categoria': 'listón'
            },
            {
                'codigo': 'LN003',
                'nombre': 'Listón Negro Elegante',
                'descripcion': 'Listón de grosgrain negro 3cm ancho',
                'tipo_material': 'liston',
                'unidad_base': 'metros',
                'factor_conversion': 25,
                'cantidad_disponible': Decimal('120.00'),
                'precio_compra': Decimal('45.00'),
                'categoria': 'listón'
            },
            {
                'codigo': 'PB004',
                'nombre': 'Perlas Blancas Grandes',
                'descripcion': 'Perlas de fantasía blancas 10mm',
                'tipo_material': 'piedra',
                'unidad_base': 'unidades',
                'factor_conversion': 100,
                'cantidad_disponible': Decimal('800.00'),
                'precio_compra': Decimal('65.00'),
                'categoria': 'piedra'
            },
            {
                'codigo': 'PD005',
                'nombre': 'Perlas Doradas',
                'descripcion': 'Perlas doradas metalizada 8mm',
                'tipo_material': 'piedra',
                'unidad_base': 'unidades',
                'factor_conversion': 150,
                'cantidad_disponible': Decimal('1200.00'),
                'precio_compra': Decimal('85.00'),
                'categoria': 'piedra'
            },
            {
                'codigo': 'CR006',
                'nombre': 'Cristales Rojos',
                'descripcion': 'Cristales facetados rojos 6mm',
                'tipo_material': 'piedra',
                'unidad_base': 'unidades',
                'factor_conversion': 80,
                'cantidad_disponible': Decimal('640.00'),
                'precio_compra': Decimal('95.00'),
                'categoria': 'piedra'
            },
            {
                'codigo': 'FR007',
                'nombre': 'Flores Rosas Pequeñas',
                'descripcion': 'Flores artificiales rosas 2cm diámetro',
                'tipo_material': 'adorno',
                'unidad_base': 'unidades',
                'factor_conversion': 50,
                'cantidad_disponible': Decimal('400.00'),
                'precio_compra': Decimal('40.00'),
                'categoria': 'adorno'
            },
            {
                'codigo': 'FB008',
                'nombre': 'Flores Blancas Medianas',
                'descripcion': 'Flores de tela blanca 3cm diámetro',
                'tipo_material': 'adorno',
                'unidad_base': 'unidades',
                'factor_conversion': 30,
                'cantidad_disponible': Decimal('240.00'),
                'precio_compra': Decimal('55.00'),
                'categoria': 'adorno'
            },
            {
                'codigo': 'ML009',
                'nombre': 'Mariposas Lilas',
                'descripcion': 'Adorno de mariposas color lila brillante',
                'tipo_material': 'adorno',
                'unidad_base': 'unidades',
                'factor_conversion': 20,
                'cantidad_disponible': Decimal('160.00'),
                'precio_compra': Decimal('32.00'),
                'categoria': 'adorno'
            },
            {
                'codigo': 'LD010',
                'nombre': 'Listón Dorado Fino',
                'descripcion': 'Listón metalizado dorado 0.5cm',
                'tipo_material': 'liston',
                'unidad_base': 'metros',
                'factor_conversion': 10,
                'cantidad_disponible': Decimal('50.00'),
                'precio_compra': Decimal('25.00'),
                'categoria': 'listón'
            }
        ]
        
        # Crear materiales
        created_materials = []
        for material_data in materiales_data:
            material, created = Material.objects.get_or_create(
                codigo=material_data['codigo'],
                defaults=material_data
            )
            if created:
                created_materials.append(material)
                self.stdout.write(f'✅ Material creado: {material.codigo}')
            else:
                self.stdout.write(f'⚠️  Ya existe: {material.codigo}')
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎯 Proceso completado:')
        )
        self.stdout.write(f'📦 Total materiales: {Material.objects.count()}')
        self.stdout.write(f'✨ Nuevos materiales: {len(created_materials)}')
        self.stdout.write(
            self.style.SUCCESS('\n🚀 ¡El sistema está listo para usar!')
        )