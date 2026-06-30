#!/bin/bash
# ─────────────────────────────────────────────────────────────
# IntelliCoop — Script de despliegue en VPS
# Uso: bash deploy.sh
# VPS: 157.230.62.218 | SSH port 443 | user: root
# ─────────────────────────────────────────────────────────────

set -e  # Salir si cualquier comando falla

VPS_IP="157.230.62.218"
VPS_PORT="443"
VPS_USER="root"
REMOTE_DIR="/var/www/seps_web"
LOCAL_DIR="."

echo "========================================"
echo "  IntelliCoop — Deploy al VPS"
echo "========================================"

# 1. Copiar archivos al VPS (excluye .env, __pycache__, db.sqlite3)
echo ""
echo "[1/5] Copiando archivos al VPS..."
rsync -avz --progress \
  --exclude='.env' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='db.sqlite3' \
  --exclude='staticfiles/' \
  --exclude='.git/' \
  -e "ssh -p $VPS_PORT" \
  "$LOCAL_DIR/" "$VPS_USER@$VPS_IP:$REMOTE_DIR/"

# 2. Instalar dependencias en el VPS
echo ""
echo "[2/5] Instalando dependencias..."
ssh -p $VPS_PORT $VPS_USER@$VPS_IP "
  cd $REMOTE_DIR
  pip install -r requirements.txt --quiet
"

# 3. Recolectar estáticos
echo ""
echo "[3/5] Recolectando archivos estáticos..."
ssh -p $VPS_PORT $VPS_USER@$VPS_IP "
  cd $REMOTE_DIR
  python manage.py collectstatic --noinput
"

# 4. Crear directorio de logs si no existe
echo ""
echo "[4/5] Preparando directorios de logs..."
ssh -p $VPS_PORT $VPS_USER@$VPS_IP "
  mkdir -p /var/log/intellicoop
"

# 5. Reiniciar servicios
echo ""
echo "[5/5] Reiniciando servicios..."
ssh -p $VPS_PORT $VPS_USER@$VPS_IP "
  systemctl restart gunicorn 2>/dev/null || echo '  (gunicorn no está como servicio todavía)'
  systemctl reload nginx 2>/dev/null || echo '  (nginx: revisar configuración)'
"

echo ""
echo "========================================"
echo "  Deploy completado"
echo "  Revisar: http://$VPS_IP"
echo "========================================"
