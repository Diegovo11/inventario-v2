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


class Reabastecimiento(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('solicitado', 'Solicitado'),
        ('en_transito', 'En Tránsito'),
        ('recibido', 'Recibido'),
        ('cancelado', 'Cancelado'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]
    
    material = models.ForeignKey(
        Material, 
        on_delete=models.CASCADE,
        help_text="Material a reabastecer"
    )
    cantidad_solicitada = models.PositiveIntegerField(
        help_text="Cantidad a solicitar en unidad base"
    )
    cantidad_recibida = models.PositiveIntegerField(
        default=0,
        help_text="Cantidad realmente recibida"
    )
    proveedor = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nombre del proveedor o lugar de compra"
    )
    precio_estimado = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Precio estimado total de la compra"
    )
    precio_real = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Precio real pagado"
    )
    estado = models.CharField(
        max_length=15, 
        choices=ESTADO_CHOICES, 
        default='pendiente'
    )
    prioridad = models.CharField(
        max_length=10, 
        choices=PRIORIDAD_CHOICES, 
        default='media'
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_estimada_llegada = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha estimada de llegada del pedido"
    )
    fecha_recepcion = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha real cuando se recibió el pedido"
    )
    notas = models.TextField(
        blank=True,
        help_text="Observaciones adicionales del reabastecimiento"
    )
    stock_minimo_sugerido = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Nivel mínimo de stock sugerido para este material"
    )
    automatico = models.BooleanField(
        default=False,
        help_text="Si fue generado automáticamente por stock bajo"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Reabastecimiento"
        verbose_name_plural = "Reabastecimientos"
        ordering = ['-fecha_solicitud']
    
    def __str__(self):
        return f"{self.material.codigo} - {self.get_estado_display()} - {self.cantidad_solicitada}"
    
    def save(self, *args, **kwargs):
        # Si se marca como recibido y no tiene fecha de recepción, asignarla
        if self.estado == 'recibido' and not self.fecha_recepcion:
            from django.utils import timezone
            self.fecha_recepcion = timezone.now()
            
            # Crear movimiento de entrada automáticamente
            if self.cantidad_recibida > 0:
                Movimiento.objects.create(
                    material=self.material,
                    tipo_movimiento='entrada',
                    cantidad=self.cantidad_recibida,
                    detalle=f'Reabastecimiento recibido - {self.proveedor or "Proveedor no especificado"}'
                )
                
                # Actualizar stock del material
                self.material.cantidad_disponible += self.cantidad_recibida
                self.material.save()
                
        super().save(*args, **kwargs)
    
    def dias_desde_solicitud(self):
        """Retorna los días transcurridos desde la solicitud"""
        from django.utils import timezone
        return (timezone.now() - self.fecha_solicitud).days
    
    def esta_retrasado(self):
        """Verifica si el pedido está retrasado"""
        if self.fecha_estimada_llegada and self.estado not in ['recibido', 'cancelado']:
            from django.utils import timezone
            return timezone.now() > self.fecha_estimada_llegada
        return False
    
    def porcentaje_completado(self):
        """Calcula el porcentaje de completado del pedido"""
        if self.cantidad_solicitada == 0:
            return 0
        return min(100, (self.cantidad_recibida * 100) // self.cantidad_solicitada)
