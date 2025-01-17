
# Simple private dictonary
API for creating own Polish-English dictionary.
The database stores words/sentences in English (word table) and their descriptions in Polish (description table).

User can add new words (full CRUD) with specifying the master level for each word separately (how well the user knows the word). Default value is set to NEW level (with default weight of 1.0). Each master level has its own default weight:
- NEW level: 1.0
- MEDIUM level: 0.8
- PERFECT level: 0.3
- HARD level: 1.5
 The user can also set their own weights for each master level (with a maximum value of 5.0).
 The weights are used for the endpoint where user can perform random choices method on words for repetition purpose (shuffle router).

For each word, the user can add multiple descriptions (translations, full CRUD). One description can also be used to define multiple words.

## Required
Python3.12

Database connection in PostgreSQL with separate database for prod/dev environment (dict) and for test environment (dict_test).


Installed libraries:
1. pip install "fastapi[standard]"
    - installed MarkupSafe-2.1.5 annotated-types-0.7.0 anyio-4.4.0 certifi-2024.8.30 click-8.1.7 dnspython-2.6.1 email-validator-2.2.0 fastapi-0.114.1 fastapi-cli-0.0.5 h11-0.14.0 httpcore-1.0.5 httptools-0.6.1 httpx-0.27.2 idna-3.8 jinja2-3.1.4 markdown-it-py-3.0.0 mdurl-0.1.2 pydantic-2.9.1 pydantic-core-2.23.3 pygments-2.18.0 python-dotenv-1.0.1 python-multipart-0.0.9 pyyaml-6.0.2 rich-13.8.1 shellingham-1.5.4 sniffio-1.3.1 starlette-0.38.5 typer-0.12.5 typing-extensions-4.12.2 uvicorn-0.30.6 uvloop-0.20.0 watchfiles-0.24.0 websockets-13.0.1
2. pip install SQLAlchemy
    - installed SQLAlchemy-2.0.34 greenlet-3.1.0
3. pip install pydantic-settings
    - installed pydantic-settings-2.5.2
4. pip install psycopg2-binary
    - installed psycopg2-binary-2.9.9
5. pip install alembic
    - installed Mako-1.3.5 alembic-1.13.2
6. pip install pytest
    - installed iniconfig-2.0.0 packaging-24.1 pluggy-1.5.0 pytest-8.3.3
7. pip install pytest-asyncio
    - installed pytest-asyncio-0.24.0
