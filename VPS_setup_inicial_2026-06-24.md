# VPS Setup Inicial — Proyecto SEPS EEFF
**Fecha:** 2026-06-24  
**Servidor:** DigitalOcean Droplet — 157.230.62.218  
**Plan:** $6/mes — 1 GB RAM, 25 GB SSD, Ubuntu 24.04.3 LTS  
**Puerto SSH:** 443

---

## 1. Conexión al servidor

```bash
ssh -p 443 root@157.230.62.218
```

---

## 2. Verificación del estado inicial

```bash
free -h
df -h /
cat /etc/os-release | grep PRETTY_NAME
python3 --version
```

**Resultado:**
```
PRETTY_NAME="Ubuntu 24.04.3 LTS"
               total        used        free      shared  buff/cache   available
Mem:           961Mi       401Mi       103Mi       4.0Mi       609Mi       559Mi
Disco: 24G total, 2.9G usado, 21G libres
Python 3.12.3
```

---

## 3. Actualización del sistema

```bash
apt update && apt upgrade -y
```

---

## 4. Instalación de Nginx, PostgreSQL y herramientas Python

```bash
apt install -y nginx postgresql postgresql-contrib python3-pip python3-venv
```

---

## 5. Habilitar e iniciar servicios

```bash
systemctl enable nginx postgresql
systemctl start nginx postgresql
systemctl status nginx postgresql --no-pager | grep -E "Active:|●"
```

**Resultado:**
```
● nginx.service - A high performance web server and a reverse proxy server
     Active: active (running) since Wed 2026-06-24 00:14:36 UTC
● postgresql.service - PostgreSQL RDBMS
     Active: active (exited) since Wed 2026-06-24 00:14:43 UTC
```

---

## 6. Crear usuario y base de datos PostgreSQL

```bash
sudo -u postgres psql -c "CREATE USER seps_user WITH PASSWORD 'seps2024';"
sudo -u postgres psql -c "CREATE DATABASE seps_eeff OWNER seps_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE seps_eeff TO seps_user;"
```

**Resultado:**
```
CREATE ROLE
CREATE DATABASE
GRANT
```

**Credenciales PostgreSQL VPS:**
- Host: localhost
- Puerto: 5432
- BD: seps_eeff
- Usuario: seps_user
- Password: seps2024

---

## 7. Crear estructura del proyecto y entorno virtual

```bash
mkdir -p /var/www/seps
cd /var/www/seps
python3 -m venv venv
source venv/bin/activate
pip install django gunicorn fastapi uvicorn psycopg2-binary python-dotenv httpx
```

---

## 8. Crear proyecto Django

```bash
cd /var/www/seps
source venv/bin/activate
django-admin startproject seps_project .
python manage.py startapp core
```

---

## 9. Configurar settings.py

```bash
cat > /var/www/seps/seps_project/settings.py << 'EOF'
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-seps-eeff-2026-cambiar-en-produccion'

DEBUG = False

ALLOWED_HOSTS = ['157.230.62.218', 'localhost']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'seps_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'seps_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'seps_eeff',
        'USER': 'seps_user',
        'PASSWORD': 'seps2024',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

LANGUAGE_CODE = 'es-ec'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EOF
```

---

## 10. Ejecutar migraciones Django

```bash
cd /var/www/seps
source venv/bin/activate
python manage.py migrate
```

**Resultado:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  ...
  Applying sessions.0001_initial... OK
