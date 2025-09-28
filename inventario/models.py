from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Material(models.Model):
    """Modelo para materiales/artículos del inventario"""
    
    TIPO_MATERIAL_CHOICES = [
        ('paquete', 'Paquete'),
        ('rollo', 'Rollo'),
    ]
    
    UNIDAD_BASE_CHOICES = [
        ('unidades', 'Unidades'),
        ('cm', 'Centímetros'),
    ]
    
    codigo = models.CharField(max_length=10, unique=True, help_text="Ej: M001")
    nombre = models.CharField(max_length=100, help_text="Ej: Listón rojo")
    descripcion = models.TextField(blank=True, help_text="Detalle del material")
    tipo_material = models.CharField(max_length=10, choices=TIPO_MATERIAL_CHOICES)
    unidad_base = models.CharField(max_length=10, choices=UNIDAD_BASE_CHOICES)
    factor_conversion = models.PositiveIntegerField(
        default=1,
        help_text="Cantidad que representa 1 paquete o 1 rollo en unidad base"
    )
    cantidad_disponible = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Stock actual en unidad base"
    )
    precio_compra = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        help_text="Precio total de la compra"
    )
    categoria = models.CharField(max_length=50, help_text="Ej: listón, piedra, adorno")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ['codigo']
    
    @property
    def costo_unitario(self):
        """Calcula el costo por unidad base"""
        if self.factor_conversion and self.precio_compra and self.factor_conversion > 0:
            return self.precio_compra / self.factor_conversion
        return 0
    
    @property
    def valor_inventario(self):
        """Calcula el valor total del inventario disponible"""
        cantidad = self.cantidad_disponible or 0
        return cantidad * self.costo_unitario
    
    @property
    def unidad(self):
        """Alias para unidad_base para mantener consistencia en templates"""
        return self.unidad_base
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Movimiento(models.Model):
    """Modelo para registrar movimientos de inventario"""
    
    TIPO_MOVIMIENTO_CHOICES = [
        ('entrada', 'Entrada/Reabastecimiento'),
        ('salida', 'Salida Normal'),
        ('produccion', 'Salida por Producción'),
        ('ajuste', 'Ajuste de Inventario'),
    ]
    
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='movimientos')
    tipo_movimiento = models.CharField(max_length=15, choices=TIPO_MOVIMIENTO_CHOICES)
    cantidad = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Cantidad afectada en unidad base (positiva para entrada, negativa para salida)"
    )
    cantidad_anterior = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Cantidad antes del movimiento"
    )
    cantidad_nueva = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Cantidad después del movimiento"
    )
    precio_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Precio unitario al momento del movimiento"
    )
    costo_total_movimiento = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Costo total del movimiento"
    )
    detalle = models.TextField(help_text="Motivo del movimiento")
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    simulacion_relacionada = models.ForeignKey(
        'Simulacion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Simulación relacionada (si aplica)"
    )
    
    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['material', 'fecha']),
            models.Index(fields=['tipo_movimiento', 'fecha']),
            models.Index(fields=['usuario', 'fecha']),
        ]
    
    def __str__(self):
        return f"{self.material.codigo} - {self.get_tipo_movimiento_display()} - {self.cantidad} ({self.fecha.strftime('%d/%m/%Y')})"
    
    @property
    def es_entrada(self):
        """Retorna True si es un movimiento de entrada"""
        return self.cantidad > 0
    
    @property
    def es_salida(self):
        """Retorna True si es un movimiento de salida"""
        return self.cantidad < 0
    
    @property
    def cantidad_absoluta(self):
        """Retorna la cantidad en valor absoluto"""
        return abs(self.cantidad)


class ConfiguracionSistema(models.Model):
    """Configuraciones generales del sistema"""
    
    nombre_empresa = models.CharField(max_length=100, default="Mi Empresa")
    moneda = models.CharField(max_length=5, default="MXN")
    stock_minimo_alerta = models.PositiveIntegerField(default=10)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"
    
    def __str__(self):
        return f"Configuración - {self.nombre_empresa}"


