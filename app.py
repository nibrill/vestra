import hmac
import os
import secrets
import uuid
from datetime import timedelta

import bcrypt
import bleach
from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)
from werkzeug.utils import secure_filename

from connection import get_connection

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32)
app.permanent_session_lifetime = timedelta(days=7)
app.config.update(
    UPLOAD_FOLDER=os.path.join(app.root_path, "static", "img"),
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5 MB por subida
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1",
)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
ESTADOS_ORDEN = {"pendiente", "confirmada", "completada", "cancelada"}
ROLES = {"usuario", "admin"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file_storage):
    """Guarda una imagen con nombre unico y devuelve el nombre, o None si es invalida."""
    if not file_storage or not file_storage.filename or not allowed_file(file_storage.filename):
        return None
    name = f"{uuid.uuid4().hex[:12]}_{secure_filename(file_storage.filename)}"
    file_storage.save(os.path.join(app.config["UPLOAD_FOLDER"], name))
    return name


# ---- CSRF, cabeceras y utilidades --------------------------------------
def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


@app.before_request
def verificar_csrf():
    if request.method == "POST":
        enviado = request.form.get("csrf_token", "")
        esperado = session.get("_csrf", "")
        if not esperado or not hmac.compare_digest(enviado, esperado):
            abort(400, "Token CSRF inválido o expirado. Recarga la página e inténtalo de nuevo.")


