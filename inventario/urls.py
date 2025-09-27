from django.urls import path
from . import views

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),
    
    # Listas
    path('materiales/', views.materiales_list, name='materiales_list'),
    path('insumos/', views.insumos_list, name='insumos_list'),
    path('movimientos/', views.movimientos_list, name='movimientos_list'),
    
    # Sistema de reabastecimiento
    path('reabastecimiento/', views.reabastecimiento_list, name='reabastecimiento_list'),
    path('reabastecimiento/nuevo/', views.reabastecimiento_create, name='reabastecimiento_create'),
    path('reabastecimiento/<int:pk>/editar/', views.reabastecimiento_update, name='reabastecimiento_update'),
    path('stock-bajo/', views.stock_bajo_check, name='stock_bajo_check'),
    
    # Sistema de producción y simulador
    path('simulador/', views.simulador, name='simulador'),
    path('tipos-mono/', views.tipos_mono_list, name='tipos_mono_list'),
    path('tipos-mono/nuevo/', views.tipo_mono_create, name='tipo_mono_create'),
    path('simulaciones/', views.simulaciones_list, name='simulaciones_list'),
    
    # Otras funcionalidades
    path('reportes/', views.reportes, name='reportes'),
    
    # Crear elementos
    path('material/nuevo/', views.material_create, name='material_create'),
    path('insumo/nuevo/', views.insumo_create, name='insumo_create'),
    path('movimiento/nuevo/', views.movimiento_create, name='movimiento_create'),
]