from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
import math
from .models import (Material, Movimiento, ConfiguracionSistema, Monos, RecetaMonos, 
                   Simulacion, DetalleSimulacion, MovimientoEfectivo, ListaProduccion,
                   DetalleListaMonos, ResumenMateriales)
from .forms import (MaterialForm, MonosForm, RecetaMonosFormSet, SimulacionForm, 
                   SimulacionBusquedaForm, EntradaMaterialForm, SalidaMaterialForm, MovimientoFiltroForm,
                   EntradaDesdeSimulacionForm, SalidaDesdeSimulacionForm, MovimientoEfectivoForm, 
                   FiltroMovimientosEfectivoForm, ListaProduccionForm, DetalleListaMonosFormSet)
from django.core.paginator import Paginator
from decimal import Decimal
import math

# Importar vistas de contaduría
from .views_contaduria import contaduria_home, flujo_efectivo, registrar_movimiento_efectivo, estado_resultados, exportar_excel_efectivo


def home(request):
    """Vista principal del sistema"""
    # Verificar si hay materiales, si no, crear algunos básicos
    if not Material.objects.exists():
        _crear_materiales_basicos()
    
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


def _crear_materiales_basicos():
    """Crea algunos materiales básicos si la base de datos está vacía"""
    materiales_basicos = [
        {
            'codigo': 'M001',
            'nombre': 'Listón Rojo',
            'descripcion': 'Listón de tela roja de 1 cm de ancho',
            'tipo_material': 'liston',
            'unidad_base': 'metros',
            'factor_conversion': 10,
            'cantidad_disponible': Decimal('50.00'),
            'precio_compra': Decimal('15.00'),
            'categoria': 'listón'
        },
        {
            'codigo': 'M002',
            'nombre': 'Perla Blanca',
            'descripcion': 'Perlas blancas para decoración',
            'tipo_material': 'piedra',
            'unidad_base': 'unidades',
            'factor_conversion': 100,
            'cantidad_disponible': Decimal('200.00'),
            'precio_compra': Decimal('25.00'),
            'categoria': 'piedra'
        },
        {
            'codigo': 'M003',
            'nombre': 'Flor Rosa',
            'descripcion': 'Flores artificiales pequeñas',
            'tipo_material': 'adorno',
            'unidad_base': 'unidades',
            'factor_conversion': 20,
            'cantidad_disponible': Decimal('40.00'),
            'precio_compra': Decimal('12.00'),
            'categoria': 'adorno'
        }
    ]
    
    for material_data in materiales_basicos:
        Material.objects.create(**material_data)


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
    try:
        material = get_object_or_404(Material, id=material_id, activo=True)
    except:
        messages.error(request, f'No se encontró un material con ID {material_id}. Puede que haya sido eliminado o no exista.')
        return redirect('inventario:lista_materiales')
    
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


# ================ VISTAS AJAX ================

@login_required
def obtener_info_material(request, material_id):
    """Vista AJAX para obtener información del material"""
    try:
        material = Material.objects.get(id=material_id, activo=True)
        data = {
            'unidad_base': material.unidad_base,
            'precio_unitario': float(material.costo_unitario),
            'nombre': material.nombre,
            'disponible': float(material.cantidad_disponible)
        }
        return JsonResponse(data)
    except Material.DoesNotExist:
        return JsonResponse({'error': 'Material no encontrado'}, status=404)

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
        
        # Debug: Imprimir los datos del POST para ver qué estamos recibiendo
        print("=== DEBUG POST DATA ===")
        for key, value in request.POST.items():
            print(f"{key}: {value}")
        print("=== END DEBUG ===")
        
        # Debug específico del formset
        print("=== FORMSET DEBUG ===")
        recetas_keys = [key for key in request.POST.keys() if 'recetas-' in key]
        print(f"Keys relacionadas con formset: {recetas_keys}")
        print("=== END FORMSET DEBUG ===")
        
        # Validar formulario principal
        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
        
        # Validación manual de recetas sin usar formset.is_valid() (que causa el error)
        recetas_validas = []
        recetas_con_errores = []
        
        # Obtener número total de formularios
        total_forms = int(request.POST.get('recetas-TOTAL_FORMS', 0))
        
        for i in range(total_forms):
            material_id = request.POST.get(f'recetas-{i}-material')
            cantidad = request.POST.get(f'recetas-{i}-cantidad_necesaria')
            
            # Si hay datos en este formulario, validarlos
            if material_id or cantidad:
                errores_form = []
                
                if not material_id:
                    errores_form.append(f'Receta #{i+1}: Debe seleccionar un material')
                else:
                    try:
                        material = Material.objects.get(id=int(material_id), activo=True)
                    except (ValueError, Material.DoesNotExist):
                        errores_form.append(f'Receta #{i+1}: Material inválido')
                        material = None
                
                if not cantidad:
                    errores_form.append(f'Receta #{i+1}: Debe especificar la cantidad')
                else:
                    try:
                        cantidad_decimal = Decimal(str(cantidad))
                        if cantidad_decimal <= 0:
                            errores_form.append(f'Receta #{i+1}: La cantidad debe ser mayor a 0')
                    except:
                        errores_form.append(f'Receta #{i+1}: Cantidad inválida')
                        cantidad_decimal = None
                
                if errores_form:
                    recetas_con_errores.extend(errores_form)
                elif material and cantidad_decimal:
                    recetas_validas.append({
                        'material': material,
                        'cantidad': cantidad_decimal
                    })
        
        # Deduplicar materiales (en caso de que haya duplicados en el formset)
        materiales_unicos = {}
        for receta in recetas_validas:
            material_id = receta['material'].id
            if material_id in materiales_unicos:
                # Si ya existe, usar la cantidad más reciente (última encontrada)
                print(f"⚠️  DUPLICADO detectado en creación: Material {material_id}, reemplazando cantidad {materiales_unicos[material_id]['cantidad']} por {receta['cantidad']}")
            materiales_unicos[material_id] = receta
        
        # Convertir de vuelta a lista sin duplicados
        recetas_validas = list(materiales_unicos.values())
        print(f"📋 Recetas después de deduplicar en creación: {[(r['material'].id, r['cantidad']) for r in recetas_validas]}")
        
        # Mostrar errores de recetas
        for error in recetas_con_errores:
            messages.error(request, error)
        
        # Verificar que hay al menos una receta válida
        if len(recetas_validas) == 0:
            messages.error(request, 'Debe agregar al menos un material a la receta del moño.')
        
        if form.is_valid() and len(recetas_con_errores) == 0 and len(recetas_validas) > 0:
            try:
                # 1. Primero guardar el moño
                monos = form.save()
                
                # 2. Guardar recetas usando los datos validados manualmente
                recetas_guardadas = 0
                for receta_data in recetas_validas:
                    RecetaMonos.objects.create(
                        monos=monos,
                        material=receta_data['material'],
                        cantidad_necesaria=receta_data['cantidad']
                    )
                    recetas_guardadas += 1
                
                messages.success(request, f'Moño {monos.codigo} agregado exitosamente con {recetas_guardadas} material(es).')
                return redirect('inventario:detalle_monos', monos_id=monos.id)
                    
            except Exception as e:
                # Si hay error, intentar eliminar el moño si fue creado
                try:
                    if 'monos' in locals():
                        monos.delete()
                except:
                    pass
                messages.error(request, f'Error al guardar: {str(e)}')
                print("Exception:", str(e))
    else:
        form = MonosForm()
        temp_monos = Monos()  # Instancia temporal sin guardar
        formset = RecetaMonosFormSet(instance=temp_monos)
    
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
    
    # Crear formset siempre (para el contexto)
    if request.method == 'POST':
        formset = RecetaMonosFormSet(request.POST, instance=monos)
    else:
        formset = RecetaMonosFormSet(instance=monos)
    
    if request.method == 'POST':
        form = MonosForm(request.POST, instance=monos)
        
        # Validar formulario principal
        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
        
        # Validación manual de recetas (misma lógica que en creación)
        recetas_validas = []
        recetas_con_errores = []
        
        # Obtener número total de formularios
        total_forms = int(request.POST.get('recetas-TOTAL_FORMS', 0))
        
        for i in range(total_forms):
            material_id = request.POST.get(f'recetas-{i}-material')
            cantidad = request.POST.get(f'recetas-{i}-cantidad_necesaria')
            delete_flag = request.POST.get(f'recetas-{i}-DELETE')
            receta_id = request.POST.get(f'recetas-{i}-id')
            
            # Si está marcado para eliminar, ignorar validación
            if delete_flag:
                continue
                
            # Si hay datos en este formulario, validarlos
            if material_id or cantidad:
                errores_form = []
                
                if not material_id:
                    errores_form.append(f'Receta #{i+1}: Debe seleccionar un material')
                else:
                    try:
                        material = Material.objects.get(id=int(material_id), activo=True)
                    except (ValueError, Material.DoesNotExist):
                        errores_form.append(f'Receta #{i+1}: Material inválido')
                        material = None
                
                if not cantidad:
                    errores_form.append(f'Receta #{i+1}: Debe especificar la cantidad')
                else:
                    try:
                        cantidad_decimal = Decimal(str(cantidad))
                        if cantidad_decimal <= 0:
                            errores_form.append(f'Receta #{i+1}: La cantidad debe ser mayor a 0')
                    except:
                        errores_form.append(f'Receta #{i+1}: Cantidad inválida')
                        cantidad_decimal = None
                
                if errores_form:
                    recetas_con_errores.extend(errores_form)
                elif material and cantidad_decimal:
                    recetas_validas.append({
                        'material': material,
                        'cantidad': cantidad_decimal,
                        'id': receta_id  # Para saber si es nueva o existente
                    })
        
        # Deduplicar materiales (en caso de que haya duplicados en el formset)
        materiales_unicos = {}
        for receta in recetas_validas:
            material_id = receta['material'].id
            if material_id in materiales_unicos:
                # Si ya existe, usar la cantidad más reciente (última encontrada)
                print(f"⚠️  DUPLICADO detectado: Material {material_id}, reemplazando cantidad {materiales_unicos[material_id]['cantidad']} por {receta['cantidad']}")
            materiales_unicos[material_id] = receta
        
        # Convertir de vuelta a lista sin duplicados
        recetas_validas = list(materiales_unicos.values())
        print(f"📋 Recetas después de deduplicar: {[(r['material'].id, r['cantidad']) for r in recetas_validas]}")
        
        # Mostrar errores de recetas
        for error in recetas_con_errores:
            messages.error(request, error)
        
        # Verificar que hay al menos una receta válida
        if len(recetas_validas) == 0:
            messages.error(request, 'Debe tener al menos un material en la receta del moño.')
        
        if form.is_valid() and len(recetas_con_errores) == 0 and len(recetas_validas) > 0:
            try:
                from django.db import transaction
                
                with transaction.atomic():
                    # 1. Actualizar el moño
                    monos_actualizado = form.save()
                    
                    # 2. Debug: ver recetas existentes antes de eliminar
                    recetas_existentes = RecetaMonos.objects.filter(monos=monos_actualizado)
                    print(f"Recetas existentes antes de eliminar: {list(recetas_existentes.values_list('material_id', 'cantidad_necesaria'))}")
                    
                    # 3. Eliminar todas las recetas existentes
                    eliminadas = recetas_existentes.delete()
                    print(f"Recetas eliminadas: {eliminadas}")
                    
                    # 4. Verificar que no quedan recetas
                    verificacion = RecetaMonos.objects.filter(monos=monos_actualizado).count()
                    print(f"Recetas restantes después de eliminar: {verificacion}")
                    
                    if verificacion > 0:
                        raise Exception(f"Error: Aún quedan {verificacion} recetas después de la eliminación")
                    
                    # 5. Crear todas las recetas nuevamente
                    recetas_guardadas = 0
                    for receta_data in recetas_validas:
                        print(f"Creando receta: Material {receta_data['material'].id}, Cantidad {receta_data['cantidad']}")
                        RecetaMonos.objects.create(
                            monos=monos_actualizado,
                            material=receta_data['material'],
                            cantidad_necesaria=receta_data['cantidad']
                        )
                        recetas_guardadas += 1
                
                messages.success(request, f'Moño {monos_actualizado.codigo} actualizado exitosamente con {recetas_guardadas} material(es).')
                return redirect('inventario:detalle_monos', monos_id=monos_actualizado.id)
                
            except Exception as e:
                messages.error(request, f'Error al actualizar: {str(e)}')
                print("Exception en edición:", str(e))
    else:
        form = MonosForm(instance=monos)
    
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


