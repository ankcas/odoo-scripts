import os
import pandas as pd
import xmlrpc.client
import shutil

# === CONFIGURACIÓN ===
EXCEL_DIR = r"C:\Users\Andriws Castillo\Desktop\inventario"
PROCESADOS_DIR = os.path.join(EXCEL_DIR, "procesados")
os.makedirs(PROCESADOS_DIR, exist_ok=True)

url = os.environ.get("ODOO_URL", "https://tu-dominio-odoo.com")
db = os.environ.get("ODOO_DB", "PRODUCCION")
username = os.environ.get("ODOO_USER", "admin")
password = os.environ.get("ODOO_PASSWORD", "")

LOCATION_PROVEEDORES = 5

# === SUCURSALES ===
SUCURSALES = {
    "ALMACEN":          {"company_id": 1,  "location_id": 8},
    "PLAZA CATALUNA":   {"company_id": 2,  "location_id": 19},
    "CHARLES SUMNER":   {"company_id": 3,  "location_id": 25},
    "AGORA MALL":       {"company_id": 4,  "location_id": 31},
    "GALERIA 360":      {"company_id": 5,  "location_id": 37},
    "COLINA CENTRO":    {"company_id": 6,  "location_id": 68},
    "PLAZA DUARTE":     {"company_id": 7,  "location_id": 106},
    "PLAZA CENTRAL":    {"company_id": 8,  "location_id": 112},
    "PATIO EMBAJADA":   {"company_id": 9,  "location_id": 118},
    "MEGACENTRO":       {"company_id": 10, "location_id": 124},
    "SAMBIL":           {"company_id": 11, "location_id": 130},
    "SANTIAGO":         {"company_id": 12, "location_id": 136},
    "METRO PLAZA":      {"company_id": 13, "location_id": 142},
    "DOWNTOWN CENTER":  {"company_id": 14, "location_id": 148},
}

# === SELECCIONAR SUCURSAL ===
nombres = list(SUCURSALES.keys())
print("SUCURSALES DISPONIBLES:")
for i, nombre in enumerate(nombres, 1):
    s = SUCURSALES[nombre]
    print(f"  {i}. {nombre} (company={s['company_id']}, location={s['location_id']})")

seleccion = input("\nNumero de sucursal: ").strip()
try:
    sucursal_nombre = nombres[int(seleccion) - 1]
except (ValueError, IndexError):
    raise Exception("Seleccion invalida")

config = SUCURSALES[sucursal_nombre]
COMPANY_ID = config["company_id"]
LOCATION_ID = config["location_id"]

print(f"\nSucursal: {sucursal_nombre}")
print(f"Company ID: {COMPANY_ID} | Location ID: {LOCATION_ID}")
confirmacion = input("Confirmar? (si/no): ").strip().lower()
if confirmacion != "si":
    print("Cancelado.")
    exit(0)

# === CONEXIÓN ===
print("\nConectando a Odoo 17...")
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})
if not uid:
    raise Exception("Error de autenticacion")
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
print("Conectado\n")

# === BUSCAR PICKING TYPE ===
pt = models.execute_kw(
    db, uid, password,
    "stock.picking.type", "search",
    [[
        ("code", "=", "incoming"),
        ("company_id", "=", COMPANY_ID),
    ]],
    {"limit": 1}
)
if not pt:
    raise Exception(f"No se encontro picking type de recepcion para {sucursal_nombre}")
picking_type_id = pt[0]
print(f"Picking type: {picking_type_id}")


# === FUNCIONES ===
def buscar_producto(barcode):
    """Busca producto por barcode exacto (principal o alternativo)."""
    # 1. Buscar por barcode principal
    product = models.execute_kw(
        db, uid, password, "product.product", "search_read",
        [[("barcode", "=", barcode)]],
        {"fields": ["id", "name", "default_code", "barcode", "uom_id"], "limit": 1}
    )
    if product:
        return product[0]

    # 2. Buscar en barcodes alternativos (product.template.barcode)
    try:
        alterno = models.execute_kw(
            db, uid, password, "product.template.barcode", "search_read",
            [[("name", "=", barcode)]],
            {"fields": ["product_id"], "limit": 1}
        )
        if alterno:
            product_id = alterno[0]["product_id"][0]
            data = models.execute_kw(
                db, uid, password, "product.product", "read",
                [product_id, ["id", "name", "default_code", "barcode", "uom_id"]]
            )
            if data:
                return data[0]
    except xmlrpc.client.Fault:
        pass

    return None


def corregir_negativo(product_id):
    """Si el quant esta en negativo, lo corrige a 0 antes de sumar."""
    quants = models.execute_kw(
        db, uid, password,
        "stock.quant", "search_read",
        [[
            ("product_id", "=", product_id),
            ("location_id", "=", LOCATION_ID),
            ("company_id", "=", COMPANY_ID),
        ]],
        {"fields": ["id", "quantity"], "limit": 1}
    )
    if not quants or quants[0]["quantity"] >= 0:
        return

    quant = quants[0]
    print(f"  Corrigiendo negativo: qty={quant['quantity']} -> 0")
    models.execute_kw(
        db, uid, password,
        "stock.quant", "write",
        [[quant["id"]], {"quantity": 0}]
    )


