from django import forms
from django.utils import timezone
from .models import Reabastecimiento, Material, TipoMono, RecetaProduccion, SimulacionProduccion, Insumo, Movimiento

class ReabastecimientoForm(forms.ModelForm):
    class Meta:
        model = Reabastecimiento
        fields = [
            'material', 'cantidad_solicitada', 'proveedor', 'precio_estimado',
            'fecha_estimada_llegada', 'prioridad', 'stock_minimo_sugerido', 'notas'
        ]
        widgets = {
            'material': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_solicitada': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1',
                'placeholder': 'Cantidad a solicitar'
            }),
            'proveedor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del proveedor'
            }),
            'precio_estimado': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'fecha_estimada_llegada': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'prioridad': forms.Select(attrs={'class': 'form-select'}),
            'stock_minimo_sugerido': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Stock mínimo recomendado'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Observaciones adicionales...'
            }),
        }
        labels = {
            'material': 'Material',
            'cantidad_solicitada': 'Cantidad a Solicitar',
            'proveedor': 'Proveedor',
            'precio_estimado': 'Precio Estimado',
            'fecha_estimada_llegada': 'Fecha Estimada de Llegada',
            'prioridad': 'Prioridad',
            'stock_minimo_sugerido': 'Stock Mínimo Sugerido',
            'notas': 'Notas',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar información de stock actual en el dropdown de materiales
        self.fields['material'].queryset = Material.objects.all().order_by('nombre')
        
        # Hacer que algunos campos sean opcionales para mejor UX
        self.fields['proveedor'].required = False
        self.fields['precio_estimado'].required = False
        self.fields['fecha_estimada_llegada'].required = False
        self.fields['stock_minimo_sugerido'].required = False
        self.fields['notas'].required = False

class ReabastecimientoUpdateForm(forms.ModelForm):
    class Meta:
        model = Reabastecimiento
        fields = [
            'cantidad_recibida', 'precio_real', 'estado', 'prioridad',
            'fecha_estimada_llegada', 'notas'
        ]
        widgets = {
            'cantidad_recibida': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'precio_real': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'prioridad': forms.Select(attrs={'class': 'form-select'}),
            'fecha_estimada_llegada': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3'
            }),
        }
        labels = {
            'cantidad_recibida': 'Cantidad Recibida',
            'precio_real': 'Precio Real',
            'estado': 'Estado',
            'prioridad': 'Prioridad',
            'fecha_estimada_llegada': 'Fecha Estimada de Llegada',
            'notas': 'Notas',
        }

class StockBajoForm(forms.Form):
    """Formulario para generar reabastecimientos automáticos por stock bajo"""
    stock_minimo = forms.IntegerField(
        min_value=1,
        initial=50,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 50'
        }),
        label='Stock Mínimo'
    )
    cantidad_a_solicitar = forms.IntegerField(
        min_value=1,
        initial=200,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 200'
        }),
        label='Cantidad a Solicitar por Defecto'
    )
    proveedor_default = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Proveedor por defecto'
        }),
        label='Proveedor por Defecto'
    )

class TipoMonoForm(forms.ModelForm):
    class Meta:
        model = TipoMono
        fields = ['nombre', 'descripcion', 'precio_venta_sugerido', 'tiempo_produccion_minutos']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Moño Básico'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Descripción del tipo de moño...'
            }),
            'precio_venta_sugerido': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'tiempo_produccion_minutos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '30'
            }),
        }
        labels = {
            'nombre': 'Nombre del Tipo de Moño',
            'descripcion': 'Descripción',
            'precio_venta_sugerido': 'Precio de Venta Sugerido',
            'tiempo_produccion_minutos': 'Tiempo de Producción (minutos)',
        }

