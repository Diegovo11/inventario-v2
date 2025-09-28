from django import forms
from django.forms import formset_factory, inlineformset_factory
from django.contrib.auth.models import User
from .models import (Material, Movimiento, Monos, RecetaMonos, Simulacion, MovimientoEfectivo,
                   ListaProduccion, DetalleListaMonos, ResumenMateriales)
from decimal import Decimal


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = [
            'codigo', 'nombre', 'descripcion', 'tipo_material', 
            'unidad_base', 'factor_conversion', 'precio_compra', 'categoria'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: M001'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Listón rojo'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo_material': forms.Select(attrs={'class': 'form-control'}),
            'unidad_base': forms.Select(attrs={'class': 'form-control'}),
            'factor_conversion': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'precio_compra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'categoria': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: listón, piedra, adorno'}),
        }
    
    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').upper()
        
        # Verificar que el código no exista (excepto en edición)
        existing = Material.objects.filter(codigo=codigo)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise forms.ValidationError('Ya existe un material con este código.')
        
        return codigo


class MonosForm(forms.ModelForm):
    """Formulario para crear y editar moños"""
    
    class Meta:
        model = Monos
        fields = ['codigo', 'nombre', 'descripcion', 'tipo_venta', 'precio_venta']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: MO001'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: Moño básico'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Descripción del moño'
            }),
            'tipo_venta': forms.Select(attrs={
                'class': 'form-control'
            }),
            'precio_venta': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'placeholder': 'Precio de venta'
            }),
        }
    
    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').upper()
        
        # Verificar que el código no exista (excepto en edición)
        existing = Monos.objects.filter(codigo=codigo)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise forms.ValidationError('Ya existe un moño con este código.')
        
        return codigo


class RecetaMonosForm(forms.ModelForm):
    """Formulario para agregar materiales a la receta de moños"""
    
    class Meta:
        model = RecetaMonos
        fields = ['material', 'cantidad_necesaria']
        widgets = {
            'material': forms.Select(attrs={
                'class': 'form-control'
            }),
            'cantidad_necesaria': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Cantidad necesaria'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar materiales activos
        self.fields['material'].queryset = Material.objects.filter(activo=True).order_by('nombre')
        # Hacer campos no requeridos por defecto - la validación se hará en el formset
        self.fields['material'].required = False
        self.fields['cantidad_necesaria'].required = False
    
    def clean(self):
        """Validación personalizada: solo validar si hay datos en el formulario"""
        cleaned_data = super().clean()
        material = cleaned_data.get('material')
        cantidad_necesaria = cleaned_data.get('cantidad_necesaria')
        
        # Si hay datos en algún campo, ambos deben estar completos
        if material or cantidad_necesaria:
            if not material:
                self.add_error('material', 'Este campo es obligatorio cuando se especifica una cantidad.')
            if not cantidad_necesaria:
                self.add_error('cantidad_necesaria', 'Este campo es obligatorio cuando se especifica un material.')
        
        return cleaned_data


class BaseRecetaMonosFormSet(forms.BaseInlineFormSet):
    """Formset personalizado para manejar recetas de moños"""
    
    def clean(self):
        """Validación del formset completo"""
        super().clean()
        
        if any(self.errors):
            return
        
        # Contar formularios válidos (que tienen datos)
        formularios_validos = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                material = form.cleaned_data.get('material')
                cantidad = form.cleaned_data.get('cantidad_necesaria')
                if material and cantidad:
                    formularios_validos += 1
        
        # Debe haber al menos un material en la receta
        if formularios_validos < 1:
            raise forms.ValidationError(
                'Debe agregar al menos un material a la receta del moño.'
            )

# Crear formset para recetas
RecetaMonosFormSet = inlineformset_factory(
    Monos, 
    RecetaMonos,
    form=RecetaMonosForm,
    formset=BaseRecetaMonosFormSet,
    extra=1,
    can_delete=True,
    min_num=0,  # Cambiado a 0 para manejar validación personalizada
    validate_min=False  # Deshabilitado para usar validación personalizada
)


class SimulacionForm(forms.ModelForm):
    """Formulario para ejecutar simulaciones de producción"""
    
    class Meta:
        model = Simulacion
        fields = ['monos', 'cantidad_producir', 'tipo_venta', 'precio_venta_unitario']
        widgets = {
            'monos': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_monos'
            }),
            'cantidad_producir': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Cantidad a producir',
                'id': 'id_cantidad_producir'
            }),
            'tipo_venta': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_tipo_venta'
            }),
            'precio_venta_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Precio de venta',
                'id': 'id_precio_venta'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar moños activos
        self.fields['monos'].queryset = Monos.objects.filter(activo=True).order_by('nombre')
        
        # Si hay un moño seleccionado, pre-cargar su precio
        if self.instance.pk and self.instance.monos:
            self.fields['precio_venta_unitario'].initial = self.instance.monos.precio_venta
            self.fields['tipo_venta'].initial = self.instance.monos.tipo_venta


