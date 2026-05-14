import os
import xmlrpc.client
import pandas as pd

# ======= CONEXIÓN ODOO (desde variables de entorno) =======
url = os.environ.get("ODOO_URL", "https://tu-dominio-odoo.com")
db = os.environ.get("ODOO_DB", "PRODUCCION")
username = os.environ.get("ODOO_USER", "admin")
password = os.environ.get("ODOO_PASSWORD", "")

# ======= AUTENTICACIÓN =======
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# ======= CARGAR ARCHIVO =======
df = pd.read_excel("precios_actualizar_odoo.xlsx")

# ======= ACTUALIZACIÓN DE PRECIOS =======
actualizados = 0
no_encontrados = []

for _, row in df.iterrows():
    codigo_raw = str(row['default_code']).strip()
    codigo = codigo_raw.zfill(6)  # 🔁 Fuerza a 6 dígitos con ceros a la izquierda
    nuevo_precio = float(row['list_price'])

    # Buscar producto por 'default_code'
    product_ids = models.execute_kw(db, uid, password,
        'product.template', 'search',
        [[['default_code', '=', codigo]]]
    )

    if product_ids:
        models.execute_kw(db, uid, password,
            'product.template', 'write',
            [[product_ids[0]], {'list_price': nuevo_precio}]
        )
        print(f"✅ Precio actualizado: {codigo} -> {nuevo_precio}")
        actualizados += 1
    else:
        print(f"❌ Producto no encontrado: {codigo}")
        no_encontrados.append(codigo)

print(f"\n✔ Total actualizados: {actualizados}")
print(f"❗ No encontrados: {len(no_encontrados)}")
