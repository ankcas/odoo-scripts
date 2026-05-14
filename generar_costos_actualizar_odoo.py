import pandas as pd

# Archivos
adcon_file = "Adcon.xlsx"
odoo_file = "Odoo.xlsx"
output_file = "costos_actualizar_odoo.xlsx"

# Leer archivos
adcon_df = pd.read_excel(adcon_file)
odoo_df = pd.read_excel(odoo_file)

# Normalizar códigos
adcon_df['Codigo interno'] = adcon_df['Codigo interno'].astype(str).str.strip().str.lstrip('0')
odoo_df['Referencia interna'] = odoo_df['Referencia interna'].astype(str).str.strip().str.lstrip('0')

# Renombrar columnas
adcon_df = adcon_df.rename(columns={
    'Codigo interno': 'default_code',
    'costo': 'adcon_cost'
})
odoo_df = odoo_df.rename(columns={
    'Referencia interna': 'default_code',
    'Costo': 'standard_price'
})

# Unir por código interno
merged_df = pd.merge(
    odoo_df,
    adcon_df[['default_code', 'adcon_cost']],
    on='default_code',
    how='inner'
)

# Filtrar diferencias en costo
diferencias_df = merged_df[merged_df['standard_price'] != merged_df['adcon_cost']]

# Preparar resultado para actualizar (sin name)
resultado_df = diferencias_df[['default_code', 'adcon_cost']]
resultado_df = resultado_df.rename(columns={'adcon_cost': 'standard_price'})

# Exportar archivo
resultado_df.to_excel(output_file, index=False)
print(f"✅ Archivo generado: {output_file} con {len(resultado_df)} productos con diferencias de costo.")
