from django.contrib import admin
from .models import Material, Insumo, Movimiento, Reabastecimiento, TipoMono, RecetaProduccion, SimulacionProduccion

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

@admin.register(Reabastecimiento)
class ReabastecimientoAdmin(admin.ModelAdmin):
    list_display = ['material', 'cantidad_solicitada', 'cantidad_recibida', 'estado', 'prioridad', 'proveedor', 'fecha_solicitud']
    list_filter = ['estado', 'prioridad', 'automatico', 'fecha_solicitud', 'material__categoria']
    search_fields = ['material__nombre', 'material__codigo', 'proveedor', 'notas']
    readonly_fields = ['fecha_solicitud', 'created_at', 'updated_at', 'dias_desde_solicitud', 'esta_retrasado', 'porcentaje_completado']
    date_hierarchy = 'fecha_solicitud'
    
    fieldsets = (
        ('Información del Pedido', {
            'fields': ('material', 'cantidad_solicitada', 'cantidad_recibida', 'proveedor')
        }),
        ('Estado y Prioridad', {
            'fields': ('estado', 'prioridad', 'automatico')
        }),
        ('Fechas', {
            'fields': ('fecha_solicitud', 'fecha_estimada_llegada', 'fecha_recepcion')
        }),
        ('Costos', {
            'fields': ('precio_estimado', 'precio_real')
        }),
        ('Configuración', {
            'fields': ('stock_minimo_sugerido', 'notas')
        }),
        ('Métricas', {
            'fields': ('dias_desde_solicitud', 'esta_retrasado', 'porcentaje_completado'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(TipoMono)
class TipoMonoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'precio_venta_sugerido', 'tiempo_produccion_minutos', 'activo']
    list_filter = ['activo', 'created_at']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['created_at', 'updated_at']

class RecetaProduccionInline(admin.TabularInline):
    model = RecetaProduccion
    extra = 1

TipoMonoAdmin.inlines = [RecetaProduccionInline]

@admin.register(RecetaProduccion)
class RecetaProduccionAdmin(admin.ModelAdmin):
    list_display = ['tipo_mono', 'insumo', 'cantidad_necesaria', 'es_opcional']
    list_filter = ['tipo_mono', 'es_opcional']

@admin.register(SimulacionProduccion)  
class SimulacionProduccionAdmin(admin.ModelAdmin):
    list_display = ['nombre_simulacion', 'tipo_mono', 'cantidad_a_producir', 'ganancia_neta', 'stock_suficiente']
    list_filter = ['stock_suficiente', 'tipo_mono']
    readonly_fields = ['costo_total_materiales', 'ingreso_total', 'ganancia_neta', 'margen_porcentaje', 'stock_suficiente', 'fecha_simulacion']
