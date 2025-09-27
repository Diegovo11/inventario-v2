from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Material(models.Model):
    TIPO_MATERIAL_CHOICES = [
        ('paquete', 'Paquete'),
        ('rollo', 'Rollo'),
    ]
    
    UNIDAD_BASE_CHOICES = [
        ('unidades', 'Unidades'),
        ('cm', 'Centímetros'),
    ]
    
    codigo = models.CharField(max_length=10, unique=True, help_text="Identificador único (ej. M001)")
    nombre = models.CharField(max_length=100, help_text="Nombre del material (ej. Listón rojo)")
    descripcion = models.TextField(blank=True, help_text="Detalle del material")
    tipo_material = models.CharField(max_length=10, choices=TIPO_MATERIAL_CHOICES)
    unidad_base = models.CharField(max_length=10, choices=UNIDAD_BASE_CHOICES)
    factor_conversion = models.PositiveIntegerField(
        help_text="Cantidad que representa 1 paquete o 1 rollo en unidad base"
    )
    cantidad_disponible = models.PositiveIntegerField(default=0, help_text="Stock actual en unidad base")
    precio_compra = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Precio total de la compra (reabastecer)"
    )
    costo_unitario = models.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0.0000'))],
        help_text="Precio por unidad base (precio_compra / factor_conversion)"
    )
    categoria = models.CharField(max_length=50, help_text="Clasificación (ej. listón, piedra, adorno)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ['codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def save(self, *args, **kwargs):
        # Calcular costo unitario automáticamente
        if self.precio_compra and self.factor_conversion:
            self.costo_unitario = self.precio_compra / self.factor_conversion
        super().save(*args, **kwargs)


class Insumo(models.Model):
    nombre = models.CharField(max_length=100, help_text="Nombre del insumo (ej. Moño básico)")
    descripcion = models.TextField(blank=True, help_text="Detalle del insumo")
    cantidad_por_unidad = models.PositiveIntegerField(
        help_text="Cantidad de material que se usa por cada moño"
    )
    unidad_consumo = models.CharField(
        max_length=10, 
        choices=Material.UNIDAD_BASE_CHOICES,
        help_text="Unidad en la que se descuenta (unidades | cm)"
    )
    material = models.ForeignKey(
        Material, 
        on_delete=models.CASCADE,
        help_text="Material al que está vinculado"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Insumo"
        verbose_name_plural = "Insumos"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.material.nombre}"
    
    def costo_por_unidad(self):
        """Calcula el costo de material por cada unidad de insumo"""
        return self.material.costo_unitario * self.cantidad_por_unidad


class Movimiento(models.Model):
    TIPO_MOVIMIENTO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
    ]
    
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO_CHOICES)
    cantidad = models.IntegerField(help_text="Cantidad afectada en unidad base (puede ser negativa)")
    fecha = models.DateTimeField(auto_now_add=True)
    detalle = models.TextField(help_text='Motivo (ej. "Compra proveedor X", "Producción de 50 moños")')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} - {self.material.codigo} - {self.cantidad}"
