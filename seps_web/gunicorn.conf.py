# Gunicorn — configuración para producción IntelliCoop
import multiprocessing

# Bind
bind = "127.0.0.1:8000"

# Workers: 2 * CPUs + 1 es la fórmula estándar
workers = multiprocessing.cpu_count() * 2 + 1

# Timeouts
timeout = 60
keepalive = 5

# Logging
accesslog = "/var/log/intellicoop/access.log"
errorlog  = "/var/log/intellicoop/error.log"
loglevel  = "info"

# Proceso
worker_class = "sync"
preload_app  = True
