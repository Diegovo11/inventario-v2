from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Material, Insumo, Movimiento, Reabastecimiento, TipoMono, RecetaProduccion, SimulacionProduccion
from .forms import (ReabastecimientoForm, ReabastecimientoUpdateForm, StockBajoForm, 
                    SimuladorForm, TipoMonoForm, MaterialForm, InsumoForm, MovimientoForm)
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
    
    # Métricas de reabastecimiento
    reabastecimientos_pendientes = Reabastecimiento.objects.filter(
        estado__in=['pendiente', 'solicitado', 'en_transito']
    ).count()
    reabastecimientos_retrasados = len([
        r for r in Reabastecimiento.objects.filter(estado__in=['pendiente', 'solicitado', 'en_transito'])
        if r.esta_retrasado()
    ])
    
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
        'reabastecimientos_pendientes': reabastecimientos_pendientes,
        'reabastecimientos_retrasados': reabastecimientos_retrasados,
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
def reabastecimiento_list(request):
    """Lista de reabastecimientos"""
    reabastecimientos = Reabastecimiento.objects.select_related('material').order_by('-fecha_solicitud')
    
    # Filtros
    estado_filter = request.GET.get('estado')
    prioridad_filter = request.GET.get('prioridad')
    
    if estado_filter:
        reabastecimientos = reabastecimientos.filter(estado=estado_filter)
    if prioridad_filter:
        reabastecimientos = reabastecimientos.filter(prioridad=prioridad_filter)
    
    # Estadísticas rápidas
    stats = {
        'pendientes': reabastecimientos.filter(estado='pendiente').count(),
        'en_transito': reabastecimientos.filter(estado='en_transito').count(),
        'recibidos': reabastecimientos.filter(estado='recibido').count(),
        'retrasados': len([r for r in reabastecimientos if r.esta_retrasado()]),
    }
    
    context = {
        'reabastecimientos': reabastecimientos,
        'stats': stats,
        'estado_filter': estado_filter,
        'prioridad_filter': prioridad_filter,
        'estados': Reabastecimiento.ESTADO_CHOICES,
        'prioridades': Reabastecimiento.PRIORIDAD_CHOICES,
    }
    
    return render(request, 'inventario/reabastecimiento_list.html', context)

@login_required
def reabastecimiento_create(request):
    """Crear nuevo reabastecimiento"""
    if request.method == 'POST':
        form = ReabastecimientoForm(request.POST)
        if form.is_valid():
            reabastecimiento = form.save()
            messages.success(request, f'Reabastecimiento creado para {reabastecimiento.material.nombre}')
            return redirect('reabastecimiento_list')
    else:
        form = ReabastecimientoForm()
        
        # Pre-llenar con material si viene en URL
        material_id = request.GET.get('material')
        if material_id:
            try:
                material = Material.objects.get(id=material_id)
                form.initial['material'] = material
            except Material.DoesNotExist:
                pass
    
    return render(request, 'inventario/reabastecimiento_form.html', {
        'form': form,
        'title': 'Crear Reabastecimiento'
    })

@login_required
def reabastecimiento_update(request, pk):
    """Actualizar reabastecimiento existente"""
    reabastecimiento = get_object_or_404(Reabastecimiento, pk=pk)
    
    if request.method == 'POST':
        form = ReabastecimientoUpdateForm(request.POST, instance=reabastecimiento)
        if form.is_valid():
            reabastecimiento = form.save()
            messages.success(request, f'Reabastecimiento actualizado para {reabastecimiento.material.nombre}')
            return redirect('reabastecimiento_list')
    else:
        form = ReabastecimientoUpdateForm(instance=reabastecimiento)
    
    return render(request, 'inventario/reabastecimiento_form.html', {
        'form': form,
        'reabastecimiento': reabastecimiento,
        'title': 'Actualizar Reabastecimiento'
    })

