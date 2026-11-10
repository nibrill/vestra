<p align="center"><img src="static/img/logo.png" width="120" alt="Logo de VESTRA"></p>

<h1 align="center">VESTRA</h1>
<p align="center">Tienda de ropa online full-stack hecha con Flask y MySQL.<br>Código abierto, pensado como base para aprender.</p>

## Características

- **Catálogo**: navegación por categorías, búsqueda, filtro por precio y ordenamiento
- **Cuentas de usuario**: registro, inicio de sesión con bcrypt, bloqueo tras 3 intentos fallidos, perfil, cambio de correo y contraseña
- **Favoritos y carrito**: persistentes por usuario, con contadores en la barra de navegación
- **Checkout y órdenes**: historial de compras y confirmación de pedido (sin pasarela de pago real; las órdenes se guardan solo con fines de demostración)
- **Panel de administración**: gestión de usuarios, productos (con subida de imágenes), categorías y órdenes
- **Seguridad básica**: consultas SQL parametrizadas, sanitización con `bleach`, control de acceso por rol y secretos mediante variables de entorno

## Tecnologías

Python · Flask · MySQL/MariaDB · Jinja2 · HTML/CSS · Bootstrap · Font Awesome

## Puesta en marcha

```bash
git clone https://github.com/nibrill/vestra.git
cd vestra
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # edita los valores
mysql -u root -p < database/schema.sql                # crea la base de datos `vestra`
python create_admin.py "Admin" admin@example.com "una-clave-segura"
flask --app app run
```

Exporta las variables de `.env` (`SECRET_KEY`, `DB_*`) en tu terminal antes de ejecutar.

## Estructura del proyecto

```
app.py            Rutas de Flask y lógica de negocio
connection.py     Conexión a MySQL (configurada por entorno)
create_admin.py   Script para crear un usuario administrador
database/         Esquema SQL y catálogo de ejemplo
templates/        Plantillas Jinja2
static/           CSS, JS e imágenes
```

## Notas

- Las fotos de los productos son de ejemplo; reemplázalas por imágenes de las que tengas derechos antes de cualquier uso comercial.
- Los pagos no están implementados a propósito.

## Licencia

[MIT](LICENSE) © 2026 nibrill
