from fastapi import FastAPI, File, UploadFile, HTTPException
from minio import Minio
from minio.error import S3Error
import uuid
from PIL import Image
import io

app = FastAPI()

# MinIO client
minio_client = Minio(
    "minio:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

BUCKET_NAME = "images"

# Убедимся, что бакет существует (создаст init-контейнер)
# Но на всякий случай проверим
try:
    if not minio_client.bucket_exists(BUCKET_NAME):
        minio_client.make_bucket(BUCKET_NAME)
except:
    pass

@app.post("/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    # Проверка, что это изображение
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    
    # Читаем содержимое
    contents = await file.read()
    
    # Сжимаем изображение
    try:
        img = Image.open(io.BytesIO(contents))
        # Конвертируем в RGB если нужно
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        # Сжимаем до 800px по ширине
        img.thumbnail((800, 800))
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85)
        compressed = output.getvalue()
    except Exception as e:
        raise HTTPException(500, f"Image processing failed: {str(e)}")
    
    # Генерируем уникальное имя
    filename = f"{uuid.uuid4().hex}.jpg"
    
    # Загружаем в MinIO
    try:
        minio_client.put_object(
            BUCKET_NAME,
            filename,
            io.BytesIO(compressed),
            len(compressed),
            content_type="image/jpeg"
        )
    except S3Error as e:
        raise HTTPException(500, f"Failed to upload to storage: {str(e)}")
    
    return {"filename": filename}
