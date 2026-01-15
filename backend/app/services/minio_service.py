import os
import asyncio
from typing import Optional, List, BinaryIO
from minio import Minio
from minio.error import S3Error
import aiofiles
from app.core.logging import logger


class MinIOService:
    """Сервис для работы с MinIO Object Storage"""
    
    def __init__(self):
        self.client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "admin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "password123"),
            secure=os.getenv("MINIO_USE_SSL", "false").lower() == "true"
        )
        
        # Проверяем подключение и создаем buckets если нужно
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """Создает необходимые buckets если они не существуют"""
        buckets = ["videos", "thumbnails", "manifests", "processed-videos"]
        
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info(f"Created MinIO bucket: {bucket}")
            except S3Error as e:
                logger.error(f"Error creating bucket {bucket}: {e}")
    
    async def upload_file_with_progress(self, bucket: str, object_name: str, file_path: str, 
                                      progress_callback=None) -> str:
        """Загружает файл в MinIO с мониторингом прогресса"""
        try:
            import os
            from io import BytesIO
            
            file_size = os.path.getsize(file_path)
            chunk_size = 8 * 1024 * 1024  # 8MB chunks
            uploaded = 0
            
            loop = asyncio.get_event_loop()
            
            def _upload_with_progress():
                with open(file_path, 'rb') as file_data:
                    # For small files, upload directly
                    if file_size <= chunk_size:
                        result = self.client.put_object(bucket, object_name, file_data, file_size)
                        if progress_callback:
                            progress_callback(100.0)
                        return result
                    
                    # For large files, use multipart upload with progress
                    return self.client.put_object(bucket, object_name, file_data, file_size)
            
            # If progress callback provided, monitor the upload
            if progress_callback and file_size > 0:
                # For now, we'll simulate progress since MinIO client doesn't provide built-in progress
                # In a real implementation, you'd need to use a custom progress callback
                progress_callback(0.0)
                
                result = await loop.run_in_executor(None, _upload_with_progress)
                
                progress_callback(100.0)
            else:
                result = await loop.run_in_executor(None, _upload_with_progress)
            
            logger.info(f"Uploaded file {file_path} to {bucket}/{object_name}")
            return object_name
            
        except S3Error as e:
            logger.error(f"Error uploading file to MinIO: {e}")
            raise e
    async def upload_file(self, bucket: str, object_name: str, file_path: str) -> str:
        """Загружает файл в MinIO"""
        return await self.upload_file_with_progress(bucket, object_name, file_path)
    
    async def upload_data(self, bucket: str, object_name: str, data: bytes, content_type: str = None) -> str:
        """Загружает данные в MinIO"""
        try:
            from io import BytesIO
            
            loop = asyncio.get_event_loop()
            
            def _upload():
                return self.client.put_object(
                    bucket, 
                    object_name, 
                    BytesIO(data), 
                    len(data),
                    content_type=content_type
                )
            
            result = await loop.run_in_executor(None, _upload)
            logger.info(f"Uploaded data to {bucket}/{object_name}")
            return object_name
            
        except S3Error as e:
            logger.error(f"Error uploading data to MinIO: {e}")
            raise e
    
    async def upload_text(self, bucket: str, object_name: str, text: str) -> str:
        """Загружает текст в MinIO"""
        return await self.upload_data(bucket, object_name, text.encode('utf-8'), 'text/plain')
    
    async def download_file(self, bucket: str, object_name: str, file_path: str) -> str:
        """Скачивает файл из MinIO"""
        try:
            loop = asyncio.get_event_loop()
            
            def _download():
                return self.client.fget_object(bucket, object_name, file_path)
            
            await loop.run_in_executor(None, _download)
            logger.info(f"Downloaded {bucket}/{object_name} to {file_path}")
            return file_path
            
        except S3Error as e:
            logger.error(f"Error downloading file from MinIO: {e}")
            raise e
    
    async def get_object_data(self, bucket: str, object_name: str) -> bytes:
        """Получает данные объекта из MinIO"""
        try:
            loop = asyncio.get_event_loop()
            
            def _get_data():
                response = self.client.get_object(bucket, object_name)
                data = response.read()
                response.close()
                response.release_conn()
                return data
            
            data = await loop.run_in_executor(None, _get_data)
            return data
            
        except S3Error as e:
            logger.error(f"Error getting object data from MinIO: {e}")
            raise e
    
    def get_object_stream(self, bucket: str, object_name: str):
        """Получает поток данных объекта из MinIO (синхронно для streaming)"""
        try:
            return self.client.get_object(bucket, object_name)
        except S3Error as e:
            logger.error(f"Error getting object stream from MinIO: {e}")
            raise e
    
    async def delete_object(self, bucket: str, object_name: str) -> bool:
        """Удаляет объект из MinIO"""
        try:
            loop = asyncio.get_event_loop()
            
            def _delete():
                return self.client.remove_object(bucket, object_name)
            
            await loop.run_in_executor(None, _delete)
            logger.info(f"Deleted {bucket}/{object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Error deleting object from MinIO: {e}")
            return False
    
    async def list_objects(self, bucket: str, prefix: str = None) -> List[str]:
        """Получает список объектов в bucket"""
        try:
            loop = asyncio.get_event_loop()
            
            def _list():
                objects = self.client.list_objects(bucket, prefix=prefix)
                return [obj.object_name for obj in objects]
            
            object_names = await loop.run_in_executor(None, _list)
            return object_names
            
        except S3Error as e:
            logger.error(f"Error listing objects from MinIO: {e}")
            return []
    
    async def object_exists(self, bucket: str, object_name: str) -> bool:
        """Проверяет существование объекта"""
        try:
            loop = asyncio.get_event_loop()
            
            def _stat():
                return self.client.stat_object(bucket, object_name)
            
            await loop.run_in_executor(None, _stat)
            return True
            
        except S3Error:
            return False
    
    async def get_presigned_url(self, bucket: str, object_name: str, expires: int = 3600) -> str:
        """Генерирует подписанный URL для доступа к объекту"""
        try:
            loop = asyncio.get_event_loop()
            
            def _get_url():
                from datetime import timedelta
                return self.client.presigned_get_object(
                    bucket, 
                    object_name, 
                    expires=timedelta(seconds=expires)
                )
            
            url = await loop.run_in_executor(None, _get_url)
            return url
            
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise e
    
    async def upload_multipart_file(self, bucket: str, object_name: str, file_data: BinaryIO, file_size: int) -> str:
        """Загружает большой файл по частям"""
        try:
            loop = asyncio.get_event_loop()
            
            def _upload():
                return self.client.put_object(
                    bucket, 
                    object_name, 
                    file_data, 
                    file_size
                )
            
            result = await loop.run_in_executor(None, _upload)
            logger.info(f"Uploaded multipart file to {bucket}/{object_name}")
            return object_name
            
        except S3Error as e:
            logger.error(f"Error uploading multipart file: {e}")
            raise e
    
    def get_bucket_policy(self, bucket: str) -> Optional[str]:
        """Получает политику bucket"""
        try:
            return self.client.get_bucket_policy(bucket)
        except S3Error:
            return None
    
    def set_bucket_policy(self, bucket: str, policy: str) -> bool:
        """Устанавливает политику bucket"""
        try:
            self.client.set_bucket_policy(bucket, policy)
            return True
        except S3Error as e:
            logger.error(f"Error setting bucket policy: {e}")
            return False