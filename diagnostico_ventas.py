#!/usr/bin/env python
"""
Script de diagnóstico para verificar el estado del sistema de ventas
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/dharyk/Desktop/Personal/inventario-v2')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario_project.settings')
django.setup()

from inventario.models import VentaMonos, ListaProduccion, Monos, MovimientoEfectivo
from django.utils import timezone

print("=" * 60)
print("DIAGNÓSTICO DEL SISTEMA DE VENTAS")
print("=" * 60)

# 1. Verificar si existe la tabla VentaMonos
print("\n1. Verificando tabla VentaMonos...")
try:
    total_ventas = VentaMonos.objects.count()
    print(f"   ✅ Tabla existe: {total_ventas} ventas registradas")
    
    if total_ventas > 0:
        print("\n   Últimas 5 ventas:")
        for venta in VentaMonos.objects.order_by('-fecha')[:5]:
            print(f"   - {venta.monos.nombre}: {venta.cantidad_vendida} ({venta.tipo_venta})")
            print(f"     Fecha: {venta.fecha}")
            print(f"     Ingreso: ${venta.ingreso_total}")
            print(f"     Lista: {venta.lista_produccion.nombre if venta.lista_produccion else 'Sin lista'}")
            print()
    else:
        print("   ⚠️  No hay ventas registradas todavía")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. Verificar listas finalizadas
print("\n2. Verificando listas finalizadas...")
try:
    listas_finalizadas = ListaProduccion.objects.filter(estado='finalizado')
    print(f"   Total listas finalizadas: {listas_finalizadas.count()}")
    
    for lista in listas_finalizadas:
        ventas_lista = VentaMonos.objects.filter(lista_produccion=lista).count()
        print(f"   - {lista.nombre}: {ventas_lista} ventas asociadas")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. Verificar MovimientoEfectivo de ventas
print("\n3. Verificando MovimientoEfectivo (ventas)...")
try:
    movimientos_venta = MovimientoEfectivo.objects.filter(
        tipo_movimiento='ingreso',
        categoria='venta'
    ).order_by('-fecha')[:5]
    
    print(f"   Total movimientos de venta: {MovimientoEfectivo.objects.filter(tipo_movimiento='ingreso', categoria='venta').count()}")
    
    if movimientos_venta:
        print("\n   Últimos 5 movimientos:")
        for mov in movimientos_venta:
            print(f"   - {mov.concepto}")
            print(f"     Fecha: {mov.fecha}")
            print(f"     Monto: ${mov.monto}")
            print()
            
except Exception as e:
    print(f"   ❌ Error: {e}")

# 4. Verificar moños disponibles
print("\n4. Verificando moños disponibles...")
try:
    monos = Monos.objects.filter(activo=True)
    print(f"   Total moños activos: {monos.count()}")
    
    for mono in monos:
        ventas_mono = VentaMonos.objects.filter(monos=mono).count()
        print(f"   - {mono.nombre} ({mono.tipo_venta}): {ventas_mono} ventas")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# 5. Verificar fechas para analytics
print("\n5. Verificando rango de fechas para analytics...")
try:
    from datetime import timedelta
    fecha_fin = timezone.now()
    fecha_inicio = fecha_fin - timedelta(days=365)
    
    ventas_en_rango = VentaMonos.objects.filter(
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    )
    
    print(f"   Fecha inicio: {fecha_inicio}")
    print(f"   Fecha fin: {fecha_fin}")
    print(f"   Ventas en rango (últimos 365 días): {ventas_en_rango.count()}")
    
    if ventas_en_rango.exists():
        print("\n   Ventas por moño:")
        from django.db.models import Sum, Count
        stats = ventas_en_rango.values('monos__nombre').annotate(
            total_cantidad=Sum('cantidad_vendida'),
            total_ingresos=Sum('ingreso_total'),
            num_ventas=Count('id')
        )
        
        for stat in stats:
            print(f"   - {stat['monos__nombre']}: {stat['total_cantidad']} unidades, ${stat['total_ingresos']}, {stat['num_ventas']} ventas")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("FIN DEL DIAGNÓSTICO")
print("=" * 60)
