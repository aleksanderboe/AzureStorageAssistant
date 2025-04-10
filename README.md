# Azure Storage Assistant

## Overview

This project provides an MCP (Multi-Component Platform) integration for interacting with Azure Blob Storage. It offers a set of tools that can be used through the FastMCP platform to manage containers, upload/download blobs, and perform various operations on Azure Storage accounts.

## Features

- **Container Management**:
  - List all containers in a storage account
  - Create new containers
  - Delete existing containers (with confirmation)

- **Blob Operations**:
  - List blobs within a container (with optional prefix filtering)
  - Upload files to blob storage
  - Download blobs to local files
  - Delete blobs (with confirmation)
  - Get detailed blob metadata and properties

- **Search Capabilities**:
  - Search for blobs using regular expression patterns
