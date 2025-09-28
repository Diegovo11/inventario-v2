from django.contrib import admin
from django.utils.html import format_html
from .models import (Material, Movimiento, ConfiguracionSistema, Monos, RecetaMonos, 
                   Simulacion, DetalleSimulacion, MovimientoEfectivo, ListaProduccion, 
                   DetalleListaMonos, ResumenMateriales)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 
        'nombre', 
        'categoria',
        'tipo_material', 
        'cantidad_disponible', 
        'unidad_base',
        'costo_unitario_formatted',
        'valor_inventario_formatted',
        'stock_status'
    ]
    list_filter = ['tipo_material', 'unidad_base', 'categoria', 'activo']
    search_fields = ['codigo', 'nombre', 'categoria']
    list_editable = ['cantidad_disponible']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion', 'costo_unitario', 'valor_inventario']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'categoria', 'activo')
        }),
        ('Configuración de Material', {
            'fields': ('tipo_material', 'unidad_base', 'factor_conversion')
        }),
        ('Inventario y Costos', {
            'fields': ('cantidad_disponible', 'precio_compra', 'costo_unitario', 'valor_inventario')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        })
    )
    
    def costo_unitario_formatted(self, obj):
        return f"${obj.costo_unitario:.2f}"
    costo_unitario_formatted.short_description = "Costo Unitario"
    
    def valor_inventario_formatted(self, obj):
        return f"${obj.valor_inventario:.2f}"
    valor_inventario_formatted.short_description = "Valor Inventario"
    
    def stock_status(self, obj):
        if obj.cantidad_disponible <= 10:
            color = 'red'
            status = 'Bajo'
        elif obj.cantidad_disponible <= 50:
            color = 'orange'
            status = 'Medio'
        else:
            color = 'green'
            status = 'Bueno'
        
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            status
        )
    stock_status.short_description = "Estado Stock"


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = [
        'fecha',
        'material',
        'tipo_movimiento',
        'cantidad',
        'cantidad_anterior',
        'cantidad_nueva',
        'usuario'
    ]
    list_filter = ['tipo_movimiento', 'fecha', 'material__categoria']
    search_fields = ['material__codigo', 'material__nombre', 'detalle']
    readonly_fields = ['fecha']
    date_hierarchy = 'fecha'
    
    fieldsets = (
        ('Movimiento', {
            'fields': ('material', 'tipo_movimiento', 'cantidad', 'detalle')
        }),
        ('Estado del Inventario', {
            'fields': ('cantidad_anterior', 'cantidad_nueva')
        }),
        ('Información del Sistema', {
            'fields': ('usuario', 'fecha'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('material', 'usuario')


@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    list_display = ['nombre_empresa', 'moneda', 'stock_minimo_alerta']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
    
    fieldsets = (
        ('Configuración General', {
            'fields': ('nombre_empresa', 'moneda', 'stock_minimo_alerta')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        # Solo permitir una configuración
        return not ConfiguracionSistema.objects.exists()


class RecetaMonosInline(admin.TabularInline):
    """Inline para gestionar recetas de moños"""
    model = RecetaMonos
    extra = 1
    fields = ['material', 'cantidad_necesaria']
    autocomplete_fields = ['material']


@admin.register(Monos)
class MonosAdmin(admin.ModelAdmin):
    list_display = [
        'codigo',
        'nombre',
        'tipo_venta',
        'precio_venta_formatted',
        'costo_produccion_formatted',
        'ganancia_unitaria_formatted',
        'activo'
    ]
    list_filter = ['tipo_venta', 'activo']
    search_fields = ['codigo', 'nombre', 'descripcion']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion', 'costo_produccion', 'ganancia_unitaria']
    inlines = [RecetaMonosInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'activo')
        }),
        ('Venta y Costos', {
            'fields': ('tipo_venta', 'precio_venta', 'costo_produccion', 'ganancia_unitaria')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        })
    )
    
    def precio_venta_formatted(self, obj):
        return f"${obj.precio_venta:.2f}"
    precio_venta_formatted.short_description = "Precio Venta"
    
    def costo_produccion_formatted(self, obj):
        return f"${obj.costo_produccion:.2f}"
    costo_produccion_formatted.short_description = "Costo Producción"
    
    def ganancia_unitaria_formatted(self, obj):
        ganancia = obj.ganancia_unitaria
        color = 'green' if ganancia > 0 else 'red' if ganancia < 0 else 'orange'
        return format_html(
            '<span style="color: {};">${:.2f}</span>',
            color,
            ganancia
        )
    ganancia_unitaria_formatted.short_description = "Ganancia Unitaria"


@admin.register(RecetaMonos)
class RecetaMonosAdmin(admin.ModelAdmin):
    list_display = ['monos', 'material', 'cantidad_necesaria', 'costo_material_formatted']
    list_filter = ['monos', 'material__categoria']
    search_fields = ['monos__nombre', 'material__nombre']
    autocomplete_fields = ['monos', 'material']
    
    def costo_material_formatted(self, obj):
        return f"${obj.costo_material:.2f}"
    costo_material_formatted.short_description = "Costo Material"


class DetalleSimulacionInline(admin.TabularInline):
    """Inline para ver detalles de simulación"""
    model = DetalleSimulacion
    extra = 0
    readonly_fields = [
        'material', 'cantidad_necesaria', 'cantidad_disponible', 
        'cantidad_faltante', 'cantidad_a_comprar', 'unidades_completas_comprar',
        'costo_compra_necesaria', 'suficiente_stock'
    ]
    can_delete = False


@admin.register(Simulacion)
class SimulacionAdmin(admin.ModelAdmin):
    list_display = [
        'fecha_creacion',
        'monos',
        'cantidad_producir',
        'tipo_venta',
        'cantidad_total_monos',
        'costo_total_produccion_formatted',
        'ingreso_total_venta_formatted',
        'ganancia_estimada_formatted',
        'necesita_compras'
    ]
    list_filter = ['necesita_compras', 'tipo_venta', 'fecha_creacion']
    search_fields = ['monos__nombre', 'monos__codigo']
    readonly_fields = [
        'cantidad_total_monos', 'costo_total_produccion', 'ingreso_total_venta',
        'ganancia_estimada', 'necesita_compras', 'costo_total_compras', 'fecha_creacion'
    ]
    date_hierarchy = 'fecha_creacion'
    inlines = [DetalleSimulacionInline]
    
    fieldsets = (
        ('Configuración de Simulación', {
            'fields': ('monos', 'cantidad_producir', 'tipo_venta', 'precio_venta_unitario')
        }),
        ('Resultados Calculados', {
            'fields': (
                'cantidad_total_monos', 'costo_total_produccion', 'ingreso_total_venta',
                'ganancia_estimada', 'necesita_compras', 'costo_total_compras'
            )
        }),
        ('Sistema', {
            'fields': ('usuario', 'fecha_creacion'),
            'classes': ('collapse',)
        })
    )
    
    def costo_total_produccion_formatted(self, obj):
        return f"${obj.costo_total_produccion:.2f}"
    costo_total_produccion_formatted.short_description = "Costo Total"
    
    def ingreso_total_venta_formatted(self, obj):
        return f"${obj.ingreso_total_venta:.2f}"
    ingreso_total_venta_formatted.short_description = "Ingreso Total"
    
    def ganancia_estimada_formatted(self, obj):
        ganancia = obj.ganancia_estimada
        color = 'green' if ganancia > 0 else 'red' if ganancia < 0 else 'orange'
        return format_html(
            '<span style="color: {};">${:.2f}</span>',
            color,
            ganancia
        )
    ganancia_estimada_formatted.short_description = "Ganancia Estimada"


@admin.register(DetalleSimulacion)
class DetalleSimulacionAdmin(admin.ModelAdmin):
    list_display = [
        'simulacion',
        'material',
        'cantidad_necesaria',
        'cantidad_disponible',
        'suficiente_stock',
        'cantidad_faltante',
        'unidades_completas_comprar',
        'costo_compra_necesaria_formatted'
    ]
    list_filter = ['suficiente_stock', 'material__categoria']
    search_fields = ['simulacion__monos__nombre', 'material__nombre']
    readonly_fields = [
        'cantidad_faltante', 'cantidad_a_comprar', 'unidades_completas_comprar',
        'costo_compra_necesaria', 'suficiente_stock'
    ]
    
    def costo_compra_necesaria_formatted(self, obj):
        return f"${obj.costo_compra_necesaria:.2f}" if obj.costo_compra_necesaria > 0 else "-"
    costo_compra_necesaria_formatted.short_description = "Costo Compra"


@admin.register(MovimientoEfectivo)
class MovimientoEfectivoAdmin(admin.ModelAdmin):
    """Administración de movimientos de efectivo"""
    list_display = [
        'fecha',
        'concepto',
        'tipo_movimiento_badge',
        'categoria',
        'monto_formatted',
        'saldo_nuevo_formatted',
        'automatico_badge',
        'usuario'
    ]
    list_filter = [
        'tipo_movimiento',
        'categoria',
        'automatico',
        'fecha',
        'usuario'
    ]
    search_fields = ['concepto', 'categoria']
    readonly_fields = ['saldo_anterior', 'saldo_nuevo', 'automatico', 'movimiento_inventario', 'simulacion_relacionada']
    date_hierarchy = 'fecha'
    
    fieldsets = [
        ('Información del Movimiento', {
            'fields': [
                'concepto',
                'tipo_movimiento',
                'categoria',
                'monto'
            ]
        }),
        ('Saldos', {
            'fields': [
                'saldo_anterior',
                'saldo_nuevo'
            ],
            'classes': ['collapse']
        }),
        ('Referencias del Sistema', {
            'fields': [
                'automatico',
                'usuario',
                'movimiento_inventario',
                'simulacion_relacionada'
            ],
            'classes': ['collapse']
        }),
    ]
    
    def tipo_movimiento_badge(self, obj):
        color = 'success' if obj.tipo_movimiento == 'ingreso' else 'danger'
        texto = 'Ingreso' if obj.tipo_movimiento == 'ingreso' else 'Egreso'
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, texto
        )
    tipo_movimiento_badge.short_description = "Tipo"
    
    def monto_formatted(self, obj):
        signo = "+" if obj.tipo_movimiento == 'ingreso' else "-"
        color = 'green' if obj.tipo_movimiento == 'ingreso' else 'red'
        return format_html(
            '<span style="color: {};">{} ${:.2f}</span>',
            color, signo, obj.monto
        )
    monto_formatted.short_description = "Monto"
    
    def saldo_nuevo_formatted(self, obj):
        return f"${obj.saldo_nuevo:.2f}"
    saldo_nuevo_formatted.short_description = "Saldo"
    
    def automatico_badge(self, obj):
        if obj.automatico:
            return format_html('<span class="badge badge-info">Automático</span>')
        return format_html('<span class="badge badge-secondary">Manual</span>')
    automatico_badge.short_description = "Origen"


class DetalleListaMonosInline(admin.TabularInline):
    model = DetalleListaMonos
    extra = 1
    fields = ['monos', 'cantidad', 'cantidad_producida', 'tipo_venta_display']
    readonly_fields = ['cantidad_producida', 'tipo_venta_display']


class ResumenMaterialesInline(admin.TabularInline):
    model = ResumenMateriales
    extra = 0
    fields = ['material', 'cantidad_necesaria', 'cantidad_disponible', 'cantidad_faltante', 
              'cantidad_comprada', 'cantidad_utilizada']
    readonly_fields = ['cantidad_necesaria', 'cantidad_disponible', 'cantidad_faltante']


@admin.register(ListaProduccion)
class ListaProduccionAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 
        'estado', 
        'total_moños_planificados',
        'total_moños_producidos', 
        'costo_total_estimado',
        'ganancia_estimada',
        'fecha_creacion',
        'usuario_creador'
    ]
    list_filter = ['estado', 'fecha_creacion', 'usuario_creador']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion', 'total_moños_planificados', 
                       'total_moños_producidos', 'costo_total_estimado', 'ganancia_estimada']
    inlines = [DetalleListaMonosInline, ResumenMaterialesInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'estado', 'usuario_creador')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
        ('Totales Calculados', {
            'fields': ('total_moños_planificados', 'total_moños_producidos', 
                      'costo_total_estimado', 'ganancia_estimada'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DetalleListaMonos)
class DetalleListaMonosAdmin(admin.ModelAdmin):
    list_display = [
        'lista_produccion',
        'monos', 
        'cantidad',
        'tipo_venta_display',
        'cantidad_total_planificada',
        'cantidad_producida',
        'cantidad_total_producida'
    ]
    list_filter = ['lista_produccion__estado', 'monos', 'monos__tipo_venta']
    search_fields = ['lista_produccion__nombre', 'monos__nombre']


@admin.register(ResumenMateriales)
class ResumenMaterialesAdmin(admin.ModelAdmin):
    list_display = [
        'lista_produccion',
        'material',
        'cantidad_necesaria',
        'cantidad_disponible', 
        'cantidad_faltante',
        'cantidad_comprada',
        'cantidad_utilizada',
        'precio_compra_real'
    ]
    list_filter = ['lista_produccion__estado', 'material__categoria']
    search_fields = ['lista_produccion__nombre', 'material__nombre']


# Personalización del admin site
admin.site.site_header = "Sistema de Inventario de Moños"
admin.site.site_title = "Inventario Admin"
admin.site.index_title = "Panel de Administración"
