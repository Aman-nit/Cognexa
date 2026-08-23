import duckdb

con = duckdb.connect("insurance.duckdb")

result = con.execute("""
    SELECT * FROM insurance_claim_analysis
    LIMIT 5;
""").fetchdf()

print(result)

con.close()