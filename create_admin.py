"""Create (or promote) an admin user: python create_admin.py <name> <email> <password>"""
import sys

import bcrypt

from connection import get_connection

if len(sys.argv) != 4:
    sys.exit(__doc__)

nombre, correo, password = sys.argv[1:]
hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

conn = get_connection()
cur = conn.cursor()
cur.execute(
    "INSERT INTO usuarios (nombre, correo, password, rol, intentos) VALUES (%s, %s, %s, 'admin', 0)",
    (nombre, correo, hashed),
)
conn.commit()
print(f"Admin '{correo}' created.")
