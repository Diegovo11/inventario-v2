Sistema de Archivo Automático de Listas

El sistema maneja 3 estados para listas completadas:

* Finalizado → Lista recién completada (0-30)
* Archivado → Lista antigua (30+) 
* Eliminado → Borrado permanente (archivo)

Archivado Automático

Ejecutar manualmente:

```bash
python manage.py archivar_listas_antiguas
```

Opciones disponibles:

```bash
Cambiar dias
python manage.py archivar_listas_antiguas --dias 60

Ver qué se archivaría sin hacer cambios
python manage.py archivar_listas_antiguas --dry-run
```

Acceso al Archivo

Desde la web:

1. Menú lateral → "Archivo"
2. Listas Activas → botón "Ver Archivo"
3. Listas Completadas → botón "Ver Archivo (30+ días)"


```
Crear Lista
    ↓
Proceso de Producción 
    ↓
Finalizado ← Aquí empieza el conteo
    ↓
    30
    ↓
Archivado ← Se archiva automáticamente
    ↓
se Puedes eliminar
    ↓
[Eliminado Permanentemente]
```

Versión: 6.0  
Fecha: Octubre 2025  
Autor: Sistema de Gestión de Inventario
