"""Smoke test de plantillas con una base de datos simulada (sin MySQL).

Ejecutar:  python tests/smoke_render.py
Sirve para detectar errores de Jinja / contratos de datos tras cambiar el diseño.
"""
import datetime as dt
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SECRET_KEY", "smoke")

import app as A  # noqa: E402

NOW = dt.datetime(2026, 11, 10, 12, 0, 0)
PROD = lambda i: (i, f"Producto {i}", "Descripción de ejemplo", 19990 + i, 10, "logo.png", 1)
CATS = [(1, "Poleras", "poleras"), (2, "Polerones", "polerones"), (3, "Jeans", "jeans")]


class Cur:
    def __init__(self, dictionary=False):
        self.d = dictionary
        self.rows = []
        self.lastrowid = 1

    def execute(self, sql, params=None):
        q = " ".join(sql.split()).lower()
        self.rows = []
        if "from categorias c left join productos" in q:
            self.rows = [("Poleras", "poleras", 8, "logo.png"), ("Jeans", "jeans", 4, "logo.png"),
                         ("Zapatillas", "zapatillas", 3, "logo.png"), ("Accesorios", "accesorios", 3, "logo.png"),
                         ("Camisas", "camisas", 2, "logo.png"), ("Perfumes", "perfumes", 1, "logo.png")]
        elif q.startswith("select id, nombre, slug from categorias"):
            self.rows = CATS
        elif q.startswith("select id, nombre from categorias where slug"):
            self.rows = [(1, "Poleras")]
        elif q.startswith("select id, nombre from categorias"):
            self.rows = [(1, "Poleras"), (2, "Polerones")]
        elif q.startswith("select * from categorias"):
            self.rows = [{"id": 1, "nombre": "Poleras", "slug": "poleras"}]
        elif "from productos p left join categorias c on p.categoria_id = c.id where p.id" in q:
            self.rows = [(1, "Polera Basic", "Algodón", 12990, 3, "logo.png", "Poleras", "poleras", 1)]
        elif "from productos p left join categorias c on p.categoria_id = c.id" in q and "order by p.id" in q:
            self.rows = [(i, f"Producto {i}", "Desc", 15990, i % 7, "logo.png", "Poleras") for i in range(1, 5)]
        elif "from productos p left join categorias" in q:  # buscar
            self.rows = [(i, f"Producto {i}", 12990, "logo.png", "Poleras") for i in range(1, 5)]
        elif q.startswith("select * from productos") and "where" not in q:
            self.rows = [PROD(i) + (NOW,) for i in range(1, 5)]
        elif "from productos where categoria_id" in q and "id <>" in q:
            self.rows = [(i, f"Rel {i}", 9990, "logo.png") for i in range(2, 5)]
        elif "from productos where stock > 0" in q or "from productos where stock" in q:
            self.rows = [PROD(i) for i in range(1, 9)]
        elif q.startswith("select count(*), coalesce"):
            self.rows = [(4, 120000)]
        elif q.startswith("select count(*)"):
            self.rows = [(5,)]
        elif q.startswith("select id, nombre, correo, rol from usuarios"):
            self.rows = [(1, "Admin", "admin@vestra.example", "admin"), (2, "Camila", "c@demo.cl", "usuario")]
        elif "from carrito_items ci" in q and "join productos p" in q and "for update" not in q:
            self.rows = [(1, "Polera Basic", "logo.png", 2, 12990, 25980)]
        elif "for update" in q:
            self.rows = [(1, "Polera Basic", 2, 12990, 25980, 10)]
        elif "from carrito_items" in q:
            self.rows = [(1, 2)] if "producto_id, cantidad" in q else [(25980,)]
        elif "from favoritos f" in q:
            self.rows = [(1, "Polera Basic", 12990, "logo.png")]
        elif "from favoritos" in q:
            self.rows = [(1,)]
        elif "from ordenes o join usuarios" in q:
            row = (7, 25980, "pendiente", NOW, "Camila", "c@demo.cl")
            self.rows = [{"id": 7, "total": 25980, "estado": "pendiente", "creado_en": NOW, "cliente": "Camila", "correo": "c@demo.cl"}] if self.d else [row]
        elif "from ordenes where id" in q:
            self.rows = [(7,)]
        elif "from ordenes" in q:
            self.rows = [{"id": 7, "total": 25980, "estado": "completada", "creado_en": NOW}] if self.d else [(7, 25980, "completada", NOW)]
        elif "from orden_items" in q:
            self.rows = [{"nombre_producto": "Polera Basic", "cantidad": 2, "precio": 12990, "subtotal": 25980, "id": 1, "producto": "Polera Basic"}]
        elif "from usuarios" in q:
            self.rows = [{"id": 2, "nombre": "Camila", "correo": "c@demo.cl", "rol": "usuario", "fecha_registro": NOW}]
        elif "from productos" in q and "where id" in q:
            self.rows = [{"id": 1, "nombre": "Polera", "descripcion": "d", "precio": 12990, "stock": 5, "imagen": "logo.png", "categoria_id": 1}]

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def close(self):
        pass


class Conn:
    def cursor(self, dictionary=False):
        return Cur(dictionary)

    def commit(self): pass
    def rollback(self): pass
    def close(self): pass


A.get_connection = lambda: Conn()


def login(client, rol="usuario"):
    with client.session_transaction() as s:
        s.update(usuario_id=2, usuario_nombre="Camila", usuario_correo="c@demo.cl", rol=rol, _csrf="tok")


def check(client, path, expect=200, text=None):
    r = client.get(path)
    body = r.get_data(as_text=True)
    ok = r.status_code == expect and (text is None or text in body)
    print(("OK  " if ok else "FAIL"), r.status_code, path)
    if not ok:
        print("     ->", re.sub(r"\s+", " ", body)[:300])
    return ok


def main():
    A.app.config.update(TESTING=False, PROPAGATE_EXCEPTIONS=True)
    results = []
    c = A.app.test_client()
    for p in ["/", "/login", "/registro", "/categorias/poleras", "/categorias/poleras?precio=0-20000&orden=desc",
              "/producto/1", "/buscar?q=pol", "/buscar?q="]:
        results.append(check(c, p))
    results.append(check(c, "/producto/999999", 200))  # fake db siempre devuelve; solo valida render

    login(c)
    for p in ["/carrito", "/checkout", "/favoritos", "/panel", "/perfil", "/historial", "/mis-compras",
              "/editar-correo", "/editar-password", "/orden-confirmada/7"]:
        results.append(check(c, p))

    login(c, "admin")
    for p in ["/admin", "/admin/productos", "/admin/categorias", "/admin/ordenes", "/admin/orden/7",
              "/admin/productos/agregar", "/admin/productos/editar/1", "/admin/categorias/agregar",
              "/admin/categorias/editar/1", "/admin/editar/2"]:
        results.append(check(c, p))

    print(f"\n{sum(results)}/{len(results)} páginas renderizan correctamente")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
