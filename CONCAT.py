import os
import fitz  # PyMuPDF
import re
import xmlrpc.client
import shutil

# === CONFIGURACIÓN LOCAL ===
PDF_DIR = r'C:\Users\Call Center\Desktop\Andrew Castillo\OdooMove\conduces'
PROCESADOS_DIR = os.path.join(PDF_DIR, 'procesados')
os.makedirs(PROCESADOS_DIR, exist_ok=True)

# === CREDENCIALES ODOO (desde variables de entorno) ===
url = os.environ.get("ODOO_URL", "https://tu-dominio-odoo.com")
db = os.environ.get("ODOO_DB", "PRODUCCION")
username = os.environ.get("ODOO_USER", "admin")
password = os.environ.get("ODOO_PASSWORD", "")

# === CONFIGURACIÓN CATALUÑA ===
picking_type_id = 6
location_id = 42
dest_location_id = 19
company_id = 2

# === CONECTAR A ODOO ===
print("🔗 Conectando a Odoo...")
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

if not uid:
    print("❌ Fallo de autenticación.")
    exit()
print("✅ Conectado a Odoo")

# === FUNCIÓN LECTURA PDF MEJORADA ===
def extraer_productos_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    lineas_total = []

    for page in doc:
        texto = page.get_text()
        lineas = texto.split('\n')
        for l in lineas:
            if l.strip():
                lineas_total.append(l.strip())

    productos = []
    omitidos = []

    for i, linea in enumerate(lineas_total):
        if re.match(r'^0\d{5}$', linea):  # Código válido: empieza en 0 y 6 dígitos
            codigo = linea
            encontrado = False
            for j in range(1, 6):  # Revisa hasta 5 líneas siguientes
                if i + j < len(lineas_total):
                    posible = lineas_total[i + j].strip().replace(' ', '')
                    if re.match(r'^\d+([.,]\d{2})$', posible):  # acepta coma o punto decimal
                        cantidad = float(posible.replace(',', '.'))
                        productos.append((codigo, cantidad))
                        encontrado = True
                        break
            if not encontrado:
                omitidos.append(codigo)

    doc.close()
    return productos, omitidos

# === PROCESAR ARCHIVOS PDF ===
for archivo in os.listdir(PDF_DIR):
    if archivo.lower().endswith('.pdf'):
        ruta_pdf = os.path.join(PDF_DIR, archivo)
        print(f"\n📄 Procesando: {archivo}")
        productos, omitidos = extraer_productos_pdf(ruta_pdf)

        if not productos:
            print(f"⚠️ No se encontraron productos válidos en {archivo}.")
            continue

        # Verificar duplicado por nombre de origen
        ya_existe = models.execute_kw(db, uid, password, 'stock.picking', 'search', [[
            ['origin', '=', f'Conduce automático - {archivo}']
        ]])
        if ya_existe:
            print(f"⚠️ Ya existe un picking para este archivo. Saltando...")
            continue

        try:
            picking_id = models.execute_kw(db, uid, password, 'stock.picking', 'create', [{
                'picking_type_id': picking_type_id,
                'location_id': location_id,
                'location_dest_id': dest_location_id,
                'company_id': company_id,
                'origin': f'Conduce automático - {archivo}'
            }])
            print(f"📦 Picking creado: {picking_id}")
        except Exception as e:
            print(f"❌ Error creando picking: {e}")
            continue

        for codigo, cantidad in productos:
            try:
                product = models.execute_kw(db, uid, password, 'product.product', 'search_read', [
                    [['default_code', '=', codigo], ['active', '=', True]]
                ], {'fields': ['id'], 'limit': 1})

                if not product:
                    print(f"❌ Producto no encontrado en Odoo: {codigo}")
                    continue

                product_id = product[0]['id']
                move_id = models.execute_kw(db, uid, password, 'stock.move', 'create', [{
                    'name': f"Ajuste producto {codigo}",
                    'product_id': product_id,
                    'product_uom_qty': cantidad,
                    'product_uom': 1,
                    'picking_id': picking_id,
                    'location_id': location_id,
                    'location_dest_id': dest_location_id,
                    'company_id': company_id,
                }])
                print(f"  ➤ Movimiento creado: {move_id}")
            except Exception as e:
                print(f"❌ Error al crear movimiento para {codigo}: {e}")
                continue

        try:
            models.execute_kw(db, uid, password, 'stock.picking', 'action_confirm', [[picking_id]])
            models.execute_kw(db, uid, password, 'stock.picking', 'button_validate', [[picking_id]])
            print(f"✅ Picking {picking_id} confirmado y validado.")
        except Exception as e:
            print(f"❌ Error al confirmar o validar picking: {e}")
            continue

        shutil.move(ruta_pdf, os.path.join(PROCESADOS_DIR, archivo))
        print(f"📁 {archivo} movido a /procesados/")

        print("\n✅ === PRODUCTOS PROCESADOS ===")
        for codigo, cantidad in productos:
            print(f"Código: {codigo} | Cantidad: {cantidad}")

        if omitidos:
            print("\n⚠️ Se omitieron códigos sin cantidad válida:")
            for cod in omitidos:
                print(f" - {cod}")
