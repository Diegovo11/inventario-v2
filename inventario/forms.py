from django import forms
from django.utils import timezone
from .models import Reabastecimiento, Material

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