class Monos(models.Model):
    """Modelo para definir tipos de moños"""
    
    TIPO_VENTA_CHOICES = [
        ('individual', 'Individual'),
        ('par', 'Par'),
    ]
    
    codigo = models.CharField(max_length=10, unique=True, help_text="Ej: MO001")
    nombre = models.CharField(max_length=100, help_text="Ej: Moño básico")
    descripcion = models.TextField(blank=True, help_text="Detalle del moño")
    precio_venta = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Precio de venta por unidad o par"
    )
    tipo_venta = models.CharField(max_length=10, choices=TIPO_VENTA_CHOICES, default='individual')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Moño"
        verbose_name_plural = "Moños"
        ordering = ['codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    @property
    def costo_produccion(self):
        """Calcula el costo total de producción basado en la receta"""
        total = 0
        for receta in self.recetas.all():
            total += receta.material.costo_unitario * receta.cantidad_necesaria
        return total
    
    @property
    def ganancia_unitaria(self):
        """Calcula la ganancia por unidad/par"""
        return self.precio_venta - self.costo_produccion


class RecetaMonos(models.Model):
    """Modelo para definir qué materiales necesita cada moño"""
    
    monos = models.ForeignKey(Monos, on_delete=models.CASCADE, related_name='recetas')
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    cantidad_necesaria = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Cantidad de material necesaria por moño en unidad base"
    )
    
    class Meta:
        verbose_name = "Receta de Moño"
        verbose_name_plural = "Recetas de Moños"
        unique_together = ['monos', 'material']
        ordering = ['material__nombre']
    
    def __str__(self):
        return f"{self.monos.nombre} - {self.material.nombre}: {self.cantidad_necesaria} {self.material.unidad_base}"
    
    @property
    def costo_material(self):
        """Calcula el costo de este material para un moño"""
        return self.cantidad_necesaria * self.material.costo_unitario


class Simulacion(models.Model):
    """Modelo para guardar simulaciones de producción"""
    
    monos = models.ForeignKey(Monos, on_delete=models.CASCADE, related_name='simulaciones')
    cantidad_producir = models.PositiveIntegerField(help_text="Cantidad de moños a producir")
    tipo_venta = models.CharField(max_length=10, choices=Monos.TIPO_VENTA_CHOICES)
    precio_venta_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Precio de venta por unidad o par"
    )
    
    # Resultados calculados
    cantidad_total_monos = models.PositiveIntegerField(help_text="Cantidad total considerando tipo de venta")
    costo_total_produccion = models.DecimalField(max_digits=12, decimal_places=2)
    ingreso_total_venta = models.DecimalField(max_digits=12, decimal_places=2)
    ganancia_estimada = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Necesidades de compra
    necesita_compras = models.BooleanField(default=False)
    costo_total_compras = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = "Simulación"
        verbose_name_plural = "Simulaciones"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Simulación {self.monos.nombre} - {self.cantidad_producir} unidades - {self.fecha_creacion.strftime('%d/%m/%Y')}"
    
    @property
    def puede_ejecutar_produccion(self):
        """Verifica si hay suficientes materiales para ejecutar la producción"""
        detalles = self.detalles.all()
        return all(detalle.faltante <= 0 for detalle in detalles)
    
    @property
    def costo_total(self):
        """Alias para compatibilidad con el template"""
        return self.costo_total_produccion
    
    @property
    def ingresos_total(self):
        """Alias para compatibilidad con el template"""
        return self.ingreso_total_venta
    
    @property
    def ganancia_neta(self):
        """Alias para compatibilidad con el template"""
        return self.ganancia_estimada
    
    @property
    def margen_ganancia(self):
        """Calcula el margen de ganancia en porcentaje"""
        if self.ingreso_total_venta > 0:
            return (self.ganancia_estimada / self.ingreso_total_venta) * 100
        return 0


