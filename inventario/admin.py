from django.contrib import admin
from .models import Material, Insumo, Movimiento

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'tipo_material', 'cantidad_disponible', 'costo_unitario', 'categoria']
    list_filter = ['tipo_material', 'unidad_base', 'categoria']
    search_fields = ['codigo', 'nombre', 'descripcion']
    readonly_fields = ['costo_unitario', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'categoria')
        }),
        ('Configuración de Material', {
            'fields': ('tipo_material', 'unidad_base', 'factor_conversion')
        }),
        ('Inventario y Costos', {
            'fields': ('cantidad_disponible', 'precio_compra', 'costo_unitario')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'material', 'cantidad_por_unidad', 'unidad_consumo']
    list_filter = ['unidad_consumo', 'material__categoria']
    search_fields = ['nombre', 'descripcion', 'material__nombre']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ['material', 'tipo_movimiento', 'cantidad', 'fecha', 'detalle']
    list_filter = ['tipo_movimiento', 'fecha', 'material__categoria']
    search_fields = ['material__nombre', 'material__codigo', 'detalle']
    readonly_fields = ['created_at']
    date_hierarchy = 'fecha'
