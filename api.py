from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "barberia.db"

app = FastAPI()

# -------------------------------------------------------------------------
# CONFIGURACIÓN DE SEGURIDAD (CORS)
# Permite que un frontend (HTML/JS) que está en otro puerto o dominio 
# pueda hacer peticiones a esta API sin que el navegador lo bloquee.
# -------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------------
# MOLDES DE DATOS (DTOs)
# Pydantic usa estas clases para validar que los datos tengan el formato exacto.
# -------------------------------------------------------------------------

# Molde de SALIDA: Define cómo se envían los datos de los servicios al frontend.
class Servicio(BaseModel):
    id: int
    nombre: str
    duracion_minutos: int
    precio: float

class Barbero(BaseModel):
    id: int
    nombre: str
    telefono: str

# Molde de ENTRADA: Define qué datos debe enviar el frontend para crear una reserva.
# Nota: No incluye id, estado ni fecha_fin porque eso lo gestiona el backend.
class ReservaEntrante(BaseModel):
    cliente_nombre: str
    cliente_telefono: str
    fecha_hora_inicio: str
    barbero_id: int
    servicio_id: int

# -------------------------------------------------------------------------
# ENDPOINTS (RUTAS DE LA API)
# -------------------------------------------------------------------------

# Endpoint GET: Lee el catálogo de servicios de la base de datos y lo devuelve.
@app.get("/servicios", response_model=list[Servicio])
def obtener_servicios():
    conexion = sqlite3.connect(DB_PATH)
    # row_factory permite que los resultados se manejen como diccionarios (con nombres de columnas)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    
    try:
        cursor.execute("SELECT id, nombre, duracion_minutos, precio FROM servicios")
        filas = cursor.fetchall()
    finally:
        # El finally garantiza que la base de datos siempre se cierre, aunque haya errores.
        conexion.close()

    # Transforma las filas crudas de la base de datos en una lista de diccionarios
    return [dict(fila) for fila in filas]

# Endpoint POST: Recibe los datos del cliente y crea una nueva reserva en la base de datos.
@app.post("/reservas")
def crear_reserva(reserva: ReservaEntrante):


    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    
    try:
        cursor.execute("SELECT id FROM barberos WHERE id = ?", (reserva.barbero_id,))
        fila_barbero = cursor.fetchone()
        if fila_barbero is None:
            raise HTTPException(status_code=404, detail="Barbero no encontrado")


        # Aquí guardamos los datos físicamente usando "?" por seguridad (evita inyección SQL).
        cursor.execute("SELECT duracion_minutos FROM servicios WHERE id = ?", (reserva.servicio_id,))
        fila_servicio = cursor.fetchone()
        if fila_servicio is None:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
             
        duracion = fila_servicio["duracion_minutos"]

        fecha_inicio_obj = datetime.strptime(reserva.fecha_hora_inicio, "%Y-%m-%d %H:%M")
        fecha_fin_obj = fecha_inicio_obj + timedelta(minutes=duracion)
        fecha_fin_texto = fecha_fin_obj.strftime("%Y-%m-%d %H:%M")

        cursor.execute("""
        SELECT id FROM reservas
        WHERE barbero_id = ?
            AND fecha_hora_inicio < ?   -- el fin de la nueva reserva
            AND fecha_hora_fin > ?      -- el inicio de la nueva reserva
            AND estado != ?
        """,
        (reserva.barbero_id, fecha_fin_texto, reserva.fecha_hora_inicio, "cancelada"))
        fila_colision= cursor.fetchone()

        if fila_colision is not None:
           raise HTTPException(status_code=409, detail="Servicio ya reservado")

        cursor.execute(
            """
            INSERT INTO reservas (cliente_nombre, cliente_telefono, fecha_hora_inicio, fecha_hora_fin, barbero_id, servicio_id) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                reserva.cliente_nombre, 
                reserva.cliente_telefono, 
                reserva.fecha_hora_inicio, 
                fecha_fin_texto, 
                reserva.barbero_id, 
                reserva.servicio_id
            )
        )
        # commit() es obligatorio en los INSERT/UPDATE/DELETE para aplicar los cambios.
        conexion.commit() 
    finally:
        conexion.close()
        
    return {"mensaje": "Reserva guardada correctamente", "datos": reserva}

@app.get("/barberos", response_model=list[Barbero])
def obtener_barberos():


    conexion = sqlite3.connect(DB_PATH)

    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    try: 
        cursor.execute("SELECT id, nombre, telefono FROM barberos")
        barberos = cursor.fetchall()
    finally:
        conexion.close()

    return [dict(barbero) for barbero in barberos]

@app.get("/reservas")
def obtener_reservas(barbero_id: int | None = None, fecha: str | None = None):
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    try:
        # AQUÍ es donde va todo lo que acabamos de practicar:
        # las dos listas, los dos "if", el .join(), y el armado del sql final
        condiciones = []
        valores =  []
        if barbero_id is not None:
            condiciones.append("barbero_id = ?")
            valores.append(barbero_id)
        if fecha is not None:
            condiciones.append("fecha_hora_inicio LIKE ?")
            valores.append(fecha + "%")
        sql= "SELECT * FROM reservas"

        if condiciones:
            sql += " WHERE " + " AND ". join(condiciones)

        cursor.execute(sql, tuple(valores))
        filas = cursor.fetchall()
    finally:
        conexion.close()

    return [dict(fila) for fila in filas]

@app.patch("/reservas/{reserva_id}/cancelar")
def cancelar_reserva(reserva_id: int):

    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    try: 
        cursor.execute("""
        SELECT id FROM reservas WHERE id = ?""", (reserva_id,))

        fila_reserva = cursor.fetchone()
        if fila_reserva is None:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        else:
            cursor.execute("""
            UPDATE reservas SET estado = ? WHERE id = ?""",("cancelada", reserva_id))
        conexion.commit()
    finally:
        conexion.close()
    return{"mensaje": "Reserva cancelada correctamente"}