@login_required
def stock_bajo_check(request):
    """Ver materiales con stock bajo y generar reabastecimientos automáticos"""
    stock_minimo = int(request.GET.get('minimo', 50))
    
    materiales_bajo_stock = Material.objects.filter(
        cantidad_disponible__lt=stock_minimo
    ).order_by('cantidad_disponible')
    
    if request.method == 'POST':
        form = StockBajoForm(request.POST)
        if form.is_valid():
            cantidad_solicitar = form.cleaned_data['cantidad_a_solicitar']
            proveedor_default = form.cleaned_data['proveedor_default']
            
            # Crear reabastecimientos automáticos
            creados = 0
            for material in materiales_bajo_stock:
                # Verificar que no existe ya un reabastecimiento pendiente
                existe = Reabastecimiento.objects.filter(
                    material=material,
                    estado__in=['pendiente', 'solicitado', 'en_transito']
                ).exists()
                
                if not existe:
                    Reabastecimiento.objects.create(
                        material=material,
                        cantidad_solicitada=cantidad_solicitar,
                        proveedor=proveedor_default,
                        prioridad='alta' if material.cantidad_disponible < (stock_minimo / 2) else 'media',
                        stock_minimo_sugerido=stock_minimo,
                        automatico=True,
                        notas=f'Generado automáticamente por stock bajo ({material.cantidad_disponible} < {stock_minimo})'
                    )
                    creados += 1
            
            messages.success(request, f'Se crearon {creados} reabastecimientos automáticos')
            return redirect('reabastecimiento_list')
    else:
        form = StockBajoForm()
    
    return render(request, 'inventario/stock_bajo.html', {
        'materiales': materiales_bajo_stock,
        'form': form,
        'stock_minimo': stock_minimo,
    })

@login_required
def simulador(request):
    """Simulador de producción y ganancias"""
    resultado = None
    mensaje_error = None
    
    if request.method == 'POST':
        form = SimuladorForm(request.POST)
        if form.is_valid():
            tipo_mono = form.cleaned_data['tipo_mono']
            cantidad = form.cleaned_data['cantidad_a_producir']
            precio_venta = form.cleaned_data['precio_venta_unitario']
            
            # Verificar stock disponible
            puede_producir, mensaje_stock = tipo_mono.puede_producir(cantidad)
            
            # Calcular métricas
            costo_unitario = tipo_mono.calcular_costo_materiales()
            costo_total = costo_unitario * cantidad
            ingreso_total = precio_venta * cantidad
            ganancia_neta = ingreso_total - costo_total
            
            if ingreso_total > 0:
                margen_porcentaje = (ganancia_neta / ingreso_total) * 100
            else:
                margen_porcentaje = 0
            
            # Obtener recetas para mostrar desglose
            recetas = RecetaProduccion.objects.filter(tipo_mono=tipo_mono).select_related('insumo__material')
            
            # Calcular tiempo de producción
            tiempo_total_minutos = tipo_mono.tiempo_produccion_minutos * cantidad
            tiempo_horas = tiempo_total_minutos / 60
            
            # Calcular rentabilidad por hora
            if tiempo_horas > 0:
                ganancia_por_hora = ganancia_neta / tiempo_horas
            else:
                ganancia_por_hora = 0
            
            resultado = {
                'tipo_mono': tipo_mono,
                'cantidad': cantidad,
                'precio_venta_unitario': precio_venta,
                'costo_unitario': costo_unitario,
                'costo_total': costo_total,
                'ingreso_total': ingreso_total,
                'ganancia_neta': ganancia_neta,
                'margen_porcentaje': margen_porcentaje,
                'puede_producir': puede_producir,
                'mensaje_stock': mensaje_stock,
                'recetas': recetas,
                'tiempo_total_minutos': tiempo_total_minutos,
                'tiempo_horas': tiempo_horas,
                'ganancia_por_hora': ganancia_por_hora,
            }
            
            # Guardar simulación si se solicitó
            if form.cleaned_data['guardar_simulacion'] and form.cleaned_data['nombre_simulacion']:
                SimulacionProduccion.objects.create(
                    nombre_simulacion=form.cleaned_data['nombre_simulacion'],
                    tipo_mono=tipo_mono,
                    cantidad_a_producir=cantidad,
                    precio_venta_unitario=precio_venta
                )
                messages.success(request, 'Simulación guardada correctamente')
            
        else:
            mensaje_error = 'Por favor corrige los errores en el formulario'
    else:
        form = SimuladorForm()
    
    # Obtener tipos de moño disponibles y simulaciones recientes
    tipos_mono = TipoMono.objects.filter(activo=True)
    simulaciones_recientes = SimulacionProduccion.objects.select_related('tipo_mono').order_by('-fecha_simulacion')[:5]
    
    return render(request, 'inventario/simulador.html', {
        'form': form,
        'resultado': resultado,
        'mensaje_error': mensaje_error,
        'tipos_mono': tipos_mono,
        'simulaciones_recientes': simulaciones_recientes
    })

@login_required
def reportes(request):
    """Página de reportes"""
    return render(request, 'inventario/reportes.html')

# Views para gestión completa de elementos
@login_required
def material_create(request):
    """Crear nuevo material"""
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save()
            messages.success(request, f'Material "{material.nombre}" creado correctamente')
            return redirect('materiales_list')
    else:
        form = MaterialForm()
    
    return render(request, 'inventario/material_form.html', {
        'form': form,
        'title': 'Crear Material'
    })

