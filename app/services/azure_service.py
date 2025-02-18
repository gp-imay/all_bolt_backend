# app/services/azure_service.py
from fastapi import HTTPException, UploadFile, status
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.exceptions import AzureError
import logging
from uuid import UUID
from typing import Optional
from config import settings
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

class AzureStorageService:
    def __init__(self):
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = settings.AZURE_CONTAINER_NAME
        self.allowed_content_types = settings.AZURE_ALLOWED_FILE_TYPES
        self.max_file_size = settings.MAX_FILE_SIZE

    async def upload_file(self, file: UploadFile, script_id: UUID) -> str:
        """
        Upload a file to Azure Blob Storage
        """
        try:
            # Validate file
            await self._validate_file(file)
            
            # Generate blob name
            blob_name = f"scripts/{script_id}/{file.filename}"
            
            # Create blob service client
            blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
            
            # Get container client
            container_client = blob_service_client.get_container_client(
                self.container_name
            )
            
            # Get blob client
            blob_client = container_client.get_blob_client(blob_name)
            
            # Set content settings
            content_settings = ContentSettings(
                content_type=file.content_type
            )
            
            # Upload file
            file_contents = await file.read()
            await asyncio.to_thread(
                blob_client.upload_blob,
                file_contents,
                overwrite=True,
                content_settings=content_settings
            )
            
            # Return the URL
            return blob_client.url
            
        except AzureError as e:
            logger.error(f"Azure storage error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error uploading file to storage"
            )
        except Exception as e:
            logger.error(f"Unexpected error during file upload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected error during file upload"
            )
        finally:
            await file.close()

    async def delete_file(self, script_id: UUID, filename: str) -> bool:
        """
        Delete a file from Azure Blob Storage
        """
        try:
            blob_name = f"scripts/{script_id}/{filename}"
            
            blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
            container_client = blob_service_client.get_container_client(
                self.container_name
            )
            blob_client = container_client.get_blob_client(blob_name)
            
            await asyncio.to_thread(blob_client.delete_blob)
            return True
            
        except AzureError as e:
            logger.error(f"Azure storage error: {str(e)}")
            return False

    async def _validate_file(self, file: UploadFile):
        """
        Validate file size and type
        """
        if file.content_type not in self.allowed_content_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {self.allowed_content_types}"
            )
        
        # Check file size
        file_size = 0
        while chunk := await file.read(8192):
            file_size += len(chunk)
            if file_size > self.max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too large. Maximum size: {self.max_file_size} bytes"
                )
        
        # Reset file position
        await file.seek(0)

    async def get_file_url(self, script_id: UUID, filename: str) -> Optional[str]:
        """
        Get the URL for a file
        """
        try:
            blob_name = f"scripts/{script_id}/{filename}"
            
            blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
            container_client = blob_service_client.get_container_client(
                self.container_name
            )
            blob_client = container_client.get_blob_client(blob_name)
            
            # Check if blob exists
            exists = await asyncio.to_thread(blob_client.exists)
            if exists:
                return blob_client.url
            return None
            
        except AzureError as e:
            logger.error(f"Azure storage error: {str(e)}")
            return None