class DetalleSimulacion(models.Model):
    """Detalle de materiales necesarios por simulación"""
    
    simulacion = models.ForeignKey(Simulacion, on_delete=models.CASCADE, related_name='detalles')
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    cantidad_necesaria = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad_disponible = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad_faltante = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cantidad_a_comprar = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unidades_completas_comprar = models.PositiveIntegerField(default=0)
    costo_compra_necesaria = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    suficiente_stock = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Detalle de Simulación"
        verbose_name_plural = "Detalles de Simulaciones"
        unique_together = ['simulacion', 'material']
    
    def __str__(self):
        return f"{self.simulacion} - {self.material.nombre}"


class MovimientoEfectivo(models.Model):
    """Modelo para registrar movimientos de efectivo/finanzas"""
    
    TIPO_MOVIMIENTO_CHOICES = [
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso'),
    ]
    
    CATEGORIA_CHOICES = [
        ('venta', 'Venta de Productos'),
        ('inventario', 'Compra de Inventario'),
        ('produccion', 'Costo de Producción'),
        ('sueldo', 'Sueldos'),
        ('renta', 'Renta'),
        ('servicio', 'Servicios (luz, agua, etc.)'),
        ('otro_gasto', 'Otros Gastos'),
        ('otro_ingreso', 'Otros Ingresos'),
    ]
    
    fecha = models.DateTimeField(auto_now_add=True)
    concepto = models.CharField(max_length=200, help_text="Descripción del movimiento")
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO_CHOICES)
    categoria = models.CharField(max_length=15, choices=CATEGORIA_CHOICES)
    monto = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Monto del movimiento (siempre positivo)"
    )
    saldo_anterior = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Saldo antes del movimiento"
    )
    saldo_nuevo = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Saldo después del movimiento"
    )
    automatico = models.BooleanField(
        default=False, 
        help_text="True si fue generado automáticamente por el sistema"
    )
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Referencias opcionales a otros modelos
    movimiento_inventario = models.ForeignKey(
        'Movimiento', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Movimiento de inventario relacionado"
    )
    simulacion_relacionada = models.ForeignKey(
        'Simulacion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Simulación relacionada"
    )
    
    class Meta:
        verbose_name = "Movimiento de Efectivo"
        verbose_name_plural = "Movimientos de Efectivo"
        ordering = ['-fecha']
    
    def __str__(self):
        tipo_signo = "+" if self.tipo_movimiento == 'ingreso' else "-"
        return f"{self.fecha.strftime('%d/%m/%Y')} - {self.concepto}: {tipo_signo}${self.monto}"
    
    @property
    def monto_con_signo(self):
        """Retorna el monto con signo según el tipo de movimiento"""
        return self.monto if self.tipo_movimiento == 'ingreso' else -self.monto
    
    @classmethod
    def calcular_saldo_actual(cls):
        """Calcula el saldo actual de efectivo"""
        movimientos = cls.objects.all()
        saldo = 0
        for mov in movimientos:
            saldo += mov.monto_con_signo
        return saldo
    
    @classmethod
    def registrar_movimiento(cls, concepto, tipo_movimiento, categoria, monto, usuario=None, 
                           movimiento_inventario=None, simulacion_relacionada=None):
        """
        Registra un nuevo movimiento de efectivo y actualiza el saldo
        """
        saldo_anterior = cls.calcular_saldo_actual()
        
        if tipo_movimiento == 'ingreso':
            saldo_nuevo = saldo_anterior + monto
        else:  # egreso
            saldo_nuevo = saldo_anterior - monto
        
        movimiento = cls.objects.create(
            concepto=concepto,
            tipo_movimiento=tipo_movimiento,
            categoria=categoria,
            monto=monto,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=saldo_nuevo,
            automatico=True if movimiento_inventario or simulacion_relacionada else False,
            usuario=usuario,
            movimiento_inventario=movimiento_inventario,
            simulacion_relacionada=simulacion_relacionada
        )
        
        return movimiento


