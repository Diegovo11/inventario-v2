from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
import math
from .models import Material, Movimiento, ConfiguracionSistema, Monos, RecetaMonos, Simulacion, DetalleSimulacion, MovimientoEfectivo
from .forms import (MaterialForm, MonosForm, RecetaMonosFormSet, SimulacionForm, 
                   SimulacionBusquedaForm, EntradaMaterialForm, SalidaMaterialForm, MovimientoFiltroForm,
                   EntradaDesdeSimulacionForm, SalidaDesdeSimulacionForm, MovimientoEfectivoForm, FiltroMovimientosEfectivoForm)
from django.core.paginator import Paginator
from decimal import Decimal
import math

# Importar vistas de contaduría
from .views_contaduria import contaduria_home, flujo_efectivo, registrar_movimiento_efectivo, estado_resultados, exportar_excel_efectivo


def home(request):
    """Vista principal del sistema"""
    # Estadísticas básicas
    total_materiales = Material.objects.filter(activo=True).count()
    materiales_bajo_stock = Material.objects.filter(
        activo=True, 
        cantidad_disponible__lte=10
    ).count()
    
    # Materiales más recientes
    materiales_recientes = Material.objects.filter(activo=True).order_by('-fecha_creacion')[:5]
    
    # Movimientos recientes
    movimientos_recientes = Movimiento.objects.select_related('material', 'usuario').order_by('-fecha')[:10]
    
    # Valor total del inventario
    valor_total = sum(material.valor_inventario for material in Material.objects.filter(activo=True))
    
    context = {
        'total_materiales': total_materiales,
        'materiales_bajo_stock': materiales_bajo_stock,
        'materiales_recientes': materiales_recientes,
        'movimientos_recientes': movimientos_recientes,
        'valor_total': valor_total,
    }
    
    return render(request, 'inventario/home.html', context)


@login_required
def lista_materiales(request):
    """Vista para listar todos los materiales"""
    query = request.GET.get('q', '')
    categoria = request.GET.get('categoria', '')
    tipo = request.GET.get('tipo', '')
    
    materiales = Material.objects.filter(activo=True)
    
    if query:
        materiales = materiales.filter(
            Q(codigo__icontains=query) |
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query)
        )
    
    if categoria:
        materiales = materiales.filter(categoria=categoria)
    
    if tipo:
        materiales = materiales.filter(tipo_material=tipo)
    
    materiales = materiales.order_by('codigo')
    
    # Paginación
    paginator = Paginator(materiales, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Para los filtros
    categorias = Material.objects.values_list('categoria', flat=True).distinct()
    tipos = Material.TIPO_MATERIAL_CHOICES
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'categoria': categoria,
        'tipo': tipo,
        'categorias': categorias,
        'tipos': tipos,
    }
    
    return render(request, 'inventario/lista_materiales.html', context)


@login_required
def detalle_material(request, material_id):
    """Vista para ver detalles de un material"""
    material = get_object_or_404(Material, id=material_id, activo=True)
    movimientos = material.movimientos.all()[:20]
    
    context = {
        'material': material,
        'movimientos': movimientos,
    }
    
    return render(request, 'inventario/detalle_material.html', context)


@login_required
def agregar_material(request):
    """Vista para agregar un nuevo material"""
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save()
            messages.success(request, f'Material {material.codigo} agregado exitosamente.')
            return redirect('inventario:detalle_material', material_id=material.id)
    else:
        form = MaterialForm()
    
    return render(request, 'inventario/form_material.html', {'form': form, 'titulo': 'Agregar Material'})


@login_required
def editar_material(request, material_id):
    """Vista para editar un material existente"""
    material = get_object_or_404(Material, id=material_id, activo=True)
    
    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, f'Material {material.codigo} actualizado exitosamente.')
            return redirect('inventario:detalle_material', material_id=material.id)
    else:
        form = MaterialForm(instance=material)
    
    return render(request, 'inventario/form_material.html', {
        'form': form, 
        'titulo': f'Editar Material {material.codigo}',
        'material': material
    })


# ================ VISTAS PARA SISTEMA DE SIMULACIÓN ================

@login_required
def lista_monos(request):
    """Vista para listar todos los moños"""
    query = request.GET.get('q', '')
    tipo_venta = request.GET.get('tipo_venta', '')
    
    monos = Monos.objects.filter(activo=True)
    
    if query:
        monos = monos.filter(
            Q(codigo__icontains=query) |
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query)
        )
    
    if tipo_venta:
        monos = monos.filter(tipo_venta=tipo_venta)
    
    monos = monos.order_by('codigo')
    
    # Paginación
    paginator = Paginator(monos, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'tipo_venta': tipo_venta,
        'tipo_venta_choices': Monos.TIPO_VENTA_CHOICES,
    }
    
    return render(request, 'inventario/lista_monos.html', context)


@login_required
def detalle_monos(request, monos_id):
    """Vista para ver detalles de un moño"""
    monos = get_object_or_404(Monos, id=monos_id, activo=True)
    recetas = monos.recetas.select_related('material').all()
    simulaciones_recientes = monos.simulaciones.order_by('-fecha_creacion')[:5]
    
    context = {
        'monos': monos,
        'recetas': recetas,
        'simulaciones_recientes': simulaciones_recientes,
    }
    
    return render(request, 'inventario/detalle_monos.html', context)


@login_required
def agregar_monos(request):
    """Vista para agregar un nuevo moño"""
    if request.method == 'POST':
        form = MonosForm(request.POST)
        formset = RecetaMonosFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            monos = form.save()
            formset.instance = monos
            formset.save()
            
            messages.success(request, f'Moño {monos.codigo} agregado exitosamente.')
            return redirect('inventario:detalle_monos', monos_id=monos.id)
    else:
        form = MonosForm()
        formset = RecetaMonosFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'titulo': 'Agregar Moño',
        'action': 'agregar'
    }
    
    return render(request, 'inventario/form_monos.html', context)


@login_required
def editar_monos(request, monos_id):
    """Vista para editar un moño existente"""
    monos = get_object_or_404(Monos, id=monos_id, activo=True)
    
    if request.method == 'POST':
        form = MonosForm(request.POST, instance=monos)
        formset = RecetaMonosFormSet(request.POST, instance=monos)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            
            messages.success(request, f'Moño {monos.codigo} actualizado exitosamente.')
            return redirect('inventario:detalle_monos', monos_id=monos.id)
    else:
        form = MonosForm(instance=monos)
        formset = RecetaMonosFormSet(instance=monos)
    
    context = {
        'form': form,
        'formset': formset,
        'titulo': f'Editar Moño {monos.codigo}',
        'monos': monos,
        'action': 'editar'
    }
    
    return render(request, 'inventario/form_monos.html', context)


