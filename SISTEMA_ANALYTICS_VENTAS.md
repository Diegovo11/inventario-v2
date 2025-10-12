Sistema de Análisis de Ventas por Moño

Se implementó

Se creó un sistema completo de registro y análisis de ventas individuales por tipo de moño. Ahora cada venta se registra de forma granular para poder hacer análisis detallados.

Componentes Implementados

1. Modelo `VentaMonos`

Nuevo modelo que registra cada venta individual:

```python
class VentaMonos(models.Model):
    lista_produccion    # Lista de donde salió (opcional)
    monos              # Tipo de moño vendido
    cantidad_vendida   # Cantidad vendida (pares o individuales)
    tipo_venta         # 'individual' o 'par'
    precio_unitario    # Precio por unidad/par
    ingreso_total      # Total de la venta
    costo_unitario     # Costo de producción
    ganancia_total     # Ganancia de esta venta
    fecha              # Cuándo se vendió
    usuario            # Quién registró la venta
```

Características:
- ✅ Distingue entre ventas individuales y por par
- ✅ Calcula automáticamente cantidad total de moños (pares = cantidad × 2)
- ✅ Registra ganancia individual por venta
- ✅ Índices en base de datos para consultas rápidas

2. Registro Automático de Ventas

Cuando registras ventas en Paso 6 (Registrar Ventas):


3. Analytics Dashboard

Gráficos y Estadísticas:
1. Moños más vendidos (por cantidad real de moños)
2. Moños con mejor rendimiento (% de ganancia)
3. Evolución mensual de ventas
4. Estadísticas generales:
   - Total de ventas ($)
   - Total de costos
   - Total de ganancias
   - Cantidad total vendida
   - Rendimiento general (%)
   - Tipos de moños vendidos
   - Total de transacciones

4. Vista Detallada por Moño

Muestra:
- Total ingresos del moño específico
- Total costos de producción
- Ganancia total
- Cantidad vendida (pares/individuales)
- Cantidad total de moños producidos
- Rendimiento (%)
- Evolución mensual
- Lista de todas las ventas del moño

5. Panel de Administración

Acceso a todas las ventas en Django Admin:

Features:
- Ver todas las ventas registradas
- Filtrar por moño, tipo_venta, fecha
- Buscar por nombre de moño o lista
- Ordenar por ingreso, ganancia, fecha
- Ganancia con colores (verde positivo, rojo negativo)
- Jerarquía de fechas para navegación rápida

Flujo de Trabajo

```
1. Crear Lista de Producción
   ↓
2. Descargar Lista de Compras
   ↓
3. Registrar Compras
   ↓
4. Iniciar Producción (descontar materiales)
   ↓
5. Registrar Moños Producidos
   ↓
6. REGISTRAR VENTAS ← Aquí se crean los VentaMonos
   ↓
   - Se crea 1 VentaMonos por cada tipo de moño vendido
   - Se registra: cantidad, precio, ingreso, costo, ganancia
   - Se actualiza lista a 'finalizado'
   - Se crea MovimientoEfectivo general
   ↓
7. ANALYTICS
   - Dashboard muestra ventas reales
   - Análisis por tipo de moño funciona
   - Gráficos muestran datos correctos
```

Consultas SQL Útiles

Ver todas las ventas de un moño específico:
```sql
SELECT fecha, cantidad_vendida, ingreso_total, ganancia_total
FROM inventario_ventamonos
WHERE monos_id = 1
ORDER BY fecha DESC;
```

Top 5 moños más vendidos (últimos 3 meses):
```sql
SELECT m.nombre, 
       SUM(v.cantidad_vendida) as total_vendido,
       SUM(v.ingreso_total) as ingresos,
       SUM(v.ganancia_total) as ganancias
FROM inventario_ventamonos v
JOIN inventario_monos m ON v.monos_id = m.id
WHERE v.fecha >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
GROUP BY m.nombre
ORDER BY total_vendido DESC
LIMIT 5;
```

Ventas por mes (año actual):
```sql
SELECT DATE_FORMAT(fecha, '%Y-%m') as mes,
       COUNT(*) as num_ventas,
       SUM(ingreso_total) as total_ingresos,
       SUM(ganancia_total) as total_ganancias
FROM inventario_ventamonos
WHERE YEAR(fecha) = YEAR(NOW())
GROUP BY DATE_FORMAT(fecha, '%Y-%m')
ORDER BY mes;
```

Migración

Archivo: `inventario/migrations/0008_ventamonos.py`



Versión: 6.0  
Fecha: Octubre 2025  
Commit: 595a0f7
