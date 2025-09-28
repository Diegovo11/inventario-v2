from django.core.management.base import BaseCommand
from inventario.models import Material, ConfiguracionSistema
from decimal import Decimal


class Command(BaseCommand):
    help = 'Crea datos de prueba para el sistema de inventario'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando datos de prueba...'))
        
        # Crear configuración del sistema
        config, created = ConfiguracionSistema.objects.get_or_create(
            defaults={
                'nombre_empresa': 'Moños Bella',
                'moneda': 'MXN',
                'stock_minimo_alerta': 10
            }
        )
        if created:
            self.stdout.write(f'✓ Configuración creada: {config.nombre_empresa}')
        
        # Materiales de prueba
        materiales_data = [
            {
                'codigo': 'L001',
                'nombre': 'Listón Rojo Satinado',
                'descripcion': 'Listón de satín rojo de alta calidad, 1.5cm de ancho',
                'tipo_material': 'rollo',
                'unidad_base': 'cm',
                'factor_conversion': 1000,  # 1 rollo = 1000 cm (10 metros)
                'cantidad_disponible': Decimal('2500.00'),
                'precio_compra': Decimal('85.00'),
                'categoria': 'listón'
            },
            {
                'codigo': 'L002', 
                'nombre': 'Listón Azul Marino',
                'descripcion': 'Listón de grosgrain azul marino, 2cm de ancho',
                'tipo_material': 'rollo',
                'unidad_base': 'cm',
                'factor_conversion': 1000,
                'cantidad_disponible': Decimal('1800.00'),
                'precio_compra': Decimal('90.00'),
                'categoria': 'listón'
            },
            {
                'codigo': 'P001',
                'nombre': 'Piedras Brillantes Pequeñas',
                'descripcion': 'Piedras decorativas cristal pequeñas, colores surtidos',
                'tipo_material': 'paquete',
                'unidad_base': 'unidades',
                'factor_conversion': 100,  # 1 paquete = 100 unidades
                'cantidad_disponible': Decimal('350.00'),
                'precio_compra': Decimal('25.00'),
                'categoria': 'piedra'
            },
            {
                'codigo': 'P002',
                'nombre': 'Piedras Grandes Doradas',
                'descripcion': 'Piedras decorativas grandes color dorado',
                'tipo_material': 'paquete',
                'unidad_base': 'unidades',
                'factor_conversion': 50,   # 1 paquete = 50 unidades
                'cantidad_disponible': Decimal('75.00'),
                'precio_compra': Decimal('45.00'),
                'categoria': 'piedra'
            },
            {
                'codigo': 'A001',
                'nombre': 'Flores de Tela Blancas',
                'descripcion': 'Flores pequeñas de tela blanca para decoración',
                'tipo_material': 'paquete',
                'unidad_base': 'unidades',
                'factor_conversion': 20,   # 1 paquete = 20 unidades
                'cantidad_disponible': Decimal('60.00'),
                'precio_compra': Decimal('35.00'),
                'categoria': 'adorno'
            },
            {
                'codigo': 'L003',
                'nombre': 'Listón Rosa Pastel',
                'descripcion': 'Listón de organza rosa pastel, 2.5cm de ancho',
                'tipo_material': 'rollo',
                'unidad_base': 'cm',
                'factor_conversion': 1500,  # 1 rollo = 1500 cm (15 metros)
                'cantidad_disponible': Decimal('750.00'),  # Stock bajo para prueba
                'precio_compra': Decimal('75.00'),
                'categoria': 'listón'
            },
            {
                'codigo': 'A002',
                'nombre': 'Perlas Nacaradas',
                'descripcion': 'Perlas sintéticas nacaradas para bordado',
                'tipo_material': 'paquete', 
                'unidad_base': 'unidades',
                'factor_conversion': 200,   # 1 paquete = 200 unidades
                'cantidad_disponible': Decimal('5.00'),  # Stock muy bajo
                'precio_compra': Decimal('60.00'),
                'categoria': 'adorno'
            }
        ]
        
        created_count = 0
        for material_data in materiales_data:
            material, created = Material.objects.get_or_create(
                codigo=material_data['codigo'],
                defaults=material_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'✓ Material creado: {material.codigo} - {material.nombre}')
            else:
                self.stdout.write(f'- Material existente: {material.codigo} - {material.nombre}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n¡Datos de prueba creados exitosamente!\n'
                f'Materiales nuevos: {created_count}\n'
                f'Total materiales: {Material.objects.count()}\n'
                f'\nCredenciales de acceso:\n'
                f'Usuario: admin\n'
                f'Contraseña: admin\n'
                f'\nAccede a: http://127.0.0.1:8000/'
            )
        )