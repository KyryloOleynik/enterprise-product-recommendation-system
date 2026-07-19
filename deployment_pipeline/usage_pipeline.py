import pandas as pd
import random
from pathlib import Path

project_root = Path.cwd().parent.parent if Path.cwd().name == "notebooks" else Path.cwd()
raw_data_dir = project_root / "data" / "raw"

xlsx_raw_file = list(raw_data_dir.glob("*.xlsx"))[0]

if not xlsx_raw_file.exists():
    raise FileNotFoundError(f"Raw data file not found in {raw_data_dir}")
else:
    input_path = xlsx_raw_file

output_path = project_root / "deployment_pipeline" / "data" / "products.csv"

df = pd.read_excel(input_path)

column_mapping = {
    "КлиентДляОплатыКод": "customer_id",
    "ТоварКод": "product_id",
    "Категория": "product_category",
    "БизнесЛиния": "business_line",
    "ДатаПродажи": "purchase_date",
    "Количество": "quantity",
    "Gen_ Bus_ Posting Group": "transaction_type",
    "Gen_ Prod_ Posting Group": "item_type",
}

missing_columns = sorted(set(column_mapping) - set(df.columns))
if missing_columns:
    raise ValueError(f"Missing expected source columns: {missing_columns}")

df = df.rename(columns=column_mapping)

text_columns = [
    "customer_id",
    "product_id",
    "product_category",
    "business_line",
    "transaction_type",
    "item_type",
]

for column in text_columns:
    df[column] = df[column].astype("string").str.strip()

df["purchase_date"] = pd.to_datetime(df["purchase_date"], errors="coerce")
df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")

purchase_mask = (
    df["customer_id"].notna()
    & df["product_id"].notna()
    & df["purchase_date"].notna()
    & df["item_type"].eq("ТОВАР")
    & df["transaction_type"].eq("ПРОДАЖА")
    & df["quantity"].gt(0)
    & df["product_id"].str.startswith('ТОВ', na=False)
)

df = df.loc[purchase_mask].copy()

user = random.choice(df['customer_id'].unique())
products = df['product_id'].unique()

df = df[df['customer_id'] == user]

grouped = (
    df.groupby(
        ["product_id", "purchase_date"],
        sort=False,
        as_index=False,
    )
    .agg(
        quantity=("quantity", "sum"),
        business_line=("business_line", "first"),
        product_category=("product_category", "first"),
    )
    .sort_values(["purchase_date", "product_id"])
    .reset_index(drop=True)
)

def eval_by_history(user_data: pd.DataFrame, products: list):
    #products_histories = {'prod_id': {'key1': 'val1', ...}}
    for product in products:
        groups = (
            grouped
            .groupby(['product_id'], sort=False, as_index=False)
        )