@app.after_request
def cabeceras_seguridad(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return resp


@app.template_filter("clp")
def formato_clp(valor):
    """12990 -> $12.990 (formato chileno)."""
    try:
        return "$" + f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return valor


def requiere_admin():
    if session.get("rol") != "admin":
        abort(403)


@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(413)
def error_pagina(e):
    textos = {
        400: ("Solicitud inválida", getattr(e, "description", "")),
        403: ("Acceso denegado", "No tienes permisos para ver esta página."),
        404: ("Página no encontrada", "No pudimos encontrar lo que buscas."),
        413: ("Archivo demasiado grande", "El límite es de 5 MB."),
    }
    titulo, detalle = textos.get(e.code, ("Error", ""))
    return render_template("error.html", codigo=e.code, titulo=titulo, detalle=detalle), e.code

def correo_valido(correo):
    return "@" in correo and "." in correo

def password_valida(password):
    return len(password) >= 6

@app.route("/")
def home():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""SELECT id, nombre, descripcion, precio, stock, imagen, categoria_id
                      FROM productos WHERE stock > 0
                      ORDER BY fecha_creacion DESC, id DESC LIMIT 8""")
    productos = cursor.fetchall()
    cursor.execute("""SELECT c.nombre, c.slug, COUNT(p.id) AS n,
                             (SELECT imagen FROM productos WHERE categoria_id = c.id ORDER BY id LIMIT 1)
                      FROM categorias c LEFT JOIN productos p ON p.categoria_id = c.id
                      GROUP BY c.id, c.nombre, c.slug
                      HAVING n > 0
                      ORDER BY n DESC, c.nombre LIMIT 6""")
    cats_home = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) FROM productos")
    total_productos = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return render_template("index.html", productos=productos, cats_home=cats_home,
                           total_productos=total_productos)



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":  
        correo = bleach.clean(request.form["correo"])  # Sanitizar correo
        password = bleach.clean(request.form["password"])  # Sanitizar contraseña

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT * FROM usuarios WHERE correo = %s"
        cursor.execute(sql, (correo,))
        usuario = cursor.fetchone()

        
        if not usuario:
           flash(bleach.clean("Error: usuario no encontrado"), "error")  # Sanitizar mensaje flash
           return redirect("/login")
        # Validar intentos bloqueados
        if usuario["intentos"] >= 3:
            flash(bleach.clean("Cuenta bloqueada por múltiples intentos"), "error")
            return redirect("/login")
        
        password_correcta = bcrypt.checkpw(password.encode('utf-8'), usuario["password"].encode('utf-8'))

        # Validar contraseña correcta
        if not password_correcta:
            nuevo_intento = usuario["intentos"] + 1
            sql_update = "UPDATE usuarios SET intentos = %s WHERE correo = %s"
            cursor.execute(sql_update, (nuevo_intento, correo))
            conn.commit()
            flash(bleach.clean(f"Contraseña incorrecta. Intento {nuevo_intento}/3"), "error")
            return redirect("/login")

        # Resetear intentos si inicia sesión bien
        sql_reset = "UPDATE usuarios SET intentos = 0 WHERE correo = %s"
        cursor.execute(sql_reset, (correo,))
        conn.commit()

        session.clear()  # evita fijacion de sesion
        session["usuario_id"] = usuario["id"]
        session["usuario_nombre"] = usuario["nombre"]
        session["usuario_correo"] = usuario["correo"]
        session["rol"] = usuario['rol']
        # 🔥 Esto mantiene la sesión activa por días
        session.permanent = True

        flash(f"Hola {usuario['nombre']}", "success")
        return redirect("/panel")

    return render_template("login.html")

   



@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        # Sanitizar los datos de entrada (nombre, correo)
        nombre = bleach.clean(request.form.get("nombre"))  # Sanitizar nombre
        correo = bleach.clean(request.form.get("correo"))  # Sanitizar correo
        password = request.form.get("password")

        # Validaciones básicas
        if not nombre or not correo or not password:
            flash("Todos los campos son obligatorios.", "error")
            return redirect("/registro")

        if not correo_valido(correo):
            flash("El correo ingresado no es válido.", "error")
            return redirect("/registro")

        if not password_valida(password):
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            return redirect("/registro")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Revisar si el correo ya existe
        cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
        existe = cursor.fetchone()

        if existe:
            flash("El correo ya está registrado. Intenta iniciar sesión.", "error")
            conn.close()
            return redirect("/registro")

        # HASH de contraseña con bcrypt
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        query = """
            INSERT INTO usuarios (nombre, correo, password, intentos)
            VALUES (%s, %s, %s, 0)
        """
        cursor.execute(query, (nombre, correo, hashed_password))
        conn.commit()

        cursor.close()
        conn.close()

        flash("Usuario registrado correctamente. Ahora puedes iniciar sesión.", "success")
        return redirect("/login")

    # Método GET → mostrar el formulario
    return render_template("formulario.html")



@app.route("/panel")
def panel():
    usuario = {
        "nombre": "ejemplo",
        "correo": "example@gmail.com",
        "fecha_registro": "2025-01-12"
    
    }
    if "usuario_id" not in session:
        return redirect("/login")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    sql = "SELECT id, nombre, correo, fecha_registro  FROM usuarios WHERE id = %s"
    cursor.execute(sql,(session["usuario_id"],))
    usuario = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("panel.html", usuario=usuario )

@app.route("/editar-correo", methods=["GET", "POST"])
def editar_correo():
    if "usuario_id" not in session:
        return redirect("/login")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, nombre, correo FROM usuarios WHERE id = %s", (session["usuario_id"],))
    usuario = cursor.fetchone()

    if request.method =="POST":
        nuevo_correo = bleach.clean(request.form.get("nuevo_correo", "")).strip()

        if not correo_valido(nuevo_correo):
            flash("El correo ingresado no es válido.", "error")
            return redirect("/editar-correo")
        
        cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (nuevo_correo,))
        
        if cursor.fetchone():
            flash("Ese correo ya esta registrado", "error")
            return redirect("/editar-correo")
        
        cursor.execute("UPDATE usuarios SET correo = %s WHERE id = %s", (nuevo_correo, session["usuario_id"]))
        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/panel")
    
    cursor.close()
    conn.close()
    return render_template("editar-correo.html", usuario=usuario)

@app.route("/carrito")
def ver_carrito():
    if "usuario_id" not in session:
        return redirect("/login")
    
    usuario_id = session["usuario_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ci.id, p.nombre, p.imagen, ci.cantidad, ci.precio_unitario,
               (ci.cantidad * ci.precio_unitario) AS subtotal
        FROM carrito_items ci
        JOIN productos p ON ci.producto_id = p.id
        WHERE ci.usuario_id = %s
    """, (usuario_id,))
    items = cursor.fetchall()

    cursor.execute("""
        SELECT COALESCE(SUM(ci.cantidad * ci.precio_unitario), 0)
        FROM carrito_items ci
        WHERE ci.usuario_id = %s
    """, (usuario_id,))
    total = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template("carrito.html", items=items, total=total)