# ============================================================================
# VISTAS DE LISTAS DE PRODUCCIÓN - NUEVO SISTEMA
# ============================================================================

@login_required
def crear_lista_produccion(request):
    """Vista para crear una nueva lista de producción con múltiples moños"""
    
    if request.method == 'POST':
        form = ListaProduccionForm(request.POST)
        formset = DetalleListaMonosFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            try:
                from django.db import transaction
                
                with transaction.atomic():
                    # 1. Crear la lista de producción
                    lista = form.save(commit=False)
                    lista.usuario_creador = request.user
                    lista.save()
                    
                    # 2. Procesar moños del formset
                    moños_agregados = 0
                    total_moños_planificados = 0
                    
                    for form_detalle in formset:
                        if form_detalle.cleaned_data and not form_detalle.cleaned_data.get('DELETE', False):
                            monos = form_detalle.cleaned_data['monos']
                            cantidad = form_detalle.cleaned_data.get('cantidad', 0)
                            
                            if cantidad > 0:
                                # Crear detalle de moños
                                detalle = DetalleListaMonos.objects.create(
                                    lista_produccion=lista,
                                    monos=monos,
                                    cantidad=cantidad
                                )
                                moños_agregados += 1
                                total_moños_planificados += detalle.cantidad_total_planificada
                    
                    if moños_agregados == 0:
                        raise ValueError("Debe agregar al menos un moño a la lista")
                    
                    # 3. Actualizar totales de la lista
                    lista.total_moños_planificados = total_moños_planificados
                    
                    # 4. Calcular materiales necesarios
                    calcular_materiales_necesarios(lista)
                    
                    # 5. Calcular costos estimados
                    calcular_costos_estimados(lista)
                    
                    # 6. Verificar si hay materiales suficientes y ajustar estado automáticamente
                    materiales_suficientes, mensaje_verificacion = verificar_materiales_suficientes(lista)
                    
                    if materiales_suficientes:
                        # Hay suficientes materiales, saltar directamente a reabastecido (Paso 4)
                        lista.estado = 'reabastecido'
                        lista.save()
                        mensaje_estado = " La lista está lista para producción (todos los materiales disponibles)."
                        messages.success(request, f'Lista de producción "{lista.nombre}" creada exitosamente con {moños_agregados} tipo(s) de moños.{mensaje_estado}')
                        return redirect('inventario:panel_lista_produccion', lista_id=lista.id)
                    else:
                        # Faltan materiales, ir a paso de compras (Paso 2)
                        lista.estado = 'pendiente_compra'
                        lista.save()
                        materiales_faltantes = lista.resumen_materiales.filter(cantidad_faltante__gt=0).count()
                        mensaje_estado = f" Se requiere comprar {materiales_faltantes} material(es)."
                        messages.success(request, f'Lista de producción "{lista.nombre}" creada exitosamente con {moños_agregados} tipo(s) de moños.{mensaje_estado}')
                        return redirect('inventario:lista_de_compras')
                    
            except Exception as e:
                messages.error(request, f'Error al crear la lista: {str(e)}')
                print(f"Error creando lista de producción: {str(e)}")
        
        else:
            # Mostrar errores del formulario
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'Error en {field}: {error}')
            
            # Mostrar errores del formset
            if not formset.is_valid():
                for i, form_errors in enumerate(formset.errors):
                    if form_errors:
                        for field, errors in form_errors.items():
                            for error in errors:
                                messages.error(request, f'Error en moño #{i+1} - {field}: {error}')
    
    else:
        form = ListaProduccionForm()
        formset = DetalleListaMonosFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'titulo': 'Crear Lista de Producción',
        'moños_disponibles': Monos.objects.filter(activo=True).order_by('nombre')
    }
    
    return render(request, 'inventario/crear_lista_produccion.html', context)


def calcular_materiales_necesarios(lista_produccion):
    """Calcula los materiales necesarios para una lista de producción"""
    
    # Eliminar resúmenes existentes
    ResumenMateriales.objects.filter(lista_produccion=lista_produccion).delete()
    
    materiales_totales = {}
    
    # Recorrer todos los moños de la lista
    for detalle in lista_produccion.detalles_monos.all():
        monos = detalle.monos
        cantidad_total = detalle.cantidad_total_planificada
        
        # Obtener receta del moño
        recetas = monos.recetas.all()
        
        for receta in recetas:
            material = receta.material
            cantidad_por_mono = receta.cantidad_necesaria
            cantidad_total_material = cantidad_por_mono * cantidad_total
            
            if material.id in materiales_totales:
                materiales_totales[material.id]['cantidad_necesaria'] += cantidad_total_material
            else:
                materiales_totales[material.id] = {
                    'material': material,
                    'cantidad_necesaria': cantidad_total_material,
                    'cantidad_disponible': material.cantidad_disponible,
                    'cantidad_faltante': max(0, cantidad_total_material - material.cantidad_disponible)
                }
    
    # Crear registros de ResumenMateriales
    for material_data in materiales_totales.values():
        ResumenMateriales.objects.create(
            lista_produccion=lista_produccion,
            material=material_data['material'],
            cantidad_necesaria=material_data['cantidad_necesaria'],
            cantidad_disponible=material_data['cantidad_disponible'],
            cantidad_faltante=material_data['cantidad_faltante']
        )


def calcular_costos_estimados(lista_produccion):
    """Calcula los costos y ganancias estimadas de la lista"""
    
    costo_total = Decimal('0')
    ganancia_estimada = Decimal('0')
    
    # Calcular costo de materiales
    for resumen in lista_produccion.resumen_materiales.all():
        if resumen.material.precio_compra > 0:
            # Calcular costo unitario del material
            costo_unitario = resumen.material.precio_compra / resumen.material.factor_conversion
            costo_material = costo_unitario * resumen.cantidad_necesaria
            costo_total += costo_material
    
    # Calcular ganancia estimada por moños
    for detalle in lista_produccion.detalles_monos.all():
        precio_por_mono = detalle.monos.precio_venta
        cantidad_total = detalle.cantidad_total_planificada
        ingreso_por_mono = precio_por_mono * cantidad_total
        ganancia_estimada += ingreso_por_mono
    
    # Actualizar la lista
    lista_produccion.costo_total_estimado = costo_total
    lista_produccion.ganancia_estimada = ganancia_estimada - costo_total


def verificar_materiales_suficientes(lista_produccion):
    """Verifica si hay suficientes materiales en inventario para la lista de producción"""
    
    # Recalcular materiales necesarios para estar seguro
    calcular_materiales_necesarios(lista_produccion)
    
    # Verificar cada material
    for resumen in lista_produccion.resumen_materiales.all():
        # Obtener la cantidad disponible actual del material
        cantidad_actual_disponible = resumen.material.cantidad_disponible
        
        # Verificar si hay suficiente material disponible
        if resumen.cantidad_necesaria > cantidad_actual_disponible:
            return False, f"Material {resumen.material.nombre}: se necesita {resumen.cantidad_necesaria} {resumen.material.unidad_base}, pero solo hay {cantidad_actual_disponible} disponible"
    
    return True, "Todos los materiales están disponibles"


