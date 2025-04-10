from fastmcp import FastMCP
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError
import os
import json
import re
import mimetypes

load_dotenv()
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")

blob_service_client = None
try:
    if not AZURE_CONNECTION_STRING:
        print("Warning: AZURE_CONNECTION_STRING environment variable not found!")
    else:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        print("Successfully connected to Azure Blob Storage")
except Exception as e:
    print(f"Error connecting to Azure Blob Storage: {str(e)}")

mcp = FastMCP("AzureStorageAssistant")

@mcp.tool(description="Lists all containers in the storage account")
def list_containers() -> str:
    if not blob_service_client:
        return "Azure Blob Storage client is not initialized. Check your connection string."
    
    try:
        containers = [container.name for container in blob_service_client.list_containers()]
        if containers:
            return f"Found {len(containers)} containers: " + ", ".join(containers)
        return "No containers found in this storage account."
    except Exception as e:
        return f"Error listing containers: {str(e)}"

@mcp.tool(description="Lists all blobs in a specified Azure storage container")
def list_blobs(container: str, prefix: str = "") -> str:
    if not blob_service_client:
        return "Azure Blob Storage client is not initialized. Check your connection string."
    
    try:
        container_client = blob_service_client.get_container_client(container)
        blobs = [blob.name for blob in container_client.list_blobs(name_starts_with=prefix)]
        if blobs:
            return f"Found {len(blobs)} blobs in {container}: " + ", ".join(blobs)
        return f"No blobs found in {container}" + (f" with prefix '{prefix}'" if prefix else ".")
    except Exception as e:
        return f"Error listing blobs in {container}: {str(e)}"

@mcp.tool(description="Get blob metadata and properties")
def get_blob_info(container: str, blob_name: str) -> str:
    if not blob_service_client:
        return "Azure Blob Storage client is not initialized. Check your connection string."
    
    try:
        blob_client = blob_service_client.get_blob_client(container=container, blob=blob_name)
        properties = blob_client.get_blob_properties()
        
        info = {
            "name": blob_name,
            "size_bytes": properties.size,
            "content_type": properties.content_settings.content_type,
            "last_modified": str(properties.last_modified),
            "creation_time": str(properties.creation_time),
            "lease_status": properties.lease.status,
            "metadata": dict(properties.metadata) if properties.metadata else {}
        }
        
        return json.dumps(info, indent=2)
    except ResourceNotFoundError:
        return f"Blob '{blob_name}' not found in container '{container}'."
    except Exception as e:
        return f"Error getting blob info: {str(e)}"

@mcp.tool(description="Create a new container")
def create_container(container: str) -> str:
    if not blob_service_client:
        return "Azure Blob Storage client is not initialized. Check your connection string."
    
    try:
        blob_service_client.create_container(container)
        return f"Container '{container}' created successfully."
    except ResourceExistsError:
        return f"Container '{container}' already exists."
    except Exception as e:
        return f"Error creating container: {str(e)}"

@mcp.tool(description="Delete a container")
def delete_container(container: str, confirm: str = "no") -> str:
    if not blob_service_client:
        return "Azure Blob Storage client is not initialized. Check your connection string."
    
    if confirm.lower() != "yes":
        return f"To delete container '{container}', set confirm parameter to 'yes'."
    
    try:
        blob_service_client.delete_container(container)
        return f"Container '{container}' deleted successfully."
    except ResourceNotFoundError:
        return f"Container '{container}' not found."
    except Exception as e:
        return f"Error deleting container: {str(e)}"

@mcp.tool(description="Upload a file to blob storage")
def upload_blob(container: str, local_file_path: str, blob_name: str = None) -> str:
    if not blob_service_client:
        return "Azure Blob Storage client is not initialized. Check your connection string."
    
    if not os.path.exists(local_file_path):
        return f"Local file '{local_file_path}' not found."
    
    if not blob_name:
        blob_name = os.path.basename(local_file_path)
    
    try:
        content_type, _ = mimetypes.guess_type(local_file_path)
        content_settings = ContentSettings(content_type=content_type)
        
        container_client = blob_service_client.get_container_client(container)
        
        with open(local_file_path, "rb") as data:
            blob_client = container_client.upload_blob(
                name=blob_name, 
                data=data, 
                overwrite=True,
                content_settings=content_settings
            )
        
        return f"File uploaded successfully to '{container}/{blob_name}'"
    except ResourceNotFoundError:
        return f"Container '{container}' not found."
    except Exception as e:
        return f"Error uploading file: {str(e)}"

@mcp.tool(description="Download a blob to local file")
def download_blob(container: str, blob_name: str, local_file_path: str = None) -> str:
    """Download a blob to a local file."""
    if not blob_service_client:
        return "Azure Blob Storage client is not initialized. Check your connection string."
    
    if not local_file_path:
        local_file_path = os.path.basename(blob_name)
    
    try:
        blob_client = blob_service_client.get_blob_client(container=container, blob=blob_name)
        
        with open(local_file_path, "wb") as file:
            data = blob_client.download_blob()
            file.write(data.readall())
        
        return f"Blob '{blob_name}' downloaded successfully to '{local_file_path}'"
    except ResourceNotFoundError:
        return f"Blob '{blob_name}' not found in container '{container}'."
    except Exception as e:
        return f"Error downloading blob: {str(e)}"

@mcp.tool(description="Delete a blob from storage")
def delete_blob(container: str, blob_name: str, confirm: str = "no") -> str:
    if not blob_service_client:
        return "Azure Blob Storage client is not initialized. Check your connection string."
    
    if confirm.lower() != "yes":
        return f"To delete blob '{blob_name}', set confirm parameter to 'yes'."
    
    try:
        blob_client = blob_service_client.get_blob_client(container=container, blob=blob_name)
        blob_client.delete_blob()
        return f"Blob '{blob_name}' deleted successfully from container '{container}'."
    except ResourceNotFoundError:
        return f"Blob '{blob_name}' not found in container '{container}'."
    except Exception as e:
        return f"Error deleting blob: {str(e)}"

@mcp.tool(description="Search for blobs matching a pattern")
def search_blobs(container: str, pattern: str) -> str:
    if not blob_service_client:
        return "Azure Blob Storage client is not initialized. Check your connection string."
    
    try:
        container_client = blob_service_client.get_container_client(container)
        all_blobs = [blob.name for blob in container_client.list_blobs()]
        
        matching_blobs = [blob for blob in all_blobs if re.search(pattern, blob)]
        
        if matching_blobs:
            return f"Found {len(matching_blobs)} matching blobs in {container}: " + ", ".join(matching_blobs)
        return f"No blobs matching pattern '{pattern}' found in {container}."
    except Exception as e:
        return f"Error searching blobs: {str(e)}"


def main():
    print("Starting Azure Assistant MCP Server...")
    try:
        mcp.run() 
    except Exception as e:
        print(f"Failed to start MCP Server: {str(e)}")

if __name__ == "__main__":
    main()