# === PROCESAR ARCHIVOS ===
resultados = []

for archivo in os.listdir(EXCEL_DIR):
    if not archivo.lower().endswith((".xlsx", ".xls", ".xlsm")):
        continue
    if archivo.startswith("~$") or archivo.lower().startswith("resultado"):
        continue

    ruta_excel = os.path.join(EXCEL_DIR, archivo)
    print(f"\nProcesando: {archivo}")

    try:
        df = pd.read_excel(ruta_excel, engine="openpyxl")
    except Exception as e:
        print(f"Error leyendo {archivo}: {e}")
        continue

    cols = {c.lower().strip(): c for c in df.columns}
    barcode_col = cols.get("codigo barra") or cols.get("codigo_barra")
    qty_col = cols.get("cant") or cols.get("cantidad")

    if not barcode_col or not qty_col:
        print(f"{archivo} sin columnas validas. Saltado.")
        continue

    df = df[df[barcode_col].notna() & df[qty_col].notna()].copy()
    df[barcode_col] = (
        df[barcode_col].astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )

    # Crear picking
    picking_id = models.execute_kw(
        db, uid, password, "stock.picking", "create", [{
            "picking_type_id": picking_type_id,
            "location_id": LOCATION_PROVEEDORES,
            "location_dest_id": LOCATION_ID,
            "company_id": COMPANY_ID,
            "origin": f"Inventario {sucursal_nombre} - {archivo}",
        }]
    )
    print(f"Picking creado: {picking_id}")

    productos_encontrados = 0

    for _, row in df.iterrows():
        barcode = str(row[barcode_col]).strip()
        try:
            cantidad = float(row[qty_col])
        except (ValueError, TypeError):
            resultados.append({
                "ARCHIVO": archivo, "CODIGO BARRA": barcode,
                "CANTIDAD": row[qty_col], "ESTADO": "Cantidad invalida",
            })
            continue

        product = buscar_producto(barcode)
        if not product:
            resultados.append({
                "ARCHIVO": archivo, "CODIGO BARRA": barcode,
                "CANTIDAD": cantidad, "ESTADO": "No encontrado",
            })
            continue

        product_id = product["id"]
        uom_id = product["uom_id"][0] if product.get("uom_id") else 1

        # Corregir negativo a 0 antes de sumar
        corregir_negativo(product_id)

        models.execute_kw(
            db, uid, password, "stock.move", "create", [{
                "name": f"Ajuste {barcode}",
                "product_id": product_id,
                "product_uom_qty": cantidad,
                "product_uom": uom_id,
                "picking_id": picking_id,
                "location_id": LOCATION_PROVEEDORES,
                "location_dest_id": LOCATION_ID,
                "company_id": COMPANY_ID,
            }]
        )
        productos_encontrados += 1

        resultados.append({
            "ARCHIVO": archivo,
            "CODIGO BARRA": barcode,
            "REFERENCIA": product.get("default_code", ""),
            "NOMBRE PRODUCTO": product["name"],
            "CANTIDAD": cantidad,
            "ESTADO": "Movimiento creado",
        })

    # Eliminar picking si no tuvo movimientos
    if productos_encontrados == 0:
        print("Sin movimientos. Eliminando picking vacio.")
        models.execute_kw(
            db, uid, password, "stock.picking", "unlink", [[picking_id]]
        )
        continue

    # Confirmar y validar
    try:
        models.execute_kw(
            db, uid, password, "stock.picking", "action_confirm", [[picking_id]]
        )
        models.execute_kw(
            db, uid, password, "stock.picking", "button_validate", [[picking_id]]
        )
        print(f"Picking {picking_id} confirmado y validado.")
    except Exception as e:
        print(f"ERROR validando picking {picking_id}: {e}")

    # Guardar resultado
    resultado_df = pd.DataFrame([r for r in resultados if r["ARCHIVO"] == archivo])
    nombre_base = os.path.splitext(archivo)[0]
    resultado_path = os.path.join(PROCESADOS_DIR, f"resultado_{nombre_base}.xlsx")
    resultado_df.to_excel(resultado_path, index=False)
    print(f"Resultado guardado: {resultado_path}")

    shutil.move(ruta_excel, os.path.join(PROCESADOS_DIR, archivo))
    print(f"{archivo} movido a procesados/")

# === RESUMEN FINAL ===
total = len(resultados)
creados = sum(1 for r in resultados if r["ESTADO"] == "Movimiento creado")
no_encontrados = sum(1 for r in resultados if r["ESTADO"] == "No encontrado")

print(f"\n{'='*40}")
print(f"RESUMEN - {sucursal_nombre}")
print(f"{'='*40}")
print(f"Total lineas:     {total}")
print(f"Movimientos:      {creados}")
print(f"No encontrados:   {no_encontrados}")
print("Proceso completado.")
