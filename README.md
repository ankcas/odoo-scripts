# Odoo Scripts

Scripts de automatizacion para **Odoo 17** y **WooCommerce** usados en operaciones de Desstenee (Republica Dominicana).

## Scripts

### CONCAT.py - Importar conduces desde PDF

Lee archivos PDF de conduces (guias de despacho), extrae codigos de productos y cantidades, y crea pickings de transferencia en Odoo automaticamente.

- Extrae codigos de 6 digitos y cantidades de PDFs
- Crea `stock.picking` con movimientos por cada producto
- Confirma y valida el picking
- Mueve los PDFs procesados a `/procesados/`
- Detecta duplicados por nombre de origen

**Requiere:** `PyMuPDF (fitz)`

### inventario.py - Carga masiva de inventario

Procesa archivos Excel con codigos de barra y cantidades para crear recepciones de inventario por sucursal.

- Seleccion interactiva de sucursal (14 sucursales configuradas)
- Busca productos por barcode principal o alternativo
- Corrige stocks negativos antes de sumar
- Crea picking de recepcion, confirma y valida
- Genera archivo de resultados por cada Excel procesado

**Requiere:** `pandas`, `openpyxl`

### generar_costos_actualizar_odoo.py - Comparar costos

Compara costos entre un archivo de proveedor (Adcon) y Odoo, genera un Excel con las diferencias para actualizar.

**Requiere:** `pandas`, `openpyxl`

### generar_precios_actualizar_odoo.py - Comparar precios de venta

Compara precios de venta entre un archivo de proveedor (Adcon) y Odoo, genera un Excel con las diferencias para actualizar.

**Requiere:** `pandas`, `openpyxl`

### PriceChangerOdoo.py - Actualizar precios en Odoo

Lee el archivo generado por `generar_precios_actualizar_odoo.py` y actualiza los precios de venta (`list_price`) directamente en Odoo via XML-RPC.

**Requiere:** `pandas`, `openpyxl`

### PriceChangerWeb.py - Actualizar precios en WooCommerce

Lee un Excel con precios y los actualiza en la tienda WooCommerce via API REST. Soporta productos simples, variables y variaciones.

**Requiere:** `pandas`, `requests`

## Configuracion

### Variables de entorno

Copiar `.env.example` a `.env` y completar con los valores reales:

```bash
cp .env.example .env
```

En **Windows** se pueden configurar las variables antes de ejecutar:

```cmd
set ODOO_URL=https://tu-dominio-odoo.com
set ODOO_PASSWORD=tu_password
python CONCAT.py
```

O en **PowerShell**:

```powershell
$env:ODOO_URL="https://tu-dominio-odoo.com"
$env:ODOO_PASSWORD="tu_password"
python CONCAT.py
```

### Dependencias

```bash
pip install pandas openpyxl PyMuPDF requests
```

## Flujo de trabajo tipico

### Actualizar precios Odoo

```
1. Exportar precios de Odoo a Odoo.xlsx
2. Obtener precios del proveedor en Adcon.xlsx
3. Ejecutar: python generar_precios_actualizar_odoo.py
   → Genera: precios_actualizar_odoo.xlsx
4. Ejecutar: python PriceChangerOdoo.py
   → Actualiza precios en Odoo
```

### Actualizar precios WooCommerce

```
1. Tener Odoo.xlsx con precios actualizados
2. Ejecutar: python PriceChangerWeb.py
   → Actualiza precios en la tienda web
```

### Cargar inventario

```
1. Preparar Excel con columnas "Codigo Barra" y "Cant"
2. Colocar en la carpeta de inventario
3. Ejecutar: python inventario.py
4. Seleccionar sucursal
   → Crea recepciones en Odoo
```

## Autor

**Andrew Castillo** - [Desstenee](https://dessteneesupply.com)
