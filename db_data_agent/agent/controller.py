import os
import re
import json
import requests
import polars as pl
from sqlalchemy import create_engine, text
from decimal import Decimal
from db_data_agent.controller import UtilsABC

class AgentController(UtilsABC):
    def __init__(self):
        super(UtilsABC, self).__init__()
        self.gpt_api_url = "https://api.openai.com/v1/chat/completions"
        self.gpt_model = "gpt-4o-mini"
        self.api_key = "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"
        

    def _convert_decimals_to_float(self, data):
        """Converte objetos Decimal em float para serialização JSON"""
        if isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, dict):
            return {key: self._convert_decimals_to_float(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_decimals_to_float(item) for item in data]
        else:
            return data

    def build_prompt(self, user_question: str, teaching_mode: int = 0, user_group: str = "amazon") -> str:
        # Filtra tabelas baseado no user_group
        schema_filter = "amazon" if user_group == "amazon" else "spotify"
        
        with self.engine.connect() as conn:
            tables = conn.execute(
                text(f"SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema = '{schema_filter}'")
            )
        
        schema_desc = "\n".join([f"{s}.{t}" for s, t in tables])
        
        if user_group == "amazon":
            schema_description = """
                Nome colunas do database "best_sellers", as colunas antes do sinal "=" e as descrições dessas colunas após:
                rank = traz a posição do best seller no ranking (de 1 a 1000)
                product_id = número de identificação padrão da amazon (id único do produto)                                
                product_title = nome completo e descrição do produto                  
                product_price = preço do produto
                product_star_rating = avaliação de satisfação do cliente (de 1 a 5 estrelas)
                product_num_ratings = número total de avaliações de clientes
                product_url = link para a página do produto da amazon
                product_photo = URL da imagem do produto
                rank_change_label = indicador de movimento no ranking
                country_abr = abreviação do país/mercado em duas letras
                page = número de referência da páginação dos dados
                full_country_name = nome completo do país/mercado 
            """
        else:  
            schema_description = """
                Nome colunas do database "churn_dataset", as colunas antes do sinal "=" e as descrições dessas colunas após:
                user_id = Identificador único do usuário na base de dados.
                gender = Gênero do usuário (ex.: masculino, feminino, outro).
                age = Idade do usuário (valor numérico).
                country_abr = Abreviação do país do usuário (ex.: US, BR, CA).
                full_country_name = Nome completo do país correspondente à abreviação.
                subscription_type = Tipo de assinatura do usuário (ex.: free, premium, family, student).
                listening_time = Tempo total de escuta em um período determinado (ex.: minutos ou horas por mês).
                songs_played_per_day = Quantidade média de músicas ouvidas por dia.
                skip_rate = Percentual médio de músicas que o usuário pula.
                device_type = Tipo de dispositivo principal utilizado (ex.: mobile, desktop, smart speaker).
                ads_listened_per_week = Quantidade de propagandas ouvidas por semana.
                offline_listening = Indica se o usuário escuta músicas offline (sim/não ou 1/0).
                is_churned = Indica se o usuário cancelou ou abandonou o serviço (1 = churn, 0 = ativo).
            """

        database_name = "2025 Amazon bestsellers" if user_group == "amazon" else "Spotify churn dataset"
        
        if teaching_mode == 1:
            sql_prompt = (
                f"Você é um agente que responde perguntas sobre um banco Postgres sobre {database_name} e ensina a criar queries sobre\n"
                f"Quando responder:\n"
                f"- Se for necessário SQL, retorne a query SQL e uma explicação técnica da consulta (campo 'query-explanation').\n"
                f"- Se a pergunta não envolver SQL, retorne apenas uma resposta textual no campo 'explanation' e defina o SQL como 'a pergunta não envolve uma consulta ou o SQL é inválido'.\n\n"
                f"Sempre responda estritamente em JSON no formato:\n"
                f"Gere uma resposta textual em explanation detalhada para ensinar a alguém que queira aprendermais sobre SQL\n"
                f"{{\"sql\": ..., \"query-explanation\": ..., \"explanation\": ...}}\n\n"
                f"Esquema detectado:\n{schema_desc}\n\n"
                f"Use estritamente as colunas inclusas em {schema_description}\n\n"
                f"Pergunta: {user_question}\n"
            )
        else: 
            sql_prompt = (
                f"Você é um agente que responde perguntas sobre um banco Postgres sobre {database_name}.\n"
                f"Quando responder:\n"
                f"- Se for necessário SQL, retorne a query SQL e uma explicação técnica da consulta (campo 'query-explanation').\n"
                f"- Se a pergunta não envolver SQL, retorne apenas uma resposta textual no campo 'explanation' e defina o SQL como 'a pergunta não envolve uma consulta ou o SQL é inválido'.\n\n"
                f"Sempre responda estritamente em JSON no formato:\n"
                f"{{\"sql\": ..., \"query-explanation\": ..., \"explanation\": ...}}\n\n"
                f"Esquema detectado:\n{schema_desc}\n\n"
                f"Use estritamente as colunas inclusas em {schema_description}\n\n"
                f"Pergunta: {user_question}\n"
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
            data_info = "A query não retornou nenhum resultado."
        elif n_rows <= 10:
            data_sample = self._convert_decimals_to_float(df.to_dicts())
            data_info = f"A query retornou {n_rows} registro(s) com {n_cols} coluna(s): {', '.join(columns)}\n\nDados completos:\n{json.dumps(data_sample, indent=2, ensure_ascii=False)}"
        else:
            data_sample = self._convert_decimals_to_float(df.head(5).to_dicts())
            data_info = f"A query retornou {n_rows} registros com {n_cols} coluna(s): {', '.join(columns)}\n\nPrimeiros 5 registros:\n{json.dumps(data_sample, indent=2, ensure_ascii=False)}"
            
            numeric_stats = []
            for col in columns:
                try:
                    if df[col].dtype in [pl.Int32, pl.Int64, pl.Float32, pl.Float64]:
                        stats = df[col].describe()
                        numeric_stats.append(f"Coluna {col}: mín={stats['min']}, máx={stats['max']}, média={stats['mean']:.2f}")
                except:
                    pass
            
            if numeric_stats:
                data_info += f"\n\nEstatísticas das colunas numéricas:\n" + "\n".join(numeric_stats)

        prompt = (
                f"PERGUNTA ORIGINAL DO USUÁRIO: {question}\n\n"
                f"QUERY SQL EXECUTADA:\n{sql}\n\n"
                f"DADOS OBTIDOS DA EXECUÇÃO:\n{data_info}\n\n"
                "Com base nos dados REAIS obtidos da execução da query SQL, gere uma explicação objetiva e direta em linguagem natural que:\n"
                "1. Responda à pergunta original de forma clara\n"
                "2. Mencione dados específicos e números concretos\n"
                "3. Seja concisa e factual, sem interpretações especulativas\n\n"
                "Retorne APENAS o texto explicativo em linguagem natural (sem JSON, sem marcação de código). "
                "Mantenha o tom neutro e informativo."
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
            return explanation_text.strip() or "Não foi possível gerar uma explicação baseada nos dados."
        except Exception as e:
            return f"Erro ao gerar explicação baseada nos dados: {str(e)}"

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
            return {"message": "Nenhum resultado encontrado", "data": []}
        elif n_rows <= 20:
            return {"total_registros": n_rows, "data": self._convert_decimals_to_float(df.to_dicts())}
        else:
            return {
                "total_registros": n_rows,
                "amostra_primeiras_10_linhas": self._convert_decimals_to_float(df.head(10).to_dicts()),
                "message": f"Mostrando apenas as primeiras 10 de {n_rows} linhas encontradas"
            }

    def run(self, question: str, user_group: str = "amazon"):
        print("Iniciando agente...")
        
        build_prompt = self.build_prompt(question, user_group=user_group)
        gpt_response = self.gpt(build_prompt)

        sql_raw = gpt_response.get("sql")
        query_explanation = gpt_response.get("query-explanation") or gpt_response.get("query_explanation") or ""
        initial_explanation = gpt_response.get("explanation") or ""
        if not sql_raw or not self.safe_sql(sql_raw):
            
            result = {
                "sql": "a pergunta não envolve uma consulta ou o SQL é inválido",
                "query-explanation": query_explanation,
                "explanation": initial_explanation or "Não foi possível gerar uma consulta SQL para esta pergunta.",
                "preview": {"message": "Nenhuma query foi executada", "data": []}
            }
            
            for key, value in result.items():
                print(f"\n\"{key}\": \"{value}\"")
            return
            
        try:
            df = self.execute_sql(sql_raw)
            execution_status = f"{sql_raw}\nQuery executada com sucesso. Retornou {df.shape[0]} linhas e {df.shape[1]} colunas."
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
            error_msg = f"Erro ao executar a consulta: {str(e)}"
            print(f"\n\"query-execution-status\": \"{error_msg}\"")
            
            exception_results = {
                "sql": sql_raw,
                "query-explanation": query_explanation,
                "explanation": f"{error_msg}. {initial_explanation}" if initial_explanation else error_msg,
                "query-execution-status": error_msg,
                "preview": {"message": "Erro na execução", "data": [], "error": str(e)}
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
                "sql": "a pergunta não envolve uma consulta ou o SQL é inválido",
                "query-explanation": query_explanation,
                "explanation": initial_explanation or "Não foi possível gerar uma consulta SQL para esta pergunta.",
                "query-execution-status": "Nenhuma query executada",
                "preview": {"message": "Nenhuma query foi executada", "data": []},
            }

        try:
            df = self.execute_sql(sql_raw)
            execution_status = f"{sql_raw}\nQuery executada com sucesso. Retornou {df.shape[0]} linhas e {df.shape[1]} colunas."
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
            error_msg = f"Erro ao executar a consulta: {str(e)}"
            return {
                "sql": sql_raw,
                "query-explanation": query_explanation,
                "explanation": f"{error_msg}. {initial_explanation}" if initial_explanation else error_msg,
                "query-execution-status": error_msg,
                "preview": {"message": "Erro na execução", "data": [], "error": str(e)},
            }