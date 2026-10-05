import os
import re
import json
from dotenv import load_dotenv
import requests
import polars as pl
from sqlalchemy import create_engine, text
from decimal import Decimal
from data_agent.controller import UtilsABC

load_dotenv()

class AgentController(UtilsABC):
    def __init__(self):
        super(UtilsABC, self).__init__()
        self.gpt_api_url = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
        self.gpt_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        

    def _convert_decimals_to_float(self, data):
        """convert decimal objects to float for json serialization"""
        if isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, dict):
            return {key: self._convert_decimals_to_float(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_decimals_to_float(item) for item in data]
        else:
            return data

    def build_prompt(self, user_question: str, teaching_mode: int = 0, user_group: str = "amazon") -> str:
        # filter tables based on the user_group
        schema_filter = "amazon" if user_group == "amazon" else "spotify"
        
        with self.engine.connect() as conn:
            tables = conn.execute(
                text(f"SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema = '{schema_filter}'")
            )
        
        schema_desc = "\n".join([f"{s}.{t}" for s, t in tables])
        
        if user_group == "amazon":
            schema_description = """
                column names in the "best_sellers" database, with the column names before the "=" sign and their descriptions after:
                rank = shows the product rank in the best-seller list (from 1 to 1000)
                product_id = standard amazon product identifier (unique product id)
                product_title = full product name and description
                product_price = product price
                product_star_rating = customer satisfaction rating (from 1 to 5 stars)
                product_num_ratings = total number of customer reviews
                product_url = link to the amazon product page
                product_photo = product image url
                rank_change_label = ranking movement indicator
                country_abr = two-letter country/market abbreviation
                page = pagination reference number
                full_country_name = full country/market name
            """
        else:
            schema_description = """
                column names in the "churn_dataset" database, with the column names before the "=" sign and their descriptions after:
                user_id = unique user identifier in the dataset.
                gender = user gender (for example: male, female, other).
                age = user age (numeric value).
                country_abr = user country abbreviation (for example: US, BR, CA).
                full_country_name = full country name corresponding to the abbreviation.
                subscription_type = user subscription type (for example: free, premium, family, student).
                listening_time = total listening time over a defined period (for example: minutes or hours per month).
                songs_played_per_day = average number of songs played per day.
                skip_rate = average percentage of songs skipped by the user.
                device_type = main device type used (for example: mobile, desktop, smart speaker).
                ads_listened_per_week = number of ads listened to per week.
                offline_listening = indicates whether the user listens offline (yes/no or 1/0).
                is_churned = indicates whether the user churned or left the service (1 = churned, 0 = active).
            """

        database_name = "2025 Amazon bestsellers" if user_group == "amazon" else "Spotify churn dataset"
        
        if teaching_mode == 1:
            sql_prompt = (
                f"you are an agent that answers questions about a Postgres database for {database_name} and teaches how to build queries for it.\n"
                f"when responding:\n"
                f"- if SQL is needed, return the SQL query and a technical explanation of the query in the 'query-explanation' field.\n"
                f"- if the question does not require SQL, return only a textual answer in the 'explanation' field and set the SQL to 'the question does not involve a query or the SQL is invalid'.\n\n"
                f"always respond strictly in JSON using this format:\n"
                f"generate a detailed textual explanation in the 'explanation' field to teach someone who wants to learn more about SQL\n"
                f"{{\"sql\": ..., \"query-explanation\": ..., \"explanation\": ...}}\n\n"
                f"detected schema:\n{schema_desc}\n\n"
                f"use only the columns included in {schema_description}\n\n"
                f"question: {user_question}\n"
            )
        else:
            sql_prompt = (
                f"you are an agent that answers questions about a Postgres database for {database_name}.\n"
                f"when responding:\n"
                f"- if SQL is needed, return the SQL query and a technical explanation of the query in the 'query-explanation' field.\n"
                f"- if the question does not require SQL, return only a textual answer in the 'explanation' field and set the SQL to 'the question does not involve a query or the SQL is invalid'.\n\n"
                f"always respond strictly in JSON using this format:\n"
                f"{{\"sql\": ..., \"query-explanation\": ..., \"explanation\": ...}}\n\n"
                f"detected schema:\n{schema_desc}\n\n"
                f"use only the columns included in {schema_description}\n\n"
                f"question: {user_question}\n"
            )

        return sql_prompt

    def _strip_code_block(self, s: str) -> str:
        if not s or not isinstance(s, str):
            return s
        s = s.strip()
        s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\s*```$", "", s)
        return s.strip()

    def _parse_json_response(self, content: str):
        if not content or not isinstance(content, str):
            return None

        try:
            return json.loads(content)
        except Exception:
            pass

        stripped = self._strip_code_block(content)
        try:
            return json.loads(stripped)
        except Exception:
            pass

        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = stripped[start:end+1]
            try:
                return json.loads(candidate)
            except Exception:
                pass

        return None

    def gpt(self, build_: str) -> dict:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.gpt_model,
            "messages": [{"role": "user", "content": build_}],
            "temperature": 0.0,
        }
        r = requests.post(self.gpt_api_url, headers=headers, json=payload)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        
        parsed = self._parse_json_response(content)
        return parsed if parsed is not None else {}

    def generate_data_explanation(self, question: str, sql: str, df: pl.DataFrame) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        
        n_rows = df.shape[0]
        n_cols = df.shape[1]
        columns = df.columns
        
        if n_rows == 0:
            data_info = "the query returned no results."
        elif n_rows <= 10:
            data_sample = self._convert_decimals_to_float(df.to_dicts())
            data_info = f"the query returned {n_rows} record(s) with {n_cols} column(s): {', '.join(columns)}\n\nfull data:\n{json.dumps(data_sample, indent=2, ensure_ascii=False)}"
        else:
            data_sample = self._convert_decimals_to_float(df.head(5).to_dicts())
            data_info = f"the query returned {n_rows} records with {n_cols} column(s): {', '.join(columns)}\n\nfirst 5 records:\n{json.dumps(data_sample, indent=2, ensure_ascii=False)}"

            numeric_stats = []
            for col in columns:
                try:
                    if df[col].dtype in [pl.Int32, pl.Int64, pl.Float32, pl.Float64]:
                        stats = df[col].describe()
                        numeric_stats.append(f"column {col}: min={stats['min']}, max={stats['max']}, avg={stats['mean']:.2f}")
                except:
                    pass

            if numeric_stats:
                data_info += f"\n\nstatistics for numeric columns:\n" + "\n".join(numeric_stats)

        prompt = (
                f"original user question: {question}\n\n"
                f"SQL query executed:\n{sql}\n\n"
                f"data obtained from execution:\n{data_info}\n\n"
                "based on the real data obtained from the SQL query execution, generate a clear and direct explanation in natural language that:\n"
                "1. answers the original question clearly\n"
                "2. mentions specific data points and concrete numbers\n"
                "3. remains concise and factual without speculative interpretation\n\n"
                "return only the explanatory text in natural language (no JSON, no code fences). "
                "keep the tone neutral and informative."
        )
        
        payload = {
            "model": self.gpt_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0
        }
        
        try:
            r = requests.post(self.gpt_api_url, headers=headers, json=payload)
            r.raise_for_status()
            explanation_text = r.json()["choices"][0]["message"]["content"]
            return explanation_text.strip() or "it was not possible to generate an explanation based on the data."
        except Exception as e:
            return f"error generating the explanation from the data: {str(e)}"

    def safe_sql(self, sql: str) -> bool:
        if not sql or not isinstance(sql, str):
            return False
        sql_lower = sql.lower().strip()
        return sql_lower.startswith("select") and ";" in sql_lower


    def execute_sql(self, sql: str) -> pl.DataFrame:
        with self.engine.connect() as conn:
            df = pl.read_database(query=text(sql), connection=conn)
        
        return df

    def prepare_preview(self, df: pl.DataFrame) -> dict:
        n_rows = df.shape[0]
        
        if n_rows == 0:
            return {"message": "no results found", "data": []}
        elif n_rows <= 20:
            return {"total_records": n_rows, "data": self._convert_decimals_to_float(df.to_dicts())}
        else:
            return {
                "total_records": n_rows,
                "sample_first_10_rows": self._convert_decimals_to_float(df.head(10).to_dicts()),
                "message": f"showing only the first 10 of {n_rows} rows found"
            }

    def run(self, question: str, user_group: str = "amazon"):
        print("starting the agent...")
        
        build_prompt = self.build_prompt(question, user_group=user_group)
        gpt_response = self.gpt(build_prompt)

        sql_raw = gpt_response.get("sql")
        query_explanation = gpt_response.get("query-explanation") or gpt_response.get("query_explanation") or ""
        initial_explanation = gpt_response.get("explanation") or ""
        if not sql_raw or not self.safe_sql(sql_raw):

            result = {
                "sql": "the question does not require a query or the SQL is invalid",
                "query-explanation": query_explanation,
                "explanation": initial_explanation or "it was not possible to generate a SQL query for this question.",
                "preview": {"message": "no query was executed", "data": []}
            }
            
            for key, value in result.items():
                print(f"\n\"{key}\": \"{value}\"")
            return
            
        try:
            df = self.execute_sql(sql_raw)
            execution_status = f"{sql_raw}\nquery executed successfully. returned {df.shape[0]} rows and {df.shape[1]} columns."
            data_based_explanation = self.generate_data_explanation(question, sql_raw, df)
            preview = df.head()

            preview_results = {
                "sql": sql_raw,
                "query-explanation": query_explanation,
                "explanation": data_based_explanation,
                "query-execution-status": execution_status,
                "preview": preview
            }
            
            for key, value in preview_results.items():
                print(f"\n\"{key}\": \"{value}\"")

            return
        
        except Exception as e:
            error_msg = f"error executing the query: {str(e)}"
            print(f"\n\"query-execution-status\": \"{error_msg}\"")

            exception_results = {
                "sql": sql_raw,
                "query-explanation": query_explanation,
                "explanation": f"{error_msg}. {initial_explanation}" if initial_explanation else error_msg,
                "query-execution-status": error_msg,
                "preview": {"message": "execution error", "data": [], "error": str(e)}
            }
            
            for key, value in exception_results.items():
                print(f"\n\"{key}\": \"{value}\"")
            return

    def run_return(self, question: str, teaching_mode: int = 0, user_group: str = "amazon") -> dict:
        build_prompt = self.build_prompt(question, teaching_mode, user_group)
        gpt_response = self.gpt(build_prompt)

        sql_raw = (gpt_response or {}).get("sql")
        query_explanation = (
            (gpt_response or {}).get("query-explanation")
            or (gpt_response or {}).get("query_explanation")
            or ""
        )
        initial_explanation = (gpt_response or {}).get("explanation") or ""

        if not sql_raw or not self.safe_sql(sql_raw):
            return {
                "sql": "the question does not require a query or the SQL is invalid",
                "query-explanation": query_explanation,
                "explanation": initial_explanation or "it was not possible to generate a SQL query for this question.",
                "query-execution-status": "no query executed",
                "preview": {"message": "no query was executed", "data": []},
            }

        try:
            df = self.execute_sql(sql_raw)
            execution_status = f"{sql_raw}\nquery executed successfully. returned {df.shape[0]} rows and {df.shape[1]} columns."
            data_based_explanation = self.generate_data_explanation(question, sql_raw, df)
            preview = self.prepare_preview(df)

            return {
                "sql": sql_raw,
                "query-explanation": query_explanation,
                "explanation": data_based_explanation,
                "query-execution-status": execution_status,
                "preview": preview,
            }
        except Exception as e:
            error_msg = f"error executing the query: {str(e)}"
            return {
                "sql": sql_raw,
                "query-explanation": query_explanation,
                "explanation": f"{error_msg}. {initial_explanation}" if initial_explanation else error_msg,
                "query-execution-status": error_msg,
                "preview": {"message": "execution error", "data": [], "error": str(e)},
            }