@login_required
def editar_lista_produccion(request, lista_id):
    """Vista para editar una lista de producción existente"""
    
    lista = get_object_or_404(ListaProduccion, id=lista_id, usuario_creador=request.user)
    
    if request.method == 'POST':
        form = ListaProduccionForm(request.POST, instance=lista)
        formset = DetalleListaMonosFormSet(request.POST, instance=lista)
        
        if form.is_valid() and formset.is_valid():
            try:
                from django.db import transaction
                
                with transaction.atomic():
                    # 1. Actualizar la lista de producción
                    lista = form.save()
                    
                    # 2. Procesar moños del formset
                    moños_agregados = 0
                    total_moños_planificados = 0
                    
                    # Primero guardar el formset para manejar deletes
                    formset.save()
                    
                    # Recalcular totales
                    for detalle in lista.detalles_monos.all():
                        moños_agregados += 1
                        total_moños_planificados += detalle.cantidad_total_planificada
                    
                    if moños_agregados == 0:
                        raise ValueError("Debe mantener al menos un moño en la lista")
                    
                    # 3. Actualizar totales de la lista
                    lista.total_moños_planificados = total_moños_planificados
                    
                    # 4. Recalcular materiales necesarios
                    calcular_materiales_necesarios(lista)
                    
                    # 5. Recalcular costos estimados
                    calcular_costos_estimados(lista)
                    
                    lista.save()
                    
                    messages.success(request, f'Lista de producción "{lista.nombre}" actualizada exitosamente.')
                    return redirect('inventario:detalle_lista_produccion', lista_id=lista.id)
                    
            except Exception as e:
                messages.error(request, f'Error al actualizar la lista: {str(e)}')
                print(f"Error editando lista de producción: {str(e)}")
        
        else:
            # Mostrar errores del formulario
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'Error en {field}: {error}')
            
            # Mostrar errores del formset
            if not formset.is_valid():
                for i, form_errors in enumerate(formset.errors):
                    if form_errors:
                        for field, errors in form_errors.items():
                            for error in errors:
                                messages.error(request, f'Error en moño #{i+1} - {field}: {error}')
    
    else:
        form = ListaProduccionForm(instance=lista)
        formset = DetalleListaMonosFormSet(instance=lista)
    
    context = {
        'form': form,
        'formset': formset,
        'lista': lista,
        'titulo': f'Editar Lista: {lista.nombre}',
        'moños_disponibles': Monos.objects.filter(activo=True).order_by('nombre'),
        'editando': True
    }
    
    return render(request, 'inventario/crear_lista_produccion.html', context)


@login_required
def eliminar_lista_produccion(request, lista_id):
    """Vista para eliminar una lista de producción"""
    
    lista = get_object_or_404(ListaProduccion, id=lista_id, usuario_creador=request.user)
    
    if request.method == 'POST':
        nombre_lista = lista.nombre
        
        # Verificar si se puede eliminar según el estado
        estados_no_eliminables = ['en_produccion']
        if lista.estado in estados_no_eliminables:
            messages.error(request, f'No se puede eliminar la lista "{nombre_lista}" porque está en producción.')
            return redirect('inventario:detalle_lista_produccion', lista_id=lista.id)
        
        try:
            # Eliminar la lista y todos sus datos relacionados
            lista.delete()
            messages.success(request, f'Lista de producción "{nombre_lista}" eliminada exitosamente.')
            return redirect('inventario:listas_produccion')
            
        except Exception as e:
            messages.error(request, f'Error al eliminar la lista: {str(e)}')
            return redirect('inventario:detalle_lista_produccion', lista_id=lista.id)
    
    # Si es GET, mostrar página de confirmación
    context = {
        'lista': lista,
        'titulo': f'Eliminar Lista: {lista.nombre}'
    }
    
    return render(request, 'inventario/eliminar_lista_produccion.html', context)


@login_required  
def generar_archivo_compras(request, lista_id):
    """Generar archivo TXT simple con lista de compras (solo material y cantidad)"""
    from django.http import HttpResponse
    from datetime import datetime
    
    lista = get_object_or_404(ListaProduccion, id=lista_id, usuario_creador=request.user)
    
    # Obtener materiales faltantes
    materiales_faltantes = lista.resumen_materiales.filter(cantidad_faltante__gt=0)
    
    # Generar contenido simple
    contenido = f"LISTA DE COMPRAS - {lista.nombre}\n"
    contenido += f"Fecha: {datetime.now().strftime('%d/%m/%Y')}\n\n"
    
    contenido += "MATERIALES A COMPRAR:\n"
    contenido += "="*50 + "\n\n"
    
    if materiales_faltantes.exists():
        for resumen in materiales_faltantes:
            material = resumen.material
            paquetes_necesarios = resumen.paquetes_rollos_necesarios
            unidad = resumen.unidad_compra_display
            
            # Formato simple: Material - Cantidad Paquetes/Rollos
            contenido += f"{material.nombre} - {paquetes_necesarios} {unidad}{'s' if paquetes_necesarios > 1 else ''}\n"
    else:
        contenido += "No hay materiales faltantes.\n"
    
    contenido += "\n" + "="*50 + "\n\n"
    contenido += "MOÑOS A PRODUCIR:\n"
    contenido += "="*50 + "\n\n"
    
    for detalle in lista.detalles_monos.all():
        contenido += f"{detalle.monos.nombre} - {detalle.cantidad_total_planificada} unidades\n"
    
    # Crear respuesta HTTP con archivo
    response = HttpResponse(contenido, content_type='text/plain; charset=utf-8')
    filename = f"compras_{lista.nombre.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Cambiar estado a comprado cuando se descarga (Paso 2 → Paso 3)
    if lista.estado == 'pendiente_compra':
        lista.estado = 'comprado'
        lista.save()
        messages.success(request, f'Lista "{lista.nombre}" descargada. Ahora pasa al Paso 3 para registrar tus compras.')
    
    return response


@login_required
@login_required
def marcar_como_comprado(request, lista_id):
    """Cambiar estado de una lista de 'pendiente_compra' a 'comprado'"""
    
    if request.method == 'POST':
        try:
            lista = get_object_or_404(ListaProduccion, id=lista_id, usuario_creador=request.user)
            
            # Verificar que esté en estado correcto
            if lista.estado != 'pendiente_compra':
                messages.error(request, f'La lista "{lista.nombre}" debe estar en estado "Pendiente de Compra" para marcar como comprado.')
                return redirect('inventario:detalle_lista_produccion', lista_id=lista.id)
            
            # Cambiar estado a comprado
            lista.estado = 'comprado'
            lista.save()
            
            messages.success(request, f'Lista "{lista.nombre}" marcada como comprada. Ahora puede registrar las compras en "Compra de Productos".')
            return redirect('inventario:detalle_lista_produccion', lista_id=lista.id)
            
        except Exception as e:
            messages.error(request, f'Error al marcar como comprado: {str(e)}')
            return redirect('inventario:detalle_lista_produccion', lista_id=lista.id)
    
    return redirect('inventario:lista_de_compras')


@login_required
def verificar_compras(request, lista_id):
    """Vista simple para ingresar cuántos paquetes/rollos se compraron realmente"""
    
    lista = get_object_or_404(ListaProduccion, id=lista_id, usuario_creador=request.user)
    
    # Solo disponible para listas en estado 'comprado' (Paso 3)
    if lista.estado != 'comprado':
        messages.warning(request, f'La lista "{lista.nombre}" no está en Paso 3 (Comprado).')
        return redirect('inventario:listado_compras_paso3')
    
    materiales_necesarios = lista.resumen_materiales.filter(cantidad_faltante__gt=0).select_related('material')
    
    if request.method == 'POST':
        try:
            materiales_procesados = 0
            materiales_registrados = 0
            
            for resumen in materiales_necesarios:
                # Obtener cantidad comprada ingresada por el usuario
                cantidad_comprada_key = f'cantidad_comprada_{resumen.id}'
                cantidad_comprada_str = request.POST.get(cantidad_comprada_key, '0').strip()
                
                if not cantidad_comprada_str or cantidad_comprada_str == '0':
                    continue  # Material no comprado, saltar
                
                try:
                    paquetes_comprados = int(cantidad_comprada_str)
                    
                    if paquetes_comprados < 0:
                        messages.warning(request, f'Cantidad inválida para {resumen.material.nombre}')
                        continue
                    
                    if paquetes_comprados > 0:
                        # Calcular cantidad en unidad base
                        cantidad_total = paquetes_comprados * resumen.material.factor_conversion
                        
                        # Guardar cantidad anterior para el movimiento
                        cantidad_anterior = resumen.material.cantidad_disponible
                        
                        # Registrar entrada al inventario
                        resumen.material.cantidad_disponible += cantidad_total
                        resumen.material.save()
                        
                        # Crear movimiento
                        Movimiento.objects.create(
                            material=resumen.material,
                            tipo_movimiento='entrada',
                            cantidad=cantidad_total,
                            cantidad_anterior=cantidad_anterior,
                            cantidad_nueva=resumen.material.cantidad_disponible,
                            usuario=request.user,
                            detalle=f'Compra para lista: {lista.nombre} - {paquetes_comprados} {resumen.unidad_compra_display}{"s" if paquetes_comprados > 1 else ""}'
                        )
                        
                        # Actualizar resumen
                        resumen.cantidad_disponible = resumen.material.cantidad_disponible
                        resumen.cantidad_faltante = max(0, resumen.cantidad_necesaria - resumen.cantidad_disponible)
                        resumen.fecha_compra = timezone.now()
                        resumen.save()
                        
                        materiales_registrados += 1
                    
                    materiales_procesados += 1
                    
                except (ValueError, TypeError) as e:
                    messages.error(request, f'Error con {resumen.material.nombre}: {str(e)}')
                    continue
            
            if materiales_registrados > 0:
                # Verificar si ya se cubrieron todos los materiales
                materiales_aun_faltantes = lista.resumen_materiales.filter(cantidad_faltante__gt=0).count()
                
                if materiales_aun_faltantes == 0:
                    # Todos los materiales están listos, mover a Paso 4
                    lista.estado = 'reabastecido'
                    lista.save()
                    messages.success(
                        request,
                        f'✅ Compras de "{lista.nombre}" registradas: {materiales_registrados} material(es). 🎉 Lista enviada al Paso 4 (Reabastecido).'
                    )
                else:
                    # Aún faltan materiales
                    messages.success(
                        request,
                        f'✅ Compras de "{lista.nombre}" registradas: {materiales_registrados} material(es). Aún faltan {materiales_aun_faltantes} material(es).'
                    )
                
                # Redirigir de vuelta al listado del Paso 3 para que pueda registrar otras listas
                return redirect('inventario:listado_compras_paso3')
            else:
                messages.warning(request, 'No se registró ninguna compra. Ingresa las cantidades.')
        
        except Exception as e:
            messages.error(request, f'Error al procesar compras: {str(e)}')
    
    # GET - Mostrar formulario simple
    # Las properties paquetes_rollos_necesarios y unidad_compra_display
    # ya están definidas en el modelo ResumenMateriales y se calculan automáticamente
    context = {
        'titulo': f'Registrar Compras - {lista.nombre}',
        'lista': lista,
        'materiales_necesarios': materiales_necesarios,
    }
    
    return render(request, 'inventario/verificar_compras.html', context)


