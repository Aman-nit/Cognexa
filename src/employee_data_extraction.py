import pandas as pd

# Load the cleaned insurance dataset
input_path = "cleaned_insurance_data.csv"

# Name of the new employee data file
output_path = "cleaned_employee_data.csv"

# Read the dataset
df = pd.read_csv(input_path)

# Select employee/profile-related columns
employee_cols = [
    "months_as_customer",
    "age",
    "insured_sex",
    "insured_education_level",
    "insured_occupation",
    "insured_hobbies",
    "insured_relationship",
    "capital-gains",
    "capital-loss",
]

# Create a separate employee dataset
employee_df = df[employee_cols].copy()

# Remove duplicate rows
employee_df = employee_df.drop_duplicates()

# Clean column names
employee_df.columns = (
    employee_df.columns.str.strip().str.lower().str.replace(" ", "_")
)

# Save the cleaned employee data
employee_df.to_csv(output_path, index=False)

print("Employee data file created successfully!")
print("Number of rows:", employee_df.shape[0])
print("Number of columns:", employee_df.shape[1])

print("\nColumns:")
print(employee_df.columns)
