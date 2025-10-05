# Sistema de Análisis de Ventas por Moño

## 📊 ¿Qué se implementó?

Se creó un **sistema completo de registro y análisis de ventas individuales** por tipo de moño. Ahora cada venta se registra de forma granular para poder hacer análisis detallados.

## 🔧 Componentes Implementados

### 1. Modelo `VentaMonos`

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

**Características:**
- ✅ Distingue entre ventas individuales y por par
- ✅ Calcula automáticamente cantidad total de moños (pares = cantidad × 2)
- ✅ Registra ganancia individual por venta
- ✅ Índices en base de datos para consultas rápidas

### 2. Registro Automático de Ventas

Cuando registras ventas en **Paso 6** (Registrar Ventas):

**ANTES:**
- Solo se creaba un `MovimientoEfectivo` general
- No había detalle por tipo de moño
- No se podía analizar qué moños se vendieron

**AHORA:**
- Se crea un `VentaMonos` por cada tipo de moño vendido
- Se mantiene el `MovimientoEfectivo` general (para contabilidad)
- Cada venta tiene su ganancia calculada
- Mensaje de éxito muestra: "✅ 3 venta(s) registrada(s) exitosamente"

### 3. Analytics Dashboard Mejorado

**URL:** `/inventario/analytics/`

**ANTES:**
- Mostraba ventas de simulaciones (datos no reales)
- No distinguía entre pares e individuales
- Análisis impreciso

**AHORA:**
- ✅ Lee datos de `VentaMonos` (ventas reales)
- ✅ Distingue correctamente pares vs individuales
- ✅ Muestra cantidad vendida Y cantidad total de moños
- ✅ Estadísticas precisas por tipo de moño

**Gráficos y Estadísticas:**
1. **Moños más vendidos** (por cantidad real de moños)
2. **Moños con mejor rendimiento** (% de ganancia)
3. **Evolución mensual de ventas**
4. **Estadísticas generales:**
   - Total de ventas ($)
   - Total de costos
   - Total de ganancias
   - Cantidad total vendida
   - Rendimiento general (%)
   - Tipos de moños vendidos
   - Total de transacciones

### 4. Vista Detallada por Moño

**URL:** `/inventario/analytics/detalle-mono/<id>/`

**Muestra:**
- Total ingresos del moño específico
- Total costos de producción
- Ganancia total
- Cantidad vendida (pares/individuales)
- Cantidad total de moños producidos
- Rendimiento (%)
- Evolución mensual
- Lista de todas las ventas del moño

### 5. Panel de Administración

Acceso a todas las ventas en Django Admin:

**Ruta:** `/admin/inventario/ventamonos/`

**Features:**
- Ver todas las ventas registradas
- Filtrar por moño, tipo_venta, fecha
- Buscar por nombre de moño o lista
- Ordenar por ingreso, ganancia, fecha
- Ganancia con colores (verde positivo, rojo negativo)
- Jerarquía de fechas para navegación rápida

## 🔄 Flujo de Trabajo

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
7. ANALYTICS ACTUALIZADO
   - Dashboard muestra ventas reales
   - Análisis por tipo de moño funciona
   - Gráficos muestran datos correctos
```

## 📈 Ejemplo de Uso

### Escenario: Vendiste 10 moños de diferentes tipos

**Paso 6 - Registrar Ventas:**
```
Moño A (individual): 5 vendidos × $10 = $50
Moño B (par): 3 vendidos × $15 = $45
Moño C (individual): 2 vendidos × $12 = $24
Total: $119
```

**Lo que se guarda en la base de datos:**

```python
VentaMonos #1:
  monos: Moño A
  cantidad_vendida: 5
  tipo_venta: individual
  cantidad_total_monos: 5
  ingreso_total: $50
  ganancia_total: $25

VentaMonos #2:
  monos: Moño B
  cantidad_vendida: 3
  tipo_venta: par
  cantidad_total_monos: 6  ← (3 pares = 6 moños)
  ingreso_total: $45
  ganancia_total: $20

VentaMonos #3:
  monos: Moño C
  cantidad_vendida: 2
  tipo_venta: individual
  cantidad_total_monos: 2
  ingreso_total: $24
  ganancia_total: $10
```

**En Analytics:**
- Total moños vendidos: 13 moños (5 + 6 + 2)
- Ingreso total: $119
- Ganancia total: $55
- Gráfico "Más Vendidos": Moño B (6), Moño A (5), Moño C (2)

## 🎯 Beneficios

1. **Análisis Preciso:**
   - Sabes exactamente qué moños se venden más
   - Identificas los más rentables
   - Puedes tomar decisiones basadas en datos reales

2. **Reportes por Período:**
   - Últimos 1, 3, 6, 12 meses
   - Evolución mensual por moño
   - Comparativas de rendimiento

3. **Toma de Decisiones:**
   - ¿Qué moños producir más?
   - ¿Cuáles tienen mejor margen?
   - ¿Qué moños eliminar del catálogo?

4. **Histórico Completo:**
   - Todas las ventas se guardan
   - Se pueden consultar en cualquier momento
   - Exportables desde admin

## 🔍 Consultas SQL Útiles

### Ver todas las ventas de un moño específico:
```sql
SELECT fecha, cantidad_vendida, ingreso_total, ganancia_total
FROM inventario_ventamonos
WHERE monos_id = 1
ORDER BY fecha DESC;
```

### Top 5 moños más vendidos (últimos 3 meses):
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

### Ventas por mes (año actual):
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

## 📝 Notas Técnicas

### Compatibilidad con Datos Antiguos

- Las ventas registradas **antes** de esta actualización no tendrán `VentaMonos`
- Solo las nuevas ventas (después del deployment) se registrarán
- Los analytics solo mostrarán datos de ventas nuevas
- Para retroalimentar: necesitarías crear manualmente `VentaMonos` de ventas pasadas

### Migración

**Archivo:** `inventario/migrations/0008_ventamonos.py`

**Ejecutar en producción:**
```bash
# Railway lo hace automáticamente
# O manualmente:
python manage.py migrate
```

### Performance

- Índices en `monos_id` y `fecha` para consultas rápidas
- Select related en queries para evitar N+1
- Caché de estadísticas generales (opcional futuro)

## 🚀 Siguientes Mejoras Posibles

1. **Exportación:**
   - Exportar analytics a Excel/PDF
   - Reportes automáticos por email

2. **Proyecciones:**
   - Predecir ventas futuras
   - Sugerencias de producción

3. **Alertas:**
   - Moños con bajo rendimiento
   - Moños que no se han vendido en X tiempo

4. **Comparativas:**
   - Comparar períodos (este mes vs mes pasado)
   - Benchmark de rendimiento

5. **Gráficos Avanzados:**
   - Heatmap de ventas por día
   - Tendencias con líneas de regresión

---

**Versión:** 1.0  
**Fecha:** Octubre 2025  
**Commit:** 595a0f7