@login_required
def enviar_a_reabastecimiento(request, lista_id):
    """Enviar lista de estado 'comprado' a 'reabastecido'"""
    
    if request.method == 'POST':
        try:
            lista = get_object_or_404(ListaProduccion, id=lista_id, usuario_creador=request.user)
            
            # Verificar que esté en estado correcto
            if lista.estado != 'comprado':
                messages.error(request, f'La lista "{lista.nombre}" debe estar en estado "Comprado" para enviar a reabastecimiento.')
                return redirect('inventario:compra_productos')
            
            # Verificar si aún faltan materiales
            materiales_faltantes = lista.resumen_materiales.filter(cantidad_faltante__gt=0).count()
            
            if materiales_faltantes > 0:
                messages.warning(request, f'La lista "{lista.nombre}" aún tiene {materiales_faltantes} material(es) faltante(s). Complete las compras primero.')
                return redirect('inventario:compra_productos')
            
            # Cambiar estado a reabastecido
            lista.estado = 'reabastecido'
            lista.save()
            
            messages.success(request, f'Lista "{lista.nombre}" enviada a reabastecimiento. Ya está lista para producción.')
            return redirect('inventario:reabastecimiento')
            
        except Exception as e:
            messages.error(request, f'Error al enviar a reabastecimiento: {str(e)}')
            return redirect('inventario:compra_productos')
    
    return redirect('inventario:compra_productos')


@login_required
def registrar_entrada_reabastecimiento(request, lista_id):
    """Registrar entrada de materiales comprados desde reabastecimiento"""
    from decimal import Decimal
    from django.db import transaction
    
    lista = get_object_or_404(ListaProduccion, id=lista_id, usuario_creador=request.user)
    
    # Verificar que esté en estado correcto
    if lista.estado not in ['comprado', 'reabastecido']:
        messages.error(request, f'La lista "{lista.nombre}" debe estar en estado "Comprado" o "Reabastecido" para registrar entradas.')
        return redirect('inventario:reabastecimiento')
    
    # Obtener materiales que aún necesitan entrada
    materiales_pendientes = lista.resumen_materiales.filter(cantidad_faltante__gt=0)
    
    if request.method == 'POST':
        materiales_ingresados = 0
        errores = []
        
        try:
            with transaction.atomic():
                for resumen in materiales_pendientes:
                    cantidad_key = f'cantidad_{resumen.id}'
                    precio_key = f'precio_{resumen.id}'
                    
                    if cantidad_key in request.POST:
                        try:
                            cantidad_entrada = Decimal(request.POST[cantidad_key])
                            precio_compra = Decimal(request.POST.get(precio_key, '0'))
                            
                            if cantidad_entrada > 0:
                                # Guardar cantidad anterior
                                cantidad_anterior = resumen.material.cantidad_disponible
                                
                                # Actualizar inventario del material
                                resumen.material.cantidad_disponible += cantidad_entrada
                                resumen.material.save()
                                
                                # Recargar para confirmar
                                resumen.material.refresh_from_db()
                                
                                # Crear movimiento de entrada con todos los detalles
                                from .models import Movimiento
                                movimiento = Movimiento.objects.create(
                                    material=resumen.material,
                                    tipo_movimiento='entrada',
                                    cantidad=cantidad_entrada,  # Positivo porque es entrada
                                    cantidad_anterior=cantidad_anterior,
                                    cantidad_nueva=resumen.material.cantidad_disponible,
                                    precio_unitario=precio_compra if precio_compra > 0 else None,
                                    costo_total_movimiento=precio_compra * cantidad_entrada if precio_compra > 0 else None,
                                    detalle=f'Reabastecimiento - Lista #{lista.id}: {lista.nombre}',
                                    usuario=request.user
                                )
                                
                                print(f"✅ Entrada registrada: {resumen.material.nombre}")
                                print(f"   Cantidad: {cantidad_anterior} → {resumen.material.cantidad_disponible} (+{cantidad_entrada})")
                                print(f"   Movimiento ID: {movimiento.id}")
                                
                                # Actualizar resumen de materiales
                                nueva_cantidad_disponible = resumen.material.cantidad_disponible
                                resumen.cantidad_disponible = nueva_cantidad_disponible
                                resumen.cantidad_faltante = max(0, resumen.cantidad_necesaria - nueva_cantidad_disponible)
                                resumen.save()
                                
                                materiales_ingresados += 1
                                
                        except (ValueError, TypeError) as e:
                            error_msg = f"Error procesando {resumen.material.nombre}: {str(e)}"
                            print(f"❌ {error_msg}")
                            errores.append(error_msg)
                            continue
                
                if materiales_ingresados > 0:
                    messages.success(request, f'✅ Se registraron {materiales_ingresados} entrada(s) de materiales correctamente.')
                    
                    # Verificar si ya no faltan materiales y cambiar estado automáticamente
                    materiales_aun_faltantes = lista.resumen_materiales.filter(cantidad_faltante__gt=0).count()
                    if materiales_aun_faltantes == 0 and lista.estado == 'comprado':
                        lista.estado = 'reabastecido'
                        lista.save()
                        messages.info(request, f'🎉 Lista "{lista.nombre}" movida automáticamente a estado "Reabastecido" - ¡Lista para producción!')
                elif errores:
                    for error in errores:
                        messages.error(request, error)
                else:
                    messages.warning(request, 'No se registró ninguna entrada. Verifique las cantidades ingresadas.')
                    
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"❌ ERROR AL REGISTRAR ENTRADAS:\n{error_detail}")
            messages.error(request, f'Error al registrar entradas: {str(e)}')
        
        return redirect('inventario:reabastecimiento')
    
    # GET request - mostrar formulario
    context = {
        'lista': lista,
        'materiales_pendientes': materiales_pendientes,
        'titulo': f'Registrar Entradas - {lista.nombre}'
    }
    
    return render(request, 'inventario/registrar_entrada_reabastecimiento.html', context)


@login_required
def listado_listas_produccion(request):
    """Vista para mostrar todas las listas de producción agrupadas por paso"""
    
    # Obtener todas las listas (excluyendo finalizadas)
    todas_listas = ListaProduccion.objects.filter(
        usuario_creador=request.user
    ).exclude(estado='finalizado').prefetch_related('detalles_monos__monos').order_by('-fecha_creacion')
    
    # Agrupar listas por paso/estado
    listas_por_paso = {
        'borrador': {
            'nombre': 'Creada',
            'numero': 1,
            'icono': 'fas fa-check-circle',
            'color': 'secondary',
            'listas': todas_listas.filter(estado='borrador')
        },
        'pendiente_compra': {
            'nombre': 'Lista de Compras',
            'numero': 2,
            'icono': 'fas fa-file-download',
            'color': 'warning',
            'listas': todas_listas.filter(estado='pendiente_compra')
        },
        'comprado': {
            'nombre': 'Registrar Compras',
            'numero': 3,
            'icono': 'fas fa-shopping-cart',
            'color': 'info',
            'listas': todas_listas.filter(estado='comprado')
        },
        'reabastecido': {
            'nombre': 'Materiales Listos',
            'numero': 4,
            'icono': 'fas fa-box-check',
            'color': 'success',
            'listas': todas_listas.filter(estado='reabastecido')
        },
        'en_produccion': {
            'nombre': 'Produciendo',
            'numero': 5,
            'icono': 'fas fa-industry',
            'color': 'primary',
            'listas': todas_listas.filter(estado='en_produccion')
        },
        'en_salida': {
            'nombre': 'Salida y Ventas',
            'numero': 6,
            'icono': 'fas fa-cash-register',
            'color': 'dark',
            'listas': todas_listas.filter(estado='en_salida')
        }
    }
    
    # Contar totales
    total_listas = todas_listas.count()
    
    context = {
        'listas_por_paso': listas_por_paso,
        'total_listas': total_listas,
        'titulo': 'Listas de Producción'
    }
    
    return render(request, 'inventario/listado_listas_produccion.html', context)


# Buscar la función lista_de_compras (línea ~1239)

@login_required
def lista_de_compras(request):
    """Vista para mostrar listas que necesitan compras (Paso 2)"""
    
    # Obtener listas en estado pendiente_compra (Paso 2)
    listas_pendientes = ListaProduccion.objects.filter(
        usuario_creador=request.user,
        estado='pendiente_compra'
    ).prefetch_related('detalles_monos__monos', 'resumen_materiales__material').order_by('-fecha_creacion')
    
    # Calcular información de materiales faltantes para cada lista
    for lista in listas_pendientes:
        materiales_faltantes = lista.resumen_materiales.filter(cantidad_faltante__gt=0)
        lista.total_materiales_faltantes = materiales_faltantes.count()
        lista.materiales_faltantes_lista = materiales_faltantes
    
    context = {
        'listas_pendientes': listas_pendientes,
        'titulo': 'Listas Pendientes de Compra - Paso 2'
    }
    
    return render(request, 'inventario/lista_de_compras.html', context)


