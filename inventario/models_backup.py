from django.db import models
from django.contrib.auth.models import User
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


class TipoMono(models.Model):
    """Modelo para diferentes tipos de moños que se pueden producir"""
    
    nombre = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Nombre del tipo de moño (ej. Moño Básico, Moño Premium)"
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción detallada del moño"
    )
    precio_venta_sugerido = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Precio de venta sugerido por unidad"
    )
    tiempo_produccion_minutos = models.PositiveIntegerField(
        default=30,
        help_text="Tiempo estimado de producción en minutos"
    )
    activo = models.BooleanField(
        default=True,
        help_text="Si el tipo de moño está disponible para producción"
    )

    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tipo de Moño"
        verbose_name_plural = "Tipos de Moños"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def calcular_costo_materiales(self):
        """Calcula el costo total de materiales necesarios"""
        recetas = self.recetaproduccion_set.all()
        costo_total = Decimal('0.00')
        
        for receta in recetas:
            costo_material = receta.insumo.costo_por_unidad()
            costo_total += costo_material * receta.cantidad_necesaria
            
        return costo_total
    
    def margen_ganancia(self):
        """Calcula el margen de ganancia"""
        costo = self.calcular_costo_materiales()
        if costo == 0:
            return Decimal('100.00')
        
        ganancia = self.precio_venta_sugerido - costo
        return (ganancia / self.precio_venta_sugerido) * 100
    
    def puede_producir(self, cantidad=1):
        """Verifica si se puede producir la cantidad especificada"""
        recetas = self.recetaproduccion_set.all()
        
        for receta in recetas:
            material_necesario = receta.cantidad_necesaria * cantidad
            if receta.insumo.material.cantidad_disponible < material_necesario:
                return False, f"Stock insuficiente de {receta.insumo.material.nombre}"
        
        return True, "Stock suficiente"


class RecetaProduccion(models.Model):
    """Modelo que define qué materiales e insumos se necesitan para cada tipo de moño"""
    
    tipo_mono = models.ForeignKey(
        TipoMono, 
        on_delete=models.CASCADE,
        help_text="Tipo de moño al que pertenece esta receta"
    )
    insumo = models.ForeignKey(
        Insumo, 
        on_delete=models.CASCADE,
        help_text="Insumo/material necesario"
    )
    cantidad_necesaria = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Cantidad del insumo necesaria para producir 1 moño"
    )
    es_opcional = models.BooleanField(
        default=False,
        help_text="Si este insumo es opcional para la producción"
    )
    notas = models.TextField(
        blank=True,
        help_text="Notas sobre el uso de este insumo"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Receta de Producción"
        verbose_name_plural = "Recetas de Producción"
        unique_together = ['tipo_mono', 'insumo']
        ordering = ['tipo_mono', 'insumo']
    
    def __str__(self):
        return f"{self.tipo_mono.nombre} - {self.insumo.nombre} ({self.cantidad_necesaria})"
    
    def costo_total_insumo(self, cantidad_monos=1):
        """Calcula el costo total de este insumo para producir X moños"""
        costo_unitario = self.insumo.costo_por_unidad()
        cantidad_total = self.cantidad_necesaria * cantidad_monos
        return costo_unitario * cantidad_total


class SimulacionProduccion(models.Model):
    """Modelo para guardar simulaciones de producción"""
    
    nombre_simulacion = models.CharField(
        max_length=150,
        help_text="Nombre para identificar esta simulación"
    )
    tipo_mono = models.ForeignKey(
        TipoMono, 
        on_delete=models.CASCADE,
        help_text="Tipo de moño a simular"
    )
    cantidad_a_producir = models.PositiveIntegerField(
        help_text="Cantidad de moños a producir en la simulación"
    )
    precio_venta_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Precio de venta por unidad para esta simulación"
    )
    
    # Campos calculados
    costo_total_materiales = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Costo total de todos los materiales"
    )
    ingreso_total = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Ingreso total estimado"
    )
    ganancia_neta = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Ganancia neta estimada"
    )
    margen_porcentaje = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Margen de ganancia en porcentaje"
    )
    
    stock_suficiente = models.BooleanField(
        default=True,
        help_text="Si hay stock suficiente para producir esta cantidad"
    )
    
    fecha_simulacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Simulación de Producción"
        verbose_name_plural = "Simulaciones de Producción"
        ordering = ['-fecha_simulacion']
    
    def __str__(self):
        return f"{self.nombre_simulacion} - {self.cantidad_a_producir} {self.tipo_mono.nombre}"
    
    def save(self, *args, **kwargs):
        # Calcular todos los valores automáticamente
        self.calcular_metricas()
        super().save(*args, **kwargs)
    
    def calcular_metricas(self):
        """Calcula todas las métricas de la simulación"""
        costo_unitario = self.tipo_mono.calcular_costo_materiales()
        
        self.costo_total_materiales = costo_unitario * self.cantidad_a_producir
        self.ingreso_total = self.precio_venta_unitario * self.cantidad_a_producir
        self.ganancia_neta = self.ingreso_total - self.costo_total_materiales
        
        if self.ingreso_total > 0:
            self.margen_porcentaje = (self.ganancia_neta / self.ingreso_total) * 100
        else:
            self.margen_porcentaje = Decimal('0.00')
        
        # Verificar si hay stock suficiente
        puede_producir, mensaje = self.tipo_mono.puede_producir(self.cantidad_a_producir)
        self.stock_suficiente = puede_producir
    
    def tiempo_total_produccion(self):
        """Calcula el tiempo total de producción en horas"""
        minutos_totales = self.tipo_mono.tiempo_produccion_minutos * self.cantidad_a_producir
        return minutos_totales / 60
    
    def rentabilidad_por_hora(self):
        """Calcula la rentabilidad por hora de trabajo"""
        tiempo_horas = self.tiempo_total_produccion()
        if tiempo_horas > 0:
            return self.ganancia_neta / Decimal(str(tiempo_horas))
        return Decimal('0.00')
