import polars as pl
from sqlalchemy import create_engine, text
import polars as pl
import kagglehub
import os
from db_data_agent.controller import UtilsABC

class ETLController(UtilsABC):
    """
    Responsible of running EXTRACT, TRANSFORM, LOAD on given dataset.
    """

    def __init__(self):
        self.raw_data = os.path.join(os.getcwd(), "db_data_agent/etl/pulled_data")
        super(UtilsABC, self).__init__()
    
    def etl(self, amazon=True, spotify=True):

        if amazon:
            amazon_df = self.extract_amazon()
            amazon_transformed = self.transform_amazon(in_df=amazon_df)
            self.load_amazon(amazon_transformed)
        
        if spotify:
            spotify_df = self.extract_spotify()
            spotify_transformed = self.transform_spotify(in_df=spotify_df)
            self.load_spotify(spotify_transformed)

    def extract_amazon(self):
         out_df = pl.read_csv(os.path.join(self.raw_data, "Amazon_bestsellers_items_2025.csv"), encoding="utf8")
         return out_df
    
    def transform_amazon(self, in_df):
        country_mapping_df = pl.read_database("SELECT * FROM amazon.countryMapping;", self.engine)

        mid_df = in_df.rename({"country": "code"})

        mid_df = mid_df.join(
            country_mapping_df,
            on=["code"],
            how="inner"
        )
        
        mid_df = mid_df.rename({
            "code": "country_abr",
            "name": "full_country_name",
            "asin": "product_id"
            }
        )

        final_df = mid_df.with_columns(
            (pl.col("product_price")
            .str.replace_all(r"[\$₹€￥]", "")
            .str.replace_all(",", "")
            .str.strip_chars()
            .cast(pl.Float64)
            .alias("product_price"))
        )

        pl.Config.set_tbl_rows(10)
        pl.Config.set_tbl_width_chars(120)

        self._print_schema("final_df (input)", final_df)
        
        return final_df

    def load_amazon(self, df):
        print(df.columns[0])
        final_df = df.drop(df.columns[0])
        final_df = final_df.to_pandas()

        final_df.to_sql(
            "best_sellers",     
            con=self.engine,         
            if_exists="replace",    
            schema="amazon",
            index=False
        )
        
        return
    
    def extract_spotify(self):
        out_df = pl.read_csv(os.path.join(self.raw_data, "spotify_churn_dataset.csv"), encoding="utf8")
        return out_df
    
    def transform_spotify(self, in_df):
        country_mapping_df = pl.read_database("SELECT * FROM spotify.countries;", self.engine)

        mid_df = in_df.rename({"country": "country_abr"})

        final_df = mid_df.join(
            country_mapping_df,
            on=["country_abr"],
            how="inner"
        )

        pl.Config.set_tbl_rows(10)
        pl.Config.set_tbl_width_chars(120)

        self._print_schema("final_df (input)", final_df)
        
        return final_df

    def load_spotify(self, df):
        print(df.columns[0])
        final_df = df.drop(df.columns[0])
        final_df = final_df.to_pandas()

        final_df.to_sql(
            "churn_dataset",     
            con=self.engine,         
            if_exists="replace",    
            schema="spotify",
            index=False
        )
        
        return

    def _print_schema(self, name: str, df: pl.DataFrame, preview: int = 5):
        print(f"\n=== {name} ===")
        print("Columns & dtypes:")
        for col, dtype in df.schema.items():
            print(f"  - {col}: {dtype}")
        print(f"\n{name} preview (first {preview} rows):")
        print(df.head(preview))