import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import os

# =====================================================
# CONFIGURACIÓN API WOOCOMMERCE
# =====================================================
WC_API_URL = os.environ.get("WC_API_URL", "https://tu-tienda.com/wp-json/wc/v3")
CK = os.environ.get("WC_CONSUMER_KEY", "")
CS = os.environ.get("WC_CONSUMER_SECRET", "")
AUTH = HTTPBasicAuth(CK, CS)
TIMEOUT = 30

def wc_get(path, params=None):
    return requests.get(
        f"{WC_API_URL}{path}",
        auth=AUTH,
        params=params or {},
        timeout=TIMEOUT
    )

def wc_put(path, payload):
    return requests.put(
        f"{WC_API_URL}{path}",
        auth=AUTH,
        json=payload,
        timeout=TIMEOUT
    )

# =====================================================
# LEER EXCEL (MISMA RUTA DEL SCRIPT)
# =====================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(SCRIPT_DIR, "Odoo.xlsx")

df = pd.read_excel(EXCEL_PATH)

# =====================================================
# PROCESO PRINCIPAL
# =====================================================
for _, row in df.iterrows():
    sku = str(row["Referencia interna"]).strip().zfill(6)

    try:
        new_price = round(float(row["Precio de venta"]), 2)
    except Exception:
        print(f"⚠️  SKU {sku}: precio inválido -> {row['Precio de venta']}")
        continue

    # -------------------------------------------------
    # 1) BUSCAR PRODUCTO POR SKU
    # -------------------------------------------------
    resp = wc_get("/products", params={"sku": sku})
    if resp.status_code != 200:
        print(f"❌ Error buscando SKU {sku}: {resp.status_code} - {resp.text}")
        continue

    items = resp.json()
    if not items:
        print(f"❌ Producto no encontrado con SKU {sku}")
        continue

    item = items[0]
    item_type = item.get("type")

    # -------------------------------------------------
    # 2) RUTEO POR TIPO
    # -------------------------------------------------
    try:
        # =============================
        # PRODUCTO SIMPLE
        # =============================
        if item_type == "simple":
            product_id = item["id"]
            payload = {"regular_price": f"{new_price:.2f}"}
            u = wc_put(f"/products/{product_id}", payload)

            if u.status_code == 200:
                print(f"✅ Simple actualizado | SKU {sku} -> {new_price:.2f}")
            else:
                print(f"❌ Error simple SKU {sku}: {u.status_code} - {u.text}")

        # =============================
        # PRODUCTO VARIABLE (SKU EN PADRE O VARIACIÓN)
        # =============================
        elif item_type == "variable":
            parent_id = item["id"]

            # Intentar variación con ese SKU
            vresp = wc_get(f"/products/{parent_id}/variations", params={"sku": sku})
            if vresp.status_code != 200:
                print(f"❌ Error buscando variaciones SKU {sku}")
                continue

            variations = vresp.json()

            # -----------------------------------------
            # CASO A: SKU ESTÁ EN UNA VARIACIÓN
            # -----------------------------------------
            if variations:
                variation_id = variations[0]["id"]
                payload = {"regular_price": f"{new_price:.2f}"}
                u = wc_put(f"/products/{parent_id}/variations/{variation_id}", payload)

                if u.status_code == 200:
                    print(f"✅ Variación actualizada | SKU {sku} -> {new_price:.2f}")
                else:
                    print(f"❌ Error variación SKU {sku}: {u.status_code}")

            # -----------------------------------------
            # CASO B: SKU ESTÁ EN EL PADRE
            # -----------------------------------------
            else:
                all_vars = wc_get(f"/products/{parent_id}/variations")
                if all_vars.status_code != 200:
                    print(f"❌ Error listando variaciones SKU {sku}")
                    continue

                for v in all_vars.json():
                    variation_id = v["id"]
                    payload = {"regular_price": f"{new_price:.2f}"}
                    u = wc_put(f"/products/{parent_id}/variations/{variation_id}", payload)

                    if u.status_code == 200:
                        print(f"✅ Variación {variation_id} actualizada | SKU padre {sku}")
                    else:
                        print(f"❌ Error variación {variation_id}: {u.status_code}")

        # =============================
        # VARIACIÓN DEVUELTA DIRECTA
        # =============================
        elif item_type == "variation":
            variation_id = item["id"]
            parent_id = item.get("parent_id")

            if not parent_id:
                print(f"❌ Variación sin parent_id | SKU {sku}")
                continue

            payload = {"regular_price": f"{new_price:.2f}"}
            u = wc_put(f"/products/{parent_id}/variations/{variation_id}", payload)

            if u.status_code == 200:
                print(f"✅ Variación directa actualizada | SKU {sku} -> {new_price:.2f}")
            else:
                print(f"❌ Error variación directa SKU {sku}: {u.status_code}")

        # =============================
        # OTROS TIPOS
        # =============================
        else:
            print(f"⚠️  SKU {sku}: tipo no soportado ({item_type})")

    except KeyError as e:
        print(f"❌ Estructura inesperada para SKU {sku}. Falta campo: {e}")
