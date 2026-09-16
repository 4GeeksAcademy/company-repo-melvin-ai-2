FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY api/requirements.txt /app/requirements.txt
ENV UV_SYSTEM_PYTHON=1
RUN uv pip install -r /app/requirements.txt

COPY api /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
