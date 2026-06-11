FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn python-jose[cryptography] pydantic

COPY security.py .

CMD ["uvicorn", "security:app", "--host", "0.0.0.0", "--port", "8080"]
