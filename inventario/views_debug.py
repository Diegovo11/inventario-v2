from django.http import HttpResponse, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Material, Monos, RecetaMonos, ListaProduccion, VentaMonos, MovimientoEfectivo
from django.db.models import Sum, Count

@staff_member_required
def verificar_unidades_web(request):
    """Vista temporal para verificar unidades de materiales y recetas"""
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Verificación de Unidades</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }
            h2 { color: #555; margin-top: 30px; border-bottom: 2px solid #28a745; padding-bottom: 8px; }
            .material { background: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #007bff; border-radius: 4px; }
            .mono { background: #fff3cd; padding: 15px; margin: 10px 0; border-left: 4px solid #ffc107; border-radius: 4px; }
            .receta { background: #d1ecf1; padding: 10px; margin: 5px 0 5px 20px; border-left: 3px solid #17a2b8; border-radius: 3px; }
            .warning { color: #dc3545; font-weight: bold; }
            .success { color: #28a745; font-weight: bold; }
            .badge { display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }
            .badge-cm { background: #007bff; color: white; }
            .badge-unidades { background: #28a745; color: white; }
            .badge-paquete { background: #6f42c1; color: white; }
            .badge-rollo { background: #fd7e14; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Verificación de Unidades de Materiales y Recetas</h1>
    """
    
    # SECCIÓN 1: MATERIALES
    html += "<h2>📦 MATERIALES ACTIVOS</h2>"
    
    materiales = Material.objects.filter(activo=True).order_by('codigo')
    
    for material in materiales:
        unidad_badge = "badge-cm" if material.unidad_base == "cm" else "badge-unidades"
        tipo_badge = "badge-rollo" if material.tipo_material == "rollo" else "badge-paquete"
        
        html += f"""
        <div class="material">
            <strong>{material.codigo} - {material.nombre}</strong><br>
            <span class="badge {unidad_badge}">{material.unidad_base}</span>
            <span class="badge {tipo_badge}">{material.tipo_material}</span>
            <br><br>
            Factor conversión: {material.factor_conversion}<br>
            Disponible: <strong>{material.cantidad_disponible} {material.unidad_base}</strong>
        """
        
        # Verificar recetas que usan este material
        recetas_usando = RecetaMonos.objects.filter(material=material).select_related('monos')
        
        if recetas_usando.exists():
            html += f"<br><br>🎀 <span class='success'>Usado en {recetas_usando.count()} receta(s):</span><br>"
            for receta in recetas_usando:
                html += f"""
                <div class="receta">
                    {receta.monos.codigo} ({receta.monos.nombre}): 
                    <strong>{receta.cantidad_necesaria} {material.unidad_base}</strong> por moño
                </div>
                """
        else:
            html += f"<br><br><span class='warning'>⚠️ No se usa en ninguna receta</span>"
        
        html += "</div>"
    
    # SECCIÓN 2: MOÑOS Y SUS RECETAS
    html += "<h2>🎀 MOÑOS Y SUS RECETAS</h2>"
    
    monos_all = Monos.objects.filter(activo=True).order_by('codigo')
    
    for monos in monos_all:
        recetas = monos.recetas.all().select_related('material')
        
        html += f"""
        <div class="mono">
            <strong>{monos.codigo} - {monos.nombre}</strong><br>
        """
        
        if recetas.exists():
            html += f"<span class='success'>✅ Recetas: {recetas.count()}</span><br><br>"
            
            for receta in recetas:
                unidad_badge = "badge-cm" if receta.material.unidad_base == "cm" else "badge-unidades"
                
                html += f"""
                <div class="receta">
                    📦 {receta.material.nombre}: 
                    <strong>{receta.cantidad_necesaria}</strong> 
                    <span class="badge {unidad_badge}">{receta.material.unidad_base}</span>
                </div>
                """
        else:
            html += f"<span class='warning'>⚠️ SIN RECETAS CONFIGURADAS</span>"
        
        html += "</div>"
    
    html += """
            <hr style="margin-top: 30px;">
            <p style="text-align: center; color: #666;">
                ✅ Verificación completada - 
                <a href="/" style="color: #007bff;">Volver al inicio</a>
            </p>
        </div>
    </body>
    </html>
    """
    
    return HttpResponse(html)


@staff_member_required
def simular_descuento_lista(request, lista_id):
    """Simula el descuento de materiales sin ejecutarlo realmente"""
    
    try:
        lista = ListaProduccion.objects.get(id=lista_id)
    except ListaProduccion.DoesNotExist:
        return JsonResponse({'error': 'Lista no encontrada'}, status=404)
    
    resultado = {
        'lista_id': lista.id,
        'estado': lista.estado,
        'detalles': []
    }
    
    for detalle in lista.detalles_monos.all():
        monos = detalle.monos
        cantidad_total_planificada = detalle.cantidad_total_planificada
        
        detalle_info = {
            'monos': f"{monos.codigo} - {monos.nombre}",
            'cantidad_planificada': float(cantidad_total_planificada),
            'recetas': []
        }
        
        recetas = monos.recetas.all()
        
        if recetas.count() == 0:
            detalle_info['warning'] = 'NO HAY RECETAS PARA ESTE MOÑO'
        
        for receta in recetas:
            material = receta.material
            cantidad_por_mono = receta.cantidad_necesaria
            cantidad_total_necesaria = cantidad_por_mono * cantidad_total_planificada
            
            receta_info = {
                'material': material.nombre,
                'material_codigo': material.codigo,
                'unidad_base': material.unidad_base,
                'cantidad_por_mono': float(cantidad_por_mono),
                'cantidad_total_necesaria': float(cantidad_total_necesaria),
                'disponible': float(material.cantidad_disponible),
                'suficiente': material.cantidad_disponible >= cantidad_total_necesaria,
                'nuevo_inventario': float(material.cantidad_disponible - cantidad_total_necesaria)
            }
            
            detalle_info['recetas'].append(receta_info)
        
        resultado['detalles'].append(detalle_info)
    
    return JsonResponse(resultado, json_dumps_params={'indent': 2})


def es_superuser(user):
    return user.is_superuser


@login_required
@user_passes_test(es_superuser)
def diagnostico_ventas_web(request):
    """Vista web para diagnóstico del sistema de ventas"""
    
    diagnostico = {
        'ventas': {},
        'listas': {},
        'movimientos': {},
        'monos': {},
        'analytics': {},
        'migraciones': {},
        'resumen': {}
    }
    
    # 1. Verificar VentaMonos
    try:
        total_ventas = VentaMonos.objects.count()
        diagnostico['ventas']['total'] = total_ventas
        diagnostico['ventas']['existe_tabla'] = True
        
        if total_ventas > 0:
            ultimas = VentaMonos.objects.select_related('monos', 'lista_produccion').order_by('-fecha')[:5]
            diagnostico['ventas']['ultimas'] = [{
                'mono': v.monos.nombre,
                'cantidad': v.cantidad_vendida,
                'tipo': v.tipo_venta,
                'fecha': v.fecha,
                'ingreso': v.ingreso_total,
                'ganancia': v.ganancia_total,
                'lista': v.lista_produccion.nombre if v.lista_produccion else 'Sin lista'
            } for v in ultimas]
        else:
            diagnostico['ventas']['ultimas'] = []
            
    except Exception as e:
        diagnostico['ventas']['error'] = str(e)
        diagnostico['ventas']['existe_tabla'] = False
    
    # 2. Verificar listas finalizadas
    try:
        listas_finalizadas = ListaProduccion.objects.filter(estado='finalizado')
        diagnostico['listas']['total_finalizadas'] = listas_finalizadas.count()
        
        if listas_finalizadas.exists():
            diagnostico['listas']['detalles'] = []
            for lista in listas_finalizadas[:10]:
                ventas_lista = VentaMonos.objects.filter(lista_produccion=lista).count()
                diagnostico['listas']['detalles'].append({
                    'nombre': lista.nombre,
                    'fecha': lista.fecha_modificacion,
                    'ventas_asociadas': ventas_lista,
                    'tiene_ventas': ventas_lista > 0
                })
    except Exception as e:
        diagnostico['listas']['error'] = str(e)
    
    # 3. Verificar MovimientoEfectivo de ventas
    try:
        movimientos_venta = MovimientoEfectivo.objects.filter(
            tipo_movimiento='ingreso',
            categoria='venta'
        ).order_by('-fecha')
        
        diagnostico['movimientos']['total'] = movimientos_venta.count()
        
        if movimientos_venta.exists():
            diagnostico['movimientos']['ultimos'] = [{
                'concepto': m.concepto,
                'fecha': m.fecha,
                'monto': m.monto
            } for m in movimientos_venta[:5]]
    except Exception as e:
        diagnostico['movimientos']['error'] = str(e)
    
    # 4. Verificar moños disponibles
    try:
        monos = Monos.objects.filter(activo=True)
        diagnostico['monos']['total_activos'] = monos.count()
        diagnostico['monos']['detalles'] = []
        
        for mono in monos:
            ventas_mono = VentaMonos.objects.filter(monos=mono).count()
            diagnostico['monos']['detalles'].append({
                'nombre': mono.nombre,
                'tipo': mono.tipo_venta,
                'ventas': ventas_mono
            })
    except Exception as e:
        diagnostico['monos']['error'] = str(e)
    
    # 5. Verificar datos para analytics (últimos 12 meses)
    try:
        fecha_fin = timezone.now()
        fecha_inicio = fecha_fin - timedelta(days=365)
        
        ventas_en_rango = VentaMonos.objects.filter(
            fecha__gte=fecha_inicio,
            fecha__lte=fecha_fin
        )
        
        diagnostico['analytics']['fecha_inicio'] = fecha_inicio
        diagnostico['analytics']['fecha_fin'] = fecha_fin
        diagnostico['analytics']['total_ventas'] = ventas_en_rango.count()
        
        if ventas_en_rango.exists():
            stats = ventas_en_rango.values('monos__nombre').annotate(
                total_cantidad=Sum('cantidad_vendida'),
                total_ingresos=Sum('ingreso_total'),
                total_ganancia=Sum('ganancia_total'),
                num_ventas=Count('id')
            ).order_by('-total_cantidad')
            
            diagnostico['analytics']['estadisticas'] = [{
                'mono': s['monos__nombre'],
                'cantidad': s['total_cantidad'],
                'ingresos': s['total_ingresos'],
                'ganancia': s['total_ganancia'],
                'num_ventas': s['num_ventas']
            } for s in stats]
        else:
            diagnostico['analytics']['estadisticas'] = []
            
    except Exception as e:
        diagnostico['analytics']['error'] = str(e)
    
    # 6. Verificar migraciones
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT name, applied FROM django_migrations WHERE app='inventario' ORDER BY applied DESC LIMIT 10")
            migraciones = cursor.fetchall()
            
        diagnostico['migraciones']['ultimas'] = [{
            'nombre': m[0],
            'fecha': m[1],
            'es_ventamonos': '0008_ventamonos' in m[0]
        } for m in migraciones]
        
    except Exception as e:
        diagnostico['migraciones']['error'] = str(e)
    
    # 7. Generar resumen
    total_ventas_obj = diagnostico['ventas'].get('total', 0)
    
    if total_ventas_obj == 0:
        diagnostico['resumen']['estado'] = 'sin_ventas'
        diagnostico['resumen']['mensaje'] = 'No hay ventas registradas en VentaMonos'
        diagnostico['resumen']['causas'] = [
            'Las ventas se registraron ANTES de aplicar la migración 0008_ventamonos',
            'Las ventas se registraron pero hubo un error al crear VentaMonos',
            'Aún no se han registrado ventas después del último deploy'
        ]
        diagnostico['resumen']['solucion'] = 'Registra una venta de prueba desde el Paso 6'
    elif diagnostico['analytics'].get('total_ventas', 0) == 0:
        diagnostico['resumen']['estado'] = 'ventas_fuera_rango'
        diagnostico['resumen']['mensaje'] = f'Hay {total_ventas_obj} ventas pero fuera del rango de fechas de analytics'
        diagnostico['resumen']['solucion'] = 'Verifica las fechas de las ventas o selecciona "Todo" en el periodo de analytics'
    else:
        diagnostico['resumen']['estado'] = 'correcto'
        diagnostico['resumen']['mensaje'] = f'✅ Sistema funcionando correctamente con {total_ventas_obj} ventas'
        diagnostico['resumen']['solucion'] = 'Analytics debería mostrar estos datos correctamente'
    
    context = {
        'diagnostico': diagnostico,
        'titulo': 'Diagnóstico del Sistema de Ventas'
    }
    
    return render(request, 'inventario/diagnostico_ventas.html', context)


@login_required
@user_passes_test(es_superuser)
def migrar_ventas_antiguas_web(request):
    """Vista web para migrar ventas antiguas de MovimientoEfectivo a VentaMonos"""
    
    resultado = {
        'ejecutado': False,
        'dry_run': True,
        'ventas_creadas': 0,
        'ventas_ya_existen': 0,
        'errores': 0,
        'detalles': [],
        'errores_detalle': []
    }
    
    if request.method == 'POST':
        dry_run = request.POST.get('dry_run') == 'true'
        resultado['dry_run'] = dry_run
        resultado['ejecutado'] = True
        
        # Buscar MovimientoEfectivo de ventas
        movimientos_venta = MovimientoEfectivo.objects.filter(
            tipo_movimiento='ingreso',
            categoria='venta'
        ).order_by('fecha')
        
        for mov in movimientos_venta:
            try:
                if 'Lista:' in mov.concepto:
                    nombre_lista = mov.concepto.split('Lista:')[1].strip()
                    
                    detalle_mov = {
                        'concepto': mov.concepto,
                        'fecha': mov.fecha,
                        'monto': mov.monto,
                        'lista': nombre_lista,
                        'ventas_creadas': []
                    }
                    
                    try:
                        # Si hay múltiples listas con el mismo nombre, buscar la más cercana a la fecha del movimiento
                        listas_candidatas = ListaProduccion.objects.filter(nombre=nombre_lista, estado='finalizado')
                        
                        if listas_candidatas.count() == 0:
                            detalle_mov['estado'] = 'error'
                            detalle_mov['mensaje'] = f'No se encontró lista finalizada con nombre "{nombre_lista}"'
                            resultado['errores'] += 1
                            resultado['errores_detalle'].append(f"{mov.concepto}: {detalle_mov['mensaje']}")
                            resultado['detalles'].append(detalle_mov)
                            continue
                        elif listas_candidatas.count() == 1:
                            lista = listas_candidatas.first()
                        else:
                            # Múltiples listas: buscar la más cercana por fecha
                            from datetime import timedelta
                            lista = None
                            menor_diferencia = None
                            
                            for l in listas_candidatas:
                                if l.fecha_finalizacion:
                                    diferencia = abs((l.fecha_finalizacion - mov.fecha).total_seconds())
                                    if menor_diferencia is None or diferencia < menor_diferencia:
                                        menor_diferencia = diferencia
                                        lista = l
                            
                            if lista is None:
                                # Si ninguna tiene fecha_finalizacion, tomar la más reciente por fecha_creacion
                                lista = listas_candidatas.order_by('-fecha_creacion').first()
                            
                            detalle_mov['info_adicional'] = f'Se encontraron {listas_candidatas.count()} listas. Usando la más cercana en fecha.'
                        
                        # Verificar si ya existen ventas
                        ventas_existentes = VentaMonos.objects.filter(lista_produccion=lista)
                        
                        if ventas_existentes.exists():
                            detalle_mov['estado'] = 'ya_existe'
                            detalle_mov['mensaje'] = f'Ya existen {ventas_existentes.count()} ventas'
                            resultado['ventas_ya_existen'] += ventas_existentes.count()
                            resultado['detalles'].append(detalle_mov)
                            continue
                        
                        # Obtener detalles de moños
                        detalles = lista.detalles_monos.all()
                        ventas_para_crear = []
                        
                        for detalle in detalles:
                            if detalle.cantidad_producida > 0:
                                cantidad_vendida = detalle.cantidad_producida
                                mono = detalle.monos
                                precio_unitario = mono.precio_venta
                                ingreso_total = Decimal(cantidad_vendida) * precio_unitario
                                costo_unitario = mono.costo_produccion
                                ganancia_total = ingreso_total - (costo_unitario * cantidad_vendida)
                                
                                venta_dict = {
                                    'mono': mono.nombre,
                                    'cantidad': cantidad_vendida,
                                    'tipo': mono.tipo_venta,
                                    'ingreso': float(ingreso_total),
                                    'ganancia': float(ganancia_total)
                                }
                                
                                if not dry_run:
                                    venta = VentaMonos.objects.create(
                                        lista_produccion=lista,
                                        monos=mono,
                                        cantidad_vendida=cantidad_vendida,
                                        tipo_venta=mono.tipo_venta,
                                        precio_unitario=precio_unitario,
                                        ingreso_total=ingreso_total,
                                        costo_unitario=costo_unitario,
                                        ganancia_total=ganancia_total,
                                        fecha=mov.fecha,
                                        usuario=mov.usuario
                                    )
                                
                                ventas_para_crear.append(venta_dict)
                                resultado['ventas_creadas'] += 1
                        
                        if ventas_para_crear:
                            detalle_mov['estado'] = 'creadas' if not dry_run else 'simuladas'
                            detalle_mov['ventas_creadas'] = ventas_para_crear
                            detalle_mov['mensaje'] = f'{"Creadas" if not dry_run else "Se crearían"} {len(ventas_para_crear)} ventas'
                        else:
                            detalle_mov['estado'] = 'sin_datos'
                            detalle_mov['mensaje'] = 'No hay detalles con cantidad_producida > 0'
                        
                        resultado['detalles'].append(detalle_mov)
                        
                    except ListaProduccion.DoesNotExist:
                        error = {
                            'concepto': mov.concepto,
                            'error': f'Lista "{nombre_lista}" no encontrada'
                        }
                        resultado['errores_detalle'].append(error)
                        resultado['errores'] += 1
                        
            except Exception as e:
                error = {
                    'concepto': mov.concepto,
                    'error': str(e)
                }
                resultado['errores_detalle'].append(error)
                resultado['errores'] += 1
    
    context = {
        'resultado': resultado,
        'titulo': 'Migrar Ventas Antiguas'
    }
    
    return render(request, 'inventario/migrar_ventas_antiguas.html', context)


@login_required
def diagnostico_perfiles_web(request):
    """Diagnostica y repara perfiles de usuario"""
    from django.contrib.auth.models import User
    from .models import UserProfile
    
    # Verificar que sea superuser o staff
    if not (request.user.is_superuser or request.user.is_staff):
        return render(request, 'inventario/sin_permiso.html', {
            'mensaje': 'Solo administradores pueden acceder a esta herramienta.'
        }, status=403)
    
    resultado = {
        'usuarios_total': 0,
        'con_perfil': 0,
        'sin_perfil': 0,
        'reparados': 0,
        'errores': 0,
        'detalles': []
    }
    
    # Si viene con acción de reparar
    reparar = request.GET.get('reparar') == 'true'
    
    try:
        usuarios = User.objects.all()
        resultado['usuarios_total'] = usuarios.count()
        
        for user in usuarios:
            detalle = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
                'tiene_perfil': False,
                'nivel': None,
                'accion': None
            }
            
            # Verificar si tiene perfil
            try:
                perfil = user.userprofile
                detalle['tiene_perfil'] = True
                detalle['nivel'] = perfil.get_nivel_display()
                resultado['con_perfil'] += 1
            except UserProfile.DoesNotExist:
                detalle['tiene_perfil'] = False
                resultado['sin_perfil'] += 1
                
                # Si está en modo reparar, crear el perfil
                if reparar:
                    try:
                        nivel = 'superuser' if user.is_superuser else 'invitado'
                        perfil = UserProfile.objects.create(user=user, nivel=nivel)
                        detalle['accion'] = f'✅ Perfil creado con nivel {perfil.get_nivel_display()}'
                        resultado['reparados'] += 1
                    except Exception as e:
                        detalle['accion'] = f'❌ Error: {str(e)}'
                        resultado['errores'] += 1
                else:
                    detalle['accion'] = '⚠️ Sin perfil - necesita reparación'
            
            resultado['detalles'].append(detalle)
    
    except Exception as e:
        resultado['error_general'] = str(e)
    
    # Verificar si se está promoviendo un usuario
    promover_user_id = request.GET.get('promover')
    if promover_user_id:
        try:
            user = User.objects.get(id=promover_user_id)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            
            if hasattr(user, 'userprofile'):
                user.userprofile.nivel = 'superuser'
                user.userprofile.save()
            
            resultado['promovido'] = f'✅ Usuario {user.username} promovido a SUPERUSUARIO'
        except Exception as e:
            resultado['error_promocion'] = f'❌ Error al promover: {str(e)}'
    
    context = {
        'resultado': resultado,
        'reparar': reparar,
        'titulo': 'Diagnóstico de Perfiles de Usuario'
    }
    
    return render(request, 'inventario/diagnostico_perfiles.html', context)
