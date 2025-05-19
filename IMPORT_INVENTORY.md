# Inventory Import Process

This document describes how to import inventory data (products and raw materials) from a backup SQL file to the ERP system.

## Prerequisites

- Access to the SQL backup file (e.g., `backup.sql`)
- Python installed with Django (for local import)
- Docker and Docker Compose installed (for Docker import)
- ERP system running either locally or in Docker

## Import Methods

There are two ways to import the data:

### 1. Standard Import (Local Environment)

If you're running the Django application locally:

```bash
# Change to the project directory
cd /path/to/erp-system

# Run the import script
./import_inventory_data.sh [path/to/backup.sql]
```

If no backup file path is provided, it will look for `backup.sql` in the current directory.

### 2. Docker Import

If you're running the application in Docker using docker-compose.dev.yml:

```bash
# Change to the project directory
cd /path/to/erp-system

# Run the Docker import script
./docker_import_inventory.sh [path/to/backup.sql]
```

## Import Process

Both scripts perform the following steps:

1. Verify the backup file exists
2. Run a dry run of the import to validate data without making changes
3. Ask for confirmation before proceeding with the actual import
4. Import the data to the database
5. Report on the results

## Import Sequence

The import process follows a specific sequence to ensure dependencies are properly handled:

1. **Inventory Categories**: First, the system extracts and imports inventory categories from the backup file
2. **Units of Measure**: Next, units of measure are imported
3. **Products**: Products are imported with references to their categories and units
4. **Raw Materials**: Raw materials are imported with references to their categories and units

This sequence ensures that any referenced data exists before the products and materials are created.

## Code Sanitization

The import process automatically sanitizes product and material codes to ensure they meet the system's validation requirements:

1. **Special Characters**: Characters like 'Ø', 'İ', 'Ü', 'Ç' are replaced with their ASCII equivalents ('O', 'I', 'U', 'C')
2. **Space Characters**: Spaces are replaced with hyphens
3. **Invalid Characters**: Any characters that are not letters, numbers, hyphens, or periods are removed

Examples of sanitization:

- `02.BİL.Ø02.00` → `02.BIL.O02.00`
- `02.TOOLOX 44.20X40X80` → `02.TOOLOX-44.20X40X80`
- `02.YAYØ00.40L05.50Dİ01.70` → `02.YAYO00.40L05.50DI01.70`

## Category Handling

The import process enforces category rules based on product and material patterns:

1. **Raw Materials**: All materials are forced into the `HAMMADDE` category (ID: 1)
2. **Process Products**: Products with codes starting with `03.0` are placed in the `PROSES` category (ID: 2)
3. **Category Validation**: The system respects validation rules that restrict which categories products can belong to:
   - Single products can only be in `HAMMADDE`, `HURDA`, or `KARANTINA` categories
   - Montaged products can only be in `MAMUL`, `KARANTINA`, or `HURDA` categories

## Manual Import

If you need to run the import command manually:

```bash
# For local environment
python manage.py import_inventory_from_backup path/to/backup.sql [--dry-run] [--sanitize-codes]

# For Docker environment
docker compose -f docker-compose.dev.yml exec web python manage.py import_inventory_from_backup /app/path/to/backup.sql [--dry-run] [--sanitize-codes]
```

Options:

- `--dry-run`: Process the backup file but do not save any changes to the database
- `--sanitize-codes`: Automatically sanitize product and material codes (default: true)

## Monitoring the Import

The import process logs detailed information to:

- Console output showing progress and any errors
- The application log file which can be accessed to review issues

## Troubleshooting

### Common Issues

1. **File not found**: Ensure the backup file exists at the specified path.
2. **Data format issues**: If the backup format has changed, the import script may need to be updated.
3. **Missing categories or units**: The system will attempt to create required inventory categories and units of measure during import, but may fail if there are ID conflicts.
4. **ID conflicts**: If IDs in the backup conflict with existing records, the system will create new records with different IDs and provide warnings.
5. **Code validation failures**: If a product or material code contains characters that cannot be sanitized, the import for that item may fail.
6. **Category validation failures**: If a product is assigned to a category that violates the system's rules, it will not be imported.

### Recovery

If the import fails or causes issues:

1. If using the Docker environment, you can restore the database container to a previous state.
2. In a development environment, you might consider clearing the imported data and retrying.

## Data Fields

The import process handles the following data:

### Inventory Categories

- id
- name
- description

### Units of Measure

- id
- unit_code
- unit_name

### Products

- product_code
- product_name
- product_type
- description
- current_stock
- inventory_category
- unit_of_measure

### Raw Materials

- material_code
- material_name
- current_stock
- material_type
- dimensions (width, height, thickness, diameter_mm)
- inventory_category
- unit of measure
