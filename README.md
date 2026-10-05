# Data Agent

Data Agent is a Python-based business intelligence assistant designed to help teams explore PostgreSQL data through natural-language questions, AI-generated SQL, and interactive reporting workflows.

## Product overview

This project turns raw database information into a faster, more intuitive decision-making experience. Instead of requiring users to write SQL manually, the system interprets business questions, generates the corresponding database query, runs it in PostgreSQL, and returns an answer with the relevant data context.

It is especially useful for teams that need to:

- answer operational questions quickly without relying on analysts for every request
- explore business datasets through a conversational interface
- validate trends, churn, sales, and performance metrics with real database data
- reduce friction between business teams and technical data infrastructure

## Why it matters

Most organizations have plenty of data, but not everyone can access it easily. Data Agent bridges that gap by combining:

- PostgreSQL data storage and querying
- AI-powered SQL generation
- ETL support for structured datasets
- a lightweight web interface for product-like interaction
- a clean environment-based configuration model for secure deployment

## Core capabilities

- Connects to PostgreSQL databases using environment variables
- Loads and transforms local datasets from CSV sources
- Builds SQL queries from natural-language prompts
- Executes queries against structured business data
- Returns human-readable explanations and previews of query results
- Supports multiple dataset workflows, including Amazon bestsellers and Spotify churn analysis
- Runs through both CLI and web-based entry points
- Keeps secrets out of source control through a local `.env` file

## Project structure

```text
.
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── main.py
├── launcher.py
├── commands.sh
├── data_agent/
│   ├── __init__.py
│   ├── controller.py
│   ├── launcher.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── controller.py
│   │   └── template/
│   └── etl/
│       ├── __init__.py
│       └── controller.py
└── workspace.ipynb
```

## Use cases

- business teams asking questions such as “which products sold the most?”
- startup teams validating customer or churn metrics
- analysts prototyping data queries faster
- internal tools that need AI-assisted access to structured data

## Requirements

- Python 3.10+
- PostgreSQL database
- OpenAI-compatible API key

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment configuration

Create a local `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Then update the values with your own credentials:

```env
PGUSER=postgres
PGPASSWORD=your_db_password
PGHOST=localhost
PGPORT=5432
PGDATABASE=postgres

OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_URL=https://api.openai.com/v1/chat/completions
OPENAI_MODEL=gpt-4o-mini
```

## Running the app

Start the project:

```bash
python main.py
```

Or run the launcher:

```bash
python launcher.py
```

## Useful commands

```bash
./commands.sh help
./commands.sh install
./commands.sh start-web
./commands.sh stop-web
```

## Security notes

- Never commit the real `.env` file
- Keep secrets in local environment variables only
- Always use `.env.example` as the public reference template

## License

This project is intended for educational, internal, and prototype use. Update the license as needed before public or production distribution.
