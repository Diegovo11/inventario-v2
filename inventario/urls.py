from django.urls import path
from . import views

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),
    
    # Listas
    path('materiales/', views.materiales_list, name='materiales_list'),
    path('insumos/', views.insumos_list, name='insumos_list'),
    path('movimientos/', views.movimientos_list, name='movimientos_list'),
    
    # Funcionalidades avanzadas
    path('reabastecimiento/', views.reabastecimiento, name='reabastecimiento'),
    path('simulador/', views.simulador, name='simulador'),
    path('reportes/', views.reportes, name='reportes'),
    
    # Crear elementos
    path('material/nuevo/', views.material_create, name='material_create'),
    path('insumo/nuevo/', views.insumo_create, name='insumo_create'),
    path('movimiento/nuevo/', views.movimiento_create, name='movimiento_create'),
]