@login_required
def material_edit(request, pk):
    """Editar material existente"""
    material = get_object_or_404(Material, pk=pk)
    
    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            material = form.save()
            messages.success(request, f'Material "{material.nombre}" actualizado correctamente')
            return redirect('materiales_list')
    else:
        form = MaterialForm(instance=material)
    
    return render(request, 'inventario/material_form.html', {
        'form': form,
        'material': material,
        'title': 'Editar Material'
    })

@login_required
def material_delete(request, pk):
    """Eliminar material"""
    material = get_object_or_404(Material, pk=pk)
    
    if request.method == 'POST':
        nombre = material.nombre
        material.delete()
        messages.success(request, f'Material "{nombre}" eliminado correctamente')
        return redirect('materiales_list')
    
    return render(request, 'inventario/confirm_delete.html', {
        'objeto': material,
        'tipo': 'Material',
        'url_cancelar': 'materiales_list'
    })

@login_required
def insumo_create(request):
    """Crear nuevo insumo"""
    if request.method == 'POST':
        form = InsumoForm(request.POST)
        if form.is_valid():
            insumo = form.save()
            messages.success(request, f'Insumo "{insumo.nombre}" creado correctamente')
            return redirect('insumos_list')
    else:
        form = InsumoForm()
    
    return render(request, 'inventario/insumo_form.html', {
        'form': form,
        'title': 'Crear Insumo'
    })

@login_required
def insumo_edit(request, pk):
    """Editar insumo existente"""
    insumo = get_object_or_404(Insumo, pk=pk)
    
    if request.method == 'POST':
        form = InsumoForm(request.POST, instance=insumo)
        if form.is_valid():
            insumo = form.save()
            messages.success(request, f'Insumo "{insumo.nombre}" actualizado correctamente')
            return redirect('insumos_list')
    else:
        form = InsumoForm(instance=insumo)
    
    return render(request, 'inventario/insumo_form.html', {
        'form': form,
        'insumo': insumo,
        'title': 'Editar Insumo'
    })

@login_required
def insumo_delete(request, pk):
    """Eliminar insumo"""
    insumo = get_object_or_404(Insumo, pk=pk)
    
    if request.method == 'POST':
        nombre = insumo.nombre
        insumo.delete()
        messages.success(request, f'Insumo "{nombre}" eliminado correctamente')
        return redirect('insumos_list')
    
    return render(request, 'inventario/confirm_delete.html', {
        'objeto': insumo,
        'tipo': 'Insumo',
        'url_cancelar': 'insumos_list'
    })

@login_required
def movimiento_create(request):
    """Crear nuevo movimiento"""
    if request.method == 'POST':
        form = MovimientoForm(request.POST)
        if form.is_valid():
            movimiento = form.save()
            tipo_texto = movimiento.get_tipo_movimiento_display()
            messages.success(request, f'{tipo_texto} de {abs(movimiento.cantidad)} {movimiento.material.unidad_base} registrado')
            return redirect('movimientos_list')
    else:
        form = MovimientoForm()
    
    return render(request, 'inventario/movimiento_form.html', {
        'form': form,
        'title': 'Registrar Movimiento'
    })

# Alias para compatibilidad con enlaces existentes
@login_required  
def reabastecimiento(request):
    """Redireccionar a la nueva vista de reabastecimiento"""
    return redirect('reabastecimiento_list')

@login_required
def tipos_mono_list(request):
    """Lista de tipos de moño"""
    tipos = TipoMono.objects.all().order_by('nombre')
    
    # Calcular métricas para cada tipo
    for tipo in tipos:
        tipo.costo_calculado = tipo.calcular_costo_materiales()
        tipo.margen_calculado = tipo.margen_ganancia()
        
    return render(request, 'inventario/tipos_mono_list.html', {
        'tipos': tipos
    })

@login_required
def tipo_mono_create(request):
    """Crear nuevo tipo de moño"""
    if request.method == 'POST':
        form = TipoMonoForm(request.POST)
        if form.is_valid():
            tipo = form.save()
            messages.success(request, f'Tipo de moño "{tipo.nombre}" creado correctamente')
            return redirect('tipos_mono_list')
    else:
        form = TipoMonoForm()
    
    return render(request, 'inventario/tipo_mono_form.html', {
        'form': form,
        'title': 'Crear Tipo de Moño'
    })

@login_required
def simulaciones_list(request):
    """Lista de simulaciones guardadas"""
    simulaciones = SimulacionProduccion.objects.select_related('tipo_mono').order_by('-fecha_simulacion')
    
    return render(request, 'inventario/simulaciones_list.html', {
        'simulaciones': simulaciones
    })