@app.route("/editar-password", methods=["GET", "POST"])
def editar_password():
    if "usuario_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        password_actual = request.form.get("password_actual")
        nueva_password = request.form.get("nueva_password")
        confirmar_password = request.form.get("confirmar_password")

        if len(nueva_password) < 6:
            flash("La nueva contraseña debe tener al menos 6 caracteres", "error")
            return redirect("/editar-password")

        if nueva_password != confirmar_password:
            flash("Las contraseñas nuevas no coinciden", "error")
            return redirect("/editar-password")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Obtener contraseña actual
        cursor.execute("SELECT password FROM usuarios WHERE id = %s",
                       (session["usuario_id"],))
        usuario = cursor.fetchone()

        if not usuario:
             flash("usuario no encontrado", "error")
             return  redirect("/editar-password")

           

        if not bcrypt.checkpw(password_actual.encode("utf-8"), usuario["password"].encode("utf-8")):
             flash( "La contraseña actual es incorrecta", "error")
             return  redirect("/editar-password")
           

        # Actualizar contraseña
        cursor.execute(
            "UPDATE usuarios SET password = %s WHERE id = %s",
            (bcrypt.hashpw(nueva_password.encode("utf-8"), bcrypt.gensalt()), session["usuario_id"])
        )
        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/panel")

    return render_template("editar-password.html")

@app.route("/logout")
def logout():
    session.clear()     # elimina todos los datos del usuario
    flash("sesion cerrada correctamente", "success")
    return redirect("/login")

@app.route("/admin")
def admin_panel():
    requiere_admin()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, correo, rol FROM usuarios ORDER BY id")
    usuarios = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) FROM productos")
    n_productos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(CASE WHEN estado <> 'cancelada' THEN total END), 0) FROM ordenes")
    n_ordenes, ingresos = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM productos WHERE stock <= 3")
    stock_bajo = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    stats = {"usuarios": len(usuarios), "productos": n_productos, "ordenes": n_ordenes,
             "ingresos": int(ingresos), "stock_bajo": stock_bajo}
    return render_template("admin.html", usuarios=usuarios, stats=stats)
      

@app.route("/admin/editar/<id>", methods=["GET","POST"])
def editar_usuario(id):

    requiere_admin()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "GET":
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
        usuario = cursor.fetchone()
        return render_template("editar_admin.html", usuario=usuario)

    # POST
    nombre = bleach.clean(request.form["nombre"])  # Sanitizar nombre
    correo = bleach.clean(request.form["correo"])  # Sanitizar correo
    rol = request.form["rol"]
    if rol not in ROLES:
        abort(400, "Rol inválido.")


    cursor.execute("""
        UPDATE usuarios 
        SET nombre=%s, correo=%s, rol=%s
        WHERE id=%s
    """, (nombre, correo, rol, id))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Usuario actualizado correctamente", "success")
    return redirect("/admin")



@app.route("/admin/productos/eliminar/<int:id>", methods=["POST"])
def admin_eliminar_produto(id):

    requiere_admin()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM productos WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Producto eliminado correctamente", "success")
    return redirect("/admin/productos")

@app.route("/admin/eliminar/<int:id>", methods=["POST"])
def admin_eliminar(id):

    requiere_admin()

    # Evitar que el admin se auto borre
    if str(session.get("usuario_id")) == str(id):
        flash("No puedes eliminar tu propia cuenta", "error")
        return redirect("/admin")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM usuarios WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Usuario eliminado correctamente", "success")
    return redirect("/admin")


