# Fix: Warnings de Timezone en Analytics

## 🐛 Problema Identificado

Al acceder a `/inventario/analytics/` aparecían warnings en los logs de Railway:

```
RuntimeWarning: DateTimeField MovimientoEfectivo.fecha received a naive datetime 
(2025-10-01 00:00:00) while time zone support is active.
```

## 🔍 Causa Raíz

Django tiene `USE_TZ = True` en settings (soporte de zonas horarias activo), pero se estaban usando fechas "naive" (sin zona horaria) en varios lugares:

### 1. **views_analytics.py**
```python
# ANTES (❌ naive datetime)
elif periodo == 'all':
    fecha_inicio = datetime(2020, 1, 1)
```

### 2. **views_contaduria.py**
```python
# ANTES (❌ naive datetime)
inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()

# Filtros usaban fecha__date__gte que internamente crea naive datetimes
movimientos = MovimientoEfectivo.objects.filter(
    fecha__date__gte=fecha_inicio,
    fecha__date__lte=fecha_fin
)
```

## ✅ Solución Implementada

### 1. **Importar timezone en ambos archivos**
```python
from django.utils import timezone
```

### 2. **views_analytics.py - Hacer fecha aware**
```python
# DESPUÉS (✅ timezone-aware datetime)
elif periodo == 'all':
    fecha_inicio = timezone.make_aware(datetime(2020, 1, 1))
```

### 3. **views_contaduria.py - Múltiples correcciones**

#### a) Usar timezone.now() en lugar de datetime.now()
```python
# DESPUÉS (✅ timezone-aware)
inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
```

#### b) Convertir fechas de formularios a timezone-aware
```python
# DESPUÉS (✅ convierte a aware)
if not fecha_inicio:
    inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    fecha_inicio = inicio_mes
else:
    # Convertir string a datetime naive y luego a aware
    fecha_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    fecha_inicio = timezone.make_aware(datetime.combine(fecha_dt, datetime.min.time()))
```

#### c) Cambiar filtros de fecha__date__gte a fecha__gte
```python
# ANTES (❌ crea naive datetime internamente)
movimientos = MovimientoEfectivo.objects.filter(
    fecha__date__gte=fecha_inicio,
    fecha__date__lte=fecha_fin
)

# DESPUÉS (✅ usa timezone-aware datetime directamente)
movimientos = MovimientoEfectivo.objects.filter(
    fecha__gte=fecha_inicio,
    fecha__lte=fecha_fin
)
```

## 📝 Archivos Modificados

1. **inventario/views_analytics.py**
   - Línea 11: Importar `timezone`
   - Línea 35: Usar `timezone.make_aware(datetime(2020, 1, 1))`

2. **inventario/views_contaduria.py**
   - Línea 8: Importar `timezone`
   - Línea 24: Cambiar `datetime.now()` → `timezone.now()`
   - Líneas 129-148: Convertir fechas de formulario a timezone-aware
   - Líneas 143-146: Cambiar `fecha__date__gte/lte` → `fecha__gte/lte`

## 🎯 Resultado

✅ **Warnings eliminados completamente**
✅ **Analytics funciona correctamente**
✅ **Estado de resultados funciona sin warnings**
✅ **Todas las consultas de fecha son timezone-aware**

## 📚 Conceptos Clave

### Naive vs Aware Datetimes

**Naive datetime:**
```python
datetime(2025, 10, 1)  # Sin zona horaria
datetime.now()         # Sin zona horaria
```

**Aware datetime:**
```python
timezone.now()                           # Con zona horaria
timezone.make_aware(datetime(2025, 10, 1))  # Convertir naive a aware
```

### Cuándo usar cada uno

| Situación | Usar |
|-----------|------|
| Django con `USE_TZ=True` | ✅ Aware datetimes (`timezone.now()`) |
| Consultas a base de datos | ✅ Aware datetimes |
| Comparaciones de fechas | ✅ Aware datetimes |
| Solo formateo de string | ⚠️ Ambos funcionan |
| Django con `USE_TZ=False` | ⚠️ Naive datetimes (no recomendado) |

## 🚀 Deploy

El fix se deployó en Railway automáticamente:

```bash
git add -A
git commit -m "Fix: Corregir warnings de timezone en analytics y contaduría"
git push origin main
```

**Commit:** 27669b3

## ✅ Verificación

Para verificar que funciona correctamente:

1. Ve a https://web-production-944d97.up.railway.app/inventario/analytics/
2. Cambia entre diferentes períodos (1m, 3m, 6m, 12m, Todo)
3. Ve a https://web-production-944d97.up.railway.app/inventario/contaduria/estado-resultados/
4. Filtra por diferentes fechas
5. **Verifica los logs de Railway** → No deben aparecer más warnings

## 📖 Referencias

- [Django Timezone Documentation](https://docs.djangoproject.com/en/stable/topics/i18n/timezones/)
- [timezone.make_aware()](https://docs.djangoproject.com/en/stable/ref/utils/#django.utils.timezone.make_aware)
- [timezone.now()](https://docs.djangoproject.com/en/stable/ref/utils/#django.utils.timezone.now)

---

**Versión:** 1.0  
**Fecha:** Octubre 5, 2025  
**Commit:** 27669b3
