"""Servidor de vista previa SIN base de datos.

Carga el catálogo real desde database/schema.sql en memoria y reemplaza la conexión a MySQL,
para poder ver y fotografiar el diseño sin instalar MariaDB.  Solo lectura (las acciones de
escritura no persisten).

    python tests/demo_server.py          # http://localhost:5056
    /__demo/usuario?next=/carrito        # inicia sesión como cliente de ejemplo
    /__demo/admin?next=/admin            # inicia sesión como administrador
"""
import datetime as dt
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("SECRET_KEY", "demo-preview")

from flask import redirect, request, session  # noqa: E402

import app as A  # noqa: E402

NOW = dt.datetime(2026, 11, 10, 12, 30)
sql = open(os.path.join(ROOT, "database", "schema.sql"), encoding="utf-8").read()

CATS = [(int(a), b, c) for a, b, c in re.findall(r"\((\d+), '([^']*)', '([^']*)'\),?", sql.split("INSERT INTO `categorias`")[1].split(";")[0])]
PRODS = [
    (int(i), n, d, int(p), int(s), img, int(c), NOW)
    for i, n, d, p, s, img, c in re.findall(
        r"\((\d+), '([^']*)', '([^']*)', (\d+), (\d+), '([^']*)', (\d+), '[^']*'\)", sql.split("INSERT INTO `productos`")[1].split(";")[0])
]
CAT_BY_ID = {c[0]: c for c in CATS}
USERS = {1: (1, "Admin", "admin@vestra.example", "admin"), 2: (2, "Camila Rojas", "camila@demo.cl", "usuario")}
CART = [(1, 2), (21, 1), (17, 1)]  # (producto_id, cantidad)
FAVS = [5, 13, 21, 38]
ORDERS = [(12, 69980, "completada", NOW - dt.timedelta(days=9), 2), (13, 34990, "pendiente", NOW - dt.timedelta(days=1), 2),
          (14, 15990, "confirmada", NOW - dt.timedelta(hours=5), 2)]
prod = lambda pid: next(p for p in PRODS if p[0] == pid)