@app.route("/admin/productos", methods=["GET","POST"])
def admin_producto():

    requiere_admin()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""SELECT p.id, p.nombre, p.descripcion, p.precio, p.stock, p.imagen, c.nombre
                      FROM productos p LEFT JOIN categorias c ON p.categoria_id = c.id
                      ORDER BY p.id""")
    productos = cursor.fetchall()

        
    cursor.close()
    conn.close()

    return render_template("admin-productos.html", productos=productos)



@app.route("/admin/productos/editar/<id>", methods=["GET","POST"])
def admin_editar_producto(id):

    requiere_admin()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # --- GET → mostrar formulario ---
    if request.method == "GET":
        cursor.execute("SELECT * FROM productos WHERE id = %s", (id,))
        producto = cursor.fetchone()
        cursor.close()
        conn.close()
        return render_template("editar_producto.html", producto=producto)

    # --- POST → actualizar producto ---
    nombre = request.form.get("nombre")
    descripcion = request.form.get("descripcion")
    precio = request.form.get("precio")
    stock = request.form.get("stock")
    categoria_id = request.form.get("categoria_id")

    # La imagen no viene como texto, sino como archivo:
    imagen_file = request.files.get("imagen")

    if imagen_file and imagen_file.filename != "":
        filename = save_upload(imagen_file)
        if not filename:
            flash("Tipo de archivo no permitido (usa png, jpg, gif o webp).", "error")
            cursor.close()
            conn.close()
            return redirect(request.url)
    else:
        # si no cambia la imagen tomamos la existente
        cursor.execute("SELECT imagen FROM productos WHERE id = %s", (id,))
        filename = cursor.fetchone()["imagen"]

    cursor.execute("""
        UPDATE productos 
        SET nombre=%s, descripcion=%s, precio=%s, stock=%s, imagen=%s, categoria_id=%s
        WHERE id=%s
    """, (nombre, descripcion, precio, stock, filename, categoria_id, id))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Producto actualizado correctamente", "success")
    return redirect("/admin/productos")
     
@app.route("/admin/categorias", methods=["GET","POST"])
def admin_categoria():

    requiere_admin()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id,nombre FROM categorias")
    categorias = cursor.fetchall()
        
    cursor.close()
    conn.close()

    return render_template("admin-categorias.html", categorias=categorias)

@app.route("/admin/categorias/editar/<id>", methods=["GET","POST"])
def editar_categoria(id):

    requiere_admin()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "GET":
        cursor.execute("SELECT * FROM categorias WHERE id = %s", (id,))
        categoria = cursor.fetchone()
        return render_template("editar_categoria.html", categoria=categoria)
    

    # POST
    nombre = request.form["nombre"]  
    cursor.execute("""
        UPDATE categorias 
        SET nombre=%s
        WHERE id=%s
    """, (nombre, id))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Categoria actualizada correctamente", "success")
    return redirect("/admin/categorias")
@app.route("/buscar")
def buscar():
    termino = request.args.get("q", "").strip()

    conn = get_connection()
    cursor = conn.cursor()

    # Si no se escribió nada → mostrar todos los productos
    if termino == "":
        cursor.execute("""
            SELECT p.id, p.nombre, p.precio, p.imagen,
                   c.nombre AS categoria
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
        """)

    else:
        escapado = termino.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        patron = f"%{escapado}%"
        cursor.execute("""
            SELECT p.id, p.nombre, p.precio, p.imagen,
                   c.nombre AS categoria
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.nombre LIKE %s
               OR p.descripcion LIKE %s
               OR c.nombre LIKE %s
        """, (patron, patron, patron))

    productos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("resultados.html",
                           productos=productos,
                           termino=termino)


@app.route("/admin/productos/agregar", methods=["GET","POST"])
def admin_producto_agregar():

    requiere_admin()

    if request.method == "POST":
        nombre = request.form["nombre"]
        precio = request.form["precio"]
        stock = request.form["stock"]
        descripcion = request.form["descripcion"]
        categoria_id = request.form["categoria_id"]

        if not nombre or not precio or not stock or not descripcion or not categoria_id:
            flash("Todos los campos son obligatorios", "error")
            return redirect(request.url)
        
        if "imagen" not in request.files:
            flash("No se seleciono ninguna imagen", "error")
            return redirect(request.url)
        
        imagen = request.files["imagen"]
        if imagen.filename == "":
            flash("No se seleccionó ninguna imagen", "error")
            return redirect(request.url)
        
        filename = save_upload(imagen)
        if not filename:
            flash("Tipo de archivo no permitido (usa png, jpg, gif o webp).", "error")
            return redirect(request.url)
        
        conn = get_connection()
        cursor = conn.cursor()
        sql = """INSERT INTO productos (nombre, precio, stock, descripcion, categoria_id, imagen)
                  VALUES   (%s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (nombre, precio, stock, descripcion, categoria_id, filename))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Producto agregado exitosamente" , "success")
        return redirect("/admin/productos")
    
    return render_template("agregar_producto.html")
    

