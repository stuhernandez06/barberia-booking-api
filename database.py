import sqlite3

DB_PATH = "barberia.db"

def crear_tablas():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor =  conn.cursor()

    # 2. Creación de la tabla Barberos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS barberos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono TEXT NOT NULL
    )
    """)

    # 3. Creación de la tabla Servicios
    # Nota: 'precio' usa el tipo REAL porque permite guardar números con decimales.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS servicios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        duracion_minutos INTEGER NOT NULL CHECK(duracion_minutos > 0),
        precio REAL NOT NULL CHECK (precio >= 0)
    )
    """)

   # 4. Creación de la tabla Reservas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_nombre TEXT NOT NULL,
        cliente_telefono TEXT NOT NULL,
        fecha_hora_inicio TEXT NOT NULL,
        fecha_hora_fin TEXT NOT NULL,
        estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'confirmada', 'cancelada', 'completada')),
        barbero_id INTEGER NOT NULL,
        servicio_id INTEGER NOT NULL,
        FOREIGN KEY (barbero_id) REFERENCES barberos (id) ON DELETE RESTRICT,
        FOREIGN KEY (servicio_id) REFERENCES servicios (id) ON DELETE RESTRICT,
        CHECK (fecha_hora_fin > fecha_hora_inicio)
    )
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_reservas_barbero_fecha
        ON reservas (barbero_id, fecha_hora_inicio)
    """)
    conn.commit()
    conn.close()
    print("base de datos creada")

if __name__ == "__main__":
    crear_tablas()