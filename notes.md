
s-bas@Brad_Laptop MINGW64 ~/Codepath AI201/pathreview (main)
$ winget install GnuWin32.Make
Found an existing package already installed. Trying to upgrade the installed package...
No available upgrade found.
No newer package versions are available from the configured sources.

s-bas@Brad_Laptop MINGW64 ~/Codepath AI201/pathreview (main)
$ echo 'export PATH="$PATH:/c/Program Files (x86)/GnuWin32/bin"' >> ~/.bashrc

s-bas@Brad_Laptop MINGW64 ~/Codepath AI201/pathreview (main)
$ source ~/.bashrc

s-bas@Brad_Laptop MINGW64 ~/Codepath AI201/pathreview (main)
$ make setup
python -m venv .venv || python3 -m venv .venv
.venv/Scripts/python -m pip install --upgrade pip setuptools wheel
Requirement already satisfied: pip in c:\users\s-bas\codepath ai201\pathreview\.venv\lib\site-packages (25.2)
Collecting pip
  Using cached pip-26.1.2-py3-none-any.whl.metadata (4.6 kB)
Collecting setuptools
  Downloading setuptools-83.0.0-py3-none-any.whl.metadata (6.6 kB)
Collecting wheel
  Downloading wheel-0.47.0-py3-none-any.whl.metadata (2.3 kB)
Collecting packaging>=24.0 (from wheel)
  Using cached packaging-26.2-py3-none-any.whl.metadata (3.5 kB)
