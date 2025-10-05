from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from inventario.models import VentaMonos, ListaProduccion, Monos, MovimientoEfectivo
from django.db.models import Sum, Count


class Command(BaseCommand):
    help = 'Diagnóstico del sistema de ventas para verificar datos en analytics'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('DIAGNÓSTICO DEL SISTEMA DE VENTAS'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # 1. Verificar VentaMonos
        self.stdout.write('\n1. Verificando tabla VentaMonos...')
        try:
            total_ventas = VentaMonos.objects.count()
            self.stdout.write(f'   ✅ Total ventas registradas: {total_ventas}')
            
            if total_ventas > 0:
                self.stdout.write('\n   Últimas 5 ventas:')
                for venta in VentaMonos.objects.select_related('monos', 'lista_produccion').order_by('-fecha')[:5]:
                    self.stdout.write(f'   - {venta.monos.nombre}: {venta.cantidad_vendida} {venta.tipo_venta}')
                    self.stdout.write(f'     Fecha: {venta.fecha.strftime("%Y-%m-%d %H:%M")}')
                    self.stdout.write(f'     Ingreso: ${venta.ingreso_total:.2f}')
                    self.stdout.write(f'     Ganancia: ${venta.ganancia_total:.2f}')
                    if venta.lista_produccion:
                        self.stdout.write(f'     Lista: {venta.lista_produccion.nombre}')
                    self.stdout.write('')
            else:
                self.stdout.write(self.style.WARNING('   ⚠️  No hay ventas registradas'))
                self.stdout.write('   Esto significa que:')
                self.stdout.write('   - No se han registrado ventas desde listas (Paso 6)')
                self.stdout.write('   - O la migración 0008_ventamonos.py no se aplicó')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error: {e}'))

        # 2. Verificar listas finalizadas
        self.stdout.write('\n2. Verificando listas finalizadas...')
        try:
            listas_finalizadas = ListaProduccion.objects.filter(estado='finalizado')
            self.stdout.write(f'   Total listas finalizadas: {listas_finalizadas.count()}')
            
            if listas_finalizadas.exists():
                for lista in listas_finalizadas[:5]:
                    ventas_lista = VentaMonos.objects.filter(lista_produccion=lista).count()
                    self.stdout.write(f'   - {lista.nombre}: {ventas_lista} ventas asociadas')
                    if ventas_lista == 0:
                        self.stdout.write(self.style.WARNING(f'     ⚠️  Esta lista no tiene ventas en VentaMonos'))
            else:
                self.stdout.write(self.style.WARNING('   ⚠️  No hay listas finalizadas'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error: {e}'))

        # 3. Verificar MovimientoEfectivo de ventas
        self.stdout.write('\n3. Verificando MovimientoEfectivo (ventas)...')
        try:
            movimientos_venta = MovimientoEfectivo.objects.filter(
                tipo_movimiento='ingreso',
                categoria='venta'
            ).order_by('-fecha')
            
            total_movimientos = movimientos_venta.count()
            self.stdout.write(f'   Total movimientos de venta: {total_movimientos}')
            
            if total_movimientos > 0:
                self.stdout.write('\n   Últimas 3 movimientos:')
                for mov in movimientos_venta[:3]:
                    self.stdout.write(f'   - {mov.concepto}')
                    self.stdout.write(f'     Fecha: {mov.fecha.strftime("%Y-%m-%d %H:%M")}')
                    self.stdout.write(f'     Monto: ${mov.monto:.2f}')
                    self.stdout.write('')
            else:
                self.stdout.write(self.style.WARNING('   ⚠️  No hay movimientos de venta registrados'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error: {e}'))

        # 4. Verificar moños disponibles
        self.stdout.write('\n4. Verificando moños disponibles...')
        try:
            monos = Monos.objects.filter(activo=True)
            self.stdout.write(f'   Total moños activos: {monos.count()}')
            
            for mono in monos:
                ventas_mono = VentaMonos.objects.filter(monos=mono).count()
                self.stdout.write(f'   - {mono.nombre} ({mono.tipo_venta}): {ventas_mono} ventas')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error: {e}'))

        # 5. Verificar rango de fechas para analytics (últimos 12 meses)
        self.stdout.write('\n5. Verificando datos para analytics (últimos 12 meses)...')
        try:
            fecha_fin = timezone.now()
            fecha_inicio = fecha_fin - timedelta(days=365)
            
            ventas_en_rango = VentaMonos.objects.filter(
                fecha__gte=fecha_inicio,
                fecha__lte=fecha_fin
            )
            
            self.stdout.write(f'   Rango: {fecha_inicio.strftime("%Y-%m-%d")} a {fecha_fin.strftime("%Y-%m-%d")}')
            self.stdout.write(f'   Ventas en rango: {ventas_en_rango.count()}')
            
            if ventas_en_rango.exists():
                self.stdout.write('\n   Estadísticas por moño:')
                stats = ventas_en_rango.values('monos__nombre').annotate(
                    total_cantidad=Sum('cantidad_vendida'),
                    total_ingresos=Sum('ingreso_total'),
                    total_ganancia=Sum('ganancia_total'),
                    num_ventas=Count('id')
                ).order_by('-total_cantidad')
                
                for stat in stats:
                    self.stdout.write(f'   - {stat["monos__nombre"]}:')
                    self.stdout.write(f'     * Cantidad vendida: {stat["total_cantidad"]}')
                    self.stdout.write(f'     * Ingresos: ${stat["total_ingresos"]:.2f}')
                    self.stdout.write(f'     * Ganancia: ${stat["total_ganancia"]:.2f}')
                    self.stdout.write(f'     * Número de ventas: {stat["num_ventas"]}')
                    
                self.stdout.write(self.style.SUCCESS('\n   ✅ Estos datos deberían aparecer en analytics'))
            else:
                self.stdout.write(self.style.WARNING('\n   ⚠️  No hay ventas en los últimos 12 meses'))
                self.stdout.write('   Por eso analytics aparece vacío')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error: {e}'))

        # 6. Verificar migraciones
        self.stdout.write('\n6. Verificando migraciones aplicadas...')
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM django_migrations WHERE app='inventario' ORDER BY applied DESC LIMIT 5")
                migraciones = cursor.fetchall()
                
            self.stdout.write('   Últimas 5 migraciones aplicadas:')
            for mig in migraciones:
                self.stdout.write(f'   - {mig[0]}')
                if '0008_ventamonos' in mig[0]:
                    self.stdout.write(self.style.SUCCESS('     ✅ Migración de VentaMonos aplicada'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error: {e}'))

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('FIN DEL DIAGNÓSTICO'))
        self.stdout.write('=' * 60)
        
        # Resumen
        self.stdout.write('\n📋 RESUMEN:')
        if total_ventas == 0:
            self.stdout.write(self.style.WARNING('⚠️  No hay ventas registradas en VentaMonos'))
            self.stdout.write('Posibles causas:')
            self.stdout.write('1. Las ventas se registraron ANTES de aplicar la migración 0008_ventamonos')
            self.stdout.write('2. Las ventas se registraron pero hubo un error al crear VentaMonos')
            self.stdout.write('3. Aún no se han registrado ventas después del último deploy')
            self.stdout.write('\n💡 Solución: Registra una venta de prueba desde el Paso 6')
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ {total_ventas} ventas encontradas'))
            self.stdout.write('Analytics debería mostrar estos datos')
