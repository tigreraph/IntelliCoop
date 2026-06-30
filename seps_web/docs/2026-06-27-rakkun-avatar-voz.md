# IntelliCoop — Rakkun Avatar con Voz

**Fecha:** 2026-06-27  
**Sesión:** Implementación de Rakkun Avatar (Live2D) + Entrada/Salida por voz

---

## Resumen

Se implementó la página `/rakkun-avatar/` como segunda opción de interacción con Rakkun, separada del chat de texto puro `/rakkun/`. El usuario tiene ahora dos opciones en el sidebar bajo "Asistente IA".

---

## Archivos creados / modificados

| Archivo | Cambio |
|---|---|
| `templates/rakkun_avatar.html` | Nuevo template: canvas Live2D + chat + voz |
| `static/live2d/rakkun/` | 54 archivos del modelo Rakkun 2.0 Live2D |
| `core/views.py` | Nueva vista `rakkun_avatar()` |
| `seps_project/urls.py` | Nueva ruta `/rakkun-avatar/` |
| `seps_project/settings.py` | `STATICFILES_DIRS`, `python-dotenv` |
| `templates/base.html` | Sidebar actualizado: 2 entradas Rakkun |
| `start_local.ps1` | Script arranque local (doble clic) |
| `requirements.txt` | Añadido `python-dotenv>=1.0` |

---

## Modelo Live2D

- **Fuente:** `Modelo Avatar/Rakkun2.0 Live2D model/rakkun/`
- **Destino static:** `static/live2d/rakkun/`
- **Formato:** Cubism 4 (`.moc3`, `.model3.json`, `.physics3.json`)
- **Texturas:** 11 archivos 4096×4096px en `rakkun.4096/`
- **Motions:** `idle`, `dance`, `karaoke`, `pentab`
- **Expresiones:** 32 expresiones (`.exp3.json`)

### Librerías CDN (orden crítico)
```html
<script src="https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/pixi.js@7/dist/pixi.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/pixi-live2d-display@0.4.0/dist/cubism4.min.js"></script>
```

### Posicionamiento del avatar (upper body)
```javascript
function positionModel(model, W, H) {
  const origW = model.internalModel.originalWidth;
  const origH = model.internalModel.originalHeight;
  const scale = (W / origW) * 1.55;   // zoom para ver torso+cabeza
  model.scale.set(scale);
  model.x = (W - origW * scale) / 2;  // centrado horizontal exacto
  model.y = H - origH * scale * 0.50; // 50% = mitad del cuerpo hacia arriba, cabeza completa visible
}
```

**Nota de ajuste:** el factor `0.50` fue calibrado para mostrar la mitad superior del modelo con la cabeza completa dentro del canvas. Valores más altos (0.57) cortaban la cabeza en el borde superior.

---

## Funcionalidades implementadas

### 1. Avatar Live2D interactivo
- Seguimiento ocular del cursor del mouse (`model.focus(x, y)`)
- Motion idle automático al cargar
- Expresiones automáticas según el contexto de la respuesta:
  - `confused` → mientras piensa
  - `excited` → respuesta positiva ("excelente", "mejor")
  - `nervous` → respuesta de riesgo ("crítico", "riesgo")
  - `sad` → error o problema
  - `sing` → mientras habla con TTS
  - `heh` → estado neutro/ok
- Botones de expresión manual: Excited, Shy, Angry, Sad, Heh
- Badge de estado: Cargando / Rakkun lista / Error
- Badge "Hablando..." mientras el TTS está activo
- Fallback emoji 🦝 si Live2D no carga

### 2. Entrada por micrófono
- `window.SpeechRecognition` / `window.webkitSpeechRecognition`
- Idioma: `es-EC` (español Ecuador)
- Botón con feedback visual (rojo pulsante mientras escucha)
- Al reconocer texto: pone el texto en el input y envía automáticamente (200ms delay)
- Expresión "excited" de Rakkun mientras escucha
- **Compatibilidad:** Chrome y Edge únicamente (Firefox no soporta SpeechRecognition)

### 3. Respuesta por voz (TTS)
- `window.SpeechSynthesis`
- Idioma: `es-ES`, pitch: 1.15, rate: 1.05, volume: 0.9
- Texto dividido en fragmentos ≤180 chars para evitar cortes del engine
- Expresión `sing` mientras habla, `heh` al terminar
- Botón topbar "Voz activa / Voz silenciada" para alternar
- `speechSynthesis.cancel()` al limpiar chat o iniciar micrófono

---

## Arranque local

**Dos servicios requeridos:**

| Servicio | Puerto | Comando |
|---|---|---|
| Django (web) | 8000 | `py manage.py runserver 8000` |
| Rakkun FastAPI | 8001 | `py -m uvicorn rakkun_api:app --port 8001 --host 127.0.0.1` |

**Script automatizado:** `start_local.ps1` — doble clic levanta ambos + abre browser.

**Variables de entorno requeridas (`.env`):**
```
OPENROUTER_KEY=sk-or-v1-...
DB_HOST=localhost
DB_PORT=5434
DB_USER=postgres
DB_PASS=seps2024
RAKKUN_API_URL=http://localhost:8001/preguntar
```

El archivo `.env` se carga automáticamente gracias a `python-dotenv` en `settings.py`.

---

## Sidebar — dos opciones de Rakkun

```html
<a href="/rakkun/"        ...>Chat Rakkun    [badge: AI]</a>
<a href="/rakkun-avatar/" ...>Rakkun Avatar  [badge: VTuber]</a>
```

---

## Pendientes / mejoras futuras

- [ ] Lip sync real con la voz TTS (requiere Web Audio API + parámetros Live2D)
- [ ] Selección de voz TTS (preferir voz femenina en español si está disponible)
- [ ] Animación de hablar más fluida (actualmente usa expresión `sing` estática)
- [ ] Deploy en VPS del modelo Live2D (copiar `static/live2d/` al servidor)