Using cached pip-26.1.2-py3-none-any.whl (1.8 MB)
Downloading setuptools-83.0.0-py3-none-any.whl (1.0 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.0/1.0 MB 20.7 MB/s  0:00:00
Downloading wheel-0.47.0-py3-none-any.whl (32 kB)
Using cached packaging-26.2-py3-none-any.whl (100 kB)
Installing collected packages: setuptools, pip, packaging, wheel
  Attempting uninstall: pip
    Found existing installation: pip 25.2
    Uninstalling pip-25.2:
      Successfully uninstalled pip-25.2
Successfully installed packaging-26.2 pip-26.1.2 setuptools-83.0.0 wheel-0.47.0
.venv/Scripts/pip install -e ".[dev]"
Obtaining file:///C:/Users/s-bas/Codepath%20AI201/pathreview
  Installing build dependencies ... done
  Checking if build backend supports build_editable ... done
  Getting requirements to build editable ... done
  Preparing editable metadata (pyproject.toml) ... done
Collecting fastapi>=0.109.0 (from pathreview==0.1.0)
  Downloading fastapi-0.139.2-py3-none-any.whl.metadata (26 kB)
Collecting uvicorn>=0.25.0 (from uvicorn[standard]>=0.25.0->pathreview==0.1.0)
  Downloading uvicorn-0.51.0-py3-none-any.whl.metadata (6.6 kB)
Collecting sqlalchemy>=2.0.0 (from pathreview==0.1.0)
  Using cached sqlalchemy-2.0.51-cp314-cp314-win_amd64.whl.metadata (9.8 kB)
Collecting alembic>=1.13.0 (from pathreview==0.1.0)
  Downloading alembic-1.18.5-py3-none-any.whl.metadata (7.2 kB)
Collecting psycopg2-binary>=2.9.9 (from pathreview==0.1.0)
  Downloading psycopg2_binary-2.9.12-cp314-cp314-win_amd64.whl.metadata (5.1 kB)
Collecting asyncpg>=0.29.0 (from pathreview==0.1.0)
  Downloading asyncpg-0.31.0-cp314-cp314-win_amd64.whl.metadata (4.5 kB)
Collecting greenlet>=3.0.0 (from pathreview==0.1.0)
  Using cached greenlet-3.5.3-cp314-cp314-win_amd64.whl.metadata (3.9 kB)
Collecting pydantic>=2.5.0 (from pydantic[email]>=2.5.0->pathreview==0.1.0)
  Using cached pydantic-2.13.4-py3-none-any.whl.metadata (109 kB)
Collecting pydantic-settings>=2.1.0 (from pathreview==0.1.0)
  Downloading pydantic_settings-2.14.2-py3-none-any.whl.metadata (3.4 kB)
Collecting python-multipart>=0.0.6 (from pathreview==0.1.0)
  Using cached python_multipart-0.0.32-py3-none-any.whl.metadata (2.1 kB)
Collecting python-jose>=3.3.0 (from python-jose[cryptography]>=3.3.0->pathreview==0.1.0)
  Downloading python_jose-3.5.0-py2.py3-none-any.whl.metadata (5.5 kB)
Collecting passlib>=1.7.4 (from passlib[bcrypt]>=1.7.4->pathreview==0.1.0)
  Downloading passlib-1.7.4-py2.py3-none-any.whl.metadata (1.7 kB)
Collecting bcrypt<5.0.0,>=4.0.1 (from pathreview==0.1.0)
  Downloading bcrypt-4.3.0-cp39-abi3-win_amd64.whl.metadata (10 kB)
Collecting openai>=1.10.0 (from pathreview==0.1.0)
  Downloading openai-2.46.0-py3-none-any.whl.metadata (34 kB)
Collecting chromadb>=0.4.22 (from pathreview==0.1.0)
  Using cached chromadb-1.5.9-cp39-abi3-win_amd64.whl.metadata (5.1 kB)
Collecting redis>=5.0.0 (from pathreview==0.1.0)
  Downloading redis-8.0.1-py3-none-any.whl.metadata (13 kB)
Collecting httpx>=0.26.0 (from pathreview==0.1.0)
  Using cached httpx-0.28.1-py3-none-any.whl.metadata (7.1 kB)
Collecting pypdf>=3.17.0 (from pathreview==0.1.0)
  Downloading pypdf-6.14.2-py3-none-any.whl.metadata (7.2 kB)
Collecting tiktoken>=0.5.2 (from pathreview==0.1.0)
  Downloading tiktoken-0.13.0-cp314-cp314-win_amd64.whl.metadata (6.8 kB)
Collecting tenacity>=8.2.0 (from pathreview==0.1.0)
  Using cached tenacity-9.1.4-py3-none-any.whl.metadata (1.2 kB)
Collecting structlog>=24.1.0 (from pathreview==0.1.0)
  Downloading structlog-26.1.0-py3-none-any.whl.metadata (9.7 kB)
Collecting rank-bm25>=0.2.2 (from pathreview==0.1.0)
  Downloading rank_bm25-0.2.2-py3-none-any.whl.metadata (3.2 kB)
Collecting numpy>=1.26.0 (from pathreview==0.1.0)
  Downloading numpy-2.5.1-cp314-cp314-win_amd64.whl.metadata (6.6 kB)
Collecting pytest>=7.4.0 (from pathreview==0.1.0)
  Using cached pytest-9.1.1-py3-none-any.whl.metadata (7.6 kB)
Collecting pytest-cov>=4.1.0 (from pathreview==0.1.0)
  Downloading pytest_cov-7.1.0-py3-none-any.whl.metadata (32 kB)
Collecting pytest-asyncio>=0.23.0 (from pathreview==0.1.0)
  Downloading pytest_asyncio-1.4.0-py3-none-any.whl.metadata (4.1 kB)
Collecting pytest-benchmark>=4.0.0 (from pathreview==0.1.0)
  Downloading pytest_benchmark-5.2.3-py3-none-any.whl.metadata (29 kB)
Collecting pytest-httpserver>=1.0.8 (from pathreview==0.1.0)
  Downloading pytest_httpserver-1.1.5-py3-none-any.whl.metadata (6.2 kB)
Collecting hypothesis>=6.92.0 (from pathreview==0.1.0)
  Downloading hypothesis-6.156.7-cp314-cp314-win_amd64.whl.metadata (5.7 kB)
Collecting ruff>=0.2.0 (from pathreview==0.1.0)
  Downloading ruff-0.15.22-py3-none-win_amd64.whl.metadata (27 kB)
Collecting black>=24.1.0 (from pathreview==0.1.0)
  Downloading black-26.5.1-cp314-cp314-win_amd64.whl.metadata (95 kB)
Collecting mypy>=1.8.0 (from pathreview==0.1.0)
  Downloading mypy-2.3.0-cp314-cp314-win_amd64.whl.metadata (2.4 kB)
Collecting pre-commit>=3.6.0 (from pathreview==0.1.0)
  Downloading pre_commit-4.6.0-py2.py3-none-any.whl.metadata (1.2 kB)
Collecting mutmut>=2.4.4 (from pathreview==0.1.0)
  Downloading mutmut-3.6.0-py3-none-any.whl.metadata (16 kB)
Collecting types-redis>=4.6.0 (from pathreview==0.1.0)
  Downloading types_redis-4.6.0.20241004-py3-none-any.whl.metadata (2.0 kB)
Collecting Mako (from alembic>=1.13.0->pathreview==0.1.0)
  Downloading mako-1.3.12-py3-none-any.whl.metadata (2.9 kB)
Collecting typing-extensions>=4.12 (from alembic>=1.13.0->pathreview==0.1.0)
  Using cached typing_extensions-4.16.0-py3-none-any.whl.metadata (3.3 kB)
Collecting click>=8.0.0 (from black>=24.1.0->pathreview==0.1.0)
  Using cached click-8.4.2-py3-none-any.whl.metadata (2.6 kB)
Collecting mypy-extensions>=0.4.3 (from black>=24.1.0->pathreview==0.1.0)
  Downloading mypy_extensions-1.1.0-py3-none-any.whl.metadata (1.1 kB)
Requirement already satisfied: packaging>=22.0 in .\.venv\Lib\site-packages (from black>=24.1.0->pathreview==0.1.0) (26.2)
Collecting pathspec>=1.0.0 (from black>=24.1.0->pathreview==0.1.0)
  Downloading pathspec-1.1.1-py3-none-any.whl.metadata (14 kB)
Collecting platformdirs>=2 (from black>=24.1.0->pathreview==0.1.0)
  Downloading platformdirs-4.10.1-py3-none-any.whl.metadata (5.5 kB)
Collecting pytokens~=0.4.0 (from black>=24.1.0->pathreview==0.1.0)
  Downloading pytokens-0.4.1-cp314-cp314-win_amd64.whl.metadata (3.9 kB)
Collecting build>=1.0.3 (from chromadb>=0.4.22->pathreview==0.1.0)
  Using cached build-1.5.0-py3-none-any.whl.metadata (5.7 kB)
Collecting pybase64>=1.4.1 (from chromadb>=0.4.22->pathreview==0.1.0)
  Using cached pybase64-1.4.3-cp314-cp314-win_amd64.whl.metadata (9.1 kB)
Collecting onnxruntime>=1.14.1 (from chromadb>=0.4.22->pathreview==0.1.0)
  Downloading onnxruntime-1.27.0-cp314-cp314-win_amd64.whl.metadata (5.6 kB)
Collecting opentelemetry-api>=1.2.0 (from chromadb>=0.4.22->pathreview==0.1.0)
  Downloading opentelemetry_api-1.44.0-py3-none-any.whl.metadata (1.4 kB)
Collecting opentelemetry-exporter-otlp-proto-grpc>=1.2.0 (from chromadb>=0.4.22->pathreview==0.1.0)
  Downloading opentelemetry_exporter_otlp_proto_grpc-1.44.0-py3-none-any.whl.metadata (2.6 kB)
Collecting opentelemetry-sdk>=1.2.0 (from chromadb>=0.4.22->pathreview==0.1.0)
  Downloading opentelemetry_sdk-1.44.0-py3-none-any.whl.metadata (1.6 kB)
Collecting tokenizers>=0.13.2 (from chromadb>=0.4.22->pathreview==0.1.0)
  Using cached tokenizers-0.23.1-cp310-abi3-win_amd64.whl.metadata (10 kB)
Collecting pypika>=0.48.9 (from chromadb>=0.4.22->pathreview==0.1.0)
  Using cached pypika-0.51.1-py2.py3-none-any.whl.metadata (51 kB)
Collecting tqdm>=4.65.0 (from chromadb>=0.4.22->pathreview==0.1.0)
  Downloading tqdm-4.69.0-py3-none-any.whl.metadata (57 kB)
Collecting overrides>=7.3.1 (from chromadb>=0.4.22->pathreview==0.1.0)
  Using cached overrides-7.7.0-py3-none-any.whl.metadata (5.8 kB)
Collecting importlib-resources (from chromadb>=0.4.22->pathreview==0.1.0)
  Using cached importlib_resources-7.1.0-py3-none-any.whl.metadata (4.0 kB)
Collecting grpcio>=1.58.0 (from chromadb>=0.4.22->pathreview==0.1.0)
  Downloading grpcio-1.82.1-cp314-cp314-win_amd64.whl.metadata (3.8 kB)
Collecting typer>=0.9.0 (from chromadb>=0.4.22->pathreview==0.1.0)
  Downloading typer-0.27.0-py3-none-any.whl.metadata (15 kB)
Collecting kubernetes>=28.1.0 (from chromadb>=0.4.22->pathreview==0.1.0)
  Downloading kubernetes-36.0.3-py2.py3-none-any.whl.metadata (1.8 kB)
Collecting pyyaml>=6.0.0 (from chromadb>=0.4.22->pathreview==0.1.0)
  Using cached pyyaml-6.0.3-cp314-cp314-win_amd64.whl.metadata (2.4 kB)
Collecting mmh3>=4.0.1 (from chromadb>=0.4.22->pathreview==0.1.0)
  Using cached mmh3-5.2.1-cp314-cp314-win_amd64.whl.metadata (15 kB)
Collecting orjson>=3.9.12 (from chromadb>=0.4.22->pathreview==0.1.0)
  Using cached orjson-3.11.9-cp314-cp314-win_amd64.whl.metadata (43 kB)
Collecting rich>=10.11.0 (from chromadb>=0.4.22->pathreview==0.1.0)
  Using cached rich-15.0.0-py3-none-any.whl.metadata (18 kB)
Collecting jsonschema>=4.19.0 (from chromadb>=0.4.22->pathreview==0.1.0)
  Using cached jsonschema-4.26.0-py3-none-any.whl.metadata (7.6 kB)
Collecting pyproject_hooks (from build>=1.0.3->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached pyproject_hooks-1.2.0-py3-none-any.whl.metadata (1.3 kB)
Collecting colorama (from build>=1.0.3->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached colorama-0.4.6-py2.py3-none-any.whl.metadata (17 kB)
Collecting starlette>=0.46.0 (from fastapi>=0.109.0->pathreview==0.1.0)
  Using cached starlette-1.3.1-py3-none-any.whl.metadata (6.4 kB)
Collecting typing-inspection>=0.4.2 (from fastapi>=0.109.0->pathreview==0.1.0)
  Using cached typing_inspection-0.4.2-py3-none-any.whl.metadata (2.6 kB)
Collecting annotated-doc>=0.0.2 (from fastapi>=0.109.0->pathreview==0.1.0)
  Using cached annotated_doc-0.0.4-py3-none-any.whl.metadata (6.6 kB)
Collecting anyio (from httpx>=0.26.0->pathreview==0.1.0)
  Downloading anyio-4.14.2-py3-none-any.whl.metadata (4.6 kB)
Collecting certifi (from httpx>=0.26.0->pathreview==0.1.0)
  Using cached certifi-2026.6.17-py3-none-any.whl.metadata (2.5 kB)
Collecting httpcore==1.* (from httpx>=0.26.0->pathreview==0.1.0)
  Using cached httpcore-1.0.9-py3-none-any.whl.metadata (21 kB)
Collecting idna (from httpx>=0.26.0->pathreview==0.1.0)
  Using cached idna-3.18-py3-none-any.whl.metadata (6.1 kB)
Collecting h11>=0.16 (from httpcore==1.*->httpx>=0.26.0->pathreview==0.1.0)
  Using cached h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Collecting sortedcontainers<3.0.0,>=2.1.0 (from hypothesis>=6.92.0->pathreview==0.1.0)
  Downloading sortedcontainers-2.4.0-py2.py3-none-any.whl.metadata (10 kB)
Collecting attrs>=22.2.0 (from jsonschema>=4.19.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached attrs-26.1.0-py3-none-any.whl.metadata (8.8 kB)
Collecting jsonschema-specifications>=2023.03.6 (from jsonschema>=4.19.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached jsonschema_specifications-2025.9.1-py3-none-any.whl.metadata (2.9 kB)
Collecting referencing>=0.28.4 (from jsonschema>=4.19.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached referencing-0.37.0-py3-none-any.whl.metadata (2.8 kB)
Collecting rpds-py>=0.25.0 (from jsonschema>=4.19.0->chromadb>=0.4.22->pathreview==0.1.0)
  Downloading rpds_py-2026.6.3-cp314-cp314-win_amd64.whl.metadata (4.2 kB)
Collecting six>=1.9.0 (from kubernetes>=28.1.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached six-1.17.0-py2.py3-none-any.whl.metadata (1.7 kB)
Collecting python-dateutil>=2.5.3 (from kubernetes>=28.1.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached python_dateutil-2.9.0.post0-py2.py3-none-any.whl.metadata (8.4 kB)
Collecting websocket-client!=0.40.0,!=0.41.*,!=0.42.*,>=0.32.0 (from kubernetes>=28.1.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached websocket_client-1.9.0-py3-none-any.whl.metadata (8.3 kB)
Collecting requests (from kubernetes>=28.1.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached requests-2.34.2-py3-none-any.whl.metadata (4.8 kB)
Collecting requests-oauthlib (from kubernetes>=28.1.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached requests_oauthlib-2.0.0-py2.py3-none-any.whl.metadata (11 kB)
Collecting urllib3!=2.6.0,>=1.24.2 (from kubernetes>=28.1.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached urllib3-2.7.0-py3-none-any.whl.metadata (6.9 kB)
Collecting durationpy>=0.7 (from kubernetes>=28.1.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached durationpy-0.10-py3-none-any.whl.metadata (340 bytes)
Collecting aiohttp<4.0.0,>=3.13.5 (from kubernetes>=28.1.0->chromadb>=0.4.22->pathreview==0.1.0)
  Downloading aiohttp-3.14.1-cp314-cp314-win_amd64.whl.metadata (8.5 kB)
Collecting aiohappyeyeballs>=2.5.0 (from aiohttp<4.0.0,>=3.13.5->kubernetes>=28.1.0->chromadb>=0.4.22->pathreview==0.1.0)
  Downloading aiohappyeyeballs-2.7.1-py3-none-any.whl.metadata (5.9 kB)
Collecting aiosignal>=1.4.0 (from aiohttp<4.0.0,>=3.13.5->kubernetes>=28.1.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached aiosignal-1.4.0-py3-none-any.whl.metadata (3.7 kB)
Collecting frozenlist>=1.1.1 (from aiohttp<4.0.0,>=3.13.5->kubernetes>=28.1.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached frozenlist-1.8.0-cp314-cp314-win_amd64.whl.metadata (21 kB)
Collecting multidict<7.0,>=4.5 (from aiohttp<4.0.0,>=3.13.5->kubernetes>=28.1.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached multidict-6.7.1-cp314-cp314-win_amd64.whl.metadata (5.5 kB)
Collecting propcache>=0.2.0 (from aiohttp<4.0.0,>=3.13.5->kubernetes>=28.1.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached propcache-0.5.2-cp314-cp314-win_amd64.whl.metadata (17 kB)
Collecting yarl<2.0,>=1.17.0 (from aiohttp<4.0.0,>=3.13.5->kubernetes>=28.1.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached yarl-1.24.2-cp314-cp314-win_amd64.whl.metadata (97 kB)
Collecting coverage>=7.3.0 (from mutmut>=2.4.4->pathreview==0.1.0)
  Downloading coverage-7.15.2-cp314-cp314-win_amd64.whl.metadata (8.8 kB)
Collecting libcst>=1.8.5 (from mutmut>=2.4.4->pathreview==0.1.0)
  Downloading libcst-1.8.6-cp314-cp314-win_amd64.whl.metadata (15 kB)
Collecting setproctitle>=1.1.0 (from mutmut>=2.4.4->pathreview==0.1.0)
  Downloading setproctitle-1.3.7-cp314-cp314-win_amd64.whl.metadata (11 kB)
Collecting textual>=1.0.0 (from mutmut>=2.4.4->pathreview==0.1.0)
  Downloading textual-8.2.8-py3-none-any.whl.metadata (9.1 kB)
Collecting librt>=0.13.0 (from mypy>=1.8.0->pathreview==0.1.0)
  Downloading librt-0.13.0-cp314-cp314-win_amd64.whl.metadata (1.3 kB)
Collecting ast-serialize<1.0.0,>=0.6.0 (from mypy>=1.8.0->pathreview==0.1.0)
  Downloading ast_serialize-0.6.0-cp39-abi3-win_amd64.whl.metadata (1.3 kB)
Collecting flatbuffers (from onnxruntime>=1.14.1->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached flatbuffers-25.12.19-py2.py3-none-any.whl.metadata (1.0 kB)
Collecting protobuf>=4.25.8 (from onnxruntime>=1.14.1->chromadb>=0.4.22->pathreview==0.1.0)
  Downloading protobuf-7.35.1-cp310-abi3-win_amd64.whl.metadata (595 bytes)
Collecting distro<2,>=1.7.0 (from openai>=1.10.0->pathreview==0.1.0)
  Using cached distro-1.9.0-py3-none-any.whl.metadata (6.8 kB)
Collecting jiter<1,>=0.10.0 (from openai>=1.10.0->pathreview==0.1.0)
  Downloading jiter-0.16.0-cp314-cp314-win_amd64.whl.metadata (5.3 kB)
Collecting sniffio (from openai>=1.10.0->pathreview==0.1.0)
  Using cached sniffio-1.3.1-py3-none-any.whl.metadata (3.9 kB)
Collecting annotated-types>=0.6.0 (from pydantic>=2.5.0->pydantic[email]>=2.5.0->pathreview==0.1.0)
  Using cached annotated_types-0.7.0-py3-none-any.whl.metadata (15 kB)
Collecting pydantic-core==2.46.4 (from pydantic>=2.5.0->pydantic[email]>=2.5.0->pathreview==0.1.0)
  Using cached pydantic_core-2.46.4-cp314-cp314-win_amd64.whl.metadata (6.7 kB)
Collecting googleapis-common-protos~=1.57 (from opentelemetry-exporter-otlp-proto-grpc>=1.2.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached googleapis_common_protos-1.75.0-py3-none-any.whl.metadata (8.6 kB)
Collecting opentelemetry-exporter-otlp-proto-common==1.44.0 (from opentelemetry-exporter-otlp-proto-grpc>=1.2.0->chromadb>=0.4.22->pathreview==0.1.0)
  Downloading opentelemetry_exporter_otlp_proto_common-1.44.0-py3-none-any.whl.metadata (1.8 kB)
Collecting opentelemetry-proto==1.44.0 (from opentelemetry-exporter-otlp-proto-grpc>=1.2.0->chromadb>=0.4.22->pathreview==0.1.0)
  Downloading opentelemetry_proto-1.44.0-py3-none-any.whl.metadata (2.3 kB)
Collecting opentelemetry-semantic-conventions==0.65b0 (from opentelemetry-sdk>=1.2.0->chromadb>=0.4.22->pathreview==0.1.0)
  Downloading opentelemetry_semantic_conventions-0.65b0-py3-none-any.whl.metadata (2.4 kB)
Collecting cfgv>=2.0.0 (from pre-commit>=3.6.0->pathreview==0.1.0)
  Downloading cfgv-3.5.0-py2.py3-none-any.whl.metadata (8.9 kB)
Collecting identify>=1.0.0 (from pre-commit>=3.6.0->pathreview==0.1.0)
  Downloading identify-2.6.19-py2.py3-none-any.whl.metadata (4.4 kB)
Collecting nodeenv>=0.11.1 (from pre-commit>=3.6.0->pathreview==0.1.0)
  Downloading nodeenv-1.10.0-py2.py3-none-any.whl.metadata (24 kB)
Collecting virtualenv>=20.10.0 (from pre-commit>=3.6.0->pathreview==0.1.0)
  Downloading virtualenv-21.6.1-py3-none-any.whl.metadata (3.4 kB)
Collecting python-dotenv>=0.21.0 (from pydantic-settings>=2.1.0->pathreview==0.1.0)
  Using cached python_dotenv-1.2.2-py3-none-any.whl.metadata (27 kB)
Collecting email-validator>=2.0.0 (from pydantic[email]>=2.5.0->pathreview==0.1.0)
  Downloading email_validator-2.3.0-py3-none-any.whl.metadata (26 kB)
Collecting dnspython>=2.0.0 (from email-validator>=2.0.0->pydantic[email]>=2.5.0->pathreview==0.1.0)
  Downloading dnspython-2.8.0-py3-none-any.whl.metadata (5.7 kB)
Collecting iniconfig>=1.0.1 (from pytest>=7.4.0->pathreview==0.1.0)
  Using cached iniconfig-2.3.0-py3-none-any.whl.metadata (2.5 kB)
Collecting pluggy<2,>=1.5 (from pytest>=7.4.0->pathreview==0.1.0)
  Using cached pluggy-1.6.0-py3-none-any.whl.metadata (4.8 kB)
Collecting pygments>=2.7.2 (from pytest>=7.4.0->pathreview==0.1.0)
  Using cached pygments-2.20.0-py3-none-any.whl.metadata (2.5 kB)
Collecting py-cpuinfo (from pytest-benchmark>=4.0.0->pathreview==0.1.0)
  Downloading py_cpuinfo-9.0.0-py3-none-any.whl.metadata (794 bytes)
Collecting Werkzeug>=2.0.0 (from pytest-httpserver>=1.0.8->pathreview==0.1.0)
  Using cached werkzeug-3.1.8-py3-none-any.whl.metadata (4.0 kB)
Collecting ecdsa!=0.15 (from python-jose>=3.3.0->python-jose[cryptography]>=3.3.0->pathreview==0.1.0)
  Downloading ecdsa-0.19.2-py2.py3-none-any.whl.metadata (29 kB)
Collecting rsa!=4.1.1,!=4.4,<5.0,>=4.0 (from python-jose>=3.3.0->python-jose[cryptography]>=3.3.0->pathreview==0.1.0)
  Downloading rsa-4.9.1-py3-none-any.whl.metadata (5.6 kB)
Collecting pyasn1>=0.5.0 (from python-jose>=3.3.0->python-jose[cryptography]>=3.3.0->pathreview==0.1.0)
  Downloading pyasn1-0.6.4-py3-none-any.whl.metadata (8.4 kB)
Collecting cryptography>=3.4.0 (from python-jose[cryptography]>=3.3.0->pathreview==0.1.0)
  Downloading cryptography-49.0.0-cp311-abi3-win_amd64.whl.metadata (4.3 kB)
Collecting cffi>=2.0.0 (from cryptography>=3.4.0->python-jose[cryptography]>=3.3.0->pathreview==0.1.0)
  Downloading cffi-2.1.0-cp314-cp314-win_amd64.whl.metadata (2.6 kB)
Collecting pycparser (from cffi>=2.0.0->cryptography>=3.4.0->python-jose[cryptography]>=3.3.0->pathreview==0.1.0)
  Downloading pycparser-3.0-py3-none-any.whl.metadata (8.2 kB)
Collecting markdown-it-py>=2.2.0 (from rich>=10.11.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached markdown_it_py-4.2.0-py3-none-any.whl.metadata (7.4 kB)
Collecting mdurl~=0.1 (from markdown-it-py>=2.2.0->rich>=10.11.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached mdurl-0.1.2-py3-none-any.whl.metadata (1.6 kB)
Collecting mdit-py-plugins (from textual>=1.0.0->mutmut>=2.4.4->pathreview==0.1.0)
  Downloading mdit_py_plugins-0.6.1-py3-none-any.whl.metadata (2.9 kB)
Collecting linkify-it-py<3,>=1 (from markdown-it-py[linkify]>=2.1.0->textual>=1.0.0->mutmut>=2.4.4->pathreview==0.1.0)
  Downloading linkify_it_py-2.1.0-py3-none-any.whl.metadata (8.5 kB)
Collecting uc-micro-py (from linkify-it-py<3,>=1->markdown-it-py[linkify]>=2.1.0->textual>=1.0.0->mutmut>=2.4.4->pathreview==0.1.0)
  Downloading uc_micro_py-2.0.0-py3-none-any.whl.metadata (2.2 kB)
Collecting regex (from tiktoken>=0.5.2->pathreview==0.1.0)
  Downloading regex-2026.7.10-cp314-cp314-win_amd64.whl.metadata (41 kB)
Collecting huggingface-hub<2.0,>=0.16.4 (from tokenizers>=0.13.2->chromadb>=0.4.22->pathreview==0.1.0)
  Downloading huggingface_hub-1.24.0-py3-none-any.whl.metadata (16 kB)
Collecting filelock>=3.10.0 (from huggingface-hub<2.0,>=0.16.4->tokenizers>=0.13.2->chromadb>=0.4.22->pathreview==0.1.0)
  Downloading filelock-3.31.0-py3-none-any.whl.metadata (2.0 kB)
Collecting fsspec>=2023.5.0 (from huggingface-hub<2.0,>=0.16.4->tokenizers>=0.13.2->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached fsspec-2026.6.0-py3-none-any.whl.metadata (10 kB)
Collecting hf-xet<2.0.0,>=1.5.1 (from huggingface-hub<2.0,>=0.16.4->tokenizers>=0.13.2->chromadb>=0.4.22->pathreview==0.1.0)
  Downloading hf_xet-1.5.2-cp38-abi3-win_amd64.whl.metadata (4.9 kB)
Collecting shellingham>=1.3.0 (from typer>=0.9.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached shellingham-1.5.4-py2.py3-none-any.whl.metadata (3.5 kB)
Collecting types-pyOpenSSL (from types-redis>=4.6.0->pathreview==0.1.0)
  Downloading types_pyOpenSSL-24.1.0.20240722-py3-none-any.whl.metadata (2.1 kB)
Collecting httptools>=0.8.0 (from uvicorn[standard]>=0.25.0->pathreview==0.1.0)
  Using cached httptools-0.8.0-cp314-cp314-win_amd64.whl.metadata (3.7 kB)
Collecting watchfiles>=0.20 (from uvicorn[standard]>=0.25.0->pathreview==0.1.0)
  Using cached watchfiles-1.2.0-cp314-cp314-win_amd64.whl.metadata (5.0 kB)
Collecting websockets>=13.0 (from uvicorn[standard]>=0.25.0->pathreview==0.1.0)
  Downloading websockets-16.1.1-cp314-cp314-win_amd64.whl.metadata (7.0 kB)
Collecting distlib<1,>=0.3.7 (from virtualenv>=20.10.0->pre-commit>=3.6.0->pathreview==0.1.0)
  Downloading distlib-0.4.3-py2.py3-none-any.whl.metadata (5.3 kB)
Collecting python-discovery>=1.4.2 (from virtualenv>=20.10.0->pre-commit>=3.6.0->pathreview==0.1.0)
  Downloading python_discovery-1.4.4-py3-none-any.whl.metadata (5.6 kB)
Collecting markupsafe>=2.1.1 (from Werkzeug>=2.0.0->pytest-httpserver>=1.0.8->pathreview==0.1.0)
  Using cached markupsafe-3.0.3-cp314-cp314-win_amd64.whl.metadata (2.8 kB)
Collecting charset_normalizer<4,>=2 (from requests->kubernetes>=28.1.0->chromadb>=0.4.22->pathreview==0.1.0)
  Downloading charset_normalizer-3.4.9-cp314-cp314-win_amd64.whl.metadata (42 kB)
Collecting oauthlib>=3.0.0 (from requests-oauthlib->kubernetes>=28.1.0->chromadb>=0.4.22->pathreview==0.1.0)
  Using cached oauthlib-3.3.1-py3-none-any.whl.metadata (7.9 kB)
Collecting types-cffi (from types-pyOpenSSL->types-redis>=4.6.0->pathreview==0.1.0)
  Downloading types_cffi-2.0.0.20260518-py3-none-any.whl.metadata (1.7 kB)
Collecting types-setuptools (from types-cffi->types-pyOpenSSL->types-redis>=4.6.0->pathreview==0.1.0)
  Downloading types_setuptools-83.0.0.20260716-py3-none-any.whl.metadata (1.9 kB)
Downloading bcrypt-4.3.0-cp39-abi3-win_amd64.whl (152 kB)
Downloading alembic-1.18.5-py3-none-any.whl (264 kB)
Downloading asyncpg-0.31.0-cp314-cp314-win_amd64.whl (604 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 604.9/604.9 kB 15.1 MB/s  0:00:00
Downloading black-26.5.1-cp314-cp314-win_amd64.whl (1.5 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.5/1.5 MB 35.5 MB/s  0:00:00
Downloading pytokens-0.4.1-cp314-cp314-win_amd64.whl (104 kB)
Using cached chromadb-1.5.9-cp39-abi3-win_amd64.whl (23.5 MB)
Using cached build-1.5.0-py3-none-any.whl (26 kB)
Using cached click-8.4.2-py3-none-any.whl (119 kB)
Downloading fastapi-0.139.2-py3-none-any.whl (130 kB)
Using cached annotated_doc-0.0.4-py3-none-any.whl (5.3 kB)
Using cached greenlet-3.5.3-cp314-cp314-win_amd64.whl (240 kB)
Downloading grpcio-1.82.1-cp314-cp314-win_amd64.whl (5.1 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 5.1/5.1 MB 70.0 MB/s  0:00:00
Using cached typing_extensions-4.16.0-py3-none-any.whl (45 kB)
Using cached httpx-0.28.1-py3-none-any.whl (73 kB)
Using cached httpcore-1.0.9-py3-none-any.whl (78 kB)
Using cached h11-0.16.0-py3-none-any.whl (37 kB)
Downloading hypothesis-6.156.7-cp314-cp314-win_amd64.whl (638 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 638.3/638.3 kB 30.1 MB/s  0:00:00
Downloading sortedcontainers-2.4.0-py2.py3-none-any.whl (29 kB)
Using cached jsonschema-4.26.0-py3-none-any.whl (90 kB)
Using cached attrs-26.1.0-py3-none-any.whl (67 kB)
Using cached jsonschema_specifications-2025.9.1-py3-none-any.whl (18 kB)
Downloading kubernetes-36.0.3-py2.py3-none-any.whl (4.6 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.6/4.6 MB 69.7 MB/s  0:00:00
Downloading aiohttp-3.14.1-cp314-cp314-win_amd64.whl (485 kB)
Using cached multidict-6.7.1-cp314-cp314-win_amd64.whl (45 kB)
Using cached yarl-1.24.2-cp314-cp314-win_amd64.whl (94 kB)
Downloading aiohappyeyeballs-2.7.1-py3-none-any.whl (15 kB)
Using cached aiosignal-1.4.0-py3-none-any.whl (7.5 kB)
Using cached certifi-2026.6.17-py3-none-any.whl (133 kB)
Using cached durationpy-0.10-py3-none-any.whl (3.9 kB)
Using cached frozenlist-1.8.0-cp314-cp314-win_amd64.whl (44 kB)
Using cached idna-3.18-py3-none-any.whl (65 kB)
Using cached mmh3-5.2.1-cp314-cp314-win_amd64.whl (42 kB)
Downloading mutmut-3.6.0-py3-none-any.whl (47 kB)
Downloading coverage-7.15.2-cp314-cp314-win_amd64.whl (224 kB)
Downloading libcst-1.8.6-cp314-cp314-win_amd64.whl (2.2 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.2/2.2 MB 71.3 MB/s  0:00:00
Downloading mypy-2.3.0-cp314-cp314-win_amd64.whl (11.4 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 11.4/11.4 MB 84.8 MB/s  0:00:00
Downloading ast_serialize-0.6.0-cp39-abi3-win_amd64.whl (1.1 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.1/1.1 MB 47.3 MB/s  0:00:00
Downloading librt-0.13.0-cp314-cp314-win_amd64.whl (121 kB)
Downloading mypy_extensions-1.1.0-py3-none-any.whl (5.0 kB)
Downloading numpy-2.5.1-cp314-cp314-win_amd64.whl (12.6 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 12.6/12.6 MB 91.5 MB/s  0:00:00
Downloading onnxruntime-1.27.0-cp314-cp314-win_amd64.whl (13.7 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 13.7/13.7 MB 85.6 MB/s  0:00:00
Downloading openai-2.46.0-py3-none-any.whl (1.6 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.6/1.6 MB 61.3 MB/s  0:00:00
Downloading anyio-4.14.2-py3-none-any.whl (125 kB)
Using cached distro-1.9.0-py3-none-any.whl (20 kB)
Downloading jiter-0.16.0-cp314-cp314-win_amd64.whl (198 kB)
Using cached pydantic-2.13.4-py3-none-any.whl (472 kB)
Using cached pydantic_core-2.46.4-cp314-cp314-win_amd64.whl (2.1 MB)
Using cached annotated_types-0.7.0-py3-none-any.whl (13 kB)
Downloading opentelemetry_api-1.44.0-py3-none-any.whl (60 kB)
Downloading opentelemetry_exporter_otlp_proto_grpc-1.44.0-py3-none-any.whl (19 kB)
Downloading opentelemetry_exporter_otlp_proto_common-1.44.0-py3-none-any.whl (17 kB)
Downloading opentelemetry_proto-1.44.0-py3-none-any.whl (72 kB)
Using cached googleapis_common_protos-1.75.0-py3-none-any.whl (300 kB)
Downloading opentelemetry_sdk-1.44.0-py3-none-any.whl (137 kB)
Downloading opentelemetry_semantic_conventions-0.65b0-py3-none-any.whl (204 kB)
Downloading protobuf-7.35.1-cp310-abi3-win_amd64.whl (439 kB)
Using cached orjson-3.11.9-cp314-cp314-win_amd64.whl (127 kB)
Using cached overrides-7.7.0-py3-none-any.whl (17 kB)
Downloading passlib-1.7.4-py2.py3-none-any.whl (525 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 525.6/525.6 kB 17.5 MB/s  0:00:00
Downloading pathspec-1.1.1-py3-none-any.whl (57 kB)
Downloading platformdirs-4.10.1-py3-none-any.whl (22 kB)
Downloading pre_commit-4.6.0-py2.py3-none-any.whl (226 kB)
Downloading cfgv-3.5.0-py2.py3-none-any.whl (7.4 kB)
Downloading identify-2.6.19-py2.py3-none-any.whl (99 kB)
Downloading nodeenv-1.10.0-py2.py3-none-any.whl (23 kB)
Using cached propcache-0.5.2-cp314-cp314-win_amd64.whl (42 kB)
Downloading psycopg2_binary-2.9.12-cp314-cp314-win_amd64.whl (2.8 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.8/2.8 MB 68.4 MB/s  0:00:00
Using cached pybase64-1.4.3-cp314-cp314-win_amd64.whl (36 kB)
Downloading pydantic_settings-2.14.2-py3-none-any.whl (61 kB)
Downloading email_validator-2.3.0-py3-none-any.whl (35 kB)
Downloading dnspython-2.8.0-py3-none-any.whl (331 kB)
Downloading pypdf-6.14.2-py3-none-any.whl (349 kB)
Using cached pypika-0.51.1-py2.py3-none-any.whl (60 kB)
Using cached pytest-9.1.1-py3-none-any.whl (386 kB)
Using cached pluggy-1.6.0-py3-none-any.whl (20 kB)
Using cached colorama-0.4.6-py2.py3-none-any.whl (25 kB)
Using cached iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
Using cached pygments-2.20.0-py3-none-any.whl (1.2 MB)
Downloading pytest_asyncio-1.4.0-py3-none-any.whl (16 kB)
Downloading pytest_benchmark-5.2.3-py3-none-any.whl (45 kB)
Downloading pytest_cov-7.1.0-py3-none-any.whl (22 kB)
Downloading pytest_httpserver-1.1.5-py3-none-any.whl (23 kB)
Using cached python_dateutil-2.9.0.post0-py2.py3-none-any.whl (229 kB)
Using cached python_dotenv-1.2.2-py3-none-any.whl (22 kB)
Downloading python_jose-3.5.0-py2.py3-none-any.whl (34 kB)
Downloading rsa-4.9.1-py3-none-any.whl (34 kB)
Downloading ecdsa-0.19.2-py2.py3-none-any.whl (150 kB)
Downloading pyasn1-0.6.4-py3-none-any.whl (84 kB)
Downloading cryptography-49.0.0-cp311-abi3-win_amd64.whl (3.8 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3.8/3.8 MB 55.5 MB/s  0:00:00
Downloading cffi-2.1.0-cp314-cp314-win_amd64.whl (187 kB)
Using cached python_multipart-0.0.32-py3-none-any.whl (30 kB)
Using cached pyyaml-6.0.3-cp314-cp314-win_amd64.whl (156 kB)
Downloading rank_bm25-0.2.2-py3-none-any.whl (8.6 kB)
Downloading redis-8.0.1-py3-none-any.whl (502 kB)
Using cached referencing-0.37.0-py3-none-any.whl (26 kB)
Using cached rich-15.0.0-py3-none-any.whl (310 kB)
Using cached markdown_it_py-4.2.0-py3-none-any.whl (91 kB)
Using cached mdurl-0.1.2-py3-none-any.whl (10.0 kB)
Downloading rpds_py-2026.6.3-cp314-cp314-win_amd64.whl (220 kB)
Downloading ruff-0.15.22-py3-none-win_amd64.whl (11.9 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 11.9/11.9 MB 49.9 MB/s  0:00:00
Downloading setproctitle-1.3.7-cp314-cp314-win_amd64.whl (13 kB)
Using cached six-1.17.0-py2.py3-none-any.whl (11 kB)
Using cached sqlalchemy-2.0.51-cp314-cp314-win_amd64.whl (2.1 MB)
Using cached starlette-1.3.1-py3-none-any.whl (73 kB)
Downloading structlog-26.1.0-py3-none-any.whl (73 kB)
Using cached tenacity-9.1.4-py3-none-any.whl (28 kB)
Downloading textual-8.2.8-py3-none-any.whl (731 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 731.4/731.4 kB 25.3 MB/s  0:00:00
Downloading linkify_it_py-2.1.0-py3-none-any.whl (19 kB)
Downloading tiktoken-0.13.0-cp314-cp314-win_amd64.whl (918 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 918.7/918.7 kB 37.3 MB/s  0:00:00
Downloading tokenizers-0.23.1-cp310-abi3-win_amd64.whl (2.8 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.8/2.8 MB 47.0 MB/s  0:00:00
Downloading huggingface_hub-1.24.0-py3-none-any.whl (771 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 771.9/771.9 kB 29.7 MB/s  0:00:00
Downloading hf_xet-1.5.2-cp38-abi3-win_amd64.whl (4.0 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.0/4.0 MB 59.8 MB/s  0:00:00
Downloading filelock-3.31.0-py3-none-any.whl (96 kB)
Using cached fsspec-2026.6.0-py3-none-any.whl (203 kB)
Downloading tqdm-4.69.0-py3-none-any.whl (676 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 676.7/676.7 kB 38.7 MB/s  0:00:00
Downloading typer-0.27.0-py3-none-any.whl (122 kB)
Using cached shellingham-1.5.4-py2.py3-none-any.whl (9.8 kB)
Downloading types_redis-4.6.0.20241004-py3-none-any.whl (58 kB)
Using cached typing_inspection-0.4.2-py3-none-any.whl (14 kB)
Using cached urllib3-2.7.0-py3-none-any.whl (131 kB)
Downloading uvicorn-0.51.0-py3-none-any.whl (73 kB)
Using cached httptools-0.8.0-cp314-cp314-win_amd64.whl (92 kB)
Downloading virtualenv-21.6.1-py3-none-any.whl (5.5 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 5.5/5.5 MB 59.5 MB/s  0:00:00
Downloading distlib-0.4.3-py2.py3-none-any.whl (470 kB)
Downloading python_discovery-1.4.4-py3-none-any.whl (34 kB)
Using cached watchfiles-1.2.0-cp314-cp314-win_amd64.whl (288 kB)
Using cached websocket_client-1.9.0-py3-none-any.whl (82 kB)
Downloading websockets-16.1.1-cp314-cp314-win_amd64.whl (179 kB)
Using cached werkzeug-3.1.8-py3-none-any.whl (226 kB)
Using cached markupsafe-3.0.3-cp314-cp314-win_amd64.whl (15 kB)
Using cached flatbuffers-25.12.19-py2.py3-none-any.whl (26 kB)
Using cached importlib_resources-7.1.0-py3-none-any.whl (37 kB)
Downloading mako-1.3.12-py3-none-any.whl (78 kB)
Downloading mdit_py_plugins-0.6.1-py3-none-any.whl (66 kB)
Downloading py_cpuinfo-9.0.0-py3-none-any.whl (22 kB)
Downloading pycparser-3.0-py3-none-any.whl (48 kB)
Using cached pyproject_hooks-1.2.0-py3-none-any.whl (10 kB)
Downloading regex-2026.7.10-cp314-cp314-win_amd64.whl (280 kB)
Using cached requests-2.34.2-py3-none-any.whl (73 kB)
Downloading charset_normalizer-3.4.9-cp314-cp314-win_amd64.whl (162 kB)
Using cached requests_oauthlib-2.0.0-py2.py3-none-any.whl (24 kB)
Using cached oauthlib-3.3.1-py3-none-any.whl (160 kB)
Using cached sniffio-1.3.1-py3-none-any.whl (10 kB)
Downloading types_pyOpenSSL-24.1.0.20240722-py3-none-any.whl (7.5 kB)
Downloading types_cffi-2.0.0.20260518-py3-none-any.whl (20 kB)
Downloading types_setuptools-83.0.0.20260716-py3-none-any.whl (68 kB)
Downloading uc_micro_py-2.0.0-py3-none-any.whl (6.4 kB)
Building wheels for collected packages: pathreview
  Building editable for pathreview (pyproject.toml) ... done
  Created wheel for pathreview: filename=pathreview-0.1.0-0.editable-py3-none-any.whl size=4732 sha256=8194e0a2fd8fa3cdc16712f9929e5b562f274c4bb1737863163d1f04aecb9893
  Stored in directory: C:\Users\s-bas\AppData\Local\Temp\pip-ephem-wheel-cache-3ahl7bq6\wheels\d6\ea\fd\bae17ebd93a27687512074fabc46342cc35f094e75f5bedf56
Successfully built pathreview
Installing collected packages: sortedcontainers, pypika, py-cpuinfo, passlib, flatbuffers, durationpy, distlib, websockets, websocket-client, urllib3, uc-micro-py, typing-extensions, types-setuptools, tenacity, structlog, sniffio, six, shellingham, setproctitle, ruff, rpds-py, regex, redis, pyyaml, pytokens, python-multipart, python-dotenv, pyproject_hooks, pypdf, pygments, pycparser, pybase64, pyasn1, psycopg2-binary, protobuf, propcache, pluggy, platformdirs, pathspec, overrides, orjson, oauthlib, numpy, nodeenv, mypy-extensions, multidict, mmh3, mdurl, markupsafe, librt, jiter, iniconfig, importlib-resources, idna, identify, hypothesis, httptools, hf-xet, h11, greenlet, fsspec, frozenlist, filelock, dnspython, distro, coverage, colorama, charset_normalizer, cfgv, certifi, bcrypt, attrs, asyncpg, ast-serialize, annotated-types, annotated-doc, aiohappyeyeballs, yarl, Werkzeug, typing-inspection, types-cffi, tqdm, sqlalchemy, rsa, requests, referencing, rank-bm25, python-discovery, python-dateutil, pytest, pydantic-core, opentelemetry-proto, opentelemetry-api, onnxruntime, mypy, markdown-it-py, Mako, linkify-it-py, libcst, httpcore, grpcio, googleapis-common-protos, email-validator, ecdsa, click, cffi, build, anyio, aiosignal, watchfiles, virtualenv, uvicorn, tiktoken, starlette, rich, requests-oauthlib, python-jose, pytest-httpserver, pytest-cov, pytest-benchmark, pytest-asyncio, pydantic, opentelemetry-semantic-conventions, opentelemetry-exporter-otlp-proto-common, mdit-py-plugins, jsonschema-specifications, httpx, cryptography, black, alembic, aiohttp, types-pyOpenSSL, typer, textual, pydantic-settings, pre-commit, opentelemetry-sdk, openai, kubernetes, jsonschema, huggingface-hub, fastapi, types-redis, tokenizers, opentelemetry-exporter-otlp-proto-grpc, mutmut, chromadb, pathreview
Successfully installed Mako-1.3.12 Werkzeug-3.1.8 aiohappyeyeballs-2.7.1 aiohttp-3.14.1 aiosignal-1.4.0 alembic-1.18.5 annotated-doc-0.0.4 annotated-types-0.7.0 anyio-4.14.2 ast-serialize-0.6.0 asyncpg-0.31.0 attrs-26.1.0 bcrypt-4.3.0 black-26.5.1 build-1.5.0 certifi-2026.6.17 cffi-2.1.0 cfgv-3.5.0 charset_normalizer-3.4.9 chromadb-1.5.9 click-8.4.2 colorama-0.4.6 coverage-7.15.2 cryptography-49.0.0 distlib-0.4.3 distro-1.9.0 dnspython-2.8.0 durationpy-0.10 ecdsa-0.19.2 email-validator-2.3.0 fastapi-0.139.2 filelock-3.31.0 flatbuffers-25.12.19 frozenlist-1.8.0 fsspec-2026.6.0 googleapis-common-protos-1.75.0 greenlet-3.5.3 grpcio-1.82.1 h11-0.16.0 hf-xet-1.5.2 httpcore-1.0.9 httptools-0.8.0 httpx-0.28.1 huggingface-hub-1.24.0 hypothesis-6.156.7 identify-2.6.19 idna-3.18 importlib-resources-7.1.0 iniconfig-2.3.0 jiter-0.16.0 jsonschema-4.26.0 jsonschema-specifications-2025.9.1 kubernetes-36.0.3 libcst-1.8.6 librt-0.13.0 linkify-it-py-2.1.0 markdown-it-py-4.2.0 markupsafe-3.0.3 mdit-py-plugins-0.6.1 mdurl-0.1.2 mmh3-5.2.1 multidict-6.7.1 mutmut-3.6.0 mypy-2.3.0 mypy-extensions-1.1.0 nodeenv-1.10.0 numpy-2.5.1 oauthlib-3.3.1 onnxruntime-1.27.0 openai-2.46.0 opentelemetry-api-1.44.0 opentelemetry-exporter-otlp-proto-common-1.44.0 opentelemetry-exporter-otlp-proto-grpc-1.44.0 opentelemetry-proto-1.44.0 opentelemetry-sdk-1.44.0 opentelemetry-semantic-conventions-0.65b0 orjson-3.11.9 overrides-7.7.0 passlib-1.7.4 pathreview-0.1.0 pathspec-1.1.1 platformdirs-4.10.1 pluggy-1.6.0 pre-commit-4.6.0 propcache-0.5.2 protobuf-7.35.1 psycopg2-binary-2.9.12 py-cpuinfo-9.0.0 pyasn1-0.6.4 pybase64-1.4.3 pycparser-3.0 pydantic-2.13.4 pydantic-core-2.46.4 pydantic-settings-2.14.2 pygments-2.20.0 pypdf-6.14.2 pypika-0.51.1 pyproject_hooks-1.2.0 pytest-9.1.1 pytest-asyncio-1.4.0 pytest-benchmark-5.2.3 pytest-cov-7.1.0 pytest-httpserver-1.1.5 python-dateutil-2.9.0.post0 python-discovery-1.4.4 python-dotenv-1.2.2 python-jose-3.5.0 python-multipart-0.0.32 pytokens-0.4.1 pyyaml-6.0.3 rank-bm25-0.2.2 redis-8.0.1 referencing-0.37.0 regex-2026.7.10 requests-2.34.2 requests-oauthlib-2.0.0 rich-15.0.0 rpds-py-2026.6.3 rsa-4.9.1 ruff-0.15.22 setproctitle-1.3.7 shellingham-1.5.4 six-1.17.0 sniffio-1.3.1 sortedcontainers-2.4.0 sqlalchemy-2.0.51 starlette-1.3.1 structlog-26.1.0 tenacity-9.1.4 textual-8.2.8 tiktoken-0.13.0 tokenizers-0.23.1 tqdm-4.69.0 typer-0.27.0 types-cffi-2.0.0.20260518 types-pyOpenSSL-24.1.0.20240722 types-redis-4.6.0.20241004 types-setuptools-83.0.0.20260716 typing-extensions-4.16.0 typing-inspection-0.4.2 uc-micro-py-2.0.0 urllib3-2.7.0 uvicorn-0.51.0 virtualenv-21.6.1 watchfiles-1.2.0 websocket-client-1.9.0 websockets-16.1.1 yarl-1.24.2
.venv/Scripts/pre-commit install
pre-commit installed at .git\hooks\pre-commit
.venv/Scripts/alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
.venv/Scripts/python scripts/seed_db.py
2026-07-18T22:38:01.361816Z [info     ] Initializing database tables... [__main__]
2026-07-18 15:38:01,411 INFO sqlalchemy.engine.Engine select pg_catalog.version()
select pg_catalog.version()
2026-07-18 15:38:01,411 INFO sqlalchemy.engine.Engine [raw sql] ()
[raw sql] ()
2026-07-18 15:38:01,416 INFO sqlalchemy.engine.Engine select current_schema()
select current_schema()
2026-07-18 15:38:01,416 INFO sqlalchemy.engine.Engine [raw sql] ()
[raw sql] ()
2026-07-18 15:38:01,420 INFO sqlalchemy.engine.Engine show standard_conforming_strings
show standard_conforming_strings
2026-07-18 15:38:01,420 INFO sqlalchemy.engine.Engine [raw sql] ()
[raw sql] ()
2026-07-18 15:38:01,424 INFO sqlalchemy.engine.Engine BEGIN (implicit)
BEGIN (implicit)
2026-07-18 15:38:01,434 INFO sqlalchemy.engine.Engine SELECT pg_catalog.pg_class.relname 
FROM pg_catalog.pg_class JOIN pg_catalog.pg_namespace ON pg_catalog.pg_namespace.oid = pg_catalog.pg_class.relnamespace 
WHERE pg_catalog.pg_class.relname = $1::VARCHAR AND pg_catalog.pg_class.relkind = ANY (ARRAY[$2::VARCHAR, $3::VARCHAR, $4::VARCHAR, $5::VARCHAR, $6::VARCHAR]) AND pg_catalog.pg_table_is_visible(pg_catalog.pg_class.oid) AND pg_catalog.pg_namespace.nspname != $7::VARCHAR
SELECT pg_catalog.pg_class.relname 
FROM pg_catalog.pg_class JOIN pg_catalog.pg_namespace ON pg_catalog.pg_namespace.oid = pg_catalog.pg_class.relnamespace 
WHERE pg_catalog.pg_class.relname = $1::VARCHAR AND pg_catalog.pg_class.relkind = ANY (ARRAY[$2::VARCHAR, $3::VARCHAR, $4::VARCHAR, $5::VARCHAR, $6::VARCHAR]) AND pg_catalog.pg_table_is_visible(pg_catalog.pg_class.oid) AND pg_catalog.pg_namespace.nspname != $7::VARCHAR
2026-07-18 15:38:01,435 INFO sqlalchemy.engine.Engine [generated in 0.00056s] ('users', 'r', 'p', 'f', 'v', 'm', 'pg_catalog')
[generated in 0.00056s] ('users', 'r', 'p', 'f', 'v', 'm', 'pg_catalog')
2026-07-18 15:38:01,444 INFO sqlalchemy.engine.Engine SELECT pg_catalog.pg_class.relname 
FROM pg_catalog.pg_class JOIN pg_catalog.pg_namespace ON pg_catalog.pg_namespace.oid = pg_catalog.pg_class.relnamespace 
WHERE pg_catalog.pg_class.relname = $1::VARCHAR AND pg_catalog.pg_class.relkind = ANY (ARRAY[$2::VARCHAR, $3::VARCHAR, $4::VARCHAR, $5::VARCHAR, $6::VARCHAR]) AND pg_catalog.pg_table_is_visible(pg_catalog.pg_class.oid) AND pg_catalog.pg_namespace.nspname != $7::VARCHAR
SELECT pg_catalog.pg_class.relname 
FROM pg_catalog.pg_class JOIN pg_catalog.pg_namespace ON pg_catalog.pg_namespace.oid = pg_catalog.pg_class.relnamespace 
WHERE pg_catalog.pg_class.relname = $1::VARCHAR AND pg_catalog.pg_class.relkind = ANY (ARRAY[$2::VARCHAR, $3::VARCHAR, $4::VARCHAR, $5::VARCHAR, $6::VARCHAR]) AND pg_catalog.pg_table_is_visible(pg_catalog.pg_class.oid) AND pg_catalog.pg_namespace.nspname != $7::VARCHAR
2026-07-18 15:38:01,444 INFO sqlalchemy.engine.Engine [cached since 0.00962s ago] ('profiles', 'r', 'p', 'f', 'v', 'm', 'pg_catalog')
[cached since 0.00962s ago] ('profiles', 'r', 'p', 'f', 'v', 'm', 'pg_catalog')
2026-07-18 15:38:01,446 INFO sqlalchemy.engine.Engine SELECT pg_catalog.pg_class.relname 
FROM pg_catalog.pg_class JOIN pg_catalog.pg_namespace ON pg_catalog.pg_namespace.oid = pg_catalog.pg_class.relnamespace 
WHERE pg_catalog.pg_class.relname = $1::VARCHAR AND pg_catalog.pg_class.relkind = ANY (ARRAY[$2::VARCHAR, $3::VARCHAR, $4::VARCHAR, $5::VARCHAR, $6::VARCHAR]) AND pg_catalog.pg_table_is_visible(pg_catalog.pg_class.oid) AND pg_catalog.pg_namespace.nspname != $7::VARCHAR
SELECT pg_catalog.pg_class.relname 
FROM pg_catalog.pg_class JOIN pg_catalog.pg_namespace ON pg_catalog.pg_namespace.oid = pg_catalog.pg_class.relnamespace 
WHERE pg_catalog.pg_class.relname = $1::VARCHAR AND pg_catalog.pg_class.relkind = ANY (ARRAY[$2::VARCHAR, $3::VARCHAR, $4::VARCHAR, $5::VARCHAR, $6::VARCHAR]) AND pg_catalog.pg_table_is_visible(pg_catalog.pg_class.oid) AND pg_catalog.pg_namespace.nspname != $7::VARCHAR
2026-07-18 15:38:01,446 INFO sqlalchemy.engine.Engine [cached since 0.01162s ago] ('ingested_sources', 'r', 'p', 'f', 'v', 'm', 'pg_catalog')
[cached since 0.01162s ago] ('ingested_sources', 'r', 'p', 'f', 'v', 'm', 'pg_catalog')
2026-07-18 15:38:01,447 INFO sqlalchemy.engine.Engine SELECT pg_catalog.pg_class.relname 
FROM pg_catalog.pg_class JOIN pg_catalog.pg_namespace ON pg_catalog.pg_namespace.oid = pg_catalog.pg_class.relnamespace 
WHERE pg_catalog.pg_class.relname = $1::VARCHAR AND pg_catalog.pg_class.relkind = ANY (ARRAY[$2::VARCHAR, $3::VARCHAR, $4::VARCHAR, $5::VARCHAR, $6::VARCHAR]) AND pg_catalog.pg_table_is_visible(pg_catalog.pg_class.oid) AND pg_catalog.pg_namespace.nspname != $7::VARCHAR
SELECT pg_catalog.pg_class.relname 
FROM pg_catalog.pg_class JOIN pg_catalog.pg_namespace ON pg_catalog.pg_namespace.oid = pg_catalog.pg_class.relnamespace 
WHERE pg_catalog.pg_class.relname = $1::VARCHAR AND pg_catalog.pg_class.relkind = ANY (ARRAY[$2::VARCHAR, $3::VARCHAR, $4::VARCHAR, $5::VARCHAR, $6::VARCHAR]) AND pg_catalog.pg_table_is_visible(pg_catalog.pg_class.oid) AND pg_catalog.pg_namespace.nspname != $7::VARCHAR
2026-07-18 15:38:01,447 INFO sqlalchemy.engine.Engine [cached since 0.01308s ago] ('reviews', 'r', 'p', 'f', 'v', 'm', 'pg_catalog')
[cached since 0.01308s ago] ('reviews', 'r', 'p', 'f', 'v', 'm', 'pg_catalog')
2026-07-18 15:38:01,449 INFO sqlalchemy.engine.Engine COMMIT
COMMIT
2026-07-18T22:38:01.451172Z [info     ] Database tables created successfully [__main__]
2026-07-18T22:38:01.451554Z [info     ] Checking for existing users... [__main__]
2026-07-18 15:38:01,455 INFO sqlalchemy.engine.Engine BEGIN (implicit)
BEGIN (implicit)
2026-07-18 15:38:01,469 INFO sqlalchemy.engine.Engine SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
2026-07-18 15:38:01,470 INFO sqlalchemy.engine.Engine [generated in 0.00053s] ('user1@example.com',)
[generated in 0.00053s] ('user1@example.com',)
2026-07-18 15:38:01,479 INFO sqlalchemy.engine.Engine SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
2026-07-18 15:38:01,479 INFO sqlalchemy.engine.Engine [cached since 0.01034s ago] ('user2@example.com',)
[cached since 0.01034s ago] ('user2@example.com',)
2026-07-18 15:38:01,482 INFO sqlalchemy.engine.Engine SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
2026-07-18 15:38:01,482 INFO sqlalchemy.engine.Engine [cached since 0.01342s ago] ('user3@example.com',)
[cached since 0.01342s ago] ('user3@example.com',)
2026-07-18T22:38:01.484644Z [info     ] Creating sample users and profiles... [__main__]
2026-07-18 15:38:01,485 INFO sqlalchemy.engine.Engine SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
2026-07-18 15:38:01,485 INFO sqlalchemy.engine.Engine [cached since 0.01606s ago] ('user1@example.com',)
[cached since 0.01606s ago] ('user1@example.com',)
(trapped) error reading bcrypt version
Traceback (most recent call last):
  File "C:\Users\s-bas\Codepath AI201\pathreview\.venv\Lib\site-packages\passlib\handlers\bcrypt.py", line 620, in _load_backend_mixin
    version = _bcrypt.__about__.__version__
              ^^^^^^^^^^^^^^^^^
AttributeError: module 'bcrypt' has no attribute '__about__'
2026-07-18 15:38:01,753 INFO sqlalchemy.engine.Engine INSERT INTO users (id, email, hashed_password, created_at, updated_at, is_active) VALUES ($1::UUID, $2::VARCHAR, $3::VARCHAR, $4::TIMESTAMP WITH TIME ZONE, $5::TIMESTAMP WITH TIME ZONE, $6::BOOLEAN)
INSERT INTO users (id, email, hashed_password, created_at, updated_at, is_active) VALUES ($1::UUID, $2::VARCHAR, $3::VARCHAR, $4::TIMESTAMP WITH TIME ZONE, $5::TIMESTAMP WITH TIME ZONE, $6::BOOLEAN)
2026-07-18 15:38:01,754 INFO sqlalchemy.engine.Engine [generated in 0.00033s] ('47b402bf-6a06-459d-a481-6d11807fb276', 'user1@example.com', '$2b$12$XB99ogbMXE1oDEcLyE8E5.vnLHv7TGBmc5ohYqoNflDxFC0Yvrkgq', datetime.datetime(2026, 7, 18, 22, 38, 1, 753775), datetime.datetime(2026, 7, 18, 22, 38, 1, 753779), True)
[generated in 0.00033s] ('47b402bf-6a06-459d-a481-6d11807fb276', 'user1@example.com', '$2b$12$XB99ogbMXE1oDEcLyE8E5.vnLHv7TGBmc5ohYqoNflDxFC0Yvrkgq', datetime.datetime(2026, 7, 18, 22, 38, 1, 753775), datetime.datetime(2026, 7, 18, 22, 38, 1, 753779), True)
2026-07-18T22:38:01.757695Z [info     ] Created user user1@example.com with profile [__main__]
2026-07-18 15:38:01,758 INFO sqlalchemy.engine.Engine SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
2026-07-18 15:38:01,758 INFO sqlalchemy.engine.Engine [cached since 0.289s ago] ('user2@example.com',)
[cached since 0.289s ago] ('user2@example.com',)
2026-07-18 15:38:01,962 INFO sqlalchemy.engine.Engine INSERT INTO users (id, email, hashed_password, created_at, updated_at, is_active) VALUES ($1::UUID, $2::VARCHAR, $3::VARCHAR, $4::TIMESTAMP WITH TIME ZONE, $5::TIMESTAMP WITH TIME ZONE, $6::BOOLEAN)
INSERT INTO users (id, email, hashed_password, created_at, updated_at, is_active) VALUES ($1::UUID, $2::VARCHAR, $3::VARCHAR, $4::TIMESTAMP WITH TIME ZONE, $5::TIMESTAMP WITH TIME ZONE, $6::BOOLEAN)
2026-07-18 15:38:01,962 INFO sqlalchemy.engine.Engine [cached since 0.2088s ago] ('63fed0b8-cee9-4b08-9502-247c289ede3d', 'user2@example.com', '$2b$12$29sAoWVtrJBUJbxw9qeA2Of97q3LbCIwQrghe.hC.VfzPZpiauIRu', datetime.datetime(2026, 7, 18, 22, 38, 1, 962176), datetime.datetime(2026, 7, 18, 22, 38, 1, 962179), True)
[cached since 0.2088s ago] ('63fed0b8-cee9-4b08-9502-247c289ede3d', 'user2@example.com', '$2b$12$29sAoWVtrJBUJbxw9qeA2Of97q3LbCIwQrghe.hC.VfzPZpiauIRu', datetime.datetime(2026, 7, 18, 22, 38, 1, 962176), datetime.datetime(2026, 7, 18, 22, 38, 1, 962179), True)
2026-07-18 15:38:01,965 INFO sqlalchemy.engine.Engine INSERT INTO profiles (id, user_id, github_username, resume_filename, resume_text, portfolio_url, created_at, updated_at) VALUES ($1::UUID, $2::UUID, $3::VARCHAR, $4::VARCHAR, $5::VARCHAR, $6::VARCHAR, $7::TIMESTAMP WITH TIME ZONE, $8::TIMESTAMP WITH TIME ZONE)
INSERT INTO profiles (id, user_id, github_username, resume_filename, resume_text, portfolio_url, created_at, updated_at) VALUES ($1::UUID, $2::UUID, $3::VARCHAR, $4::VARCHAR, $5::VARCHAR, $6::VARCHAR, $7::TIMESTAMP WITH TIME ZONE, $8::TIMESTAMP WITH TIME ZONE)
2026-07-18 15:38:01,965 INFO sqlalchemy.engine.Engine [generated in 0.00041s] ('3eafb0a5-8113-4b6f-ac38-6b8543b0a950', '47b402bf-6a06-459d-a481-6d11807fb276', 'user1-github', None, None, 'https://user1.dev', datetime.datetime(2026, 7, 18, 22, 38, 1, 964986), datetime.datetime(2026, 7, 18, 22, 38, 1, 964989))
[generated in 0.00041s] ('3eafb0a5-8113-4b6f-ac38-6b8543b0a950', '47b402bf-6a06-459d-a481-6d11807fb276', 'user1-github', None, None, 'https://user1.dev', datetime.datetime(2026, 7, 18, 22, 38, 1, 964986), datetime.datetime(2026, 7, 18, 22, 38, 1, 964989))
2026-07-18T22:38:01.969513Z [info     ] Created user user2@example.com with profile [__main__]
2026-07-18 15:38:01,970 INFO sqlalchemy.engine.Engine SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
2026-07-18 15:38:01,970 INFO sqlalchemy.engine.Engine [cached since 0.5008s ago] ('user3@example.com',)
[cached since 0.5008s ago] ('user3@example.com',)
2026-07-18 15:38:02,173 INFO sqlalchemy.engine.Engine INSERT INTO users (id, email, hashed_password, created_at, updated_at, is_active) VALUES ($1::UUID, $2::VARCHAR, $3::VARCHAR, $4::TIMESTAMP WITH TIME ZONE, $5::TIMESTAMP WITH TIME ZONE, $6::BOOLEAN)
INSERT INTO users (id, email, hashed_password, created_at, updated_at, is_active) VALUES ($1::UUID, $2::VARCHAR, $3::VARCHAR, $4::TIMESTAMP WITH TIME ZONE, $5::TIMESTAMP WITH TIME ZONE, $6::BOOLEAN)
2026-07-18 15:38:02,173 INFO sqlalchemy.engine.Engine [cached since 0.4196s ago] ('c1ce0298-285d-4179-9407-e7045c8d0d24', 'user3@example.com', '$2b$12$9eIrM0yEfkVCpIffKhzHkuW4NIAPhVVxwk538VcZkCTgvnONRbNTe', datetime.datetime(2026, 7, 18, 22, 38, 2, 173003), datetime.datetime(2026, 7, 18, 22, 38, 2, 173008), True)
[cached since 0.4196s ago] ('c1ce0298-285d-4179-9407-e7045c8d0d24', 'user3@example.com', '$2b$12$9eIrM0yEfkVCpIffKhzHkuW4NIAPhVVxwk538VcZkCTgvnONRbNTe', datetime.datetime(2026, 7, 18, 22, 38, 2, 173003), datetime.datetime(2026, 7, 18, 22, 38, 2, 173008), True)
2026-07-18 15:38:02,174 INFO sqlalchemy.engine.Engine INSERT INTO profiles (id, user_id, github_username, resume_filename, resume_text, portfolio_url, created_at, updated_at) VALUES ($1::UUID, $2::UUID, $3::VARCHAR, $4::VARCHAR, $5::VARCHAR, $6::VARCHAR, $7::TIMESTAMP WITH TIME ZONE, $8::TIMESTAMP WITH TIME ZONE)
INSERT INTO profiles (id, user_id, github_username, resume_filename, resume_text, portfolio_url, created_at, updated_at) VALUES ($1::UUID, $2::UUID, $3::VARCHAR, $4::VARCHAR, $5::VARCHAR, $6::VARCHAR, $7::TIMESTAMP WITH TIME ZONE, $8::TIMESTAMP WITH TIME ZONE)
2026-07-18 15:38:02,175 INFO sqlalchemy.engine.Engine [cached since 0.2101s ago] ('6b64ef94-b7c3-4622-aa40-6ff3ed25340b', '63fed0b8-cee9-4b08-9502-247c289ede3d', 'user2-github', None, None, 'https://user2.portfolio', datetime.datetime(2026, 7, 18, 22, 38, 2, 174864), datetime.datetime(2026, 7, 18, 22, 38, 2, 174866))
[cached since 0.2101s ago] ('6b64ef94-b7c3-4622-aa40-6ff3ed25340b', '63fed0b8-cee9-4b08-9502-247c289ede3d', 'user2-github', None, None, 'https://user2.portfolio', datetime.datetime(2026, 7, 18, 22, 38, 2, 174864), datetime.datetime(2026, 7, 18, 22, 38, 2, 174866))
2026-07-18T22:38:02.176401Z [info     ] Created user user3@example.com with profile [__main__]
2026-07-18 15:38:02,176 INFO sqlalchemy.engine.Engine INSERT INTO profiles (id, user_id, github_username, resume_filename, resume_text, portfolio_url, created_at, updated_at) VALUES ($1::UUID, $2::UUID, $3::VARCHAR, $4::VARCHAR, $5::VARCHAR, $6::VARCHAR, $7::TIMESTAMP WITH TIME ZONE, $8::TIMESTAMP WITH TIME ZONE)
INSERT INTO profiles (id, user_id, github_username, resume_filename, resume_text, portfolio_url, created_at, updated_at) VALUES ($1::UUID, $2::UUID, $3::VARCHAR, $4::VARCHAR, $5::VARCHAR, $6::VARCHAR, $7::TIMESTAMP WITH TIME ZONE, $8::TIMESTAMP WITH TIME ZONE)
2026-07-18 15:38:02,177 INFO sqlalchemy.engine.Engine [cached since 0.2122s ago] ('bad0cfe3-cf15-4181-bb14-11e2bfc2cc56', 'c1ce0298-285d-4179-9407-e7045c8d0d24', 'user3-github', None, None, 'https://user3.io', datetime.datetime(2026, 7, 18, 22, 38, 2, 176945), datetime.datetime(2026, 7, 18, 22, 38, 2, 176948))
[cached since 0.2122s ago] ('bad0cfe3-cf15-4181-bb14-11e2bfc2cc56', 'c1ce0298-285d-4179-9407-e7045c8d0d24', 'user3-github', None, None, 'https://user3.io', datetime.datetime(2026, 7, 18, 22, 38, 2, 176945), datetime.datetime(2026, 7, 18, 22, 38, 2, 176948))
2026-07-18 15:38:02,178 INFO sqlalchemy.engine.Engine COMMIT
COMMIT
2026-07-18T22:38:02.181707Z [info     ] Creating sample reviews...     [__main__]
2026-07-18 15:38:02,184 INFO sqlalchemy.engine.Engine BEGIN (implicit)
BEGIN (implicit)
2026-07-18 15:38:02,185 INFO sqlalchemy.engine.Engine SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
2026-07-18 15:38:02,185 INFO sqlalchemy.engine.Engine [cached since 0.7159s ago] ('user1@example.com',)
[cached since 0.7159s ago] ('user1@example.com',)
2026-07-18 15:38:02,189 INFO sqlalchemy.engine.Engine SELECT profiles.id, profiles.user_id, profiles.github_username, profiles.resume_filename, profiles.resume_text, profiles.portfolio_url, profiles.created_at, profiles.updated_at 
FROM profiles 
WHERE profiles.user_id = $1::UUID
SELECT profiles.id, profiles.user_id, profiles.github_username, profiles.resume_filename, profiles.resume_text, profiles.portfolio_url, profiles.created_at, profiles.updated_at 
FROM profiles 
WHERE profiles.user_id = $1::UUID
2026-07-18 15:38:02,189 INFO sqlalchemy.engine.Engine [generated in 0.00034s] ('47b402bf-6a06-459d-a481-6d11807fb276',)
[generated in 0.00034s] ('47b402bf-6a06-459d-a481-6d11807fb276',)
C:\Users\s-bas\Codepath AI201\pathreview\scripts\seed_db.py:127: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  created_at=datetime.utcnow() - timedelta(days=14),
C:\Users\s-bas\Codepath AI201\pathreview\scripts\seed_db.py:128: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  updated_at=datetime.utcnow() - timedelta(days=14),
C:\Users\s-bas\Codepath AI201\pathreview\scripts\seed_db.py:167: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  created_at=datetime.utcnow() - timedelta(days=3),
C:\Users\s-bas\Codepath AI201\pathreview\scripts\seed_db.py:168: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  updated_at=datetime.utcnow() - timedelta(days=3),
C:\Users\s-bas\Codepath AI201\pathreview\scripts\seed_db.py:207: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  created_at=datetime.utcnow() - timedelta(hours=1),
C:\Users\s-bas\Codepath AI201\pathreview\scripts\seed_db.py:208: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  updated_at=datetime.utcnow() - timedelta(hours=1),
2026-07-18T22:38:02.193625Z [info     ] Created reviews for user1      [__main__]
2026-07-18 15:38:02,194 INFO sqlalchemy.engine.Engine SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
2026-07-18 15:38:02,194 INFO sqlalchemy.engine.Engine [cached since 0.725s ago] ('user2@example.com',)
[cached since 0.725s ago] ('user2@example.com',)
2026-07-18 15:38:02,196 INFO sqlalchemy.engine.Engine SELECT profiles.id, profiles.user_id, profiles.github_username, profiles.resume_filename, profiles.resume_text, profiles.portfolio_url, profiles.created_at, profiles.updated_at 
FROM profiles 
WHERE profiles.user_id = $1::UUID
SELECT profiles.id, profiles.user_id, profiles.github_username, profiles.resume_filename, profiles.resume_text, profiles.portfolio_url, profiles.created_at, profiles.updated_at 
FROM profiles 
WHERE profiles.user_id = $1::UUID
2026-07-18 15:38:02,197 INFO sqlalchemy.engine.Engine [cached since 0.008129s ago] ('63fed0b8-cee9-4b08-9502-247c289ede3d',)
[cached since 0.008129s ago] ('63fed0b8-cee9-4b08-9502-247c289ede3d',)
C:\Users\s-bas\Codepath AI201\pathreview\scripts\seed_db.py:234: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  created_at=datetime.utcnow() - timedelta(days=7),
C:\Users\s-bas\Codepath AI201\pathreview\scripts\seed_db.py:235: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  updated_at=datetime.utcnow() - timedelta(days=7),
2026-07-18T22:38:02.199080Z [info     ] Created reviews for user2      [__main__]
2026-07-18 15:38:02,199 INFO sqlalchemy.engine.Engine SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
SELECT users.id, users.email, users.hashed_password, users.created_at, users.updated_at, users.is_active 
FROM users 
WHERE users.email = $1::VARCHAR
2026-07-18 15:38:02,199 INFO sqlalchemy.engine.Engine [cached since 0.7304s ago] ('user3@example.com',)
[cached since 0.7304s ago] ('user3@example.com',)
2026-07-18 15:38:02,202 INFO sqlalchemy.engine.Engine SELECT profiles.id, profiles.user_id, profiles.github_username, profiles.resume_filename, profiles.resume_text, profiles.portfolio_url, profiles.created_at, profiles.updated_at 
FROM profiles 
WHERE profiles.user_id = $1::UUID
SELECT profiles.id, profiles.user_id, profiles.github_username, profiles.resume_filename, profiles.resume_text, profiles.portfolio_url, profiles.created_at, profiles.updated_at 
FROM profiles 
WHERE profiles.user_id = $1::UUID
2026-07-18 15:38:02,202 INFO sqlalchemy.engine.Engine [cached since 0.01326s ago] ('c1ce0298-285d-4179-9407-e7045c8d0d24',)
[cached since 0.01326s ago] ('c1ce0298-285d-4179-9407-e7045c8d0d24',)
C:\Users\s-bas\Codepath AI201\pathreview\scripts\seed_db.py:291: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  created_at=datetime.utcnow() - timedelta(days=21),
C:\Users\s-bas\Codepath AI201\pathreview\scripts\seed_db.py:292: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  updated_at=datetime.utcnow() - timedelta(days=21),
C:\Users\s-bas\Codepath AI201\pathreview\scripts\seed_db.py:331: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  created_at=datetime.utcnow() - timedelta(days=2),
C:\Users\s-bas\Codepath AI201\pathreview\scripts\seed_db.py:332: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  updated_at=datetime.utcnow() - timedelta(days=2),
2026-07-18T22:38:02.204814Z [info     ] Created reviews for user3      [__main__]
2026-07-18 15:38:02,206 INFO sqlalchemy.engine.Engine INSERT INTO reviews (id, profile_id, status, sections, overall_score, error_message, created_at, updated_at) VALUES ($1::UUID, $2::UUID, $3::VARCHAR, $4::JSON, $5::FLOAT, $6::VARCHAR, $7::TIMESTAMP WITH TIME ZONE, $8::TIMESTAMP WITH TIME ZONE)
INSERT INTO reviews (id, profile_id, status, sections, overall_score, error_message, created_at, updated_at) VALUES ($1::UUID, $2::UUID, $3::VARCHAR, $4::JSON, $5::FLOAT, $6::VARCHAR, $7::TIMESTAMP WITH TIME ZONE, $8::TIMESTAMP WITH TIME ZONE)
2026-07-18 15:38:02,206 INFO sqlalchemy.engine.Engine [generated in 0.00047s] [('cdb4ae23-ff30-462b-892e-6ef087722991', '3eafb0a5-8113-4b6f-ac38-6b8543b0a950', 'complete', '[{"section_name": "Technical Skills", "content": "Your GitHub profile shows strong proficiency in Python and JavaScript. You\'ve contributed to 12 pu ... (1564 characters truncated) ... ", "Optimize your portfolio site\'s load time and add responsive CSS", "Add 2\\u20133 sentences to your GitHub bio describing your specialization"]}]', 0.74, None, datetime.datetime(2026, 7, 4, 22, 38, 2, 192817), datetime.datetime(2026, 7, 4, 22, 38, 2, 192891)), ('c17d7a1b-6330-4de9-beda-5c8117ba0b09', '3eafb0a5-8113-4b6f-ac38-6b8543b0a950', 'complete', '[{"section_name": "Technical Skills", "content": "Significant improvement since your last review. You\'ve added READMEs to all pinned repositories wi ... (1361 characters truncated) ... rch", "Add your CodePath AI 201 completion to your resume education section", "Request LinkedIn recommendations from peers who\'ve seen your code"]}]', 0.81, None, datetime.datetime(2026, 7, 15, 22, 38, 2, 193068), datetime.datetime(2026, 7, 15, 22, 38, 2, 193153)), ('6e5323cd-009a-440f-b51a-1a06b22401f2', '3eafb0a5-8113-4b6f-ac38-6b8543b0a950', 'failed', 'null', None, 'GitHub API rate limit exceeded. Please try again later.', datetime.datetime(2026, 7, 18, 21, 38, 2, 193388), datetime.datetime(2026, 7, 18, 21, 38, 2, 193476)), ('afd9e396-626f-48da-b5c8-2e77c84c523f', '6b64ef94-b7c3-4622-aa40-6ff3ed25340b', 'complete', '[{"section_name": "Technical Skills", "content": "Your profile shows 4 public repositories, all created within the last 6 months. The code quality is ... (1475 characters truncated) ... eplace your portfolio URL \\u2014 even a simple GitHub Pages site is better than a 404", "Create a LinkedIn profile and connect it to your GitHub"]}]', 0.58, None, datetime.datetime(2026, 7, 11, 22, 38, 2, 198874), datetime.datetime(2026, 7, 11, 22, 38, 2, 198943)), ('20962dc4-b53e-4d10-b888-2ec36a0b7b7d', 'bad0cfe3-cf15-4181-bb14-11e2bfc2cc56', 'complete', '[{"section_name": "Technical Skills", "content": "Strong technical foundation across your 23 public repositories. Your most recent projects show cons ... (1646 characters truncated) ...  proposal to a local Python or backend engineering meetup", "Ask two former collaborators for LinkedIn recommendations focused on technical depth"]}]', 0.87, None, datetime.datetime(2026, 6, 27, 22, 38, 2, 204407), datetime.datetime(2026, 6, 27, 22, 38, 2, 204490)), ('c6b07062-f777-46eb-afb6-89710d090b3e', 'bad0cfe3-cf15-4181-bb14-11e2bfc2cc56', 'complete', '[{"section_name": "Technical Skills", "content": "Excellent progress. Your new Rust project shows you\'re actively expanding beyond your Python comfo ... (1528 characters truncated) ...  "Add a brief \'currently interested in\' note to your GitHub bio", "Reach out directly to 3\\u20135 companies whose engineering blogs you follow"]}]', 0.91, None, datetime.datetime(2026, 7, 16, 22, 38, 2, 204627), datetime.datetime(2026, 7, 16, 22, 38, 2, 204703))]
[generated in 0.00047s] [('cdb4ae23-ff30-462b-892e-6ef087722991', '3eafb0a5-8113-4b6f-ac38-6b8543b0a950', 'complete', '[{"section_name": "Technical Skills", "content": "Your GitHub profile shows strong proficiency in Python and JavaScript. You\'ve contributed to 12 pu ... (1564 characters truncated) ... ", "Optimize your portfolio site\'s load time and add responsive CSS", "Add 2\\u20133 sentences to your GitHub bio describing your specialization"]}]', 0.74, None, datetime.datetime(2026, 7, 4, 22, 38, 2, 192817), datetime.datetime(2026, 7, 4, 22, 38, 2, 192891)), ('c17d7a1b-6330-4de9-beda-5c8117ba0b09', '3eafb0a5-8113-4b6f-ac38-6b8543b0a950', 'complete', '[{"section_name": "Technical Skills", "content": "Significant improvement since your last review. You\'ve added READMEs to all pinned repositories wi ... (1361 characters truncated) ... rch", "Add your CodePath AI 201 completion to your resume education section", "Request LinkedIn recommendations from peers who\'ve seen your code"]}]', 0.81, None, datetime.datetime(2026, 7, 15, 22, 38, 2, 193068), datetime.datetime(2026, 7, 15, 22, 38, 2, 193153)), ('6e5323cd-009a-440f-b51a-1a06b22401f2', '3eafb0a5-8113-4b6f-ac38-6b8543b0a950', 'failed', 'null', None, 'GitHub API rate limit exceeded. Please try again later.', datetime.datetime(2026, 7, 18, 21, 38, 2, 193388), datetime.datetime(2026, 7, 18, 21, 38, 2, 193476)), ('afd9e396-626f-48da-b5c8-2e77c84c523f', '6b64ef94-b7c3-4622-aa40-6ff3ed25340b', 'complete', '[{"section_name": "Technical Skills", "content": "Your profile shows 4 public repositories, all created within the last 6 months. The code quality is ... (1475 characters truncated) ... eplace your portfolio URL \\u2014 even a simple GitHub Pages site is better than a 404", "Create a LinkedIn profile and connect it to your GitHub"]}]', 0.58, None, datetime.datetime(2026, 7, 11, 22, 38, 2, 198874), datetime.datetime(2026, 7, 11, 22, 38, 2, 198943)), ('20962dc4-b53e-4d10-b888-2ec36a0b7b7d', 'bad0cfe3-cf15-4181-bb14-11e2bfc2cc56', 'complete', '[{"section_name": "Technical Skills", "content": "Strong technical foundation across your 23 public repositories. Your most recent projects show cons ... (1646 characters truncated) ...  proposal to a local Python or backend engineering meetup", "Ask two former collaborators for LinkedIn recommendations focused on technical depth"]}]', 0.87, None, datetime.datetime(2026, 6, 27, 22, 38, 2, 204407), datetime.datetime(2026, 6, 27, 22, 38, 2, 204490)), ('c6b07062-f777-46eb-afb6-89710d090b3e', 'bad0cfe3-cf15-4181-bb14-11e2bfc2cc56', 'complete', '[{"section_name": "Technical Skills", "content": "Excellent progress. Your new Rust project shows you\'re actively expanding beyond your Python comfo ... (1528 characters truncated) ...  "Add a brief \'currently interested in\' note to your GitHub bio", "Reach out directly to 3\\u20135 companies whose engineering blogs you follow"]}]', 0.91, None, datetime.datetime(2026, 7, 16, 22, 38, 2, 204627), datetime.datetime(2026, 7, 16, 22, 38, 2, 204703))]
2026-07-18 15:38:02,213 INFO sqlalchemy.engine.Engine COMMIT
COMMIT
2026-07-18T22:38:02.216542Z [info     ] Sample reviews created successfully [__main__]
2026-07-18T22:38:02.216829Z [info     ] Database seeding completed successfully [__main__]

✓ Database seeded successfully!

Sample user credentials:
  Email: user1@example.com
  Password: password1

  Email: user2@example.com
  Password: password2

  Email: user3@example.com
  Password: password3

cd frontend && npm install
/usr/bin/sh: line 1: npm: command not found
make: *** [setup] Error 127

s-bas@Brad_Laptop MINGW64 ~/Codepath AI201/pathreview (main)
$ 















