
import pandas as pd

# Cargar los archivos
adcon_file = "Adcon.xlsx"
odoo_file = "Odoo.xlsx"
output_file = "precios_actualizar_odoo.xlsx"

# Leer los archivos
adcon_df = pd.read_excel(adcon_file)
odoo_df = pd.read_excel(odoo_file)

# Normalizar columnas clave
adcon_df['Codigo interno'] = adcon_df['Codigo interno'].astype(str).str.strip().str.lstrip('0')
odoo_df['Referencia interna'] = odoo_df['Referencia interna'].astype(str).str.strip().str.lstrip('0')

# Renombrar columnas para uniformidad
odoo_df = odoo_df.rename(columns={
    'Referencia interna': 'default_code',
    'Nombre': 'name',
    'Precio de venta': 'list_price'
})
adcon_df = adcon_df.rename(columns={
    'Codigo interno': 'default_code',
    'Precio de venta': 'adcon_price'
})

# Hacer el merge por código interno sin ceros
merged_df = pd.merge(
    odoo_df,
    adcon_df[['default_code', 'adcon_price']],
    on='default_code',
    how='inner'
)

# Filtrar solo si hay diferencia de precios
diferencias_df = merged_df[merged_df['list_price'] != merged_df['adcon_price']]

# Dejar solo columnas necesarias para actualizar
resultado_df = diferencias_df[['default_code', 'name', 'adcon_price']]
resultado_df = resultado_df.rename(columns={'adcon_price': 'list_price'})

# Exportar archivo final
resultado_df.to_excel(output_file, index=False)
print(f"✅ Archivo generado: {output_file} con {len(resultado_df)} productos para actualizar.")
