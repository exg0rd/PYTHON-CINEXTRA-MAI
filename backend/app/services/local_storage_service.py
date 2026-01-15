"""
Local file storage service - альтернатива MinIO для режима разработки
"""
import os
import shutil
import asyncio
from typing import Optional, List, BinaryIO
from pathlib import Path
import aiofiles
from app.core.logging import logger


class LocalStorageService:
    """Сервис для локального хранения файлов (альтернатива MinIO)"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getenv("LOCAL_STORAGE_PATH", "storage"))
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Создает необходимые директории"""
        directories = ["videos", "thumbnails", "manifests", "processed-videos"]
        
        for directory in directories:
            dir_path = self.base_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {dir_path}")
    
    def _get_full_path(self, bucket: str, object_name: str) -> Path:
        """Получает полный путь к файлу"""
        return self.base_path / bucket / object_name
    
    async def upload_file(self, bucket: str, object_name: str, file_path: str) -> str:
        """Копирует файл в локальное хранилище"""
        try:
            dest_path = self._get_full_path(bucket, object_name)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, shutil.copy2, file_path, str(dest_path))
            
            logger.info(f"Uploaded file {file_path} to {bucket}/{object_name}")
            return object_name
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise e
    
    async def upload_data(self, bucket: str, object_name: str, data: bytes, content_type: str = None) -> str:
        """Сохраняет данные в файл"""
        try:
            dest_path = self._get_full_path(bucket, object_name)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(dest_path, 'wb') as f:
                await f.write(data)
            
            logger.info(f"Uploaded data to {bucket}/{object_name}")
            return object_name
            
        except Exception as e:
            logger.error(f"Error uploading data: {e}")
            raise e
    
    async def upload_text(self, bucket: str, object_name: str, text: str) -> str:
        """Сохраняет текст в файл"""
        return await self.upload_data(bucket, object_name, text.encode('utf-8'), 'text/plain')
    
    async def download_file(self, bucket: str, object_name: str, file_path: str) -> str:
        """Копирует файл из хранилища"""
        try:
            src_path = self._get_full_path(bucket, object_name)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, shutil.copy2, str(src_path), file_path)
            
            logger.info(f"Downloaded {bucket}/{object_name} to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            raise e
    
    async def get_object_data(self, bucket: str, object_name: str) -> bytes:
        """Читает данные файла"""
        try:
            file_path = self._get_full_path(bucket, object_name)
            
            async with aiofiles.open(file_path, 'rb') as f:
                data = await f.read()
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting object data: {e}")
            raise e
    
    def get_object_stream(self, bucket: str, object_name: str):
        """Получает поток данных файла"""
        try:
            file_path = self._get_full_path(bucket, object_name)
            return open(file_path, 'rb')
        except Exception as e:
            logger.error(f"Error getting object stream: {e}")
            raise e
    
    async def delete_object(self, bucket: str, object_name: str) -> bool:
        """Удаляет файл"""
        try:
            file_path = self._get_full_path(bucket, object_name)
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted {bucket}/{object_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting object: {e}")
            return False
    
    async def list_objects(self, bucket: str, prefix: str = None) -> List[str]:
        """Получает список файлов"""
        try:
            bucket_path = self.base_path / bucket
            
            if prefix:
                search_path = bucket_path / prefix
            else:
                search_path = bucket_path
            
            if not search_path.exists():
                return []
            
            objects = []
            for path in search_path.rglob('*'):
                if path.is_file():
                    rel_path = path.relative_to(bucket_path)
                    objects.append(str(rel_path))
            
            return objects
            
        except Exception as e:
            logger.error(f"Error listing objects: {e}")
            return []
    
    async def object_exists(self, bucket: str, object_name: str) -> bool:
        """Проверяет существование файла"""
        file_path = self._get_full_path(bucket, object_name)
        return file_path.exists()
    
    async def get_presigned_url(self, bucket: str, object_name: str, expires: int = 3600) -> str:
        """Возвращает локальный путь (для dev режима)"""
        return f"/storage/{bucket}/{object_name}"
    
    async def upload_multipart_file(self, bucket: str, object_name: str, file_data: BinaryIO, file_size: int) -> str:
        """Сохраняет большой файл"""
        try:
            dest_path = self._get_full_path(bucket, object_name)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(dest_path, 'wb') as f:
                while chunk := file_data.read(8192):
                    await f.write(chunk)
            
            logger.info(f"Uploaded multipart file to {bucket}/{object_name}")
            return object_name
            
        except Exception as e:
            logger.error(f"Error uploading multipart file: {e}")
            raise e


def get_storage_service():
    """Возвращает сервис хранения в зависимости от конфигурации"""
    use_minio = os.getenv("USE_MINIO", "false").lower() == "true"
    
    if use_minio:
        from app.services.minio_service import MinIOService
        return MinIOService()
    else:
        return LocalStorageService()