class SimuladorForm(forms.Form):
    tipo_mono = forms.ModelChoiceField(
        queryset=TipoMono.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tipo de Moño'
    )
    cantidad_a_producir = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'placeholder': '1'
        }),
        label='Cantidad a Producir'
    )
    precio_venta_unitario = forms.DecimalField(
        min_value=0.01,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0.01',
            'step': '0.01',
            'placeholder': '0.00'
        }),
        label='Precio de Venta por Unidad'
    )
    guardar_simulacion = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Guardar esta simulación'
    )
    nombre_simulacion = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre para la simulación (opcional)'
        }),
        label='Nombre de la Simulación'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-llenar precio con el sugerido si se selecciona un tipo
        if self.initial.get('tipo_mono'):
            try:
                tipo = TipoMono.objects.get(id=self.initial['tipo_mono'])
                self.initial['precio_venta_unitario'] = tipo.precio_venta_sugerido
            except TipoMono.DoesNotExist:
                pass

class RecetaProduccionForm(forms.ModelForm):
    class Meta:
        model = RecetaProduccion
        fields = ['insumo', 'cantidad_necesaria', 'es_opcional', 'notas']
        widgets = {
            'insumo': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_necesaria': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01'
            }),
            'es_opcional': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '2'
            }),
        }
        labels = {
            'insumo': 'Material/Insumo',
            'cantidad_necesaria': 'Cantidad Necesaria',
            'es_opcional': 'Es Opcional',
            'notas': 'Notas',
        }

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['codigo', 'nombre', 'descripcion', 'tipo_material', 'unidad_base', 
                 'factor_conversion', 'cantidad_disponible', 'precio_compra', 'categoria']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: M001'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Listón rojo'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Descripción detallada del material...'
            }),
            'tipo_material': forms.Select(attrs={'class': 'form-select'}),
            'unidad_base': forms.Select(attrs={'class': 'form-select'}),
            'factor_conversion': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '100'
            }),
            'cantidad_disponible': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'precio_compra': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'categoria': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: listón, piedra, adorno'
            }),
        }
        labels = {
            'codigo': 'Código',
            'nombre': 'Nombre del Material',
            'descripcion': 'Descripción',
            'tipo_material': 'Tipo de Material',
            'unidad_base': 'Unidad Base',
            'factor_conversion': 'Factor de Conversión',
            'cantidad_disponible': 'Cantidad Disponible',
            'precio_compra': 'Precio de Compra',
            'categoria': 'Categoría',
        }

class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumo
        fields = ['nombre', 'descripcion', 'cantidad_por_unidad', 'unidad_consumo', 'material']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Moño básico'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Descripción del insumo...'
            }),
            'cantidad_por_unidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '10'
            }),
            'unidad_consumo': forms.Select(attrs={'class': 'form-select'}),
            'material': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'nombre': 'Nombre del Insumo',
            'descripcion': 'Descripción',
            'cantidad_por_unidad': 'Cantidad por Unidad',
            'unidad_consumo': 'Unidad de Consumo',
            'material': 'Material Asociado',
        }

class MovimientoForm(forms.ModelForm):
    class Meta:
        model = Movimiento
        fields = ['material', 'tipo_movimiento', 'cantidad', 'detalle']
        widgets = {
            'material': forms.Select(attrs={'class': 'form-select'}),
            'tipo_movimiento': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0'
            }),
            'detalle': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Motivo del movimiento...'
            }),
        }
        labels = {
            'material': 'Material',
            'tipo_movimiento': 'Tipo de Movimiento',
            'cantidad': 'Cantidad',
            'detalle': 'Detalle/Motivo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar help text para cantidad según tipo de movimiento
        self.fields['cantidad'].help_text = "Para salidas, usar número positivo (se convertirá automáticamente)"

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Convertir salidas a negativo automáticamente
        if instance.tipo_movimiento == 'salida' and instance.cantidad > 0:
            instance.cantidad = -instance.cantidad
        
        if commit:
            instance.save()
            
            # Actualizar el stock del material
            if instance.tipo_movimiento in ['entrada', 'salida']:
                material = instance.material
                material.cantidad_disponible += instance.cantidad
                material.save()
                
        return instance