@app.route("/carrito/agregar/<int:producto_id>", methods=["POST"])
def agregar_carrito(producto_id):
    if "usuario_id" not in session:
        return redirect("/login")

    usuario_id = session["usuario_id"]

    conn = get_connection()
    cursor = conn.cursor()

    # Obtener precio del producto
    cursor.execute("SELECT precio FROM productos WHERE id = %s", (producto_id,))
    row = cursor.fetchone()

    if not row:
        flash("El producto no existe.", "error")
        cursor.close()
        conn.close()
        return redirect(request.referrer or "/")

    precio_producto = row[0]

    # Buscar si el producto ya está en el carrito
    cursor.execute("""
        SELECT id, cantidad 
        FROM carrito_items
        WHERE usuario_id = %s AND producto_id = %s
    """, (usuario_id, producto_id))
    
    item = cursor.fetchone()

    if item:
        # Ya existe → subir cantidad
        item_id = item[0]
        nueva_cantidad = item[1] + 1

        cursor.execute("""
            UPDATE carrito_items
            SET cantidad = %s
            WHERE id = %s
        """, (nueva_cantidad, item_id))

    else:
        # No existe → insert nuevo
        cursor.execute("""
            INSERT INTO carrito_items (usuario_id, producto_id, cantidad, precio_unitario)
            VALUES (%s, %s, %s, %s)
        """, (usuario_id, producto_id, 1, precio_producto))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Producto agregado al carrito.", "success")
    return redirect(request.referrer or "/")

@app.route("/carrito/cantidad/<int:item_id>", methods=["POST"])
def cambiar_cantidad(item_id):
    if "usuario_id" not in session:
        return redirect("/login")

    delta = 1 if request.form.get("delta") == "1" else -1
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""SELECT ci.cantidad, p.stock FROM carrito_items ci
                      JOIN productos p ON p.id = ci.producto_id
                      WHERE ci.id = %s AND ci.usuario_id = %s""", (item_id, session["usuario_id"]))
    fila = cursor.fetchone()
    if fila:
        nueva = fila[0] + delta
        if nueva < 1:
            cursor.execute("DELETE FROM carrito_items WHERE id = %s AND usuario_id = %s",
                           (item_id, session["usuario_id"]))
        elif nueva > fila[1]:
            flash(f"Solo quedan {fila[1]} unidades disponibles.", "warning")
        else:
            cursor.execute("UPDATE carrito_items SET cantidad = %s WHERE id = %s AND usuario_id = %s",
                           (nueva, item_id, session["usuario_id"]))
        conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("ver_carrito"))


@app.route("/carrito/eliminar/<int:item_id>", methods=["POST"])
def eliminar_item_carrito(item_id):
    if "usuario_id" not in session:
        return redirect("/login")

    usuario_id = session["usuario_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM carrito_items
        WHERE id = %s AND usuario_id = %s
    """, (item_id, usuario_id))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Producto eliminado del carrito.", "info")
    return redirect(url_for("ver_carrito"))

