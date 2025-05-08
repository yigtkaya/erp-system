# Common Module - Product Requirements Document

## Overview

The Common module provides shared functionality and services used across all modules of the ERP system. It implements reusable components, utilities, and integrations that promote consistency and reduce duplication across the system.

## Features

### File Management System

- **Version Control**: Track multiple versions of files with version history
- **File Categorization**: Organize files by category (Technical, Quality, Order, Product, etc.)
- **Content Type Association**: Associate files with specific content types in the system
- **Metadata Storage**: Store file metadata including size, checksum, and custom attributes
- **Image Processing**: Automatically generate thumbnails and previews for image files
- **File Validation**: Enforce file type and size restrictions based on categories
- **Storage Abstraction**: Support for Cloudflare R2 or local file storage

### File Type Management

- **Allowed File Types**: Define and manage allowed file extensions and MIME types
- **Size Restrictions**: Set maximum file sizes by file type and category
- **Security Controls**: Prevent upload of potentially harmful file types

### Common UI Components

- **Reusable Views**: Shared view implementations for common patterns
- **File Upload/Download**: Standardized interfaces for file operations
- **Serialization**: Common serialization patterns for API responses

### Permission Management

- **Centralized Permissions**: Shared permission definitions and checks
- **Cross-Module Access Control**: Consistent permission enforcement across modules

### Utilities

- **File Storage Management**: Statistics and management of file storage usage
- **Integrity Verification**: File checksum generation and validation
- **Path Generation**: Standardized file path generation for organized storage

## Technical Requirements

### Models

- `FileVersion`: Version-controlled file storage with metadata
- `AllowedFileType`: Definitions of permitted file types and restrictions
- `FileVersionManager`: Static utility class for file management operations

### Services

- File integrity validation
- Storage management and monitoring
- Image processing for thumbnails and previews

### Integration Points

- Core module for user information
- All other modules for file storage needs
- External storage systems (Cloudflare R2)

## Security Considerations

- File type validation to prevent security vulnerabilities
- File integrity verification with checksums
- Size restrictions to prevent denial of service
- Permissions for file access across modules

## Future Enhancements

- Advanced search capabilities for files
- Document preview for various file types
- OCR for document indexing
- Full-text search for document content
- Enhanced file compression
- Virus scanning for uploaded files
- Watermarking for sensitive documents
- Digital signatures for document authenticity
