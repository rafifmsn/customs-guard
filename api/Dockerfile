FROM langflowai/langflow:latest

WORKDIR /app

COPY scripts ./scripts
COPY api ./api
COPY data/seed ./data/seed

EXPOSE 8000

ENTRYPOINT ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
