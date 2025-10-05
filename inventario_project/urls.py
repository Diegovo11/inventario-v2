"""
URL configuration for inventario_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from django.http import JsonResponse

def redirect_to_inventario(request):
    """Redirigir desde la raíz al inventario"""
    return redirect('/inventario/')

def healthcheck(request):
    """Vista simple para healthcheck de Railway"""
    return JsonResponse({"status": "ok", "service": "inventario-v2"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('inventario/', include('inventario.urls')),
    
    # Healthcheck endpoint
    path('health/', healthcheck, name='healthcheck'),
    
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    path('', redirect_to_inventario),  # Página raíz redirige al inventario
]
