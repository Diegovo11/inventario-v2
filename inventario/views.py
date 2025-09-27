from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Material, Insumo, Movimiento
import json

@login_required
def dashboard(request):
    """Dashboard principal con métricas y gráficos"""
    
    # Métricas básicas
    total_materiales = Material.objects.count()
    stock_bajo = Material.objects.filter(cantidad_disponible__lt=100).count()
    
    # Valor total del inventario
    valor_total = Material.objects.aggregate(
        total=Sum(F('cantidad_disponible') * F('costo_unitario'))
    )['total'] or 0
    
    # Movimientos de hoy
    hoy = timezone.now().date()
    movimientos_hoy = Movimiento.objects.filter(fecha__date=hoy).count()
    
    # Materiales con stock bajo (menos de 100 unidades)
    materiales_stock_bajo = Material.objects.filter(
        cantidad_disponible__lt=100
    ).order_by('cantidad_disponible')[:5]
    
    # Materiales más utilizados (simulado por ahora)
    materiales_mas_usados = Material.objects.all()[:5]
    
    # Movimientos recientes
    movimientos_recientes = Movimiento.objects.select_related('material').order_by('-fecha')[:8]
    
    # Datos para gráficos (últimos 7 días)
    fechas_movimientos = []
    entradas_data = []
    salidas_data = []
    
    for i in range(6, -1, -1):
        fecha = hoy - timedelta(days=i)
        fechas_movimientos.append(fecha.strftime('%d/%m'))
        
        entradas = Movimiento.objects.filter(
            fecha__date=fecha,
            tipo_movimiento='entrada'
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        salidas = Movimiento.objects.filter(
            fecha__date=fecha,
            tipo_movimiento='salida'
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        entradas_data.append(entradas)
        salidas_data.append(abs(salidas))  # Convertir a positivo para el gráfico
    
    context = {
        'total_materiales': total_materiales,
        'stock_bajo': stock_bajo,
        'valor_total': valor_total,
        'movimientos_hoy': movimientos_hoy,
        'materiales_stock_bajo': materiales_stock_bajo,
        'materiales_mas_usados': materiales_mas_usados,
        'movimientos_recientes': movimientos_recientes,
        'fechas_movimientos': json.dumps(fechas_movimientos),
        'entradas_data': json.dumps(entradas_data),
        'salidas_data': json.dumps(salidas_data),
    }
    
    return render(request, 'inventario/dashboard.html', context)

@login_required
def materiales_list(request):
    """Lista de materiales"""
    materiales = Material.objects.all().order_by('-created_at')
    return render(request, 'inventario/materiales_list.html', {
        'materiales': materiales
    })

@login_required
def insumos_list(request):
    """Lista de insumos"""
    insumos = Insumo.objects.select_related('material').all().order_by('-created_at')
    return render(request, 'inventario/insumos_list.html', {
        'insumos': insumos
    })

@login_required
def movimientos_list(request):
    """Lista de movimientos"""
    movimientos = Movimiento.objects.select_related('material').order_by('-fecha')
    return render(request, 'inventario/movimientos_list.html', {
        'movimientos': movimientos
    })

@login_required
def reabastecimiento(request):
    """Sistema de reabastecimiento"""
    materiales = Material.objects.all().order_by('nombre')
    return render(request, 'inventario/reabastecimiento.html', {
        'materiales': materiales
    })

@login_required
def simulador(request):
    """Simulador de producción y ganancias"""
    insumos = Insumo.objects.select_related('material').all()
    return render(request, 'inventario/simulador.html', {
        'insumos': insumos
    })

@login_required
def reportes(request):
    """Página de reportes"""
    return render(request, 'inventario/reportes.html')

# Views para crear nuevos elementos (placeholder)
@login_required
def material_create(request):
    messages.info(request, 'Funcionalidad de crear material próximamente')
    return redirect('dashboard')

@login_required
def insumo_create(request):
    messages.info(request, 'Funcionalidad de crear insumo próximamente')
    return redirect('dashboard')

@login_required
def movimiento_create(request):
    messages.info(request, 'Funcionalidad de crear movimiento próximamente')
    return redirect('dashboard')