@app.route("/favoritos/toggle/<int:producto_id>", methods=["POST"])
def toggle_favorito(producto_id):

    if "usuario_id" not in session:
        return redirect("/login")

    usuario_id = session["usuario_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""SELECT id FROM favoritos WHERE usuario_id = %s AND producto_id = %s
                    """,(usuario_id, producto_id))
    existe = cursor.fetchone()

    if existe: 
        cursor.execute("""DELETE FROM favoritos
                       WHERE usuario_id = %s AND producto_id = %s
                       """,(usuario_id, producto_id))
        flash("Producto eliminado de favoritos.", "success")
    else:
        cursor.execute("""INSERT INTO favoritos (usuario_id, producto_id)
                       VALUES (%s, %s)""", (usuario_id, producto_id))
        flash("Producto agregado a favoritos", "success")
    
    conn.commit()
    cursor.close()
    conn.close()

    

    return redirect(request.referrer or url_for("productos"))

@app.route("/favoritos")
def ver_favoritos():
    if "usuario_id" not in session:
        return redirect("/login")
    
    usuario_id = session["usuario_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.id, p.nombre, p.precio, p.imagen
        FROM favoritos f
        JOIN productos p ON f.producto_id = p.id
        WHERE f.usuario_id = %s
    """, (usuario_id,))
    favoritos = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("favoritos.html", productos=favoritos)



@app.route("/producto/<int:producto_id>")
def producto_detalle(producto_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""SELECT p.id, p.nombre, p.descripcion, p.precio, p.stock, p.imagen,
                             c.nombre AS categoria, c.slug, p.categoria_id
                      FROM productos p
                      LEFT JOIN categorias c ON p.categoria_id = c.id
                      WHERE p.id = %s""", (producto_id,))
    producto = cursor.fetchone()
    if not producto:
        cursor.close()
        conn.close()
        abort(404)

    cursor.execute("""SELECT id, nombre, precio, imagen FROM productos
                      WHERE categoria_id = %s AND id <> %s AND stock > 0
                      ORDER BY id LIMIT 4""", (producto[8], producto_id))
    relacionados = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("producto_detalle.html", producto=producto, relacionados=relacionados)


@app.route("/perfil" , methods=["GET","POST"])
def perfil():
    if "usuario_id" not in session:
        return redirect("/login")
    
    usuario_id = session["usuario_id"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""SELECT id, nombre, correo, rol, fecha_registro
                   FROM usuarios
                   WHERE id = %s """, (usuario_id,))
    
    usuario= cursor.fetchone()

    cursor.execute(""" SELECT id, total, estado, creado_en
                   FROM ordenes 
                   WHERE usuario_id = %s
                   ORDER BY creado_en DESC""", (usuario_id,))
    ordenes = cursor.fetchall()

    compras= {}
    for orden in ordenes:
        cursor.execute("""SELECT nombre_producto, cantidad, precio, subtotal
                       FROM orden_items 
                       WHERE orden_id = %s""" , (orden["id"], ))
        compras[orden["id"]] = cursor.fetchall()
    

    cursor.close()
    conn.close()
    
    return render_template("perfil.html", usuario=usuario, ordenes=ordenes, compras=compras)

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "usuario_id" not in session:
        return redirect("/login")

    usuario_id = session["usuario_id"]
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # FOR UPDATE bloquea los productos para que dos compras no vendan el mismo stock
        cursor.execute("""SELECT ci.producto_id, p.nombre, ci.cantidad, p.precio,
                                 (ci.cantidad * p.precio) AS subtotal, p.stock
                          FROM carrito_items ci
                          JOIN productos p ON ci.producto_id = p.id
                          WHERE ci.usuario_id = %s
                          FOR UPDATE""", (usuario_id,))
        items = cursor.fetchall()

        if not items:
            conn.rollback()
            flash("Tu carrito está vacío.", "warning")
            return redirect(url_for("ver_carrito"))

        total = sum(item[4] for item in items)

        if request.method == "POST":
            for item in items:
                if item[2] > item[5]:
                    conn.rollback()
                    flash(f"Stock insuficiente para {item[1]} (quedan {item[5]}).", "error")
                    return redirect(url_for("ver_carrito"))

            cursor.execute("INSERT INTO ordenes (usuario_id, total) VALUES (%s, %s)",
                           (usuario_id, total))
            orden_id = cursor.lastrowid
            for item in items:
                cursor.execute("""INSERT INTO orden_items
                                  (orden_id, producto_id, nombre_producto, precio, cantidad, subtotal)
                                  VALUES (%s, %s, %s, %s, %s, %s)""",
                               (orden_id, item[0], item[1], item[3], item[2], item[4]))
                cursor.execute("UPDATE productos SET stock = stock - %s WHERE id = %s",
                               (item[2], item[0]))
            cursor.execute("DELETE FROM carrito_items WHERE usuario_id = %s", (usuario_id,))
            conn.commit()

            flash("Compra realizada con éxito", "success")
            return redirect(url_for("orden_confirmada", orden_id=orden_id))

        conn.rollback()
        items_vista = [i[:5] for i in items]
        return render_template("checkout.html", items=items_vista, total=total)
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


