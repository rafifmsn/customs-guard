FROM langflowai/langflow:latest

WORKDIR /app

COPY .streamlit ./.streamlit
COPY scripts ./scripts
COPY api ./api
COPY ui ./ui
COPY data/seed ./data/seed

EXPOSE 8501

ENTRYPOINT ["sh", "-c", "uv pip install streamlit && python -m streamlit run ui/app.py --server.port=8501 --server.address=0.0.0.0"]