@login_required
def listado_compras_paso3(request):
    """Vista para mostrar listas en Paso 3 (comprado) para registrar compras"""
    
    # Obtener listas en estado comprado (Paso 3)
    listas_compradas = ListaProduccion.objects.filter(
        usuario_creador=request.user,
        estado='comprado'
    ).prefetch_related('detalles_monos__monos', 'resumen_materiales__material').order_by('-fecha_creacion')
    
    # Calcular información de materiales faltantes para cada lista
    for lista in listas_compradas:
        materiales_faltantes = lista.resumen_materiales.filter(cantidad_faltante__gt=0)
        lista.total_materiales_faltantes = materiales_faltantes.count()
        lista.materiales_faltantes_lista = materiales_faltantes
    
    context = {
        'listas_compradas': listas_compradas,
        'titulo': 'Registrar Compras - Paso 3'
    }
    
    return render(request, 'inventario/listado_compras_paso3.html', context)


def consolidar_materiales_listas(listas_produccion):
    """Consolida materiales necesarios de múltiples listas de producción"""
    
    materiales_consolidados = {}
    
    for lista in listas_produccion:
        for resumen in lista.resumen_materiales.all():
            material_id = resumen.material.id
            
            if material_id in materiales_consolidados:
                materiales_consolidados[material_id]['cantidad_necesaria'] += resumen.cantidad_necesaria
                materiales_consolidados[material_id]['cantidad_faltante'] += max(0, resumen.cantidad_faltante)
            else:
                materiales_consolidados[material_id] = {
                    'material': resumen.material,
                    'cantidad_necesaria': resumen.cantidad_necesaria,
                    'cantidad_disponible': resumen.material.cantidad_disponible,
                    'cantidad_faltante': max(0, resumen.cantidad_faltante),
                }
    
    # Recalcular con stock actual y calcular paquetes/rollos necesarios
    resultado = []
    for material_data in materiales_consolidados.values():
        material = material_data['material']
        cantidad_necesaria = material_data['cantidad_necesaria']
        cantidad_disponible = material.cantidad_disponible
        cantidad_faltante = max(0, cantidad_necesaria - cantidad_disponible)
        
        # Calcular paquetes/rollos necesarios
        if cantidad_faltante > 0 and material.factor_conversion > 0:
            import math
            paquetes_rollos_necesarios = math.ceil(float(cantidad_faltante / material.factor_conversion))
            cantidad_total_compra = paquetes_rollos_necesarios * material.factor_conversion
        else:
            paquetes_rollos_necesarios = 0
            cantidad_total_compra = 0
        
        # Determinar unidad de compra
        unidad_compra_display = material.get_tipo_material_display()
        
        resultado.append({
            'material': material,
            'cantidad_necesaria': cantidad_necesaria,
            'cantidad_disponible': cantidad_disponible,
            'cantidad_faltante': cantidad_faltante,
            'paquetes_rollos_necesarios': paquetes_rollos_necesarios,
            'cantidad_total_compra': cantidad_total_compra,
            'unidad_compra_display': unidad_compra_display,
            'costo_estimado_compra': paquetes_rollos_necesarios * material.precio_compra if material.precio_compra > 0 else 0
        })
    
    # Ordenar por nombre de material
    return sorted(resultado, key=lambda x: x['material'].nombre)

# ...existing code...

@login_required
def detalle_lista_produccion(request, lista_id):
    """Vista para mostrar detalles de una lista de producción específica"""
    
    lista = get_object_or_404(
        ListaProduccion, 
        id=lista_id, 
        usuario_creador=request.user
    )
    
    # Obtener detalles de moños y materiales
    detalles_monos = lista.detalles_monos.select_related('monos').all()
    resumen_materiales = lista.resumen_materiales.select_related('material').all()
    
    context = {
        'lista': lista,
        'detalles_monos': detalles_monos,
        'resumen_materiales': resumen_materiales,
        'titulo': f'Detalles - {lista.nombre}'
    }
    
    return render(request, 'inventario/detalle_lista_produccion.html', context)


@login_required
def compra_productos(request):
    """Vista para registrar compras reales de materiales"""
    from decimal import Decimal
    
    # Obtener listas en estado 'comprado' que necesitan registro de compras
    listas_comprado = ListaProduccion.objects.filter(
        usuario_creador=request.user,
        estado='comprado'
    ).prefetch_related('resumen_materiales__material')
    
    # Obtener todos los materiales de todas las listas en estado comprado
    materiales_pendientes = []
    for lista in listas_comprado:
        for resumen in lista.resumen_materiales.filter(cantidad_faltante__gt=0):
            # Solo materiales que aún faltan por comprar completamente
            if resumen.cantidad_comprada < resumen.cantidad_faltante:
                materiales_pendientes.append({
                    'resumen': resumen,
                    'lista': lista,
                    'material': resumen.material,
                    'cantidad_faltante': resumen.cantidad_faltante,
                    'paquetes_rollos_necesarios': resumen.paquetes_rollos_necesarios,
                    'unidad_compra_display': resumen.unidad_compra_display,
                    'cantidad_total_compra': resumen.paquetes_rollos_necesarios * resumen.material.factor_conversion,
                    'costo_estimado': resumen.paquetes_rollos_necesarios * resumen.material.precio_compra if resumen.material.precio_compra > 0 else 0
                })
    
    # Procesar formulario de compra
    if request.method == 'POST':
        materiales_actualizados = 0
        total_invertido = Decimal('0')
        errores = []
        
        print(f"\n{'='*60}")
        print(f"🛒 PROCESANDO COMPRAS DE MATERIALES")
        print(f"{'='*60}")
        
        for material_info in materiales_pendientes:
            resumen = material_info['resumen']
            
            # Obtener datos del formulario para cada material
            paquetes_key = f'paquetes_{resumen.id}'
            precio_key = f'precio_{resumen.id}'
            proveedor_key = f'proveedor_{resumen.id}'
            
            paquetes_comprados = request.POST.get(paquetes_key)
            precio_real = request.POST.get(precio_key)
            proveedor = request.POST.get(proveedor_key, '')
            
            if paquetes_comprados and precio_real:
                try:
                    paquetes = Decimal(str(paquetes_comprados))
                    precio = Decimal(str(precio_real))
                    cantidad = paquetes * resumen.material.factor_conversion
                    
                    if paquetes > 0 and precio > 0:
                        # Actualizar resumen de material
                        cantidad_anterior = resumen.material.cantidad_disponible
                        
                        resumen.cantidad_comprada += cantidad
                        resumen.precio_compra_real = precio
                        resumen.proveedor = proveedor
                        resumen.fecha_compra = timezone.now()
                        resumen.cantidad_disponible = material.cantidad_disponible
                        resumen.cantidad_faltante = max(0, resumen.cantidad_necesaria - material.cantidad_disponible)
                        resumen.save()
                        
                        # Actualizar inventario del material
                        material = resumen.material
                        material.cantidad_disponible += cantidad
                        material.save()
                        
                        materiales_actualizados += 1
                        total_invertido += paquetes * precio
                    
                except (ValueError, TypeError) as e:
                    errores.append(f"{resumen.material.nombre}: Error - {str(e)}")
                    continue
        
        if materiales_actualizados > 0:
            # Verificar si todas las compras están completas
            listas_reabastecidas = []
            for lista in listas_comprado:
                compras_completas = True
                for resumen in lista.resumen_materiales.all():
                    if resumen.material.cantidad_disponible < resumen.cantidad_necesaria:
                        compras_completas = False
                        break
                
                if compras_completas and lista.estado == 'comprado':
                    lista.estado = 'reabastecido'
                    lista.save()
                    listas_reabastecidas.append(lista.nombre)
            
            mensaje_base = f'✅ Se registraron {materiales_actualizados} compra(s) por ${total_invertido:.2f}.'
            if listas_reabastecidas:
                mensaje_base += f' 🎉 Lista(s) REABASTECIDA(S): {", ".join(listas_reabastecidas)}'
            
            messages.success(request, mensaje_base)
            
            if errores:
                for error in errores:
                    messages.warning(request, f"⚠️ {error}")
            
            return redirect('inventario:lista_de_compras')
        else:
            messages.warning(request, 'No se registró ninguna compra.')
            if errores:
                for error in errores:
                    messages.error(request, f"❌ {error}")
    
    context = {
        'listas_comprado': listas_comprado,
        'materiales_pendientes': materiales_pendientes,
        'titulo': 'Compra de Productos'
    }
    
    return render(request, 'inventario/compra_productos.html', context)


