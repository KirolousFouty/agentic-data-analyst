# License and dependency notes

Project source: Apache-2.0 (see `LICENSE`). The synthetic data is generated locally and may be used under the same license.

Key dependencies retain their own licenses: FastAPI (MIT), SQLAlchemy (MIT), SQLGlot (MIT), LangGraph/LangChain components (MIT), Streamlit (Apache-2.0), Plotly.py (MIT), Prometheus Python client (Apache-2.0), PostgreSQL (PostgreSQL License), and Ollama (MIT). Review the installed lock/artifact metadata before redistribution.

The recommended `qwen2.5:3b-instruct` model is downloaded locally by Ollama. Its model license and usage terms are distributed with the model registry; operators must review and accept the model card/license applicable to the exact tag they pull. This project does not bundle model weights.
