#!/bin/bash
# Script para configurar Railway con PostgreSQL

echo "🚀 Configurando Railway con PostgreSQL persistente..."

# 1. Verificar si Railway CLI está instalado
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI no está instalado. Instalando..."
    npm install -g @railway/cli
fi

# 2. Login a Railway (necesitarás autenticarte)
echo "🔑 Iniciando sesión en Railway..."
railway login

# 3. Agregar PostgreSQL al proyecto
echo "📊 Agregando PostgreSQL al proyecto..."
railway add --database postgresql

# 4. Redeploy para aplicar cambios
echo "🔄 Redespleegando con PostgreSQL..."
railway up

echo "✅ ¡Configuración completa! Tu aplicación ahora usa PostgreSQL persistente."
echo "📄 Verifica en Railway Dashboard que tienes el servicio PostgreSQL activo."