@login_required
def simulador(request):
    """Vista principal del simulador de producción"""
    if request.method == 'POST':
        form = SimulacionForm(request.POST)
        if form.is_valid():
            # Ejecutar simulación
            simulacion_data = ejecutar_simulacion(form.cleaned_data, request.user)
            return render(request, 'inventario/resultado_simulacion.html', {
                'simulacion': simulacion_data['simulacion'],
                'detalles': simulacion_data['detalles'],
                'resumen': simulacion_data['resumen']
            })
    else:
        form = SimulacionForm()
    
    # Obtener estadísticas recientes
    simulaciones_recientes = Simulacion.objects.select_related('monos').order_by('-fecha_creacion')[:5]
    total_monos = Monos.objects.filter(activo=True).count()
    
    context = {
        'form': form,
        'simulaciones_recientes': simulaciones_recientes,
        'total_monos': total_monos,
    }
    
    return render(request, 'inventario/simulador.html', context)


@login_required
def historial_simulaciones(request):
    """Vista para ver historial de simulaciones"""
    form = SimulacionBusquedaForm(request.GET or None)
    
    simulaciones = Simulacion.objects.select_related('monos', 'usuario').all()
    
    if form.is_valid():
        if form.cleaned_data.get('monos'):
            simulaciones = simulaciones.filter(monos=form.cleaned_data['monos'])
        
        if form.cleaned_data.get('fecha_desde'):
            simulaciones = simulaciones.filter(fecha_creacion__date__gte=form.cleaned_data['fecha_desde'])
        
        if form.cleaned_data.get('fecha_hasta'):
            simulaciones = simulaciones.filter(fecha_creacion__date__lte=form.cleaned_data['fecha_hasta'])
        
        if form.cleaned_data.get('necesita_compras'):
            necesita = form.cleaned_data['necesita_compras'] == 'true'
            simulaciones = simulaciones.filter(necesita_compras=necesita)
    
    simulaciones = simulaciones.order_by('-fecha_creacion')
    
    # Paginación
    paginator = Paginator(simulaciones, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
    }
    
    return render(request, 'inventario/historial_simulaciones.html', context)


@login_required
def detalle_simulacion(request, simulacion_id):
    """Vista para ver detalles de una simulación específica"""
    simulacion = get_object_or_404(Simulacion, id=simulacion_id)
    detalles = simulacion.detalles.select_related('material').all()
    
    context = {
        'simulacion': simulacion,
        'detalles': detalles,
    }
    
    return render(request, 'inventario/detalle_simulacion.html', context)


def ejecutar_simulacion(data, usuario):
    """
    Función principal para ejecutar simulación de producción
    Calcula materiales necesarios, costos, ganancias y necesidades de compra
    """
    monos = data['monos']
    cantidad_producir = data['cantidad_producir']
    tipo_venta = data['tipo_venta']
    precio_venta_unitario = data['precio_venta_unitario']
    
    # Calcular cantidad total de moños según tipo de venta
    if tipo_venta == 'par':
        cantidad_total_monos = cantidad_producir * 2
    else:
        cantidad_total_monos = cantidad_producir
    
    # Crear simulación
    simulacion = Simulacion.objects.create(
        monos=monos,
        cantidad_producir=cantidad_producir,
        tipo_venta=tipo_venta,
        precio_venta_unitario=precio_venta_unitario,
        cantidad_total_monos=cantidad_total_monos,
        costo_total_produccion=Decimal('0'),
        ingreso_total_venta=Decimal('0'),
        ganancia_estimada=Decimal('0'),
        necesita_compras=False,
        costo_total_compras=Decimal('0'),
        usuario=usuario
    )
    
    # Obtener recetas del moño
    recetas = monos.recetas.select_related('material').all()
    
    costo_total = Decimal('0')
    costo_compras = Decimal('0')
    necesita_compras = False
    detalles = []
    
    for receta in recetas:
        material = receta.material
        cantidad_por_mono = receta.cantidad_necesaria
        cantidad_total_necesaria = cantidad_por_mono * cantidad_total_monos
        
        # Verificar stock disponible
        cantidad_disponible = material.cantidad_disponible
        cantidad_faltante = max(Decimal('0'), cantidad_total_necesaria - cantidad_disponible)
        suficiente_stock = cantidad_faltante == 0
        
        # Calcular necesidades de compra si hace falta
        cantidad_a_comprar = Decimal('0')
        unidades_completas_comprar = 0
        costo_compra_material = Decimal('0')
        
        if not suficiente_stock:
            necesita_compras = True
            cantidad_a_comprar = cantidad_faltante
            
            # Calcular unidades completas a comprar (paquetes/rollos)
            unidades_completas_comprar = math.ceil(float(cantidad_a_comprar / material.factor_conversion))
            
            # Calcular costo de compra
            costo_compra_material = Decimal(str(unidades_completas_comprar)) * material.precio_compra
            costo_compras += costo_compra_material
        
        # Calcular costo de material usado
        costo_material_usado = cantidad_total_necesaria * material.costo_unitario
        costo_total += costo_material_usado
        
        # Crear detalle de simulación
        detalle = DetalleSimulacion.objects.create(
            simulacion=simulacion,
            material=material,
            cantidad_necesaria=cantidad_total_necesaria,
            cantidad_disponible=cantidad_disponible,
            cantidad_faltante=cantidad_faltante,
            cantidad_a_comprar=cantidad_a_comprar,
            unidades_completas_comprar=unidades_completas_comprar,
            costo_compra_necesaria=costo_compra_material,
            suficiente_stock=suficiente_stock
        )
        
        detalles.append(detalle)
    
    # Calcular totales
    if tipo_venta == 'par':
        ingreso_total = precio_venta_unitario * cantidad_producir  # precio por par
    else:
        ingreso_total = precio_venta_unitario * cantidad_total_monos  # precio por unidad
    
    ganancia_estimada = ingreso_total - costo_total
    
    # Actualizar simulación con resultados
    simulacion.costo_total_produccion = costo_total
    simulacion.ingreso_total_venta = ingreso_total
    simulacion.ganancia_estimada = ganancia_estimada
    simulacion.necesita_compras = necesita_compras
    simulacion.costo_total_compras = costo_compras
    simulacion.save()
    
    return {
        'simulacion': simulacion,
        'detalles': detalles,
        'resumen': {
            'cantidad_total_monos': cantidad_total_monos,
            'costo_total': costo_total,
            'ingreso_total': ingreso_total,
            'ganancia_estimada': ganancia_estimada,
            'necesita_compras': necesita_compras,
            'costo_total_compras': costo_compras,
        }
    }