```

---

## 11. Colectar archivos estáticos e iniciar Gunicorn

```bash
cd /var/www/seps
source venv/bin/activate
mkdir -p templates staticfiles
python manage.py collectstatic --noinput
gunicorn --bind 0.0.0.0:8000 seps_project.wsgi:application --daemon
```

**Resultado:**
```
130 static files copied to '/var/www/seps/staticfiles'.
Gunicorn iniciado
```

---

## 12. Configurar Nginx como proxy reverso

```bash
cat > /etc/nginx/sites-available/seps << 'EOF'
server {
    listen 80;
    server_name 157.230.62.218;

    location /static/ {
        alias /var/www/seps/staticfiles/;
    }

    location /api/rakkun/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

ln -sf /etc/nginx/sites-available/seps /etc/nginx/sites-enabled/seps
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
```

**Resultado:**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
Nginx OK
```

---

## 13. Crear microservicio FastAPI para Rakkun

Archivo: `/var/www/seps/rakkun_api.py`

> Nota: se usó base64 para escribir el archivo porque la consola web tiene problemas con heredocs con comillas anidadas.

```python
from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
import httpx
import os

app = FastAPI()

DB = {
    "host": "localhost", "port": 5432,
    "dbname": "seps_eeff", "user": "seps_user", "password": "seps2024"
}

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "")

class Pregunta(BaseModel):
    texto: str

@app.get("/health")
def health():
    return {"status": "ok", "servicio": "Rakkun API"}

@app.post("/preguntar")
async def preguntar(p: Pregunta):
    schema = "public"
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='{schema}'")
    tablas = cur.fetchone()[0]
    conn.close()
    contexto = f"Base de datos SEPS con {tablas} tablas disponibles."
    if not OPENROUTER_KEY:
        return {"respuesta": f"[Sin API key] Pregunta recibida: {p.texto}. {contexto}"}
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": f"Eres Rakkun, asistente financiero SEPS Ecuador. {contexto}"},
                    {"role": "user", "content": p.texto}
                ]
            }
        )
    return {"respuesta": r.json()["choices"][0]["message"]["content"]}
```

---

## 14. Crear servicios systemd

```bash
cat > /etc/systemd/system/seps-django.service << 'EOF'
[Unit]
Description=SEPS Django Gunicorn
After=network.target postgresql.service

[Service]
User=root
WorkingDirectory=/var/www/seps
ExecStart=/var/www/seps/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 seps_project.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/seps-rakkun.service << 'EOF'
[Unit]
Description=SEPS Rakkun FastAPI
After=network.target postgresql.service

[Service]
User=root
WorkingDirectory=/var/www/seps
ExecStart=/var/www/seps/venv/bin/uvicorn rakkun_api:app --host 127.0.0.1 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable seps-django seps-rakkun
systemctl start seps-django seps-rakkun
```

---

## 15. Verificación final

```bash
# Estado de servicios
systemctl status seps-django seps-rakkun --no-pager | grep -E "●|Active:"

# Test Django vía Nginx
curl -s -o /dev/null -w "%{http_code}" http://157.230.62.218/admin/

# Test Rakkun health
curl http://127.0.0.1:8001/health

# Test Rakkun vía Nginx
curl http://127.0.0.1:80/api/rakkun/health
```

**Resultados:**
```
● seps-django.service   Active: active (running)
● seps-rakkun.service   Active: active (running)

Django /admin/  → 302  (redirect a login — correcto)
Rakkun health   → {"status":"ok","servicio":"Rakkun API"}
Rakkun via Nginx → {"status":"ok","servicio":"Rakkun API"}
```

---

## Estructura final del proyecto en VPS

```
/var/www/seps/
├── venv/                        # virtualenv Python 3.12
├── seps_project/
│   ├── settings.py              # configurado con PostgreSQL VPS
│   ├── urls.py
│   └── wsgi.py
├── core/                        # app Django principal
├── templates/                   # templates HTML (pendiente)
├── staticfiles/                 # 130 archivos estáticos
└── rakkun_api.py                # microservicio FastAPI Rakkun
```

---

## Pendientes

- [ ] Agregar `OPENROUTER_KEY` como variable de entorno en `seps-rakkun.service`
- [ ] Migrar `fact_indicadores` desde PC local al PostgreSQL del VPS
- [ ] Construir templates Django (dashboard, cooperativa, ranking CAMEL, comparativo, VTuber)
- [ ] Integrar Live2D Rakkun 2.0 en template del VTuber
- [ ] Configurar dominio + SSL con Let's Encrypt
