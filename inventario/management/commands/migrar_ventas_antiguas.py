from django.core.management.base import BaseCommand
from django.utils import timezone
from inventario.models import MovimientoEfectivo, VentaMonos, ListaProduccion
from decimal import Decimal


class Command(BaseCommand):
    help = 'Migra ventas antiguas de MovimientoEfectivo a VentaMonos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la migración sin guardar cambios',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODO SIMULACIÓN - No se guardarán cambios'))
        else:
            self.stdout.write(self.style.SUCCESS('💾 MODO REAL - Se guardarán los cambios'))
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('MIGRACIÓN DE VENTAS ANTIGUAS')
        self.stdout.write('=' * 60 + '\n')

        # Buscar MovimientoEfectivo de ventas que no tengan VentaMonos asociados
        movimientos_venta = MovimientoEfectivo.objects.filter(
            tipo_movimiento='ingreso',
            categoria='venta'
        ).order_by('fecha')

        self.stdout.write(f'📊 Total movimientos de venta encontrados: {movimientos_venta.count()}\n')

        ventas_creadas = 0
        ventas_ya_existen = 0
        errores = 0

        for mov in movimientos_venta:
            try:
                # Extraer nombre de lista del concepto
                # Formato: "Venta de producción - Lista: NOMBRE_LISTA"
                if 'Lista:' in mov.concepto:
                    nombre_lista = mov.concepto.split('Lista:')[1].strip()
                    
                    self.stdout.write(f'\n🔍 Procesando: {mov.concepto}')
                    self.stdout.write(f'   Fecha: {mov.fecha.strftime("%Y-%m-%d %H:%M")}')
                    self.stdout.write(f'   Monto: ${mov.monto:.2f}')
                    self.stdout.write(f'   Lista: {nombre_lista}')
                    
                    # Buscar la lista
                    try:
                        lista = ListaProduccion.objects.get(nombre=nombre_lista)
                        self.stdout.write(f'   ✅ Lista encontrada: {lista.nombre}')
                        
                        # Verificar si ya existen ventas para esta lista
                        ventas_existentes = VentaMonos.objects.filter(lista_produccion=lista)
                        
                        if ventas_existentes.exists():
                            self.stdout.write(self.style.WARNING(f'   ⚠️  Ya existen {ventas_existentes.count()} ventas para esta lista'))
                            ventas_ya_existen += 1
                            continue
                        
                        # Obtener detalles de moños de la lista
                        detalles = lista.detalles_monos.all()
                        
                        if not detalles:
                            self.stdout.write(self.style.WARNING('   ⚠️  Lista sin detalles de moños'))
                            continue
                        
                        self.stdout.write(f'   📦 Detalles encontrados: {detalles.count()}')
                        
                        # Crear VentaMonos por cada detalle que tenga cantidad_producida > 0
                        ventas_para_crear = []
                        
                        for detalle in detalles:
                            if detalle.cantidad_producida > 0:
                                cantidad_vendida = detalle.cantidad_producida
                                mono = detalle.monos
                                precio_unitario = mono.precio_venta
                                ingreso_total = Decimal(cantidad_vendida) * precio_unitario
                                costo_unitario = mono.costo_produccion
                                ganancia_total = ingreso_total - (costo_unitario * cantidad_vendida)
                                
                                venta = VentaMonos(
                                    lista_produccion=lista,
                                    monos=mono,
                                    cantidad_vendida=cantidad_vendida,
                                    tipo_venta=mono.tipo_venta,
                                    precio_unitario=precio_unitario,
                                    ingreso_total=ingreso_total,
                                    costo_unitario=costo_unitario,
                                    ganancia_total=ganancia_total,
                                    fecha=mov.fecha,  # Usar fecha del movimiento
                                    usuario=mov.usuario
                                )
                                
                                ventas_para_crear.append(venta)
                                
                                self.stdout.write(f'      → {mono.nombre}: {cantidad_vendida} {mono.tipo_venta} = ${ingreso_total:.2f}')
                        
                        if ventas_para_crear:
                            if not dry_run:
                                VentaMonos.objects.bulk_create(ventas_para_crear)
                                self.stdout.write(self.style.SUCCESS(f'   ✅ Creadas {len(ventas_para_crear)} ventas'))
                            else:
                                self.stdout.write(self.style.WARNING(f'   🔍 Se crearían {len(ventas_para_crear)} ventas'))
                            
                            ventas_creadas += len(ventas_para_crear)
                        else:
                            self.stdout.write(self.style.WARNING('   ⚠️  No hay detalles con cantidad_producida > 0'))
                            
                    except ListaProduccion.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'   ❌ Lista "{nombre_lista}" no encontrada'))
                        errores += 1
                        
                else:
                    self.stdout.write(self.style.WARNING(f'\n⚠️  Movimiento sin formato esperado: {mov.concepto}'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'\n❌ Error procesando movimiento {mov.id}: {str(e)}'))
                errores += 1

        # Resumen
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('RESUMEN DE MIGRACIÓN')
        self.stdout.write('=' * 60)
        self.stdout.write(f'✅ Ventas creadas: {ventas_creadas}')
        self.stdout.write(f'⚠️  Ventas que ya existían: {ventas_ya_existen}')
        self.stdout.write(f'❌ Errores: {errores}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 Esto fue una SIMULACIÓN. Ejecuta sin --dry-run para aplicar cambios.'))
        else:
            self.stdout.write(self.style.SUCCESS('\n💾 Migración completada.'))
            self.stdout.write('Ahora puedes ir a /inventario/analytics/ para ver los datos.')