@login_required
def get_monos_info(request, monos_id):
    """Vista AJAX para obtener información de un moño"""
    try:
        monos = Monos.objects.get(id=monos_id, activo=True)
        data = {
            'precio_venta': float(monos.precio_venta),
            'tipo_venta': monos.tipo_venta,
            'costo_produccion': float(monos.costo_produccion),
            'ganancia_unitaria': float(monos.ganancia_unitaria),
        }
        return JsonResponse(data)
    except Monos.DoesNotExist:
        return JsonResponse({'error': 'Moño no encontrado'}, status=404)


# ========== SISTEMA DE ENTRADA Y SALIDA DE MATERIALES ==========

@login_required
def entrada_material(request):
    """Vista para registrar entrada/reabastecimiento de materiales"""
    if request.method == 'POST':
        form = EntradaMaterialForm(request.POST)
        if form.is_valid():
            # Obtener datos del formulario
            material = form.cleaned_data['material']
            cantidad_comprada = form.cleaned_data['cantidad_comprada']
            detalle = form.cleaned_data.get('detalle', '')
            
            # Calcular precio automáticamente basado en el precio de compra del material
            precio_compra_total = cantidad_comprada * material.precio_compra
            
            # Cálculos automáticos
            cantidad_en_unidad_base = form.cleaned_data['cantidad_en_unidad_base']
            costo_unitario = form.cleaned_data['costo_unitario']
            nuevo_stock = form.cleaned_data['nuevo_stock']
            
            # Actualizar el stock del material
            cantidad_anterior = material.cantidad_disponible
            material.cantidad_disponible = nuevo_stock
            material.precio_compra = precio_compra_total
            material.save()
            
            # Registrar el movimiento
            movimiento = Movimiento.objects.create(
                material=material,
                tipo_movimiento='entrada',
                cantidad=cantidad_en_unidad_base,
                cantidad_anterior=cantidad_anterior,
                cantidad_nueva=nuevo_stock,
                precio_unitario=costo_unitario,
                costo_total_movimiento=precio_compra_total,
                detalle=detalle or f"Reabastecimiento de {cantidad_comprada} {material.tipo_material}(s)",
                usuario=request.user
            )
            
            # Registrar movimiento de efectivo automático
            MovimientoEfectivo.registrar_movimiento(
                concepto=f"Compra de inventario: {material.nombre}",
                tipo_movimiento='egreso',
                categoria='inventario',
                monto=precio_compra_total,
                usuario=request.user,
                movimiento_inventario=movimiento
            )
            
            messages.success(
                request, 
                f"Entrada registrada exitosamente. {material.nombre}: "
                f"+{cantidad_en_unidad_base} {material.unidad_base}. "
                f"Nuevo stock: {nuevo_stock} {material.unidad_base}"
            )
            return redirect('inventario:detalle_material', material_id=material.id)
    else:
        # Verificar si viene con material preseleccionado
        material_id = request.GET.get('material')
        initial_data = {}
        if material_id:
            try:
                material = Material.objects.get(id=material_id, activo=True)
                initial_data['material'] = material
            except Material.DoesNotExist:
                pass
        
        form = EntradaMaterialForm(initial=initial_data)
    
    context = {
        'form': form,
        'title': 'Entrada de Material',
        'breadcrumb': 'Reabastecimiento'
    }
    return render(request, 'inventario/entrada_material.html', context)


@login_required
def salida_material(request):
    """Vista para registrar salida normal de materiales"""
    if request.method == 'POST':
        form = SalidaMaterialForm(request.POST)
        if form.is_valid():
            try:
                # Obtener datos del formulario
                material = form.cleaned_data['material']
                cantidad_utilizada = form.cleaned_data['cantidad_utilizada']
                destino = form.cleaned_data['destino']
                detalle = form.cleaned_data['detalle']
                
                # Verificar stock suficiente
                if material.cantidad_disponible < cantidad_utilizada:
                    messages.error(request, f'Stock insuficiente. Stock actual: {material.cantidad_disponible} {material.unidad_base}')
                    return render(request, 'inventario/salida_material.html', {'form': form})
                
                # Calcular nuevo stock y costo
                cantidad_anterior = material.cantidad_disponible
                nuevo_stock = cantidad_anterior - cantidad_utilizada
                costo_total_movimiento = cantidad_utilizada * material.costo_unitario
                
                # Crear descripción completa
                descripcion_completa = f"Salida para {destino}"
                if detalle:
                    descripcion_completa += f" - {detalle}"
                
                # Registrar el movimiento
                movimiento = Movimiento.objects.create(
                    material=material,
                    tipo_movimiento='salida',
                    cantidad=-cantidad_utilizada,  # Negativo para salida
                    cantidad_anterior=cantidad_anterior,
                    cantidad_nueva=nuevo_stock,
                    precio_unitario=material.costo_unitario,
                    costo_total_movimiento=costo_total_movimiento,
                    detalle=descripcion_completa,
                    usuario=request.user
                )
                
                # Actualizar el stock del material
                material.cantidad_disponible = nuevo_stock
                material.save()
                
                # Registrar movimiento de efectivo automático (costo de materiales utilizados)
                MovimientoEfectivo.registrar_movimiento(
                    concepto=f"Costo de materiales: {material.nombre} - {descripcion_completa}",
                    tipo_movimiento='egreso',
                    categoria='produccion',
                    monto=costo_total_movimiento,
                    usuario=request.user,
                    movimiento_inventario=movimiento
                )
                
                messages.success(
                    request, 
                    f"Salida registrada exitosamente. {material.nombre}: "
                    f"-{cantidad_utilizada} {material.unidad_base}. "
                    f"Nuevo stock: {nuevo_stock} {material.unidad_base}"
                )
                return redirect('inventario:salida_material')
                
            except Exception as e:
                messages.error(request, f'Error al registrar la salida: {str(e)}')
    else:
        # Verificar si viene con material preseleccionado
        material_id = request.GET.get('material')
        initial_data = {}
        if material_id:
            try:
                material = Material.objects.get(id=material_id, activo=True)
                initial_data['material'] = material
            except Material.DoesNotExist:
                pass
        
        form = SalidaMaterialForm(initial=initial_data)
    
    context = {
        'form': form,
        'title': 'Salida de Material',
        'breadcrumb': 'Salida Normal'
    }
    return render(request, 'inventario/salida_material.html', context)


