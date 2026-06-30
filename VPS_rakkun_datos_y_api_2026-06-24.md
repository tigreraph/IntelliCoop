# VPS — Rakkun con Datos Reales SEPS
**Fecha:** 2026-06-24  
**Continuación de:** `VPS_setup_inicial_2026-06-24.md`

---

## 1. Configurar OPENROUTER_KEY en el servicio Rakkun

```bash
# Reemplazar TU_KEY_AQUI con la key real de OpenRouter (key: rakkun-seps)
sed -i '/\[Service\]/a Environment="OPENROUTER_KEY=TU_KEY_AQUI"' /etc/systemd/system/seps-rakkun.service
systemctl daemon-reload
systemctl restart seps-rakkun
```

---

## 2. Migración de datos desde PC local al VPS

### En PowerShell de la PC local — exportar tablas

```powershell
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -h localhost -p 5434 -U postgres -d seps_eeff -t fact_indicadores -t dim_cooperativa -t dim_cuenta --no-owner --no-acl -f "$env:USERPROFILE\Desktop\seps_migracion.sql" -W
```

### Transferir al VPS por SCP (puerto 443)

```powershell
scp -P 443 "$env:USERPROFILE\Desktop\seps_migracion.sql" root@157.230.62.218:/root/seps_migracion.sql
```

### En el VPS — importar datos

```bash
PGPASSWORD=seps2024 psql -h localhost -U seps_user -d seps_eeff -f /root/seps_migracion.sql
```

### Verificar conteos

```bash
PGPASSWORD=seps2024 psql -h localhost -U seps_user -d seps_eeff -c "SELECT COUNT(*) FROM fact_indicadores; SELECT COUNT(*) FROM dim_cooperativa; SELECT COUNT(*) FROM dim_cuenta;"
```

**Resultado esperado:**
```
 count  → 23175  (fact_indicadores)
 count  → 242    (dim_cooperativa)
 count  → 1642   (dim_cuenta)
```

---

## 3. Estructura real de las tablas

```bash
# Ver estructura de tablas
PGPASSWORD=seps2024 psql -h localhost -U seps_user -d seps_eeff -c "\d dim_cooperativa"
PGPASSWORD=seps2024 psql -h localhost -U seps_user -d seps_eeff -c "\d fact_indicadores"
```

**dim_cooperativa:** ruc (PK), razon_social, segmento, primera_fecha, ultima_fecha, meses_activo, estado  
**fact_indicadores:** fecha_corte, ruc (FK), activo_total, patrimonio, cartera_bruta, depositos, capitalizacion_pct, morosidad_pct, cobertura_pct, roa_pct, roe_pct, nim_pct, liquidez_ampliada, eficiencia_op_pct, apalancamiento, intermediacion, camel_score, rating_camel

---

## 4. Comandos para consultar a Rakkun

### Health check

```bash
curl http://127.0.0.1:8001/health
```

### Preguntar a Rakkun (directo en VPS)

```bash
curl -s -X POST http://127.0.0.1:8001/preguntar \
  -H "Content-Type: application/json" \
  -d '{"texto": "TU PREGUNTA AQUI"}'
```

### Preguntar a Rakkun (vía Nginx desde internet)

```bash
curl -s -X POST http://157.230.62.218/api/rakkun/preguntar \
  -H "Content-Type: application/json" \
  -d '{"texto": "TU PREGUNTA AQUI"}'
```

### Ejemplos de preguntas probadas

```bash
# Distribución por segmento
curl -s -X POST http://127.0.0.1:8001/preguntar \
  -H "Content-Type: application/json" \
  -d '{"texto": "cuantas cooperativas hay y como se distribuyen por segmento?"}'

# Top CAMEL
curl -s -X POST http://127.0.0.1:8001/preguntar \
  -H "Content-Type: application/json" \
  -d '{"texto": "cuales son las cooperativas con mejor score CAMEL?"}'

# Morosidad
curl -s -X POST http://127.0.0.1:8001/preguntar \
  -H "Content-Type: application/json" \
  -d '{"texto": "cual es la morosidad promedio del segmento 1?"}'
```

---

## 5. Gestión de servicios

```bash
# Ver estado de todos los servicios
systemctl status nginx seps-django seps-rakkun --no-pager | grep -E "●|Active:"

# Reiniciar servicios
systemctl restart seps-rakkun
systemctl restart seps-django
systemctl reload nginx

# Ver logs de Rakkun en tiempo real
journalctl -u seps-rakkun -f

# Ver últimos errores
journalctl -u seps-rakkun --no-pager -n 30
```

---

## 6. Consultas útiles en PostgreSQL

```bash
# Cooperativas por segmento
PGPASSWORD=seps2024 psql -h localhost -U seps_user -d seps_eeff -c "
SELECT segmento, COUNT(*) as cantidad
FROM dim_cooperativa
GROUP BY segmento ORDER BY segmento;"

# Top 10 CAMEL último corte
PGPASSWORD=seps2024 psql -h localhost -U seps_user -d seps_eeff -c "
SELECT dc.razon_social, dc.segmento, fi.camel_score, fi.rating_camel
FROM fact_indicadores fi
JOIN dim_cooperativa dc ON fi.ruc = dc.ruc
WHERE fi.fecha_corte = (SELECT MAX(fecha_corte) FROM fact_indicadores)
ORDER BY fi.camel_score DESC LIMIT 10;"

# Último corte disponible
PGPASSWORD=seps2024 psql -h localhost -U seps_user -d seps_eeff -c "
SELECT MAX(fecha_corte) FROM fact_indicadores;"
```

---

## 7. Estado final al cierre de sesión

| Componente | Estado |
|---|---|
| Nginx | ✓ Corriendo — proxy reverso |
| Django + Gunicorn | ✓ Corriendo — puerto 8000 |
| FastAPI Rakkun v3 | ✓ Corriendo — datos reales SEPS |
| PostgreSQL | ✓ Con datos migrados |
| OpenRouter API key | ✓ Configurada (key: rakkun-seps) |
| Modelo LLM | DeepSeek V3.2 |

---

## 8. Pendientes próxima sesión

- [ ] Templates Django — 5 secciones del sitio
  - Dashboard general
  - Análisis por cooperativa
  - Ranking CAMEL
  - Comparativo entre segmentos
  - VTuber interactivo (Rakkun)
- [ ] Integrar Live2D Rakkun 2.0 en template VTuber
- [ ] SSL con Let's Encrypt
- [ ] Dominio personalizado (opcional)