class Cur:
    def __init__(self, dictionary=False):
        self.d, self.rows, self.lastrowid = dictionary, [], 1

    def execute(self, sql, params=None):
        q = " ".join(sql.split()).lower()
        params = params or ()
        R = []
        uid = session.get("usuario_id")
        if "from categorias c left join productos" in q:
            for c in CATS:
                items = [p for p in PRODS if p[6] == c[0]]
                if items:
                    R.append((c[1], c[2], len(items), items[0][5]))
            R = sorted(R, key=lambda r: -r[2])[:6]
        elif q.startswith("select id, nombre, slug from categorias"):
            R = sorted(CATS, key=lambda c: c[1])
        elif q.startswith("select id, nombre from categorias where slug"):
            R = [(c[0], c[1]) for c in CATS if c[2] == params[0]]
        elif q.startswith("select id, nombre from categorias"):
            R = [(c[0], c[1]) for c in CATS]
        elif q.startswith("select * from categorias"):
            R = [{"id": c[0], "nombre": c[1], "slug": c[2]} for c in CATS if c[0] == int(params[0])]
        elif "from productos p left join categorias c on p.categoria_id = c.id where p.id" in q:
            p = prod(int(params[0]))
            c = CAT_BY_ID[p[6]]
            R = [(p[0], p[1], p[2], p[3], p[4], p[5], c[1], c[2], p[6])]
        elif "from productos p left join categorias c on p.categoria_id = c.id" in q and "order by p.id" in q:
            R = [(p[0], p[1], p[2], p[3], p[4], p[5], CAT_BY_ID[p[6]][1]) for p in PRODS]
        elif "from productos p left join categorias" in q:  # buscar
            t = (params[0].strip("%").lower() if params else "")
            R = [(p[0], p[1], p[3], p[5], CAT_BY_ID[p[6]][1]) for p in PRODS
                 if not t or t in p[1].lower() or t in p[2].lower() or t in CAT_BY_ID[p[6]][1].lower()]
        elif "from productos where categoria_id" in q and "id <>" in q:
            R = [(p[0], p[1], p[3], p[5]) for p in PRODS if p[6] == int(params[0]) and p[0] != int(params[1]) and p[4] > 0][:4]
        elif q.startswith("select * from productos where categoria_id"):
            R = [p for p in PRODS if p[6] == int(params[0])]
            if len(params) == 3:
                R = [p for p in R if params[1] <= p[3] <= params[2]]
            R = sorted(R, key=lambda p: p[3], reverse="desc" in q)
        elif "from productos where stock > 0" in q:
            R = [p[:7] for p in sorted(PRODS, key=lambda p: -p[0]) if p[4] > 0][:8]
        elif q.startswith("select count(*), coalesce"):
            R = [(len(ORDERS), sum(o[1] for o in ORDERS))]
        elif q.startswith("select count(*) from productos where stock"):
            R = [(sum(1 for p in PRODS if p[4] <= 3),)]
        elif q.startswith("select count(*) from productos"):
            R = [(len(PRODS),)]
        elif q.startswith("select id, nombre, correo, rol from usuarios"):
            R = list(USERS.values())
        elif "for update" in q:
            R = [(p, p_[1], n, p_[3], n * p_[3], p_[4]) for (p, n) in CART for p_ in [prod(p)]]
        elif "from carrito_items ci" in q and "join productos p" in q:
            R = [(i + 1, prod(p)[1], prod(p)[5], n, prod(p)[3], n * prod(p)[3]) for i, (p, n) in enumerate(CART)]
        elif "coalesce(sum(ci.cantidad * ci.precio_unitario)" in q:
            R = [(sum(n * prod(p)[3] for p, n in CART),)]
        elif "from carrito_items" in q:
            R = [(p, n) for p, n in CART] if uid else []
        elif "from favoritos f" in q:
            R = [(p[0], p[1], p[3], p[5]) for p in PRODS if p[0] in FAVS]
        elif "from favoritos" in q:
            R = [(f,) for f in FAVS] if uid else []
        elif "from ordenes o join usuarios" in q:
            o = ORDERS[0]
            row = {"id": o[0], "total": o[1], "estado": o[2], "creado_en": o[3], "cliente": USERS[2][1], "correo": USERS[2][2]}
            R = [row] if self.d else [(x[0], x[1], x[2], x[3], USERS[2][1], USERS[2][2]) for x in ORDERS]
        elif "from ordenes where id" in q:
            R = [(int(params[0]),)]
        elif "from ordenes" in q:
            R = [{"id": o[0], "total": o[1], "estado": o[2], "creado_en": o[3]} for o in ORDERS] if self.d else [o[:4] for o in ORDERS]
        elif "from orden_items" in q:
            items = [(1, 2), (21, 1)] if int(params[0]) != 13 else [(5, 1)]
            R = [{"id": i, "nombre_producto": prod(p)[1], "producto": prod(p)[1], "cantidad": n, "precio": prod(p)[3], "subtotal": n * prod(p)[3]}
                 for i, (p, n) in enumerate(items, 1)]
        elif "from usuarios" in q:
            u = USERS[uid or 2]
            R = [{"id": u[0], "nombre": u[1], "correo": u[2], "rol": u[3], "fecha_registro": NOW - dt.timedelta(days=120)}]
        elif "from productos" in q and "where id" in q:
            p = prod(int(params[0]))
            R = [{"id": p[0], "nombre": p[1], "descripcion": p[2], "precio": p[3], "stock": p[4], "imagen": p[5], "categoria_id": p[6]}]
        self.rows = R

    def fetchall(self): return self.rows
    def fetchone(self): return self.rows[0] if self.rows else None
    def close(self): pass


class Conn:
    def cursor(self, dictionary=False): return Cur(dictionary)
    def commit(self): pass
    def rollback(self): pass
    def close(self): pass


A.get_connection = lambda: Conn()
A.app.config["TEMPLATES_AUTO_RELOAD"] = True


@A.app.route("/__demo/<quien>")
def demo(quien):
    u = USERS[1 if quien == "admin" else 2]
    session.clear()
    session.update(usuario_id=u[0], usuario_nombre=u[1], usuario_correo=u[2], rol=u[3])
    return redirect(request.args.get("next", "/"))


if __name__ == "__main__":
    print(f"{len(PRODS)} productos · {len(CATS)} categorías cargados desde schema.sql")
    A.app.run(port=int(os.environ.get("PORT", 5056)), threaded=True)