@login_required
def material_info_api(request):
    """API para obtener información del material vía AJAX"""
    material_id = request.GET.get('material_id')
    if not material_id:
        return JsonResponse({'error': 'ID de material requerido'}, status=400)
    
    try:
        material = Material.objects.get(id=material_id, activo=True)
        data = {
            'stock_actual': float(material.cantidad_disponible),
            'unidad': material.unidad_base,
            'costo_unitario': float(material.costo_unitario),
            'nombre': material.nombre,
            'valor_inventario': float(material.valor_inventario)
        }
        return JsonResponse(data)
    except Material.DoesNotExist:
        return JsonResponse({'error': 'Material no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def procesar_simulacion_completa(request, simulacion_id):
    """
    Procesa una simulación completada registrando todas las salidas de materiales automáticamente
    """
    try:
        simulacion = Simulacion.objects.get(id=simulacion_id)
        
        if request.method == 'POST':
            # Verificar que la simulación no haya sido procesada antes
            if simulacion.movimiento_set.filter(tipo_movimiento='produccion').exists():
                messages.warning(request, 'Esta simulación ya fue procesada anteriormente.')
                return redirect('inventario:detalle_simulacion', simulacion_id=simulacion.id)
            
            materiales_utilizados = []
            materiales_faltantes = []
            
            # Procesar cada detalle de la simulación
            for detalle in simulacion.detalles.all():
                material = detalle.material
                cantidad_necesaria = detalle.cantidad_necesaria
                
                if material.cantidad_disponible >= cantidad_necesaria:
                    # Hay stock suficiente - registrar salida
                    cantidad_anterior = material.cantidad_disponible
                    material.cantidad_disponible -= cantidad_necesaria
                    material.save()
                    
                    # Crear movimiento de salida por producción
                    movimiento = Movimiento.objects.create(
                        material=material,
                        tipo_movimiento='produccion',
                        cantidad=-cantidad_necesaria,
                        cantidad_anterior=cantidad_anterior,
                        cantidad_nueva=material.cantidad_disponible,
                        precio_unitario=material.costo_unitario,
                        costo_total_movimiento=cantidad_necesaria * material.costo_unitario,
                        detalle=f"Salida por producción - Simulación #{simulacion.id}",
                        usuario=request.user,
                        simulacion_relacionada=simulacion
                    )
                    
                    materiales_utilizados.append({
                        'material': material.nombre,
                        'cantidad': cantidad_necesaria,
                        'nuevo_stock': material.cantidad_disponible
                    })
                else:
                    # Stock insuficiente
                    materiales_faltantes.append({
                        'material': material.nombre,
                        'disponible': material.cantidad_disponible,
                        'necesario': cantidad_necesaria,
                        'faltante': cantidad_necesaria - material.cantidad_disponible
                    })
            
            if materiales_faltantes:
                # Hay materiales faltantes - mostrar opción de reabastecimiento
                context = {
                    'simulacion': simulacion,
                    'materiales_faltantes': materiales_faltantes,
                    'materiales_utilizados': materiales_utilizados
                }
                messages.error(request, f'Faltan {len(materiales_faltantes)} materiales para completar la simulación.')
                return render(request, 'inventario/confirmar_reabastecimiento.html', context)
            else:
                # Todo procesado correctamente - registrar la venta de la producción
                MovimientoEfectivo.registrar_movimiento(
                    concepto=f'Venta de producción - {simulacion.monos.nombre} - Simulación #{simulacion.id}',
                    tipo_movimiento='ingreso',
                    categoria='venta',
                    monto=simulacion.ingreso_total_venta,
                    usuario=request.user,
                    simulacion_relacionada=simulacion
                )
                
                messages.success(request, f'Simulación procesada exitosamente. {len(materiales_utilizados)} materiales utilizados. Venta registrada por ${simulacion.ingreso_total_venta:.2f}.')
                return redirect('inventario:detalle_simulacion', simulacion_id=simulacion.id)
        
        # GET request - mostrar confirmación
        detalles = simulacion.detalles.all()
        context = {
            'simulacion': simulacion,
            'detalles': detalles,
            'total_materiales': detalles.count()
        }
        return render(request, 'inventario/confirmar_simulacion.html', context)
        
    except Simulacion.DoesNotExist:
        messages.error(request, 'Simulación no encontrada.')
        return redirect('inventario:historial_simulaciones')
    except Exception as e:
        messages.error(request, f'Error al procesar simulación: {str(e)}')
        return redirect('inventario:detalle_simulacion', simulacion_id=simulacion_id)


@login_required 
def reabastecer_desde_simulacion(request, simulacion_id):
    """
    Reabastece automáticamente los materiales faltantes para una simulación
    """
    try:
        simulacion = Simulacion.objects.get(id=simulacion_id)
        
        if request.method == 'POST':
            materiales_reabastecidos = []
            costo_total_reabastecimiento = 0
            
            # Obtener materiales faltantes
            for detalle in simulacion.detalles.all():
                material = detalle.material
                cantidad_necesaria = detalle.cantidad_necesaria
                
                if material.cantidad_disponible < cantidad_necesaria:
                    cantidad_faltante = cantidad_necesaria - material.cantidad_disponible
                    
                    # Calcular cantidad a comprar en unidades completas (paquetes/rollos)
                    if material.factor_conversion > 0:
                        paquetes_necesarios = math.ceil(cantidad_faltante / material.factor_conversion)
                        cantidad_a_comprar = paquetes_necesarios * material.factor_conversion
                    else:
                        cantidad_a_comprar = cantidad_faltante
                    
                    # Calcular costo (asumiendo mismo precio por unidad)
                    costo_compra = cantidad_a_comprar * material.costo_unitario
                    
                    # Registrar entrada
                    cantidad_anterior = material.cantidad_disponible
                    material.cantidad_disponible += cantidad_a_comprar
                    material.save()
                    
                    # Crear movimiento de entrada
                    movimiento = Movimiento.objects.create(
                        material=material,
                        tipo_movimiento='entrada',
                        cantidad=cantidad_a_comprar,
                        cantidad_anterior=cantidad_anterior,
                        cantidad_nueva=material.cantidad_disponible,
                        precio_unitario=material.costo_unitario,
                        costo_total_movimiento=costo_compra,
                        detalle=f"Reabastecimiento automático para Simulación #{simulacion.id}",
                        usuario=request.user,
                        simulacion_relacionada=simulacion
                    )
                    
                    materiales_reabastecidos.append({
                        'material': material.nombre,
                        'cantidad_comprada': cantidad_a_comprar,
                        'costo': costo_compra,
                        'nuevo_stock': material.cantidad_disponible
                    })
                    
                    costo_total_reabastecimiento += costo_compra
            
            if materiales_reabastecidos:
                messages.success(
                    request,
                    f'Reabastecimiento completado: {len(materiales_reabastecidos)} materiales. '
                    f'Costo total: ${costo_total_reabastecimiento:.2f}'
                )
                # Ahora intentar procesar la simulación automáticamente
                return redirect('inventario:procesar_simulacion_completa', simulacion_id=simulacion.id)
            else:
                messages.info(request, 'No se necesita reabastecimiento para esta simulación.')
                return redirect('inventario:procesar_simulacion_completa', simulacion_id=simulacion.id)
        
        # GET - mostrar materiales faltantes
        materiales_faltantes = []
        costo_estimado = 0
        
        for detalle in simulacion.detalles.all():
            material = detalle.material
            cantidad_necesaria = detalle.cantidad_necesaria
            
            if material.cantidad_disponible < cantidad_necesaria:
                cantidad_faltante = cantidad_necesaria - material.cantidad_disponible
                
                if material.factor_conversion > 0:
                    paquetes_necesarios = math.ceil(cantidad_faltante / material.factor_conversion)
                    cantidad_a_comprar = paquetes_necesarios * material.factor_conversion
                else:
                    cantidad_a_comprar = cantidad_faltante
                
                costo_material = cantidad_a_comprar * material.costo_unitario
                costo_estimado += costo_material
                
                materiales_faltantes.append({
                    'material': material,
                    'faltante': cantidad_faltante,
                    'cantidad_a_comprar': cantidad_a_comprar,
                    'costo': costo_material
                })
        
        context = {
            'simulacion': simulacion,
            'materiales_faltantes': materiales_faltantes,
            'costo_total_estimado': costo_estimado
        }
        return render(request, 'inventario/reabastecer_simulacion.html', context)
        
    except Simulacion.DoesNotExist:
        messages.error(request, 'Simulación no encontrada.')
        return redirect('inventario:historial_simulaciones')
    except Exception as e:
        messages.error(request, f'Error en reabastecimiento: {str(e)}')
        return redirect('inventario:detalle_simulacion', simulacion_id=simulacion_id)


@login_required
def entrada_rapida_simulacion(request, simulacion_id):
    """
    Vista para entrada rápida de materiales específicos para una simulación
    """
    try:
        simulacion = Simulacion.objects.get(id=simulacion_id)
        
        if request.method == 'POST':
            materiales_ingresados = []
            costo_total = 0
            
            # Procesar cada material del POST
            for key, value in request.POST.items():
                if key.startswith('cantidad_') and value:
                    material_id = key.split('_')[1]
                    try:
                        material = Material.objects.get(id=material_id)
                        cantidad = float(value)
                        
                        # Obtener precio si se proporcionó
                        precio_key = f'precio_{material_id}'
                        if precio_key in request.POST and request.POST[precio_key]:
                            precio_total = float(request.POST[precio_key])
                        else:
                            precio_total = cantidad * material.costo_unitario
                        
                        if cantidad > 0:
                            # Registrar entrada
                            cantidad_anterior = material.cantidad_disponible
                            material.cantidad_disponible += cantidad
                            material.save()
                            
                            # Crear movimiento
                            movimiento = Movimiento.objects.create(
                                material=material,
                                tipo_movimiento='entrada',
                                cantidad=cantidad,
                                cantidad_anterior=cantidad_anterior,
                                cantidad_nueva=material.cantidad_disponible,
                                precio_unitario=precio_total / cantidad if cantidad > 0 else material.costo_unitario,
                                costo_total_movimiento=precio_total,
                                detalle=f'Entrada rápida para Simulación #{simulacion.id} - {simulacion.monos.nombre}',
                                usuario=request.user,
                                simulacion_relacionada=simulacion
                            )
                            
                            materiales_ingresados.append({
                                'material': material.nombre,
                                'cantidad': cantidad,
                                'costo': precio_total,
                                'nuevo_stock': material.cantidad_disponible
                            })
                            
                            costo_total += precio_total
                            
                    except (Material.DoesNotExist, ValueError) as e:
                        messages.warning(request, f'Error con material ID {material_id}: {str(e)}')
            
            if materiales_ingresados:
                messages.success(
                    request,
                    f'Entrada completada: {len(materiales_ingresados)} materiales ingresados. '
                    f'Costo total: ${costo_total:.2f}'
                )
            else:
                messages.warning(request, 'No se registraron entradas.')
                
            return redirect('inventario:detalle_simulacion', simulacion_id=simulacion.id)
        
        # GET - mostrar formulario
        from .forms import EntradaDesdeSimulacionForm
        form = EntradaDesdeSimulacionForm(simulacion=simulacion)
        
        context = {
            'simulacion': simulacion,
            'form': form,
            'title': f'Entrada Rápida - Simulación #{simulacion.id}'
        }
        return render(request, 'inventario/entrada_rapida_simulacion.html', context)
        
    except Simulacion.DoesNotExist:
        messages.error(request, 'Simulación no encontrada.')
        return redirect('inventario:historial_simulaciones')
    except Exception as e:
        messages.error(request, f'Error en entrada rápida: {str(e)}')
        return redirect('inventario:detalle_simulacion', simulacion_id=simulacion_id)


@login_required
def generar_salida_directa(request, simulacion_id):
    """
    Genera salidas directas para todos los materiales de una simulación
    Solo funciona si todos los materiales están disponibles
    """
    try:
        simulacion = Simulacion.objects.get(id=simulacion_id)
        
        # Verificar que todos los materiales estén disponibles
        materiales_faltantes = []
        materiales_procesados = []
        
        for detalle in simulacion.detalles.all():
            material = detalle.material
            cantidad_necesaria = detalle.cantidad_necesaria
            
            if material.cantidad_disponible < cantidad_necesaria:
                materiales_faltantes.append({
                    'material': material.nombre,
                    'disponible': material.cantidad_disponible,
                    'necesario': cantidad_necesaria,
                    'faltante': cantidad_necesaria - material.cantidad_disponible
                })
            else:
                # Registrar salida
                cantidad_anterior = material.cantidad_disponible
                material.cantidad_disponible -= cantidad_necesaria
                material.save()
                
                # Crear movimiento de salida
                movimiento = Movimiento.objects.create(
                    material=material,
                    tipo_movimiento='salida',
                    cantidad=-cantidad_necesaria,
                    cantidad_anterior=cantidad_anterior,
                    cantidad_nueva=material.cantidad_disponible,
                    precio_unitario=material.costo_unitario,
                    costo_total_movimiento=cantidad_necesaria * material.costo_unitario,
                    detalle=f'Salida directa - Simulación #{simulacion.id} ({simulacion.monos.nombre})',
                    usuario=request.user,
                    simulacion_relacionada=simulacion
                )
                
                # Registrar movimiento de efectivo automático
                MovimientoEfectivo.registrar_movimiento(
                    concepto=f'Costo de producción - {material.nombre} - Simulación #{simulacion.id}',
                    tipo_movimiento='egreso',
                    categoria='produccion',
                    monto=cantidad_necesaria * material.costo_unitario,
                    usuario=request.user,
                    simulacion_relacionada=simulacion,
                    movimiento_inventario=movimiento
                )
                
                materiales_procesados.append({
                    'material': material.nombre,
                    'cantidad': cantidad_necesaria,
                    'costo': cantidad_necesaria * material.costo_unitario,
                    'nuevo_stock': material.cantidad_disponible
                })
        
        if materiales_faltantes:
            messages.error(
                request,
                f'No se puede generar salida directa. Faltan {len(materiales_faltantes)} materiales. '
                f'Usa la opción "Generar Entrada" primero.'
            )
        else:
            # Registrar la venta de la producción (ingreso por la simulación completada)
            MovimientoEfectivo.registrar_movimiento(
                concepto=f'Venta de producción - {simulacion.monos.nombre} - Simulación #{simulacion.id}',
                tipo_movimiento='ingreso',
                categoria='venta',
                monto=simulacion.ingreso_total_venta,
                usuario=request.user,
                simulacion_relacionada=simulacion
            )
            
            messages.success(
                request,
                f'Salida directa generada exitosamente. '
                f'{len(materiales_procesados)} materiales procesados. '
                f'Venta registrada por ${simulacion.ingreso_total_venta:.2f}.'
            )
        
        return redirect('inventario:detalle_simulacion', simulacion_id=simulacion.id)
        
    except Simulacion.DoesNotExist:
        messages.error(request, 'Simulación no encontrada.')
        return redirect('inventario:historial_simulaciones')
    except Exception as e:
        messages.error(request, f'Error al generar salida directa: {str(e)}')
        return redirect('inventario:detalle_simulacion', simulacion_id=simulacion_id)


@login_required
def generar_entrada_faltante(request, simulacion_id):
    """
    Genera entradas automáticas solo para los materiales faltantes de una simulación
    """
    try:
        simulacion = Simulacion.objects.get(id=simulacion_id)
        
        materiales_ingresados = []
        costo_total_entradas = 0
        
        for detalle in simulacion.detalles.all():
            material = detalle.material
            cantidad_necesaria = detalle.cantidad_necesaria
            
            if material.cantidad_disponible < cantidad_necesaria:
                cantidad_faltante = cantidad_necesaria - material.cantidad_disponible
                
                # Calcular cantidad a comprar considerando factor de conversión
                if material.factor_conversion > 0:
                    paquetes_necesarios = math.ceil(cantidad_faltante / material.factor_conversion)
                    cantidad_a_comprar = paquetes_necesarios * material.factor_conversion
                else:
                    cantidad_a_comprar = cantidad_faltante
                
                # Registrar entrada
                cantidad_anterior = material.cantidad_disponible
                material.cantidad_disponible += cantidad_a_comprar
                material.save()
                
                costo_entrada = cantidad_a_comprar * material.costo_unitario
                
                # Crear movimiento de entrada
                movimiento = Movimiento.objects.create(
                    material=material,
                    tipo_movimiento='entrada',
                    cantidad=cantidad_a_comprar,
                    cantidad_anterior=cantidad_anterior,
                    cantidad_nueva=material.cantidad_disponible,
                    precio_unitario=material.costo_unitario,
                    costo_total_movimiento=costo_entrada,
                    detalle=f'Entrada automática de faltante - Simulación #{simulacion.id} ({simulacion.monos.nombre})',
                    usuario=request.user,
                    simulacion_relacionada=simulacion
                )
                
                # Registrar movimiento de efectivo automático
                MovimientoEfectivo.registrar_movimiento(
                    concepto=f'Compra automática - {material.nombre} - Simulación #{simulacion.id}',
                    tipo_movimiento='egreso',
                    categoria='inventario',
                    monto=costo_entrada,
                    usuario=request.user,
                    simulacion_relacionada=simulacion,
                    movimiento_inventario=movimiento
                )
                
                materiales_ingresados.append({
                    'material': material.nombre,
                    'faltante': cantidad_faltante,
                    'comprado': cantidad_a_comprar,
                    'costo': costo_entrada,
                    'nuevo_stock': material.cantidad_disponible
                })
                
                costo_total_entradas += costo_entrada
        
        if materiales_ingresados:
            messages.success(
                request,
                f'Entradas generadas exitosamente: {len(materiales_ingresados)} materiales. '
                f'Costo total: ${costo_total_entradas:.2f}'
            )
        else:
            messages.info(request, 'No hay materiales faltantes para esta simulación.')
        
        return redirect('inventario:detalle_simulacion', simulacion_id=simulacion.id)
        
    except Simulacion.DoesNotExist:
        messages.error(request, 'Simulación no encontrada.')
        return redirect('inventario:historial_simulaciones')
    except Exception as e:
        messages.error(request, f'Error al generar entradas faltantes: {str(e)}')
        return redirect('inventario:detalle_simulacion', simulacion_id=simulacion_id)


@login_required
def historial_movimientos(request):
    """Vista para mostrar historial completo de movimientos de inventario"""
    filtro_form = MovimientoFiltroForm(request.GET or None)
    
    movimientos = Movimiento.objects.select_related('material', 'usuario', 'simulacion_relacionada').all()
    
    if filtro_form.is_valid():
        if filtro_form.cleaned_data.get('material'):
            movimientos = movimientos.filter(material=filtro_form.cleaned_data['material'])
        
        if filtro_form.cleaned_data.get('tipo_movimiento'):
            movimientos = movimientos.filter(tipo_movimiento=filtro_form.cleaned_data['tipo_movimiento'])
        
        if filtro_form.cleaned_data.get('fecha_inicio'):
            movimientos = movimientos.filter(fecha__date__gte=filtro_form.cleaned_data['fecha_inicio'])
        
        if filtro_form.cleaned_data.get('fecha_fin'):
            movimientos = movimientos.filter(fecha__date__lte=filtro_form.cleaned_data['fecha_fin'])
        
        if filtro_form.cleaned_data.get('usuario'):
            movimientos = movimientos.filter(usuario=filtro_form.cleaned_data['usuario'])
    
    movimientos = movimientos.order_by('-fecha')
    
    # Calcular estadísticas
    from django.db.models import Count, Sum, Q
    stats = {
        'total_entradas': movimientos.filter(tipo_movimiento='entrada').count(),
        'total_salidas': movimientos.filter(tipo_movimiento='salida').count(),
        'valor_total_entradas': movimientos.filter(
            tipo_movimiento='entrada', 
            precio_unitario__isnull=False
        ).aggregate(
            total=Sum('precio_unitario')
        )['total'] or 0,
        'valor_total_salidas': movimientos.filter(
            tipo_movimiento='salida',
            precio_unitario__isnull=False
        ).aggregate(
            total=Sum('precio_unitario')
        )['total'] or 0,
    }
    
    # Paginación
    paginator = Paginator(movimientos, 50)
    page_number = request.GET.get('page')
    movimientos_paginados = paginator.get_page(page_number)
    
    context = {
        'filtro_form': filtro_form,
        'movimientos': movimientos_paginados,
        'stats': stats,
        'title': 'Historial de Movimientos',
    }
    
    return render(request, 'inventario/historial_movimientos.html', context)


@login_required
def get_material_info_entrada(request, material_id):
    """Vista AJAX para obtener información del material para entrada"""
    try:
        material = Material.objects.get(id=material_id, activo=True)
        data = {
            'nombre': material.nombre,
            'codigo': material.codigo,
            'tipo_material': material.get_tipo_material_display(),
            'unidad_base': material.get_unidad_base_display(),
            'factor_conversion': material.factor_conversion,
            'cantidad_disponible': float(material.cantidad_disponible),
            'precio_compra_anterior': float(material.precio_compra),
            'costo_unitario_actual': float(material.costo_unitario),
        }
        return JsonResponse(data)
    except Material.DoesNotExist:
        return JsonResponse({'error': 'Material no encontrado'}, status=404)


def registrar_movimiento_produccion(material, cantidad_usada, simulacion, usuario=None, detalle_extra=""):
    """
    Función auxiliar para registrar movimientos por producción
    Usado por el sistema de simulaciones cuando se confirma una producción
    """
    if cantidad_usada <= 0:
        return None
    
    if material.cantidad_disponible < cantidad_usada:
        raise ValueError(f"No hay suficiente stock de {material.nombre}")
    
    # Actualizar stock
    cantidad_anterior = material.cantidad_disponible
    material.cantidad_disponible -= cantidad_usada
    material.save()
    
    # Registrar movimiento
    detalle = f"Producción: {simulacion.monos.nombre} (x{simulacion.cantidad_producir})"
    if detalle_extra:
        detalle += f" - {detalle_extra}"
    
    movimiento = Movimiento.objects.create(
        material=material,
        tipo_movimiento='produccion',
        cantidad=-cantidad_usada,  # Negativo para salida
        cantidad_anterior=cantidad_anterior,
        cantidad_nueva=material.cantidad_disponible,
        precio_unitario=material.costo_unitario,
        costo_total_movimiento=cantidad_usada * material.costo_unitario,
        detalle=detalle,
        usuario=usuario,
        simulacion_relacionada=simulacion
    )
    
    return movimiento


# Vistas AJAX para entrada/salida
@login_required
def material_info_entrada(request, material_id):
    """Información del material para entrada"""
    try:
        material = Material.objects.get(id=material_id, activo=True)
        return JsonResponse({
            'codigo': material.codigo,
            'nombre': material.nombre,
            'tipo_material': material.tipo_material,
            'unidad_base': material.unidad_base,
            'cantidad_disponible': float(material.cantidad_disponible),
            'factor_conversion': float(material.factor_conversion),
            'costo_unitario': float(material.costo_unitario or 0)
        })
    except Material.DoesNotExist:
        return JsonResponse({'error': 'Material no encontrado'}, status=404)


@login_required
def material_info_salida(request, material_id):
    """Información del material para salida"""
    try:
        material = Material.objects.get(id=material_id, activo=True)
        
        # Calcular costo promedio de movimientos recientes
        movimientos_entrada = Movimiento.objects.filter(
            material=material,
            tipo_movimiento='entrada'
        ).exclude(precio_unitario__isnull=True).order_by('-fecha_movimiento')[:10]
        
        costo_promedio = None
        if movimientos_entrada:
            total_costo = sum(m.precio_unitario for m in movimientos_entrada)
            costo_promedio = total_costo / len(movimientos_entrada)
        
        return JsonResponse({
            'codigo': material.codigo,
            'nombre': material.nombre,
            'tipo_material': material.tipo_material,
            'unidad_base': material.unidad_base,
            'cantidad_disponible': float(material.cantidad_disponible),
            'costo_promedio': float(costo_promedio) if costo_promedio else None,
            'costo_unitario': float(material.costo_unitario or 0)
        })
    except Material.DoesNotExist:
        return JsonResponse({'error': 'Material no encontrado'}, status=404)


@login_required
def detalle_movimiento_ajax(request, movimiento_id):
    """Detalle completo de un movimiento"""
    try:
        movimiento = Movimiento.objects.select_related(
            'material', 'usuario', 'simulacion_relacionada'
        ).get(id=movimiento_id)
        
        data = {
            'id': movimiento.id,
            'fecha_movimiento': movimiento.fecha.strftime('%d/%m/%Y %H:%M'),
            'tipo_movimiento': movimiento.tipo_movimiento,
            'tipo_movimiento_display': movimiento.get_tipo_movimiento_display(),
            'cantidad': float(movimiento.cantidad),
            'precio_unitario': float(movimiento.precio_unitario) if movimiento.precio_unitario else None,
            'detalle': movimiento.detalle,
            'usuario': f"{movimiento.usuario.first_name} {movimiento.usuario.last_name}" if movimiento.usuario and movimiento.usuario.first_name else movimiento.usuario.username if movimiento.usuario else 'Sistema',
            'material': {
                'codigo': movimiento.material.codigo,
                'nombre': movimiento.material.nombre,
                'tipo_material': movimiento.material.tipo_material,
                'unidad_base': movimiento.material.unidad_base,
            }
        }
        
        if movimiento.simulacion_relacionada:
            data['simulacion'] = {
                'id': movimiento.simulacion_relacionada.id,
                'fecha_simulacion': movimiento.simulacion_relacionada.fecha_simulacion.strftime('%d/%m/%Y %H:%M'),
            }
        
        return JsonResponse(data)
        
    except Movimiento.DoesNotExist:
        return JsonResponse({'error': 'Movimiento no encontrado'}, status=404)


# Vistas de integración Simulación-Inventario
@login_required
def confirmar_produccion(request, simulacion_id):
    """Confirma la producción y registra salidas de materiales"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        simulacion = Simulacion.objects.get(id=simulacion_id)
        
        # Verificar que hay suficientes materiales
        detalles = simulacion.detalles.all()
        materiales_insuficientes = []
        
        for detalle in detalles:
            if detalle.material.cantidad_disponible < detalle.cantidad_necesaria:
                materiales_insuficientes.append({
                    'material': detalle.material.nombre,
                    'disponible': float(detalle.material.cantidad_disponible),
                    'necesaria': float(detalle.cantidad_necesaria),
                    'faltante': float(detalle.cantidad_necesaria - detalle.material.cantidad_disponible)
                })
        
        if materiales_insuficientes:
            return JsonResponse({
                'success': False,
                'error': 'Materiales insuficientes',
                'materiales_insuficientes': materiales_insuficientes
            })
        
        # Ejecutar producción: registrar movimientos de salida
        movimientos_creados = []
        
        for detalle in detalles:
            material = detalle.material
            cantidad_anterior = material.cantidad_disponible
            
            # Actualizar inventario
            material.cantidad_disponible -= detalle.cantidad_necesaria
            material.save()
            
            # Registrar movimiento
            movimiento = Movimiento.objects.create(
                material=material,
                tipo_movimiento='produccion',
                cantidad=detalle.cantidad_necesaria,
                cantidad_anterior=cantidad_anterior,
                cantidad_nueva=material.cantidad_disponible,
                precio_unitario=material.costo_unitario,
                costo_total_movimiento=detalle.cantidad_necesaria * material.costo_unitario if material.costo_unitario else None,
                detalle=f"Producción de {simulacion.cantidad_total_monos} moños ({simulacion.monos.nombre}) - Simulación #{simulacion.id}",
                usuario=request.user,
                simulacion_relacionada=simulacion
            )
            
            movimientos_creados.append({
                'material': material.nombre,
                'cantidad_usada': float(detalle.cantidad_necesaria),
                'unidad': material.unidad_base
            })
        
        mensaje_detalle = f"Producción de {simulacion.cantidad_total_monos} moños completada.\n\nMateriales utilizados:\n"
        for mov in movimientos_creados:
            mensaje_detalle += f"• {mov['material']}: {mov['cantidad_usada']} {mov['unidad']}\n"
        
        return JsonResponse({
            'success': True,
            'mensaje': mensaje_detalle,
            'movimientos_creados': len(movimientos_creados)
        })
        
    except Simulacion.DoesNotExist:
        return JsonResponse({'error': 'Simulación no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)


@login_required
def reabastecer_automatico(request, simulacion_id):
    """Reabastece automáticamente los materiales faltantes para una simulación"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        simulacion = Simulacion.objects.get(id=simulacion_id)
        detalles = simulacion.detalles.all()
        
        # Identificar materiales que necesitan reabastecimiento
        reabastecimientos = []
        costo_total_reabastecimiento = 0
        
        for detalle in detalles:
            material = detalle.material
            cantidad_faltante = detalle.cantidad_necesaria - material.cantidad_disponible
            
            if cantidad_faltante > 0:
                # Calcular cantidad a comprar en unidades completas
                if material.tipo_material == 'paquete':
                    unidades_a_comprar = math.ceil(cantidad_faltante / material.factor_conversion)
                elif material.tipo_material == 'rollo':
                    unidades_a_comprar = math.ceil(cantidad_faltante / material.factor_conversion)
                else:
                    unidades_a_comprar = math.ceil(cantidad_faltante)
                
                # Cantidad en unidad base que se agregará
                cantidad_en_unidad_base = unidades_a_comprar * material.factor_conversion
                
                # Costo estimado (usando el costo unitario actual)
                costo_unitario = material.costo_unitario or Decimal('0')
                precio_compra_total = cantidad_en_unidad_base * costo_unitario
                
                # Actualizar inventario
                cantidad_anterior = material.cantidad_disponible
                material.cantidad_disponible += cantidad_en_unidad_base
                
                # Actualizar precio de compra y costo unitario si es necesario
                if costo_unitario > 0:
                    material.precio_compra = precio_compra_total
                
                material.save()
                
                # Registrar movimiento de entrada
                movimiento = Movimiento.objects.create(
                    material=material,
                    tipo_movimiento='entrada',
                    cantidad=cantidad_en_unidad_base,
                    cantidad_anterior=cantidad_anterior,
                    cantidad_nueva=material.cantidad_disponible,
                    precio_unitario=costo_unitario,
                    costo_total_movimiento=precio_compra_total,
                    detalle=f"Reabastecimiento automático para simulación #{simulacion.id} - {unidades_a_comprar} {material.tipo_material}(s)",
                    usuario=request.user
                )
                
                reabastecimientos.append({
                    'material': material.nombre,
                    'unidades_compradas': unidades_a_comprar,
                    'tipo_unidad': material.tipo_material,
                    'cantidad_agregada': float(cantidad_en_unidad_base),
                    'unidad_base': material.unidad_base,
                    'costo': float(precio_compra_total)
                })
                
                costo_total_reabastecimiento += precio_compra_total
        
        if not reabastecimientos:
            return JsonResponse({
                'success': False,
                'error': 'No hay materiales que requieran reabastecimiento'
            })
        
        mensaje_detalle = f"Reabastecimiento automático completado.\n\nMateriales reabastecidos:\n"
        for reab in reabastecimientos:
            mensaje_detalle += f"• {reab['material']}: {reab['unidades_compradas']} {reab['tipo_unidad']}(s) = {reab['cantidad_agregada']} {reab['unidad_base']} (${reab['costo']:.2f})\n"
        
        mensaje_detalle += f"\nCosto total: ${costo_total_reabastecimiento:.2f}"
        
        return JsonResponse({
            'success': True,
            'mensaje': mensaje_detalle,
            'reabastecimientos': len(reabastecimientos),
            'costo_total': float(costo_total_reabastecimiento)
        })
        
    except Simulacion.DoesNotExist:
        return JsonResponse({'error': 'Simulación no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