class SimulacionBusquedaForm(forms.Form):
    """Formulario para buscar y filtrar simulaciones"""
    
    monos = forms.ModelChoiceField(
        queryset=Monos.objects.filter(activo=True).order_by('nombre'),
        required=False,
        empty_label="Todos los moños",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    necesita_compras = forms.ChoiceField(
        choices=[('', 'Todas'), ('true', 'Necesitan compra'), ('false', 'No necesitan compra')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class EntradaMaterialForm(forms.Form):
    """Formulario para registrar entrada/reabastecimiento de materiales"""
    
    material = forms.ModelChoiceField(
        queryset=Material.objects.filter(activo=True).order_by('nombre'),
        empty_label="Seleccionar material",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_material_entrada'
        }),
        help_text="Material a reabastecer"
    )
    
    cantidad_comprada = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'placeholder': 'Cantidad comprada',
            'id': 'id_cantidad_comprada'
        }),
        help_text="Cantidad comprada en su presentación original (paquetes/rollos)"
    )
    
    # El precio se calculará automáticamente: cantidad_comprada * precio_compra del material
    precio_compra_total = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,  # No requerido porque se calcula automáticamente
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'placeholder': 'Se calculará automáticamente',
            'id': 'id_precio_compra'
        }),
        help_text="Se calcula automáticamente: cantidad × precio unitario del material"
    )
    
    detalle = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Compra proveedor ABC',
            'id': 'id_detalle_entrada'
        }),
        help_text="Descripción opcional del reabastecimiento"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cargar información del material seleccionado via AJAX
        
    def clean(self):
        cleaned_data = super().clean()
        material = cleaned_data.get('material')
        cantidad_comprada = cleaned_data.get('cantidad_comprada')
        
        if material and cantidad_comprada:
            # Calcular precio automáticamente basado en el precio de compra del material
            precio_compra_total = cantidad_comprada * material.precio_compra
            cleaned_data['precio_compra_total'] = precio_compra_total
            
            # Calcular conversiones automáticamente
            cleaned_data['cantidad_en_unidad_base'] = cantidad_comprada * material.factor_conversion
            cleaned_data['costo_unitario'] = precio_compra_total / (cantidad_comprada * material.factor_conversion)
            cleaned_data['nuevo_stock'] = material.cantidad_disponible + cleaned_data['cantidad_en_unidad_base']
            
        return cleaned_data


class SalidaMaterialForm(forms.Form):
    """Formulario para registrar salida normal de materiales"""
    
    material = forms.ModelChoiceField(
        queryset=Material.objects.filter(activo=True).order_by('nombre'),
        empty_label="Seleccionar material",
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        help_text="Material del que se realizará la salida"
    )
    
    cantidad_utilizada = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'placeholder': 'Cantidad utilizada'
        }),
        help_text="Cantidad utilizada en unidad base del material"
    )
    
    destino = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Producción, Venta, Uso interno'
        }),
        help_text="Destino o propósito de la salida"
    )
    
    detalle = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Información adicional sobre la salida (opcional)'
        }),
        help_text="Detalles adicionales sobre la salida (opcional)"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        material = cleaned_data.get('material')
        cantidad_retirar = cleaned_data.get('cantidad_retirar')
        
        if material and cantidad_retirar:
            # Verificar stock disponible
            if cantidad_retirar > material.cantidad_disponible:
                raise forms.ValidationError(
                    f"No hay suficiente stock. Disponible: {material.cantidad_disponible} {material.unidad_base}, "
                    f"solicitado: {cantidad_retirar} {material.unidad_base}"
                )
            
            cleaned_data['nuevo_stock'] = material.cantidad_disponible - cantidad_retirar
            cleaned_data['costo_total_movimiento'] = cantidad_retirar * material.costo_unitario
            
        return cleaned_data


