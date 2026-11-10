<p align="center"><img src="static/img/logo.png" width="120" alt="VESTRA logo"></p>

<h1 align="center">VESTRA</h1>
<p align="center">Full-stack fashion e-commerce built with Flask and MySQL.<br>Open source, free to use as a learning base.</p>

## Features

- **Catalog** – browse by category, search, price filter and sorting
- **Accounts** – registration, login with bcrypt hashing, lockout after 3 failed attempts, profile, change email/password
- **Favorites & cart** – persistent per user, live counters in the navbar
- **Checkout & orders** – order history, order confirmation (no real payment gateway; orders are stored for demo purposes)
- **Admin panel** – manage users, products (image upload), categories and orders
- **Security basics** – parameterized SQL queries, input sanitizing with `bleach`, role-based access, secrets via environment variables

## Stack

Python · Flask · MySQL/MariaDB · Jinja2 · HTML/CSS · Bootstrap · Font Awesome

## Getting started

```bash
git clone https://github.com/nibrill/vestra.git
cd vestra
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # then edit values
mysql -u root -p < database/schema.sql                # creates the `vestra` database
python create_admin.py "Admin" admin@example.com "a-strong-password"
flask --app app run
```

Export the variables from `.env` (`SECRET_KEY`, `DB_*`) in your shell before running.

## Project layout

```
app.py            Flask routes and business logic
connection.py     MySQL connection (env-driven)
create_admin.py   CLI to create an admin user
database/         SQL schema and sample catalog
templates/        Jinja2 templates
static/           CSS, JS and images
```

## Notes

- Sample product photos are demo placeholders; replace them with images you have rights to use before any commercial use.
- Payments are intentionally not implemented.

## License

[MIT](LICENSE) © 2026 nibrill
