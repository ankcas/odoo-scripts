# Odoo Scripts

Scripts de automatizacion para **Odoo 17** y **WooCommerce** usados en las operaciones de [Desstenee Beauty Supply](https://dessteneesupply.com) (Republica Dominicana, 14 sucursales).

Comunicacion con Odoo via **XML-RPC** (`xmlrpc/2/object`). Comunicacion con WooCommerce via **REST API** (`wc/v3`).

## Scripts

| Script | Descripcion |
|--------|-------------|
| `CONCAT.py` | Importar conduces PDF a pickings de transferencia en Odoo |
| `inventario.py` | Carga masiva de inventario por sucursal desde Excel |
| `generar_costos_actualizar_odoo.py` | Comparar costos proveedor vs Odoo, genera Excel de diferencias |
| `generar_precios_actualizar_odoo.py` | Comparar precios de venta proveedor vs Odoo, genera Excel de diferencias |
| `PriceChangerOdoo.py` | Actualizar precios de venta en Odoo desde Excel |
| `PriceChangerWeb.py` | Actualizar precios en WooCommerce desde Excel |

### CONCAT.py - Importar conduces desde PDF

Lee archivos PDF de conduces (guias de despacho), extrae codigos de productos y cantidades, y crea pickings de transferencia en Odoo automaticamente.

- Extrae codigos de 6 digitos y cantidades de PDFs con regex
- Crea `stock.picking` con `stock.move` por cada producto
- Confirma y valida el picking
- Mueve los PDFs procesados a `/procesados/`
- Detecta duplicados por nombre de origen para evitar doble carga

### inventario.py - Carga masiva de inventario

Procesa archivos Excel con codigos de barra y cantidades para crear recepciones de inventario por sucursal.

- Seleccion interactiva de sucursal (14 sucursales configuradas)
- Busca productos por barcode principal o alternativo (`product.template.barcode`)
- Corrige stocks negativos a 0 antes de sumar
- Crea picking de recepcion, confirma y valida
- Genera archivo de resultados por cada Excel procesado
- Elimina pickings vacios si no se encontraron productos

### generar_costos_actualizar_odoo.py - Comparar costos

Compara el campo `costo` de un archivo del proveedor (Adcon.xlsx) contra `standard_price` de Odoo (Odoo.xlsx). Genera `costos_actualizar_odoo.xlsx` solo con los productos que tienen diferencias.

### generar_precios_actualizar_odoo.py - Comparar precios de venta

Compara `Precio de venta` del proveedor (Adcon.xlsx) contra `list_price` de Odoo (Odoo.xlsx). Genera `precios_actualizar_odoo.xlsx` solo con los productos que tienen diferencias.

### PriceChangerOdoo.py - Actualizar precios en Odoo

Lee `precios_actualizar_odoo.xlsx` (generado por el script anterior) y actualiza `list_price` en `product.template` via XML-RPC. Los codigos se normalizan a 6 digitos con ceros a la izquierda.

### PriceChangerWeb.py - Actualizar precios en WooCommerce

Lee `Odoo.xlsx` con precios actualizados y los sincroniza a WooCommerce via API REST. Soporta:

- **Productos simples** - actualiza `regular_price` directamente
- **Productos variables** - busca la variacion por SKU o actualiza todas
- **Variaciones directas** - actualiza via `parent_id`

## Configuracion

### Variables de entorno

Copiar `.env.example` a `.env` y completar con los valores reales:

```bash
cp .env.example .env
```

| Variable | Usado por | Descripcion |
|----------|-----------|-------------|
| `ODOO_URL` | CONCAT, inventario, PriceChangerOdoo | URL del servidor Odoo |
| `ODOO_DB` | CONCAT, inventario, PriceChangerOdoo | Nombre de la base de datos |
| `ODOO_USER` | CONCAT, inventario, PriceChangerOdoo | Usuario Odoo |
| `ODOO_PASSWORD` | CONCAT, inventario, PriceChangerOdoo | Password Odoo |
| `WC_API_URL` | PriceChangerWeb | URL API WooCommerce |
| `WC_CONSUMER_KEY` | PriceChangerWeb | Consumer Key WooCommerce |
| `WC_CONSUMER_SECRET` | PriceChangerWeb | Consumer Secret WooCommerce |

En **Windows CMD**:

```cmd
set ODOO_URL=https://tu-dominio-odoo.com
set ODOO_PASSWORD=tu_password
python CONCAT.py
```

En **PowerShell**:

```powershell
$env:ODOO_URL="https://tu-dominio-odoo.com"
$env:ODOO_PASSWORD="tu_password"
python CONCAT.py
```

### Dependencias

```bash
pip install pandas openpyxl PyMuPDF requests
```

## Flujo de trabajo

### Actualizar precios Odoo

```
1. Exportar precios de Odoo a Odoo.xlsx
2. Obtener precios del proveedor en Adcon.xlsx
3. python generar_precios_actualizar_odoo.py
   → Genera: precios_actualizar_odoo.xlsx
4. python PriceChangerOdoo.py
   → Actualiza precios en Odoo
```

### Actualizar precios WooCommerce

```
1. Tener Odoo.xlsx con precios actualizados
2. python PriceChangerWeb.py
   → Actualiza precios en la tienda web
```

### Cargar inventario por sucursal

```
1. Preparar Excel con columnas "Codigo Barra" y "Cant"
2. Colocar en la carpeta de inventario
3. python inventario.py
4. Seleccionar sucursal (1-14)
   → Crea recepciones en Odoo
   → Genera resultado_*.xlsx en procesados/
```

### Importar conduces PDF

```
1. Colocar PDFs de conduces en la carpeta configurada
2. python CONCAT.py
   → Crea pickings de transferencia en Odoo
   → Mueve PDFs a procesados/
```

## Autor

**Andrew Castillo** - [Desstenee](https://dessteneesupply.com)