@login_required
def reabastecimiento(request):
    """Vista para gestionar el proceso de producción/reabastecimiento"""
    
    # Obtener listas en estado 'reabastecido' listas para producción
    listas_reabastecidas = ListaProduccion.objects.filter(
        usuario_creador=request.user,
        estado='reabastecido'
    ).prefetch_related('detalles_monos__monos__recetas__material', 'resumen_materiales__material')
    
    # Procesar inicio o finalización de producción
    if request.method == 'POST':
        accion = request.POST.get('accion')
        lista_id = request.POST.get('lista_id')
        
        try:
            lista = ListaProduccion.objects.get(id=lista_id, usuario_creador=request.user)
            
            if accion == 'iniciar_produccion':
                # Verificar que hay suficientes materiales antes de iniciar producción
                materiales_suficientes, mensaje_verificacion = verificar_materiales_suficientes(lista)
                
                if not materiales_suficientes:
                    messages.error(
                        request, 
                        f'No se puede iniciar la producción de "{lista.nombre}". {mensaje_verificacion}'
                    )
                    return redirect('inventario:reabastecimiento')
                
                # Cambiar estado a 'en_produccion'
                lista.estado = 'en_produccion'
                lista.save()
                
                # Verificar nuevamente justo antes del descuento (por seguridad)
                materiales_suficientes_final, _ = verificar_materiales_suficientes(lista)
                if not materiales_suficientes_final:
                    # Revertir estado si ya no hay suficientes materiales
                    lista.estado = 'reabastecido'
                    lista.save()
                    messages.error(
                        request, 
                        f'Error: Los materiales cambiaron durante el proceso. No se pudo iniciar la producción de "{lista.nombre}".'
                    )
                    return redirect('inventario:reabastecimiento')
                
                # Descontar materiales del inventario
                try:
                    materiales_descontados = descontar_materiales_produccion(lista, request.user)
                    
                    messages.success(
                        request, 
                        f'Se inició la producción de "{lista.nombre}". '
                        f'Se descontaron {materiales_descontados} materiales del inventario.'
                    )
                except Exception as e:
                    # Revertir estado si hay error
                    lista.estado = 'reabastecido'
                    lista.save()
                    
                    import traceback
                    error_detalle = traceback.format_exc()
                    print(f"\n❌ ERROR AL DESCONTAR MATERIALES:\n{error_detalle}")
                    
                    messages.error(
                        request,
                        f'Error al descontar materiales de "{lista.nombre}": {str(e)}'
                    )
                    return redirect('inventario:reabastecimiento')
                
            elif accion == 'finalizar_produccion':
                # Obtener cantidades producidas del formulario
                cantidades_actualizadas = 0
                
                for detalle in lista.detalles_monos.all():
                    cantidad_key = f'cantidad_producida_{detalle.id}'
                    cantidad_producida = request.POST.get(cantidad_key)
                    
                    if cantidad_producida:
                        try:
                            cantidad = int(cantidad_producida)
                            if cantidad >= 0:
                                detalle.cantidad_producida = cantidad
                                detalle.save()
                                cantidades_actualizadas += 1
                        except (ValueError, TypeError):
                            continue
                
                if cantidades_actualizadas > 0:
                    # Actualizar total de moños producidos
                    total_producidos = sum(
                        detalle.cantidad_total_producida 
                        for detalle in lista.detalles_monos.all()
                    )
                    lista.total_moños_producidos = total_producidos
                    
                    # SIEMPRE cambiar a estado EN_SALIDA al guardar producción
                    lista.estado = 'en_salida'
                    lista.save()
                    
                    # Verificar si la producción está completa para el mensaje
                    produccion_completa = all(
                        detalle.cantidad_producida >= detalle.cantidad 
                        for detalle in lista.detalles_monos.all()
                    )
                    
                    if produccion_completa:
                        messages.success(
                            request, 
                            f'✅ Producción de "{lista.nombre}" completada! '
                            f'Se produjeron {total_producidos} moños en total. '
                            f'Lista enviada a Salida para registrar ventas.'
                        )
                    else:
                        messages.success(
                            request, 
                            f'✅ Producción de "{lista.nombre}" guardada! '
                            f'Se produjeron {total_producidos} moños hasta ahora. '
                            f'Lista enviada a Salida para registrar ventas.'
                        )
                else:
                    messages.warning(request, 'No se actualizó ninguna cantidad.')
            
            elif accion == 'marcar_salida':
                # Esta acción finaliza la lista y registra la venta
                if lista.estado != 'en_salida':
                    messages.error(
                        request,
                        f'La lista "{lista.nombre}" debe estar en estado "En Salida" para marcar la salida.'
                    )
                    return redirect('inventario:reabastecimiento')
                
                # Cambiar a estado FINALIZADO
                lista.estado = 'finalizado'
                lista.save()
                
                # Registrar venta automática en contabilidad
                from .models import MovimientoEfectivo
                
                # Calcular ingreso total de la venta
                ingreso_total_venta = Decimal('0')
                for detalle in lista.detalles_monos.all():
                    precio_venta = detalle.monos.precio_venta
                    cantidad_producida = detalle.cantidad_producida
                    ingreso_detalle = precio_venta * cantidad_producida
                    ingreso_total_venta += ingreso_detalle
                
                # Crear movimiento de efectivo por la venta
                if ingreso_total_venta > 0:
                    MovimientoEfectivo.registrar_movimiento(
                        concepto=f'Venta de producción - Lista: {lista.nombre}',
                        tipo_movimiento='ingreso',
                        categoria='venta',
                        monto=ingreso_total_venta,
                        usuario=request.user
                    )
                
                messages.success(
                    request, 
                    f'¡Salida de "{lista.nombre}" registrada exitosamente! '
                    f'Venta registrada en contaduría: ${ingreso_total_venta:,.2f}'
                )
                    
        except ListaProduccion.DoesNotExist:
            messages.error(request, 'Lista de producción no encontrada.')
        except Exception as e:
            messages.error(request, f'Error al procesar la acción: {str(e)}')
            
        return redirect('inventario:reabastecimiento')
    
    # Obtener también listas en producción para mostrar progreso
    listas_en_produccion = ListaProduccion.objects.filter(
        usuario_creador=request.user,
        estado='en_produccion'
    ).prefetch_related('detalles_monos__monos')
    
    # Obtener listas en salida (producción completada, esperando salida)
    listas_en_salida = ListaProduccion.objects.filter(
        usuario_creador=request.user,
        estado='en_salida'
    ).prefetch_related('detalles_monos__monos')
    
    context = {
        'listas_reabastecidas': listas_reabastecidas,
        'listas_en_produccion': listas_en_produccion,
        'listas_en_salida': listas_en_salida,
        'titulo': 'Reabastecimiento y Producción'
    }
    
    return render(request, 'inventario/reabastecimiento.html', context)