@app.route("/orden-confirmada/<int:orden_id>")
def orden_confirmada(orden_id):
    if "usuario_id" not in session:
        return redirect("/login")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM ordenes WHERE id = %s AND usuario_id = %s",
                   (orden_id, session["usuario_id"]))
    existe = cursor.fetchone()
    cursor.close()
    conn.close()
    if not existe:
        abort(404)
    return render_template("orden_confirmada.html", orden_id=orden_id)

@app.route("/mis-compras")
def mis_compras():
    if "usuario_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""SELECT id, total, estado, creado_en
                   FROM ordenes
                   WHERE usuario_id = %s
                   ORDER BY creado_en DESC""", (session["usuario_id"],))
    ordenes = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("mis_compras.html", ordenes=ordenes)


@app.route("/historial")
def historial():
    if "usuario_id" not in session:
        return redirect("/login")

    usuario_id = session["usuario_id"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # ÓRDENES DEL USUARIO
    cursor.execute("""
        SELECT id, total, estado, creado_en
        FROM ordenes
        WHERE usuario_id = %s
        ORDER BY creado_en DESC
    """, (usuario_id,))
    ordenes = cursor.fetchall()

    # ITEMS POR ORDEN
    compras = {}
    for orden in ordenes:
        cursor.execute("""
            SELECT nombre_producto, cantidad, precio, subtotal
            FROM orden_items
            WHERE orden_id = %s
        """, (orden["id"],))
        compras[orden["id"]] = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "historial.html",
        ordenes=ordenes,
        compras=compras
    )


@app.route("/admin/ordenes")
def admin_ordenes():

    requiere_admin()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            o.id,
            o.total,
            o.estado,
            o.creado_en,
            u.nombre AS cliente,
            u.correo
        FROM ordenes o
        JOIN usuarios u ON o.usuario_id = u.id
        ORDER BY o.creado_en DESC
    """)

    ordenes = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin-ordenes.html", ordenes=ordenes)

