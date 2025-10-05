from django.urls import path
from . import views
from .views_contaduria import contaduria_home, flujo_efectivo, registrar_movimiento_efectivo, estado_resultados, exportar_excel_efectivo
from . import views_analytics
from .views_debug import verificar_unidades_web, simular_descuento_lista

app_name = 'inventario'

urlpatterns = [
    # Vista principal
    path('', views.home, name='home'),
    
    # Materiales
    path('materiales/', views.lista_materiales, name='lista_materiales'),
    path('material/<int:material_id>/', views.detalle_material, name='detalle_material'),
    path('material/agregar/', views.agregar_material, name='agregar_material'),
    path('material/<int:material_id>/editar/', views.editar_material, name='editar_material'),
    
    # AJAX
    path('ajax/material/<int:material_id>/info/', views.obtener_info_material, name='obtener_info_material'),
    
    # Moños
    path('monos/', views.lista_monos, name='lista_monos'),
    path('monos/<int:monos_id>/', views.detalle_monos, name='detalle_monos'),
    path('monos/agregar/', views.agregar_monos, name='agregar_monos'),
    path('monos/<int:monos_id>/editar/', views.editar_monos, name='editar_monos'),
    
    # Sistema de Simulación (Legacy)
    path('simulador/', views.simulador, name='simulador'),
    path('simulaciones/', views.historial_simulaciones, name='historial_simulaciones'),
    path('simulacion/<int:simulacion_id>/', views.detalle_simulacion, name='detalle_simulacion'),
    
    # Sistema de Listas de Producción (Nuevo)
    path('listas-produccion/', views.listado_listas_produccion, name='listas_produccion'),
    path('lista-produccion/crear/', views.crear_lista_produccion, name='crear_lista_produccion'),
    path('lista-produccion/<int:lista_id>/editar/', views.editar_lista_produccion, name='editar_lista_produccion'),
    path('lista-produccion/<int:lista_id>/eliminar/', views.eliminar_lista_produccion, name='eliminar_lista_produccion'),
    path('lista-produccion/<int:lista_id>/generar-compras/', views.generar_archivo_compras, name='generar_archivo_compras'),
    path('lista-produccion/<int:lista_id>/marcar-comprado/', views.marcar_como_comprado, name='marcar_como_comprado'),
    path('lista-produccion/<int:lista_id>/enviar-reabastecimiento/', views.enviar_a_reabastecimiento, name='enviar_a_reabastecimiento'),
    path('lista-produccion/<int:lista_id>/registrar-entrada/', views.registrar_entrada_reabastecimiento, name='registrar_entrada_reabastecimiento'),
    path('lista-produccion/<int:lista_id>/enviar-salida/', views.enviar_a_salida, name='enviar_a_salida'),
    path('lista-produccion/<int:lista_id>/registrar-salida-materiales/', views.registrar_salida_materiales, name='registrar_salida_materiales'),
    path('lista-produccion/<int:lista_id>/registrar-ventas/', views.registrar_ventas_contaduria, name='registrar_ventas_contaduria'),
    path('lista-compras/', views.lista_de_compras, name='lista_de_compras'),
    path('compra-productos/', views.compra_productos, name='compra_productos'),
    path('reabastecimiento/', views.reabastecimiento, name='reabastecimiento'),
    path('lista-en-salida/', views.lista_en_salida, name='lista_en_salida'),
    path('lista-produccion/<int:lista_id>/', views.detalle_lista_produccion, name='detalle_lista_produccion'),
    # path('lista-produccion/<int:lista_id>/compras/', views.lista_compras, name='lista_compras'),
    # path('lista-produccion/<int:lista_id>/produccion/', views.posible_venta, name='posible_venta'),
    # path('lista-produccion/<int:lista_id>/finalizar/', views.venta_final, name='venta_final'),
    
    # Sistema de Entrada y Salida
    path('entrada-material/', views.entrada_material, name='entrada_material'),
    path('entrada-reabastecimiento/', views.entrada_material, name='reabastecimiento_list'),  # Redirect to entrada_material
    path('salida-material/', views.salida_material, name='salida_material'),
    path('historial-movimientos/', views.historial_movimientos, name='historial_movimientos'),
    
    # Integración Simulación-Inventario
    path('confirmar-produccion/<int:simulacion_id>/', views.confirmar_produccion, name='confirmar_produccion'),
    path('reabastecer-automatico/<int:simulacion_id>/', views.reabastecer_automatico, name='reabastecer_automatico'),
    path('procesar-simulacion/<int:simulacion_id>/', views.procesar_simulacion_completa, name='procesar_simulacion_completa'),
    path('reabastecer-simulacion/<int:simulacion_id>/', views.reabastecer_desde_simulacion, name='reabastecer_desde_simulacion'),
    path('entrada-rapida-simulacion/<int:simulacion_id>/', views.entrada_rapida_simulacion, name='entrada_rapida_simulacion'),
    path('generar-salida-directa/<int:simulacion_id>/', views.generar_salida_directa, name='generar_salida_directa'),
    path('generar-entrada-faltante/<int:simulacion_id>/', views.generar_entrada_faltante, name='generar_entrada_faltante'),
    
    # Sistema de Contaduría y Finanzas
    path('contaduria/', contaduria_home, name='contaduria_home'),
    path('contaduria/flujo-efectivo/', flujo_efectivo, name='flujo_efectivo'),
    path('contaduria/registrar-movimiento/', registrar_movimiento_efectivo, name='registrar_movimiento_efectivo'),
    path('contaduria/estado-resultados/', estado_resultados, name='estado_resultados'),
    path('contaduria/exportar-excel/', exportar_excel_efectivo, name='exportar_excel_efectivo'),
    
    # Sistema de Análisis y Reportes
    path('analytics/', views_analytics.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/mono/<int:mono_id>/', views_analytics.analytics_detalle_mono, name='analytics_detalle_mono'),
    
    # DEBUG - Vista temporal para verificar unidades
    path('debug/verificar-unidades/', verificar_unidades_web, name='verificar_unidades_web'),
    path('debug/simular-descuento/<int:lista_id>/', simular_descuento_lista, name='simular_descuento_lista'),
    
    # AJAX
    path('api/monos/<int:monos_id>/', views.get_monos_info, name='get_monos_info'),
    path('material-info-entrada/<int:material_id>/', views.material_info_entrada, name='material_info_entrada'),
    path('material-info-salida/<int:material_id>/', views.material_info_salida, name='material_info_salida'),
    path('api/material-info/', views.material_info_api, name='material_info_api'),
    path('detalle-movimiento/<int:movimiento_id>/', views.detalle_movimiento_ajax, name='detalle_movimiento_ajax'),

]