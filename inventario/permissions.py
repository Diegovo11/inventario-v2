"""
Decoradores y funciones auxiliares para control de permisos
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponseForbidden


def requiere_nivel(*niveles_permitidos):
    """
    Decorador que verifica el nivel del usuario
    
    Uso:
        @requiere_nivel('superuser', 'admin')
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            # Verificar si el usuario tiene perfil
            if not hasattr(request.user, 'userprofile'):
                return render(request, 'inventario/sin_permiso.html', {
                    'mensaje': 'Tu cuenta no tiene un perfil asignado. Contacta al administrador.'
                }, status=403)
            
            # Verificar nivel
            if request.user.userprofile.nivel not in niveles_permitidos:
                return render(request, 'inventario/sin_permiso.html', {
                    'mensaje': 'No tienes permisos para acceder a esta página.',
                    'nivel_requerido': ', '.join(niveles_permitidos),
                    'tu_nivel': request.user.userprofile.get_nivel_display()
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def puede_ver_precios(user):
    """Verifica si el usuario puede ver precios"""
    if not hasattr(user, 'userprofile'):
        return False
    return user.userprofile.puede_ver_precios()


def puede_ver_flujo_efectivo(user):
    """Verifica si el usuario puede ver flujo de efectivo"""
    if not hasattr(user, 'userprofile'):
        return False
    return user.userprofile.puede_ver_flujo_efectivo()


def puede_gestionar_ventas(user):
    """Verifica si el usuario puede gestionar ventas"""
    if not hasattr(user, 'userprofile'):
        return False
    return user.userprofile.puede_gestionar_ventas()


def puede_ver_analytics(user):
    """Verifica si el usuario puede ver analytics"""
    if not hasattr(user, 'userprofile'):
        return False
    return user.userprofile.puede_ver_analytics()
