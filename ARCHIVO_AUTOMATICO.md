# Sistema de Archivo Automático de Listas

## 📦 ¿Cómo funciona?

El sistema maneja 3 estados para listas completadas:

1. **Finalizado** → Lista recién completada (0-30 días)
2. **Archivado** → Lista antigua (30+ días) 
3. **Eliminado** → Borrado permanente (solo desde archivo)

## ⏰ Archivado Automático

Las listas se archivan **automáticamente después de 30 días** de haber sido finalizadas.

### Ejecutar manualmente:

```bash
python manage.py archivar_listas_antiguas
```

### Opciones disponibles:

```bash
# Cambiar días (ej: 60 días)
python manage.py archivar_listas_antiguas --dias 60

# Ver qué se archivaría sin hacer cambios
python manage.py archivar_listas_antiguas --dry-run
```

## 🔄 Configurar en Railway (Automático)

Para que se ejecute automáticamente cada día:

### Opción 1: Cron Job (Recomendado)

1. Ir a tu proyecto en Railway
2. Agregar servicio "Cron"
3. Configurar:
   ```
   0 2 * * * cd /app && python manage.py archivar_listas_antiguas
   ```
   (Se ejecuta todos los días a las 2 AM)

### Opción 2: Script en Procfile

Modificar `Procfile`:
```
web: gunicorn inventario_project.wsgi
worker: while true; do python manage.py archivar_listas_antiguas && sleep 86400; done
```

## 📂 Acceso al Archivo

### Desde la web:

1. **Menú lateral** → "Archivo"
2. **Listas Activas** → botón "Ver Archivo"
3. **Listas Completadas** → botón "Ver Archivo (30+ días)"

### Desde el archivo puedes:

- ✅ Ver todas las listas archivadas
- ✅ Ver detalles completos de cada lista
- ✅ Eliminar listas permanentemente (una por una)
- ❌ NO puedes editar listas archivadas

## 🗑️ Eliminación

Las listas archivadas **PUEDEN SER ELIMINADAS**:

1. Ir a "Archivo"
2. Click en "Eliminar Permanentemente" en la lista
3. Confirmar eliminación
4. **⚠️ Esta acción NO se puede deshacer**

## 📊 Flujo Completo

```
Crear Lista (Paso 1)
    ↓
Proceso de Producción (Pasos 2-6)
    ↓
[Finalizado] ← Aquí empieza el conteo
    ↓
    📅 30 días
    ↓
[Archivado] ← Se archiva automáticamente
    ↓
    🗑️ Puedes eliminar
    ↓
[Eliminado Permanentemente]
```

## ⚙️ Configuración

### Cambiar días para archivado:

Editar `archivar_listas_antiguas.py`:

```python
parser.add_argument(
    '--dias',
    type=int,
    default=30,  # ← Cambiar aquí (ej: 60, 90)
    help='Número de días...',
)
```

### Deshabilitar archivado automático:

Simplemente no ejecutes el comando. Las listas permanecerán en "Finalizado" indefinidamente.

## 🔍 Consultas SQL Útiles

### Ver todas las listas archivadas:

```sql
SELECT nombre, fecha_modificacion, ganancia_real 
FROM inventario_listaproduccion 
WHERE estado = 'archivado' 
ORDER BY fecha_modificacion DESC;
```

### Ver listas próximas a archivarse:

```sql
SELECT nombre, 
       fecha_modificacion,
       DATEDIFF(NOW(), fecha_modificacion) as dias_finalizados
FROM inventario_listaproduccion 
WHERE estado = 'finalizado'
  AND DATEDIFF(NOW(), fecha_modificacion) >= 25;
```

## 💡 Mejores Prácticas

1. **Revisa el archivo mensualmente** para decidir qué eliminar
2. **Exporta estadísticas importantes** antes de eliminar
3. **Ejecuta --dry-run primero** para verificar qué se archivará
4. **Mantén backups regulares** de la base de datos
5. **Documenta listas importantes** antes de archivarlas

## 🚨 Consideraciones

- Las listas archivadas **conservan todos sus datos**
- La ganancia y estadísticas **se mantienen intactas**
- Los moños y materiales **NO se afectan**
- Solo el **estado cambia** de 'finalizado' a 'archivado'
- Las listas archivadas **NO aparecen en reportes activos**

## 📞 Soporte

Si necesitas recuperar una lista archivada:

```python
from inventario.models import ListaProduccion

# Encontrar la lista
lista = ListaProduccion.objects.get(id=123, estado='archivado')

# Restaurar a finalizado
lista.estado = 'finalizado'
lista.save()
```

---

**Versión:** 1.0  
**Fecha:** Octubre 2025  
**Autor:** Sistema de Gestión de Inventario
