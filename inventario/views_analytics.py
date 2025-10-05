from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F, IntegerField
from django.db.models.functions import TruncMonth, TruncYear
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
import json
from decimal import Decimal

from .models import MovimientoEfectivo, Simulacion, Monos, VentaMonos


@login_required
def analytics_dashboard(request):
    """Dashboard de análisis de ventas y rendimiento"""
    
    # Filtros de fecha
    fecha_fin = timezone.now()
    fecha_inicio = fecha_fin - timedelta(days=365)  # Último año por defecto
    
    # Aplicar filtros si vienen en el request
    periodo = request.GET.get('periodo', '12m')
    
    if periodo == '1m':
        fecha_inicio = fecha_fin - timedelta(days=30)
    elif periodo == '3m':
        fecha_inicio = fecha_fin - timedelta(days=90)
    elif periodo == '6m':
        fecha_inicio = fecha_fin - timedelta(days=180)
    elif periodo == '12m':
        fecha_inicio = fecha_fin - timedelta(days=365)
    elif periodo == 'all':
        fecha_inicio = datetime(2020, 1, 1)  # Desde el inicio
    
    # Obtener VENTAS REALES desde el nuevo modelo VentaMonos
    ventas_reales = VentaMonos.objects.filter(
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    ).select_related('monos')
    
    # 1. MOÑOS MÁS VENDIDOS (por cantidad)
    monos_vendidos = {}
    for venta in ventas_reales:
        mono = venta.monos
        mono_nombre = mono.nombre
        
        if mono_nombre not in monos_vendidos:
            monos_vendidos[mono_nombre] = {
                'id': mono.id,
                'cantidad': 0,
                'cantidad_total_monos': 0,  # Total considerando pares
                'ingresos': Decimal('0'),
                'costos': Decimal('0'),
                'ganancia': Decimal('0'),
                'ventas_count': 0
            }
        
        monos_vendidos[mono_nombre]['cantidad'] += venta.cantidad_vendida
        monos_vendidos[mono_nombre]['cantidad_total_monos'] += venta.cantidad_total_monos
        monos_vendidos[mono_nombre]['ingresos'] += venta.ingreso_total
        monos_vendidos[mono_nombre]['costos'] += venta.costo_unitario * venta.cantidad_vendida
        monos_vendidos[mono_nombre]['ganancia'] += venta.ganancia_total
        monos_vendidos[mono_nombre]['ventas_count'] += 1
    
    # Calcular rendimiento
    for mono_nombre, data in monos_vendidos.items():
        data['rendimiento'] = float((data['ganancia'] / data['costos'] * 100)) if data['costos'] > 0 else 0
    
    # Ordenar por cantidad vendida (usar cantidad_total_monos para el análisis real)
    top_monos_cantidad = sorted(
        monos_vendidos.items(),
        key=lambda x: x[1]['cantidad_total_monos'],
        reverse=True
    )[:10]
    
    # Ordenar por rendimiento
    top_monos_rendimiento = sorted(
        monos_vendidos.items(),
        key=lambda x: x[1]['rendimiento'],
        reverse=True
    )[:10]
    
    # 2. VENTAS POR MES
    ventas_por_mes = ventas_reales.annotate(
        mes=TruncMonth('fecha')
    ).values('mes').annotate(
        total_ventas=Sum('ingreso_total'),
        cantidad_ventas=Count('id'),
        total_cantidad_monos=Sum('cantidad_vendida')
    ).order_by('mes')
    
    # 3. EVOLUCIÓN MENSUAL DE CADA MOÑO
    evolución_monos = defaultdict(lambda: defaultdict(int))
    for venta in ventas_reales:
        mes = venta.fecha.strftime('%Y-%m')
        mono_nombre = venta.monos.nombre
        evolución_monos[mono_nombre][mes] += venta.cantidad_total_monos
    
    # 4. ESTADÍSTICAS GENERALES
    stats = {
        'total_ventas': sum(data['ingresos'] for data in monos_vendidos.values()),
        'total_costos': sum(data['costos'] for data in monos_vendidos.values()),
        'total_ganancias': sum(data['ganancia'] for data in monos_vendidos.values()),
        'total_cantidad_vendida': sum(data['cantidad_total_monos'] for data in monos_vendidos.values()),
        'tipos_monos_vendidos': len(monos_vendidos),
        'total_transacciones': len(ventas_reales),
    }
    
    if stats['total_costos'] > 0:
        stats['rendimiento_general'] = float(stats['total_ganancias'] / stats['total_costos'] * 100)
    else:
        stats['rendimiento_general'] = 0
    
    # Preparar datos para gráficos (convertir a JSON)
    chart_data = {
        'monos_cantidad': {
            'labels': [item[0] for item in top_monos_cantidad],
            'data': [float(item[1]['cantidad_total_monos']) for item in top_monos_cantidad],
            'colors': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384']
        },
        'monos_rendimiento': {
            'labels': [item[0] for item in top_monos_rendimiento],
            'data': [float(item[1]['rendimiento']) for item in top_monos_rendimiento],
            'colors': ['#4BC0C0', '#36A2EB', '#FF9F40', '#9966FF', '#FF6384', '#FFCE56', '#C9CBCF', '#4BC0C0', '#36A2EB', '#FF6384']
        },
        'ventas_mensuales': {
            'labels': [venta['mes'].strftime('%Y-%m') for venta in ventas_por_mes],
            'ingresos': [float(venta['total_ventas']) for venta in ventas_por_mes],
            'cantidad_transacciones': [venta['cantidad_ventas'] for venta in ventas_por_mes]
        }
    }
    
    context = {
        'stats': stats,
        'top_monos_cantidad': top_monos_cantidad,
        'top_monos_rendimiento': top_monos_rendimiento,
        'chart_data_json': json.dumps(chart_data),
        'periodo_seleccionado': periodo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    return render(request, 'inventario/analytics_dashboard.html', context)


@login_required
def analytics_detalle_mono(request, mono_id):
    """Vista detallada de análisis para un moño específico"""
    
    try:
        mono = Monos.objects.get(id=mono_id)
    except Monos.DoesNotExist:
        return render(request, '404.html')
    
    # Filtros de fecha
    fecha_fin = timezone.now()
    fecha_inicio = fecha_fin - timedelta(days=365)
    
    # Ventas del moño específico desde VentaMonos
    ventas_mono = VentaMonos.objects.filter(
        monos=mono,
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    ).order_by('-fecha')
    
    # Estadísticas del moño
    total_ingresos = sum(venta.ingreso_total for venta in ventas_mono)
    total_costos = sum(venta.costo_unitario * venta.cantidad_vendida for venta in ventas_mono)
    total_ganancia = sum(venta.ganancia_total for venta in ventas_mono)
    total_cantidad = sum(venta.cantidad_vendida for venta in ventas_mono)
    total_cantidad_monos = sum(venta.cantidad_total_monos for venta in ventas_mono)
    
    rendimiento = float(total_ganancia / total_costos * 100) if total_costos > 0 else 0
    
    # Evolución mensual
    ventas_por_mes = ventas_mono.annotate(
        mes=TruncMonth('fecha')
    ).values('mes').annotate(
        ingresos=Sum('ingreso_total'),
        cantidad=Sum('cantidad_vendida'),
        total_monos=Sum(F('cantidad_vendida') * 2, output_field=IntegerField()) if mono.tipo_venta == 'par' else Sum('cantidad_vendida')
    ).order_by('mes')
    
    # Preparar datos para gráficos
    chart_data = {
        'ventas_por_mes': [
            {
                'mes': venta['mes'].strftime('%Y-%m'),
                'ingresos': float(venta['ingresos']),
                'cantidad': venta['cantidad']
            } for venta in ventas_por_mes
        ]
    }
    
    context = {
        'mono': mono,
        'total_ingresos': total_ingresos,
        'total_costos': total_costos,
        'total_ganancia': total_ganancia,
        'total_cantidad': total_cantidad,
        'total_cantidad_monos': total_cantidad_monos,
        'rendimiento': rendimiento,
        'ventas_por_mes': ventas_por_mes,
        'ventas_detalle': ventas_mono,
        'chart_data_json': json.dumps(chart_data),
    }
    
    return render(request, 'inventario/analytics_detalle_mono.html', context)