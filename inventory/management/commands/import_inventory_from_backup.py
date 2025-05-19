import os
import re
import unicodedata
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from inventory.models import (
    Product, RawMaterial, InventoryCategory, UnitOfMeasure,
    MaterialType, ProductType
)
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import inventory data (products and raw materials) from a SQL backup file'

    def add_arguments(self, parser):
        parser.add_argument('backup_file', type=str, help='Path to the SQL backup file')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Parse the backup file but do not save to database',
        )
        parser.add_argument(
            '--sanitize-codes',
            action='store_true',
            help='Sanitize product and material codes by replacing special characters',
            default=True,
        )

    def handle(self, *args, **options):
        backup_file_path = options['backup_file']
        dry_run = options['dry_run']
        self.sanitize_codes = options['sanitize_codes']
        
        # Check if file exists
        if not os.path.exists(backup_file_path):
            raise CommandError(f'Backup file {backup_file_path} does not exist')
        
        self.stdout.write(f"Starting import from {backup_file_path}")
        
        try:
            # Extract and import categories first
            categories_data = self.extract_inventory_categories(backup_file_path)
            if not dry_run:
                categories_created = self.import_inventory_categories(categories_data)
                self.stdout.write(self.style.SUCCESS(f"Imported {categories_created} inventory categories"))
            
            # Load categories and units from database
            self.categories = {cat.name: cat for cat in InventoryCategory.objects.all()}
            self.units = {unit.unit_code: unit for unit in UnitOfMeasure.objects.all()}
            
            # Extract units of measure if needed
            units_data = self.extract_units_of_measure(backup_file_path)
            if not dry_run and units_data:
                units_created = self.import_units_of_measure(units_data)
                self.stdout.write(self.style.SUCCESS(f"Imported {units_created} units of measure"))
                # Refresh units cache
                self.units = {unit.unit_code: unit for unit in UnitOfMeasure.objects.all()}
            
            # Parse SQL file and extract data
            product_data = self.extract_product_data(backup_file_path)
            raw_material_data = self.extract_raw_material_data(backup_file_path)
            
            if dry_run:
                self.stdout.write(self.style.SUCCESS(
                    f"Found {len(categories_data)} categories, {len(units_data)} units, "
                    f"{len(product_data)} products and {len(raw_material_data)} raw materials. "
                    f"Dry run - no changes made to database."
                ))
                return
            
            # Import data
            with transaction.atomic():
                products_created, products_updated = self.import_products(product_data)
                materials_created, materials_updated = self.import_raw_materials(raw_material_data)
            
            # Print summary
            self.stdout.write(self.style.SUCCESS(
                f"Import completed! Created {products_created} and updated {products_updated} products. "
                f"Created {materials_created} and updated {materials_updated} raw materials."
            ))
            
        except Exception as e:
            logger.error(f"Error during import: {str(e)}")
            raise CommandError(f"Failed to import data: {str(e)}")

    def sanitize_code(self, code):
        """Sanitize product or material codes by replacing special characters"""
        if not code or not self.sanitize_codes:
            return code
            
        # Replace specific Turkish/special characters
        replacements = {
            'Ø': 'O',
            'İ': 'I',
            'Ü': 'U',
            'Ğ': 'G',
            'Ş': 'S',
            'Ç': 'C',
            'Ö': 'O',
            ' ': '-',
        }
        
        sanitized = code
        for char, replacement in replacements.items():
            sanitized = sanitized.replace(char, replacement)
            
        # Remove any remaining non-ASCII characters
        sanitized = ''.join(c for c in unicodedata.normalize('NFD', sanitized)
                          if unicodedata.category(c) != 'Mn')
        
        # Remove any characters that are not letters, numbers, hyphens, or periods
        sanitized = re.sub(r'[^a-zA-Z0-9\-\.]', '', sanitized)
        
        if sanitized != code:
            self.stdout.write(f"Sanitized code: {code} -> {sanitized}")
            
        return sanitized
        
    def extract_inventory_categories(self, backup_file_path):
        """Extract inventory categories from SQL backup file"""
        categories = []
        category_pattern = r"COPY public\.inventory_inventorycategory.*?\\\.(?=\n\n)"
        copy_line_pattern = r"COPY public\.inventory_inventorycategory \((.*?)\) FROM stdin;"
        
        with open(backup_file_path, 'r', errors='replace') as f:
            content = f.read()
            
            # Find the COPY block for categories
            category_match = re.search(category_pattern, content, re.DOTALL)
            if not category_match:
                self.stdout.write(self.style.WARNING("No inventory category data found in backup file"))
                return categories
                
            category_block = category_match.group(0)
            
            # Extract column names
            copy_match = re.search(copy_line_pattern, category_block)
            if not copy_match:
                return categories
                
            column_names = [c.strip() for c in copy_match.group(1).split(',')]
            
            # Extract data rows
            data_lines = category_block.split('\n')[1:-1]  # Skip COPY line and trailing line
            
            for line in data_lines:
                if not line.strip():
                    continue
                    
                values = line.split('\t')
                category_dict = {}
                
                for i, col in enumerate(column_names):
                    if i < len(values):
                        val = values[i]
                        # Convert \N to None
                        category_dict[col] = None if val == '\\N' else val
                
                categories.append(category_dict)
                
        self.stdout.write(f"Extracted {len(categories)} inventory categories from backup")
        return categories

    def import_inventory_categories(self, category_data):
        """Import inventory categories into database"""
        created_count = 0
        
        for data in category_data:
            try:
                category_id = data.get('id')
                category_name = data.get('name')
                if not category_name:
                    continue
                    
                # Try to find existing category
                try:
                    # If the category exists, don't update it
                    InventoryCategory.objects.get(name=category_name)
                    self.stdout.write(f"Category already exists: {category_name}")
                    continue
                except InventoryCategory.DoesNotExist:
                    # Try to preserve the original ID if possible
                    if category_id and category_id.isdigit():
                        try:
                            InventoryCategory.objects.get(id=int(category_id))
                            # ID exists but with a different name, create a new one
                            category = InventoryCategory(name=category_name)
                        except InventoryCategory.DoesNotExist:
                            # We can use the original ID
                            category = InventoryCategory(id=int(category_id), name=category_name)
                    else:
                        category = InventoryCategory(name=category_name)
                        
                    category.description = data.get('description', '')
                    category.save()
                    created_count += 1
                    self.stdout.write(f"Created category: {category_name} (ID: {category.id})")
                    
            except Exception as e:
                logger.error(f"Error importing category {data.get('name')}: {str(e)}")
                self.stdout.write(self.style.ERROR(f"Failed to import category: {str(e)}"))
        
        return created_count

    def extract_units_of_measure(self, backup_file_path):
        """Extract units of measure from SQL backup file"""
        units = []
        unit_pattern = r"COPY public\.inventory_unitofmeasure.*?\\\.(?=\n\n)"
        copy_line_pattern = r"COPY public\.inventory_unitofmeasure \((.*?)\) FROM stdin;"
        
        with open(backup_file_path, 'r', errors='replace') as f:
            content = f.read()
            
            # Find the COPY block for units
            unit_match = re.search(unit_pattern, content, re.DOTALL)
            if not unit_match:
                self.stdout.write(self.style.WARNING("No unit of measure data found in backup file"))
                return units
                
            unit_block = unit_match.group(0)
            
            # Extract column names
            copy_match = re.search(copy_line_pattern, unit_block)
            if not copy_match:
                return units
                
            column_names = [c.strip() for c in copy_match.group(1).split(',')]
            
            # Extract data rows
            data_lines = unit_block.split('\n')[1:-1]  # Skip COPY line and trailing line
            
            for line in data_lines:
                if not line.strip():
                    continue
                    
                values = line.split('\t')
                unit_dict = {}
                
                for i, col in enumerate(column_names):
                    if i < len(values):
                        val = values[i]
                        # Convert \N to None
                        unit_dict[col] = None if val == '\\N' else val
                
                units.append(unit_dict)
                
        self.stdout.write(f"Extracted {len(units)} units of measure from backup")
        return units

    def import_units_of_measure(self, unit_data):
        """Import units of measure into database"""
        created_count = 0
        
        for data in unit_data:
            try:
                unit_id = data.get('id')
                unit_code = data.get('unit_code')
                unit_name = data.get('unit_name')
                
                if not unit_code or not unit_name:
                    continue
                    
                # Try to find existing unit
                try:
                    # If the unit exists by code, don't update it
                    UnitOfMeasure.objects.get(unit_code=unit_code)
                    self.stdout.write(f"Unit of measure already exists: {unit_code}")
                    continue
                except UnitOfMeasure.DoesNotExist:
                    # Try to preserve the original ID if possible
                    if unit_id and unit_id.isdigit():
                        try:
                            UnitOfMeasure.objects.get(id=int(unit_id))
                            # ID exists but with a different code, create a new one
                            unit = UnitOfMeasure(unit_code=unit_code, unit_name=unit_name)
                        except UnitOfMeasure.DoesNotExist:
                            # We can use the original ID
                            unit = UnitOfMeasure(id=int(unit_id), unit_code=unit_code, unit_name=unit_name)
                    else:
                        unit = UnitOfMeasure(unit_code=unit_code, unit_name=unit_name)
                        
                    unit.save()
                    created_count += 1
                    self.stdout.write(f"Created unit of measure: {unit_code} (ID: {unit.id})")
                    
            except Exception as e:
                logger.error(f"Error importing unit {data.get('unit_code')}: {str(e)}")
                self.stdout.write(self.style.ERROR(f"Failed to import unit: {str(e)}"))
        
        return created_count

    def extract_product_data(self, backup_file_path):
        """Extract product data from SQL backup file"""
        products = []
        product_pattern = r"COPY public\.inventory_product.*?\\\.(?=\n\n)"
        copy_line_pattern = r"COPY public\.inventory_product \((.*?)\) FROM stdin;"
        
        with open(backup_file_path, 'r', errors='replace') as f:
            content = f.read()
            
            # Find the COPY block for products
            product_match = re.search(product_pattern, content, re.DOTALL)
            if not product_match:
                self.stdout.write(self.style.WARNING("No product data found in backup file"))
                return products
                
            product_block = product_match.group(0)
            
            # Extract column names
            copy_match = re.search(copy_line_pattern, product_block)
            if not copy_match:
                return products
                
            column_names = [c.strip() for c in copy_match.group(1).split(',')]
            
            # Extract data rows
            data_lines = product_block.split('\n')[1:-1]  # Skip COPY line and trailing line
            
            for line in data_lines:
                if not line.strip():
                    continue
                    
                values = line.split('\t')
                product_dict = {}
                
                for i, col in enumerate(column_names):
                    if i < len(values):
                        val = values[i]
                        # Convert \N to None
                        product_dict[col] = None if val == '\\N' else val
                
                products.append(product_dict)
                
        self.stdout.write(f"Extracted {len(products)} products from backup")
        return products

    def extract_raw_material_data(self, backup_file_path):
        """Extract raw material data from SQL backup file"""
        materials = []
        material_pattern = r"COPY public\.inventory_rawmaterial.*?\\\.(?=\n\n)"
        copy_line_pattern = r"COPY public\.inventory_rawmaterial \((.*?)\) FROM stdin;"
        
        with open(backup_file_path, 'r', errors='replace') as f:
            content = f.read()
            
            # Find the COPY block for raw materials
            material_match = re.search(material_pattern, content, re.DOTALL)
            if not material_match:
                self.stdout.write(self.style.WARNING("No raw material data found in backup file"))
                return materials
                
            material_block = material_match.group(0)
            
            # Extract column names
            copy_match = re.search(copy_line_pattern, material_block)
            if not copy_match:
                return materials
                
            column_names = [c.strip() for c in copy_match.group(1).split(',')]
            
            # Extract data rows
            data_lines = material_block.split('\n')[1:-1]  # Skip COPY line and trailing line
            
            for line in data_lines:
                if not line.strip():
                    continue
                    
                values = line.split('\t')
                material_dict = {}
                
                for i, col in enumerate(column_names):
                    if i < len(values):
                        val = values[i]
                        # Convert \N to None
                        material_dict[col] = None if val == '\\N' else val
                
                materials.append(material_dict)
                
        self.stdout.write(f"Extracted {len(materials)} raw materials from backup")
        return materials

    def import_products(self, product_data):
        """Import products into database"""
        created_count = 0
        updated_count = 0
        
        for data in product_data:
            try:
                product_code = data.get('product_code')
                if not product_code:
                    continue
                
                # Sanitize product code if needed
                original_code = product_code
                product_code = self.sanitize_code(product_code)
                if not product_code:
                    self.stdout.write(self.style.WARNING(f"Could not sanitize product code: {original_code}"))
                    continue
                    
                # Fix inventory_category based on product_code pattern
                category_id = data.get('inventory_category_id')
                # If product code starts with 03.0, it should be in PROSES category (ID: 2)
                if product_code.startswith('03.0') and category_id not in ['1', '4', '5']:  # Not in HAMMADDE, KARANTINA, HURDA
                    # Force PROSES category (ID: 2) 
                    data['inventory_category_id'] = '2'
                    self.stdout.write(f"Forced PROSES category for product: {product_code}")
                
                # Try to find existing product
                try:
                    product = Product.objects.get(product_code=product_code)
                    is_new = False
                    self.stdout.write(f"Updating existing product: {product_code}")
                except Product.DoesNotExist:
                    product = Product(product_code=product_code)
                    is_new = True
                    self.stdout.write(f"Creating new product: {product_code}")
                
                # Update fields
                product.product_name = data.get('product_name', '')
                
                # Convert product_type to enum if needed
                product_type = data.get('product_type')
                if product_type and hasattr(ProductType, product_type):
                    product.product_type = product_type
                
                product.description = data.get('description', '')
                
                # Handle current_stock
                if data.get('current_stock') is not None:
                    product.current_stock = int(data.get('current_stock', 0))
                
                # Handle category
                category_id = data.get('inventory_category_id')
                if category_id and category_id.isdigit():
                    try:
                        category = InventoryCategory.objects.get(id=int(category_id))
                        product.inventory_category = category
                    except InventoryCategory.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f"Category ID {category_id} not found for product {product_code}")
                        )
                
                # Set default unit of measure if not present
                unit_id = data.get('unit_of_measure_id')
                if unit_id and unit_id.isdigit():
                    try:
                        unit = UnitOfMeasure.objects.get(id=int(unit_id))
                        product.unit_of_measure = unit
                    except UnitOfMeasure.DoesNotExist:
                        # Fallback to a default unit
                        default_unit = UnitOfMeasure.objects.filter(unit_code='PCS').first()
                        if default_unit:
                            product.unit_of_measure = default_unit
                            self.stdout.write(self.style.WARNING(
                                f"Using default unit PCS for product {product_code}, as unit ID {unit_id} not found")
                            )
                elif not hasattr(product, 'unit_of_measure') or not product.unit_of_measure:
                    default_unit = UnitOfMeasure.objects.filter(unit_code='PCS').first()
                    if default_unit:
                        product.unit_of_measure = default_unit
                
                # Save the product
                try:
                    product.save()
                    
                    if is_new:
                        created_count += 1
                    else:
                        updated_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to import product: {str(e)}"))
                    
            except Exception as e:
                logger.error(f"Error importing product {data.get('product_code')}: {str(e)}")
                self.stdout.write(self.style.ERROR(f"Failed to import product: {str(e)}"))
        
        return created_count, updated_count

    def import_raw_materials(self, material_data):
        """Import raw materials into database"""
        created_count = 0
        updated_count = 0
        
        for data in material_data:
            try:
                material_code = data.get('material_code')
                if not material_code:
                    continue
                    
                # Sanitize material code if needed
                original_code = material_code
                material_code = self.sanitize_code(material_code)
                if not material_code:
                    self.stdout.write(self.style.WARNING(f"Could not sanitize material code: {original_code}"))
                    continue
                
                # Make sure material is in HAMMADDE category (ID: 1) 
                data['inventory_category_id'] = '1'
                
                # Try to find existing material
                try:
                    material = RawMaterial.objects.get(material_code=material_code)
                    is_new = False
                    self.stdout.write(f"Updating existing material: {material_code}")
                except RawMaterial.DoesNotExist:
                    material = RawMaterial(material_code=material_code)
                    is_new = True
                    self.stdout.write(f"Creating new material: {material_code}")
                
                # Update fields
                material.material_name = data.get('material_name', '')
                
                # Handle current_stock
                if data.get('current_stock') is not None:
                    try:
                        material.current_stock = Decimal(data.get('current_stock', '0'))
                    except:
                        material.current_stock = Decimal('0')
                
                # Handle material_type
                material_type = data.get('material_type')
                if material_type and hasattr(MaterialType, material_type):
                    material.material_type = material_type
                
                # Handle dimensions
                for field in ['width', 'height', 'thickness', 'diameter_mm']:
                    if data.get(field) is not None and data.get(field) != '\\N':
                        try:
                            setattr(material, field, float(data.get(field)))
                        except:
                            pass
                
                # Handle category
                category_id = data.get('inventory_category_id')
                if category_id and category_id.isdigit():
                    try:
                        category = InventoryCategory.objects.get(id=int(category_id))
                        material.inventory_category = category
                    except InventoryCategory.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f"Category ID {category_id} not found for material {material_code}")
                        )
                
                # Handle unit
                unit_id = data.get('unit_id')
                if unit_id and unit_id.isdigit():
                    try:
                        unit = UnitOfMeasure.objects.get(id=int(unit_id))
                        material.unit = unit
                    except UnitOfMeasure.DoesNotExist:
                        # Fallback to a default unit
                        default_unit = UnitOfMeasure.objects.first()
                        if default_unit:
                            material.unit = default_unit
                            self.stdout.write(self.style.WARNING(
                                f"Using default unit for material {material_code}, as unit ID {unit_id} not found")
                            )
                
                # Save the material
                try:
                    material.save()
                    
                    if is_new:
                        created_count += 1
                    else:
                        updated_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to import material: {str(e)}"))
                    
            except Exception as e:
                logger.error(f"Error importing material {data.get('material_code')}: {str(e)}")
                self.stdout.write(self.style.ERROR(f"Failed to import material: {str(e)}"))
        
        return created_count, updated_count 