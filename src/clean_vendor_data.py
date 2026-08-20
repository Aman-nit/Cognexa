import numpy as np
import pandas as pd

# 1. Load raw vendor dataset
df_ven = pd.read_csv("vendor_data(vendor_data).csv")

# 2. Standardize column names (lowercase & trimmed)
df_ven.columns = df_ven.columns.str.strip().str.lower()

# 3. Trim whitespace across string columns
string_cols = ["vendor_id", "vendor_name", "address_line1", "city", "state"]
for col in string_cols:
    df_ven[col] = df_ven[col].astype(str).str.strip()

# 4. Format postal code with 5-digit string padding (restores leading zeros)
df_ven["postal_code"] = df_ven["postal_code"].astype(str).str.zfill(5)

# 5. Impute missing cities using Vermont ZIP lookup dictionary
vt_zip_map = {
    "05647": "Calais",
    "05443": "Bristol",
    "05149": "Ludlow",
    "05468": "Milton",
}
df_ven["city"] = (
    df_ven["city"]
    .replace({"nan": np.nan})
    .fillna(df_ven["postal_code"].map(vt_zip_map))
)

# 6. Explicitly set missing secondary addresses to NaN (null)
df_ven["address_line2"] = df_ven["address_line2"].replace(
    {"nan": np.nan, "": np.nan}
)

# 7. Create fraud risk flag (shared physical address + ZIP code)
df_ven["is_shared_address"] = df_ven.duplicated(
    subset=["address_line1", "postal_code"], keep=False
)

# 8. Export clean dataset
output_file = "vendor_data_final.csv"
df_ven.to_csv(output_file, index=False)

print(
    f"Success! Saved clean dataset to '{output_file}' ({len(df_ven)} rows)."
)
print("\nNull Summary:")
print(df_ven.isnull().sum())