def descontar_materiales_produccion(lista_produccion, usuario=None):
    """Descuenta materiales del inventario según las recetas de los moños"""
    
    from django.db import transaction
    import traceback
    
    materiales_descontados = 0
    errores = []
    
    print(f"\n{'='*60}")
    print(f"🏭 INICIANDO DESCUENTO DE MATERIALES - Lista #{lista_produccion.id}")
    print(f"{'='*60}")
    
    try:
        with transaction.atomic():
            for detalle in lista_produccion.detalles_monos.all():
                monos = detalle.monos
                cantidad_total_planificada = detalle.cantidad_total_planificada
                
                print(f"\n🎀 Moño: {monos.codigo} - {monos.nombre}")
                print(f"   Cantidad planificada: {cantidad_total_planificada}")
                
                # Obtener recetas del moño
                recetas = monos.recetas.all()
                print(f"   Recetas encontradas: {recetas.count()}")
                
                if recetas.count() == 0:
                    print(f"   ⚠️  NO HAY RECETAS para este moño!")
                    continue
                
                for receta in recetas:
                    try:
                        # Recargar el material desde la BD para asegurar datos frescos
                        material = receta.material
                        material.refresh_from_db()
                        
                        cantidad_por_mono = receta.cantidad_necesaria
                        cantidad_total_necesaria = cantidad_por_mono * cantidad_total_planificada
                        
                        print(f"\n   📦 Material: {material.nombre} (ID: {material.id})")
                        print(f"      Código: {material.codigo}")
                        print(f"      Unidad: {material.unidad_base}")
                        print(f"      Cantidad por moño: {cantidad_por_mono} {material.unidad_base}")
                        print(f"      Cantidad total necesaria: {cantidad_total_necesaria} {material.unidad_base}")
                        print(f"      Disponible en inventario: {material.cantidad_disponible} {material.unidad_base}")
                        
                        # Verificar si hay suficiente material antes de descontar
                        if material.cantidad_disponible >= cantidad_total_necesaria:
                            # Guardar cantidad anterior para el registro de movimiento
                            cantidad_anterior = material.cantidad_disponible
                            
                            print(f"\n📦 Material: {material.nombre}")
                            print(f"   Cantidad anterior: {cantidad_anterior} {material.unidad_base}")
                            print(f"   Cantidad a descontar: {cantidad_total_necesaria} {material.unidad_base}")
                            
                            # Descontar del inventario solo si hay suficiente
                            material.cantidad_disponible -= cantidad_total_necesaria
                            material.save()
                            
                            # Recargar para confirmar que se guardó
                            material.refresh_from_db()
                            
                            print(f"   Cantidad nueva: {material.cantidad_disponible} {material.unidad_base}")
                            print(f"   ✅ Material guardado en BD correctamente")
                            
                            # Registrar movimiento de salida por producción
                            costo_unitario = material.costo_unitario
                            costo_total = costo_unitario * cantidad_total_necesaria if costo_unitario else None
                            
                            movimiento = Movimiento.objects.create(
                                material=material,
                                tipo_movimiento='produccion',
                                cantidad=-cantidad_total_necesaria,  # Negativo porque es salida
                                cantidad_anterior=cantidad_anterior,
                                cantidad_nueva=material.cantidad_disponible,
                                precio_unitario=costo_unitario,
                                costo_total_movimiento=costo_total,
                                detalle=f"Producción - Lista #{lista_produccion.id}: {monos.codigo} ({cantidad_total_planificada} moños)",
                                usuario=usuario
                            )
                            print(f"   ✅ Movimiento registrado: ID={movimiento.id}")
                            print(f"   💰 Costo unitario: ${costo_unitario or 0:.2f}")
                            print(f"   💰 Costo total: ${costo_total or 0:.2f}")
                            
                            # Actualizar cantidad utilizada en el resumen
                            try:
                                resumen = ResumenMateriales.objects.get(
                                    lista_produccion=lista_produccion,
                                    material=material
                                )
                                resumen.cantidad_utilizada += cantidad_total_necesaria
                                resumen.save()
                                print(f"   ✅ Resumen actualizado")
                            except ResumenMateriales.DoesNotExist:
                                print(f"   ⚠️  No existe ResumenMateriales para este material")
                            
                            materiales_descontados += 1
                        else:
                            # ERROR: No hay suficiente material - esto no debería pasar
                            # si la validación funcionó correctamente
                            error_msg = f"Material {material.nombre} insuficiente! Necesario: {cantidad_total_necesaria}, Disponible: {material.cantidad_disponible}"
                            print(f"\n      ❌ ERROR: {error_msg}")
                            errores.append(error_msg)
                            
                    except Exception as e:
                        error_msg = f"Error procesando material {material.nombre}: {str(e)}"
                        print(f"\n      ❌ EXCEPCIÓN: {error_msg}")
                        print(f"      Traceback: {traceback.format_exc()}")
                        errores.append(error_msg)
                        # NO hacer raise aquí para seguir procesando otros materiales
            
            print(f"\n{'='*60}")
            print(f"✅ DESCUENTO COMPLETADO: {materiales_descontados} materiales procesados")
            if errores:
                print(f"⚠️  ERRORES ENCONTRADOS: {len(errores)}")
                for error in errores:
                    print(f"   - {error}")
            print(f"{'='*60}\n")
            
    except Exception as e:
        error_msg = f"Error crítico en descuento de materiales: {str(e)}"
        print(f"\n❌ ERROR CRÍTICO: {error_msg}")
        print(f"Traceback completo:\n{traceback.format_exc()}")
        errores.append(error_msg)
        raise  # Re-lanzar para que se revierta la transacción
    
    return materiales_descontados


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
            
            materiales_insuficientes = []
            materiales_utilizados = []
            
            # Procesar cada detalle de la simulación
            for detalle in simulacion.detalles.all():
                material = detalle.material
                cantidad_necesaria = detalle.cantidad_necesaria
                
                if material.cantidad_disponible >= cantidad_necesaria:
                    # Hay stock suficiente - registrar salida
                    registrar_movimiento_produccion(material, cantidad_necesaria, simulacion, request.user)
                    materiales_utilizados.append({
                        'material': material.nombre,
                        'cantidad': cantidad_necesaria
                    })
                else:
                    # Stock insuficiente
                    materiales_insuficientes.append({
                        'material': material.nombre,
                        'disponible': material.cantidad_disponible,
                        'necesario': cantidad_necesaria,
                        'faltante': cantidad_necesaria - material.cantidad_disponible
                    })
            
            if materiales_insuficientes:
                # Hay materiales faltantes - mostrar opción de reabastecimiento
                context = {
                    'simulacion': simulacion,
                    'materiales_faltantes': materiales_insuficientes,
                    'materiales_utilizados': materiales_utilizados
                }
                messages.error(request, f'Faltan {len(materiales_insuficientes)} materiales para completar la simulación.')
                return render(request, 'inventario/confirmar_reabastecimiento.html', context)
            else:
                # Todo procesado correctamente - registrar la venta de la producción
                MovimientoEfectivo.registrar_movimiento(
                    concepto=f'Venta de producción - {simulacion.monos.nombre} - Simulación #{simulacion.id}',
                    tipo_movimiento='ingreso',
                    categoria='venta',
                    monto=simulacion.ingreso_total_venta,
                    usuario=request.user
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
        return JsonResponse({'error': 'Simulación no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)


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
                cantidad_faltante = detalle.cantidad_necesaria - material.cantidad_disponible
                
                # Calcular cantidad a comprar en unidades completas (paquetes/rollos)
                if material.factor_conversion > 0:
                    paquetes_necesarios = math.ceil(cantidad_faltante / material.factor_conversion)
                    cantidad_a_comprar = paquetes_necesarios * material.factor_conversion
                    unidades_a_comprar = paquetes_necesarios
                else:
                    cantidad_a_comprar = cantidad_faltante
                    unidades_a_comprar = cantidad_faltante
                
                # Calcular costo (asumiendo mismo precio por unidad)
                costo_unitario = material.costo_unitario or Decimal('0')
                precio_compra_total = cantidad_a_comprar * costo_unitario
                
                # Actualizar inventario
                cantidad_anterior = material.cantidad_disponible
                material.cantidad_disponible += cantidad_a_comprar
                
                # Actualizar precio de compra y costo unitario si es necesario
                if costo_unitario > 0:
                    material.precio_compra = precio_compra_total
                
                material.save()
                
                # Registrar movimiento de entrada
                movimiento = Movimiento.objects.create(
                    material=material,
                    tipo_movimiento='entrada',
                    cantidad=cantidad_a_comprar,
                    cantidad_anterior=cantidad_anterior,
                    cantidad_nueva=material.cantidad_disponible,
                    precio_unitario=costo_unitario,
                    costo_total_movimiento=precio_compra_total,
                    detalle=f"Reabastecimiento automático para Simulación #{simulacion.id} - {unidades_a_comprar} {material.tipo_material}(s)",
                    usuario=request.user
                )
                
                materiales_reabastecidos.append({
                    'material': material.nombre,
                    'unidades_compradas': unidades_a_comprar,
                    'tipo_unidad': material.tipo_material,
                    'cantidad_agregada': float(cantidad_a_comprar),
                    'unidad_base': material.unidad_base,
                    'costo': float(precio_compra_total)
                })
                
                costo_total_reabastecimiento += precio_compra_total
            
            if materiales_reabastecidos:
                messages.success(
                    request,
                    f'Reabastecimiento automático completado: {len(materiales_reabastecidos)} materiales. '
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
        
        # Verificar que la simulación no haya sido procesada antes
        if simulacion.movimiento_set.filter(tipo_movimiento='produccion').exists():
            return JsonResponse({'success': False, 'mensaje': 'Esta simulación ya fue procesada anteriormente.'})
        
        materiales_insuficientes = []
        
        # Procesar cada detalle de la simulación
        for detalle in simulacion.detalles.all():
            material = detalle.material
            cantidad_necesaria = detalle.cantidad_necesaria
            
            if material.cantidad_disponible >= cantidad_necesaria:
                # Hay stock suficiente - registrar salida
                registrar_movimiento_produccion(material, cantidad_necesaria, simulacion, request.user)
            else:
                # Stock insuficiente
                materiales_insuficientes.append({
                    'material': material.nombre,
                    'disponible': material.cantidad_disponible,
                    'necesario': cantidad_necesaria,
                    'faltante': cantidad_necesaria - material.cantidad_disponible
                })
        
        if materiales_insuficientes:
            return JsonResponse({
                'success': False,
                'error': 'Materiales insuficientes',
                'materiales_insuficientes': materiales_insuficientes
            })
        else:
            # Todo procesado correctamente - registrar la venta de la producción
            MovimientoEfectivo.registrar_movimiento(
                concepto=f'Venta de producción - {simulacion.monos.nombre} - Simulación #{simulacion.id}',
                tipo_movimiento='ingreso',
                categoria='venta',
                monto=simulacion.ingreso_total_venta,
                usuario=request.user
            )
            
            return JsonResponse({
                'success': True,
                'mensaje': f'Simulación procesada exitosamente. {len(simulacion.detalles.all())} materiales utilizados. Venta registrada por ${simulacion.ingreso_total_venta:.2f}.'
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
                    detalle=f"Reabastecimiento automático para Simulación #{simulacion.id} - {unidades_a_comprar} {material.tipo_material}(s)",
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
        
        if reabastecimientos:
            messages.success(
                request,
                f'Reabastecimiento automático completado: {len(reabastecimientos)} materiales. '
                f'Costo total: ${costo_total_reabastecimiento:.2f}'
            )
            # Ahora intentar procesar la simulación automáticamente
            return redirect('inventario:procesar_simulacion_completa', simulacion_id=simulacion.id)
        else:
            messages.info(request, 'No se necesita reabastecimiento para esta simulación.')
            return redirect('inventario:procesar_simulacion_completa', simulacion_id=simulacion.id)
        
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
        
        # Verificar que la simulación no haya sido procesada antes
        if simulacion.movimiento_set.filter(tipo_movimiento='produccion').exists():
            return JsonResponse({'success': False, 'mensaje': 'Esta simulación ya fue procesada anteriormente.'})
        
        materiales_insuficientes = []
        
        # Procesar cada detalle de la simulación
        for detalle in simulacion.detalles.all():
            material = detalle.material
            cantidad_necesaria = detalle.cantidad_necesaria
            
            if material.cantidad_disponible >= cantidad_necesaria:
                # Hay stock suficiente - registrar salida
                registrar_movimiento_produccion(material, cantidad_necesaria, simulacion, request.user)
            else:
                # Stock insuficiente
                materiales_insuficientes.append({
                    'material': material.nombre,
                    'disponible': material.cantidad_disponible,
                    'necesario': cantidad_necesaria,
                    'faltante': cantidad_necesaria - material.cantidad_disponible
                })
        
        if materiales_insuficientes:
            return JsonResponse({
                'success': False,
                'error': 'Materiales insuficientes',
                'materiales_insuficientes': materiales_insuficientes
            })
        else:
            # Todo procesado correctamente - registrar la venta de la producción
            MovimientoEfectivo.registrar_movimiento(
                concepto=f'Venta de producción - {simulacion.monos.nombre} - Simulación #{simulacion.id}',
                tipo_movimiento='ingreso',
                categoria='venta',
                monto=simulacion.ingreso_total_venta,
                usuario=request.user
            )
            
            return JsonResponse({
                'success': True,
                'mensaje': f'Simulación procesada exitosamente. {len(simulacion.detalles.all())} materiales utilizados. Venta registrada por ${simulacion.ingreso_total_venta:.2f}.'
            })
        
    except Simulacion.DoesNotExist:
        return JsonResponse({'error': 'Simulación no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)



# ============================================================================
# FUNCIONES DE PRODUCCIÓN - SISTEMA DE LISTAS
# ============================================================================

@login_required
def iniciar_produccion(request, lista_id):
    """Inicia la producción de una lista, descontando materiales del inventario"""
    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('inventario:reabastecimiento')
    
    try:
        lista = get_object_or_404(ListaProduccion, id=lista_id, usuario_creador=request.user)
        
        if lista.estado != 'reabastecido':
            messages.error(request, f'La lista "{lista.nombre}" debe estar en estado "Reabastecido" para iniciar producción.')
            return redirect('inventario:reabastecimiento')
        
        # Descontar materiales
        materiales_descontados = descontar_materiales_produccion(lista, request.user)
        
        # Cambiar estado
        lista.estado = 'en_produccion'
        lista.save()
        
        messages.success(request, f'Producción iniciada para "{lista.nombre}". {materiales_descontados} materiales descontados del inventario.')
        return redirect('inventario:reabastecimiento')
        
    except Exception as e:
        messages.error(request, f'Error al iniciar producción: {str(e)}')
        return redirect('inventario:reabastecimiento')


@login_required
def lista_en_salida(request):
    """Vista para mostrar listas en estado de salida"""
    listas_en_salida = ListaProduccion.objects.filter(
        usuario_creador=request.user,
        estado='en_salida'
    ).prefetch_related('detalles_monos__monos').order_by('-fecha_actualizacion')
    
    context = {
        'listas_en_salida': listas_en_salida,
        'titulo': 'Listas en Salida - Pendientes de Venta'
    }
    
    return render(request, 'inventario/lista_en_salida.html', context)


@login_required
def registrar_salida_materiales(request, lista_id):
    """Registra la salida final de materiales (ya se hizo en iniciar_produccion)"""
    # Esta función es redundante ya que los materiales se descontaron al iniciar producción
    # Solo redirige al detalle
    lista = get_object_or_404(ListaProduccion, id=lista_id, usuario_creador=request.user)
    messages.info(request, 'Los materiales ya fueron descontados al iniciar la producción.')
    return redirect('inventario:detalle_lista_produccion', lista_id=lista.id)


@login_required
def registrar_ventas_contaduria(request, lista_id):
    """Registra las ventas de una lista de producción en contaduría"""
    lista = get_object_or_404(ListaProduccion, id=lista_id, usuario_creador=request.user)
    
    if lista.estado != 'en_salida':
        messages.error(request, f'La lista "{lista.nombre}" debe estar en estado "En Salida" para registrar ventas.')
        return redirect('inventario:lista_en_salida')
    
    if request.method == 'POST':
        try:
            # Calcular ingreso total de las ventas
            ingreso_total = Decimal('0')
            
            for detalle in lista.detalles_monos.all():
                cantidad_vendida = Decimal(request.POST.get(f'cantidad_vendida_{detalle.id}', 0))
                precio_venta = detalle.monos.precio_venta
                
                if cantidad_vendida > 0:
                    ingreso_venta = cantidad_vendida * precio_venta
                    ingreso_total += ingreso_venta
                    
                    # Actualizar cantidad producida en el detalle
                    detalle.cantidad_producida = cantidad_vendida
                    detalle.save()
            
            if ingreso_total > 0:
                # Registrar el ingreso en contaduría
                MovimientoEfectivo.registrar_movimiento(
                    concepto=f'Venta de producción - Lista: {lista.nombre}',
                    tipo_movimiento='ingreso',
                    categoria='venta',
                    monto=ingreso_total,
                    usuario=request.user
                )
                
                # Actualizar ganancia real de la lista
                lista.ganancia_real = ingreso_total - (lista.costo_total_estimado or Decimal('0'))
                lista.estado = 'finalizado'
                lista.save()
                
                messages.success(
                    request,
                    f'Ventas registradas exitosamente. Ingreso total: ${ingreso_total:.2f}. '
                    f'Ganancia: ${lista.ganancia_real:.2f}'
                )
                return redirect('inventario:listas_produccion')
            else:
                messages.warning(request, 'No se registraron ventas. Ingresa al menos una cantidad vendida.')
                
        except Exception as e:
            messages.error(request, f'Error al registrar ventas: {str(e)}')
    
    context = {
        'lista': lista,
        'detalles_monos': lista.detalles_monos.all(),
        'titulo': f'Registrar Ventas - {lista.nombre}'
    }
    
    return render(request, 'inventario/registrar_ventas_contaduria.html', context)


# ============================================================================
# PANEL UNIFICADO DE GESTIÓN DE LISTAS - SISTEMA DE 7 PASOS
# ============================================================================

@login_required
def panel_lista_produccion(request, lista_id):
    """Panel unificado para gestionar lista de producción con stepper visual de 7 pasos"""
    
    lista = get_object_or_404(ListaProduccion, id=lista_id, usuario_creador=request.user)
    
    # Definir los 7 pasos del proceso
    pasos = [
        {
            'numero': 1,
            'nombre': 'Creada',
            'estado_requerido': 'borrador',
            'icono': 'fas fa-check-circle',
            'color': 'success',
            'descripcion': 'Lista creada exitosamente'
        },
        {
            'numero': 2,
            'nombre': 'Lista de Compras',
            'estado_requerido': 'pendiente_compra',
            'icono': 'fas fa-file-download',
            'color': 'primary',
            'descripcion': 'Descargar lista de materiales a comprar'
        },
        {
            'numero': 3,
            'nombre': 'Registrar Compras',
            'estado_requerido': 'comprado',
            'icono': 'fas fa-shopping-cart',
            'color': 'info',
            'descripcion': 'Ingresar cantidades compradas'
        },
        {
            'numero': 4,
            'nombre': 'Materiales Listos',
            'estado_requerido': 'reabastecido',
            'icono': 'fas fa-box-check',
            'color': 'warning',
            'descripcion': 'Verificar inventario actualizado'
        },
        {
            'numero': 5,
            'nombre': 'Produciendo',
            'estado_requerido': 'en_produccion',
            'icono': 'fas fa-industry',
            'color': 'purple',
            'descripcion': 'Crear moños y registrar producción'
        },
        {
            'numero': 6,
            'nombre': 'Salida y Ventas',
            'estado_requerido': 'en_salida',
            'icono': 'fas fa-cash-register',
            'color': 'orange',
            'descripcion': 'Registrar ventas realizadas'
        },
        {
            'numero': 7,
            'nombre': 'Completado',
            'estado_requerido': 'finalizado',
            'icono': 'fas fa-trophy',
            'color': 'success',
            'descripcion': 'Lista finalizada exitosamente'
        }
    ]
    
    # Determinar paso actual
    mapa_estados_a_paso = {
        'borrador': 1,
        'pendiente_compra': 2,
        'comprado': 3,
        'reabastecido': 4,
        'en_produccion': 5,
        'en_salida': 6,
        'finalizado': 7
    }
    
    paso_actual = mapa_estados_a_paso.get(lista.estado, 1)
    
    # Marcar pasos como completados, actual o pendientes
    for paso in pasos:
        if paso['numero'] < paso_actual:
            paso['status'] = 'completado'
        elif paso['numero'] == paso_actual:
            paso['status'] = 'actual'
        else:
            paso['status'] = 'pendiente'
    
    # Obtener datos específicos según el paso actual
    materiales_necesarios = None
    materiales_faltantes = None
    detalles_monos = lista.detalles_monos.all()
    
    if paso_actual >= 2:
        materiales_faltantes = lista.resumen_materiales.filter(cantidad_faltante__gt=0)
    
    if paso_actual == 3:
        materiales_necesarios = lista.resumen_materiales.filter(cantidad_faltante__gt=0).select_related('material')
    
    # Determinar acción siguiente
    accion_siguiente = None
    
    if paso_actual == 1:
        accion_siguiente = {
            'texto': 'Descargar Lista de Compras',
            'url': 'inventario:generar_archivo_compras',
            'clase': 'btn-primary',
            'icono': 'fas fa-download'
        }
    elif paso_actual == 2:
        accion_siguiente = {
            'texto': 'Registrar Compras Realizadas',
            'url': 'inventario:verificar_compras',
            'clase': 'btn-success',
            'icono': 'fas fa-shopping-cart'
        }
    elif paso_actual == 3:
        # Verificar si ya se registraron todas las compras
        if lista.resumen_materiales.filter(cantidad_faltante__gt=0).count() == 0:
            accion_siguiente = {
                'texto': 'Continuar a Materiales Listos',
                'url': 'inventario:enviar_a_reabastecimiento',
                'clase': 'btn-success',
                'icono': 'fas fa-arrow-right',
                'tipo': 'POST'
            }
    elif paso_actual == 4:
        accion_siguiente = {
            'texto': 'Iniciar Producción',
            'url': 'inventario:iniciar_produccion',
            'clase': 'btn-warning',
            'icono': 'fas fa-play',
            'tipo': 'POST'
        }
    elif paso_actual == 5:
        accion_siguiente = {
            'texto': 'Enviar a Salida',
            'url': 'inventario:enviar_a_salida',
            'clase': 'btn-info',
            'icono': 'fas fa-truck',
            'tipo': 'POST'
        }
    elif paso_actual == 6:
        accion_siguiente = {
            'texto': 'Registrar Ventas',
            'url': 'inventario:registrar_ventas_contaduria',
            'clase': 'btn-success',
            'icono': 'fas fa-dollar-sign'
        }
    
    # Verificar si aún quedan materiales faltantes (para paso 3)
    materiales_aun_faltantes = lista.resumen_materiales.filter(cantidad_faltante__gt=0).count()
    
    context = {
        'titulo': f'Panel de Gestión - {lista.nombre}',
        'lista': lista,
        'pasos': pasos,
        'paso_actual': paso_actual,
        'detalles_monos': detalles_monos,
        'materiales_necesarios': materiales_necesarios,
        'materiales_faltantes': materiales_faltantes,
        'materiales_aun_faltantes': materiales_aun_faltantes,
        'accion_siguiente': accion_siguiente,
    }
    
    return render(request, 'inventario/panel_lista_produccion.html', context)
