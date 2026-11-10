import uuid

from conftest import token


def registrar_y_entrar(client, db):
    correo = f"{uuid.uuid4().hex[:8]}@test.example"
    t = token(client, "/registro")
    client.post("/registro", data={"nombre": "Tester", "correo": correo,
                                   "password": "secreto123", "csrf_token": t})
    t = token(client)
    r = client.post("/login", data={"correo": correo, "password": "secreto123", "csrf_token": t})
    assert r.status_code == 302
    return correo


def test_paginas_publicas(client):
    for ruta in ("/", "/login", "/registro", "/categorias/camisas", "/producto/1", "/buscar?q=polera"):
        assert client.get(ruta).status_code == 200, ruta


def test_404_amigable(client):
    r = client.get("/categorias/no-existe")
    assert r.status_code == 404
    assert "Página no encontrada" in r.get_data(as_text=True)


def test_post_sin_csrf_rechazado(client):
    r = client.post("/login", data={"correo": "a@b.cl", "password": "x"})
    assert r.status_code == 400


def test_busqueda_con_comodin_no_devuelve_todo(client):
    todo = client.get("/buscar?q=").get_data(as_text=True)
    comodin = client.get("/buscar?q=%25").get_data(as_text=True)
    assert len(comodin) < len(todo)


def test_admin_protegido(client, db):
    assert client.get("/admin").status_code == 403
    registrar_y_entrar(client, db)
    assert client.get("/admin").status_code == 403
    assert client.get("/admin/productos").status_code == 403


def test_borrado_no_acepta_get(client):
    assert client.get("/admin/eliminar/1").status_code == 405
    assert client.get("/admin/productos/eliminar/1").status_code == 405
    assert client.get("/admin/ordenes/eliminar/1").status_code == 405


def test_cambio_de_password_usa_bcrypt(client, db):
    correo = registrar_y_entrar(client, db)
    t = token(client, "/editar-password")
    client.post("/editar-password", data={"password_actual": "secreto123",
                                          "nueva_password": "otraclave1",
                                          "confirmar_password": "otraclave1", "csrf_token": t})
    client.get("/logout")
    t = token(client)
    r = client.post("/login", data={"correo": correo, "password": "otraclave1", "csrf_token": t})
    assert r.status_code == 302 and r.headers["Location"].endswith("/panel")


def test_compra_descuenta_stock_y_vacia_carrito(client, db):
    registrar_y_entrar(client, db)
    cur = db.cursor()
    cur.execute("SELECT id, stock FROM productos WHERE stock > 1 LIMIT 1")
    pid, stock = cur.fetchone()

    t = token(client, f"/producto/{pid}")
    client.post(f"/carrito/agregar/{pid}", data={"csrf_token": t})
    t = token(client, "/checkout")
    r = client.post("/checkout", data={"csrf_token": t})
    assert r.status_code == 302 and "orden-confirmada" in r.headers["Location"]

    db.commit()
    cur.execute("SELECT stock FROM productos WHERE id = %s", (pid,))
    assert cur.fetchone()[0] == stock - 1
    assert client.get("/carrito").get_data(as_text=True).count("Eliminar") == 0


def test_compra_sin_stock_suficiente(client, db):
    registrar_y_entrar(client, db)
    cur = db.cursor()
    cur.execute("SELECT id FROM productos LIMIT 1")
    pid = cur.fetchone()[0]
    t = token(client, f"/producto/{pid}")
    client.post(f"/carrito/agregar/{pid}", data={"csrf_token": t})
    cur.execute("UPDATE productos SET stock = 0 WHERE id = %s", (pid,))
    db.commit()
    t = token(client, "/checkout")
    r = client.post("/checkout", data={"csrf_token": t})
    assert r.status_code == 302 and r.headers["Location"].endswith("/carrito")
