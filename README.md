# API de Reservas - Barbería Local
Backend de un sistema de reservas para barbería, construido con FastAPI y SQLite.

## Funcionalidades
- Listado de servicios con precios y duración
- Listado de barberos disponibles
- Creación de reservas con validación automática de horarios
- Cancelación de reservas manteniendo el historial
  
- ## Tecnologías
- Python
- FastAPI
- SQLite

## Cómo ejecutarlo
```bash
pip install fastapi uvicorn
uvicorn api:app --reload
```
La documentación interactiva queda en `http://127.0.0.1:8000/docs`.

## Endpoints
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/servicios` | Lista de servicios con precio y duración |
| GET | `/barberos` | Lista de barberos |
| POST | `/reservas` | Crea una reserva (valida horarios y colisiones) |
| GET | `/reservas` | Lista reservas, filtrable por `barbero_id` y `fecha` |
| PATCH | `/reservas/{id}/cancelar` | Cancela una reserva sin borrarla |

Las fechas usan el formato `YYYY-MM-DD HH:MM`.