class MovimientoFiltroForm(forms.Form):
    """Formulario para filtrar el historial de movimientos"""
    
    material = forms.ModelChoiceField(
        queryset=Material.objects.filter(activo=True).order_by('nombre'),
        required=False,
        empty_label="Todos los materiales",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    tipo_movimiento = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + Movimiento.TIPO_MOVIMIENTO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class EntradaDesdeSimulacionForm(forms.Form):
    """Formulario para entrada de materiales desde simulación"""
    
    def __init__(self, simulacion=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.simulacion = simulacion
        
        if simulacion:
            # Crear campos dinámicos para cada material faltante
            for detalle in simulacion.detallesimulacion_set.all():
                material = detalle.material
                cantidad_necesaria = detalle.cantidad_requerida
                
                if material.cantidad_disponible < cantidad_necesaria:
                    cantidad_faltante = cantidad_necesaria - material.cantidad_disponible
                    
                    # Campo para cantidad a comprar
                    self.fields[f'cantidad_{material.id}'] = forms.DecimalField(
                        label=f'{material.nombre} (Falta: {cantidad_faltante} {material.unidad_base})',
                        initial=cantidad_faltante,
                        min_value=0,
                        max_digits=10,
                        decimal_places=2,
                        widget=forms.NumberInput(attrs={
                            'class': 'form-control',
                            'step': '0.01'
                        }),
                        help_text=f'Stock actual: {material.cantidad_disponible} {material.unidad_base}'
                    )
                    
                    # Campo para precio de compra (opcional)
                    self.fields[f'precio_{material.id}'] = forms.DecimalField(
                        label=f'Precio total de compra para {material.nombre}',
                        required=False,
                        min_value=0,
                        max_digits=10,
                        decimal_places=2,
                        widget=forms.NumberInput(attrs={
                            'class': 'form-control',
                            'step': '0.01',
                            'placeholder': f'Precio sugerido: ${(cantidad_faltante * material.costo_unitario):.2f}'
                        }),
                        help_text='Dejar vacío para usar precio actual del material'
                    )


class SalidaDesdeSimulacionForm(forms.Form):
    """Formulario para confirmar salidas desde simulación"""
    
    def __init__(self, simulacion=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.simulacion = simulacion
        
        if simulacion:
            # Crear campos de confirmación para cada material
            for detalle in simulacion.detallesimulacion_set.all():
                material = detalle.material
                cantidad_necesaria = detalle.cantidad_requerida
                
                self.fields[f'confirmar_{material.id}'] = forms.BooleanField(
                    label=f'{material.nombre}: {cantidad_necesaria} {material.unidad_base}',
                    initial=True,
                    required=False,
                    widget=forms.CheckboxInput(attrs={
                        'class': 'form-check-input'
                    }),
                    help_text=f'Stock disponible: {material.cantidad_disponible} {material.unidad_base}'
                )
                
                # Campo para observaciones específicas del material
                self.fields[f'observacion_{material.id}'] = forms.CharField(
                    label=f'Observaciones para {material.nombre}',
                    required=False,
                    max_length=255,
                    widget=forms.TextInput(attrs={
                        'class': 'form-control',
                        'placeholder': 'Observaciones específicas (opcional)'
                    })
                )


class MovimientoEfectivoForm(forms.ModelForm):
    """Formulario para registrar movimientos de efectivo manuales"""
    
    class Meta:
        model = MovimientoEfectivo
        fields = ['concepto', 'tipo_movimiento', 'categoria', 'monto']
        widgets = {
            'concepto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del movimiento (ej: Pago de renta)'
            }),
            'tipo_movimiento': forms.Select(attrs={
                'class': 'form-control'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            })
        }
        labels = {
            'concepto': 'Descripción',
            'tipo_movimiento': 'Tipo de Movimiento',
            'categoria': 'Categoría',
            'monto': 'Monto'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar categorías según el tipo de movimiento
        self.fields['categoria'].choices = [
            ('sueldo', 'Sueldos'),
            ('renta', 'Renta'),
            ('servicio', 'Servicios (luz, agua, etc.)'),
            ('otro_gasto', 'Otros Gastos'),
            ('otro_ingreso', 'Otros Ingresos'),
        ]
    
    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto and monto <= 0:
            raise forms.ValidationError('El monto debe ser mayor a cero.')
        return monto


class FiltroMovimientosEfectivoForm(forms.Form):
    """Formulario para filtrar movimientos de efectivo"""
    
    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Fecha Inicio'
    )
    
    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Fecha Fin'
    )
    
    tipo_movimiento = forms.ChoiceField(
        choices=[('', 'Todos')] + MovimientoEfectivo.TIPO_MOVIMIENTO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo'
    )
    
    categoria = forms.ChoiceField(
        choices=[('', 'Todas')] + MovimientoEfectivo.CATEGORIA_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Categoría'
    )
    
    automatico = forms.ChoiceField(
        choices=[('', 'Todos'), ('true', 'Automático'), ('false', 'Manual')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Origen'
    )


class ListaProduccionForm(forms.ModelForm):
    """Formulario para crear listas de producción"""
    
    class Meta:
        model = ListaProduccion
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Lista Navidad 2024'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción opcional de la lista de producción'
            }),
        }


class DetalleListaMonosForm(forms.Form):
    """Formulario para especificar cantidades de moños en la lista"""
    
    monos = forms.ModelChoiceField(
        queryset=Monos.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-control moños-select'}),
        empty_label="Seleccionar moño"
    )
    cantidad = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1'
        }),
        help_text="Cantidad a producir (pares o individuales según el tipo del moño)"
    )


# Crear formset para múltiples moños (inline formset para edición)
DetalleListaMonosFormSet = inlineformset_factory(
    ListaProduccion,
    DetalleListaMonos,
    form=DetalleListaMonosForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


