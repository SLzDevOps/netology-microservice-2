FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn python-multipart pillow minio

COPY uploader.py .

CMD ["uvicorn", "uploader:app", "--host", "0.0.0.0", "--port", "8080"]