class ListaProduccion(models.Model):
    """Modelo principal para gestionar listas de producción de moños"""
    
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('pendiente_compra', 'Pendiente de Compra'),
        ('comprado', 'Materiales Comprados'),
        ('reabastecido', 'Inventario Reabastecido'),
        ('en_produccion', 'En Producción'),
        ('finalizado', 'Finalizado'),
    ]
    
    nombre = models.CharField(
        max_length=100, 
        help_text="Nombre descriptivo de la lista de producción"
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción opcional de la lista"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='borrador'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    usuario_creador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='listas_produccion'
    )
    
    # Totales calculados
    total_moños_planificados = models.PositiveIntegerField(default=0)
    total_moños_producidos = models.PositiveIntegerField(default=0)
    costo_total_estimado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    ganancia_estimada = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    class Meta:
        verbose_name = "Lista de Producción"
        verbose_name_plural = "Listas de Producción"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_estado_display()})"


class DetalleListaMonos(models.Model):
    """Detalles de moños incluidos en cada lista de producción"""
    
    lista_produccion = models.ForeignKey(
        ListaProduccion,
        on_delete=models.CASCADE,
        related_name='detalles_monos'
    )
    monos = models.ForeignKey(
        Monos,
        on_delete=models.CASCADE,
        related_name='detalles_lista'
    )
    cantidad = models.PositiveIntegerField(
        default=0,
        help_text="Cantidad a producir (pares o individuales según el tipo del moño)"
    )
    
    # Cantidad producida realmente (se actualiza en "Posible Venta")
    cantidad_producida = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Detalle de Moños en Lista"
        verbose_name_plural = "Detalles de Moños en Listas"
        unique_together = ['lista_produccion', 'monos']
    
    @property
    def cantidad_total_planificada(self):
        """Total de moños planificados según el tipo de venta"""
        if self.monos.tipo_venta == 'par':
            return self.cantidad * 2  # Si es par, cada cantidad son 2 moños
        else:
            return self.cantidad  # Si es individual, la cantidad es directa
    
    @property
    def cantidad_total_producida(self):
        """Total de moños producidos realmente según el tipo de venta"""
        if self.monos.tipo_venta == 'par':
            return self.cantidad_producida * 2
        else:
            return self.cantidad_producida
    
    @property
    def tipo_venta_display(self):
        """Muestra el tipo de venta con explicación"""
        if self.monos.tipo_venta == 'par':
            return f"{self.cantidad} pares (= {self.cantidad_total_planificada} moños)"
        else:
            return f"{self.cantidad} individuales"
    
    def __str__(self):
        return f"{self.monos.nombre} - {self.tipo_venta_display}"


class ResumenMateriales(models.Model):
    """Resumen de materiales necesarios por lista de producción"""
    
    lista_produccion = models.ForeignKey(
        ListaProduccion,
        on_delete=models.CASCADE,
        related_name='resumen_materiales'
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name='resumenes_lista'
    )
    
    # Cantidades calculadas
    cantidad_necesaria = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Cantidad total necesaria para la producción"
    )
    cantidad_disponible = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Cantidad disponible al momento de crear la lista"
    )
    cantidad_faltante = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Cantidad que falta comprar"
    )
    
    # Compras
    cantidad_comprada = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Cantidad realmente comprada"
    )
    precio_compra_real = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Precio real pagado por el material"
    )
    
    # Uso real
    cantidad_utilizada = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Cantidad realmente utilizada en la producción"
    )
    
    class Meta:
        verbose_name = "Resumen de Material"
        verbose_name_plural = "Resumen de Materiales"
        unique_together = ['lista_produccion', 'material']
    
    def __str__(self):
        return f"{self.material.nombre} - Lista: {self.lista_produccion.nombre}"
