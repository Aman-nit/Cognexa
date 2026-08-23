import duckdb

import duckdb
import pandas as pd

pd.set_option("display.max_columns", None)

con = duckdb.connect("insurance_project.duckdb")

result = con.execute("""
    SELECT * FROM insured LIMIT 5
""").fetchdf()

print(result)

con.close()