@app.route("/admin/orden/<int:orden_id>")
def admin_orden_detalle(orden_id):

    requiere_admin()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            o.id,
            o.total,
            o.estado,
            o.creado_en,
            u.nombre AS cliente,
            u.correo
        FROM ordenes o
        JOIN usuarios u ON o.usuario_id = u.id
        WHERE o.id = %s
        ORDER BY o.creado_en DESC
    """, (orden_id,))
    orden = cursor.fetchone()

    if not orden:
        cursor.close()
        conn.close()
        abort(404)

    cursor.execute("""SELECT id, nombre_producto AS producto, precio,subtotal, cantidad
                   FROM orden_items 
                   WHERE orden_id = %s""" , (orden_id,))
    items = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("admin_orden_detalle.html", orden=orden , items=items)



@app.route("/admin/ordenes/eliminar/<int:id>", methods=["POST"])
def admin_eliminar_orden(id):

    requiere_admin()

    conn = get_connection()
    cursor = conn.cursor()

    # 1️⃣ Eliminar primero los items de la orden
    cursor.execute(
        "DELETE FROM orden_items WHERE orden_id = %s",
        (id,)
    )

    # 2️⃣ Eliminar la orden
    cursor.execute(
        "DELETE FROM ordenes WHERE id = %s",
        (id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    flash("Orden eliminada correctamente", "success")
    return redirect("/admin/ordenes")


@app.route("/admin/orden/<int:id>/estado", methods=["POST"])
def editar_estado_orden(id):

    requiere_admin()

    conn = get_connection()
    cursor = conn.cursor()

    # POST (FORMA CORRECTA)
    nuevo_estado = request.form.get("estado")

    if nuevo_estado not in ESTADOS_ORDEN:
        flash("Estado inválido", "error")
        return redirect(url_for("admin_orden_detalle", orden_id=id))

    cursor.execute("""
        UPDATE ordenes 
        SET estado = %s
        WHERE id = %s
    """, (nuevo_estado, id))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Estado actualizado correctamente", "success")
    return redirect(url_for("admin_orden_detalle", orden_id=id))

@app.route("/categorias/<slug>")
def categoria(slug):
    precio = request.args.get("precio")
    orden = request.args.get("orden", "asc")

    conn = get_connection()
    cursor = conn.cursor()

    # Obtener categoría por slug
    cursor.execute("""
        SELECT id, nombre
        FROM categorias
        WHERE slug = %s
    """, (slug,))

    categoria = cursor.fetchone()
    if not categoria:
        abort(404)

    categoria_id = categoria[0]

    # Query base
    query = """
        SELECT *
        FROM productos
        WHERE categoria_id = %s
    """
    params = [categoria_id]

    # Filtro por precio
    if precio:
        try:
            min_p, max_p = map(int, precio.split("-"))
            query += " AND precio BETWEEN %s AND %s"
            params.extend([min_p, max_p])
        except ValueError:
            pass

    # Orden por precio
    if orden == "desc":
        query += " ORDER BY precio DESC"
    else:
        query += " ORDER BY precio ASC"

    cursor.execute(query, params)
    productos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "categorias/categoria.html",
        productos=productos,
        categoria_nombre=categoria[1],
        categoria_slug=slug,
        precio_activo=precio or "",
        orden_activo=orden,
    )



@app.route("/admin/categorias/agregar", methods=["GET","POST"])
def admin_categorias_agregar():

    requiere_admin()

    if request.method == "POST":
        nombre = request.form["nombre"]
        slug = request.form["slug"]
       
        if not nombre or not slug :
            flash("Todos los campos son obligatorios", "error")
            return redirect(request.url)
    
        
        conn = get_connection()
        cursor = conn.cursor()
        sql = """INSERT INTO categorias (nombre, slug)
                  VALUES   (%s, %s)"""
        cursor.execute(sql, (nombre,slug))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Categoria agregado exitosamente" , "success")
        return redirect("/admin/categorias")
    
    return render_template("agregar_categoria.html")

   


@app.context_processor
def contexto_global():
    """Una sola conexion por render: categorias, carrito y favoritos del usuario."""
    ctx = {"csrf_token": csrf_token, "nav_categorias": [], "cat_opciones": [], "carrito_cantidad": 0,
           "carrito_ids": [], "favoritos_ids": [], "favoritos_count": 0}
    try:
        conn = get_connection()
    except Exception:
        return ctx
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, slug FROM categorias ORDER BY nombre ASC")
        filas_cat = cur.fetchall()
        ctx["nav_categorias"] = [(f[1], f[2]) for f in filas_cat]
        ctx["cat_opciones"] = [(f[0], f[1]) for f in filas_cat]
        uid = session.get("usuario_id")
        if uid:
            cur.execute("SELECT producto_id, cantidad FROM carrito_items WHERE usuario_id = %s", (uid,))
            filas = cur.fetchall()
            ctx["carrito_ids"] = [f[0] for f in filas]
            ctx["carrito_cantidad"] = int(sum(f[1] for f in filas))
            cur.execute("SELECT producto_id FROM favoritos WHERE usuario_id = %s", (uid,))
            ctx["favoritos_ids"] = [f[0] for f in cur.fetchall()]
            ctx["favoritos_count"] = len(ctx["favoritos_ids"])
        cur.close()
    finally:
        conn.close()
    return ctx


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")




