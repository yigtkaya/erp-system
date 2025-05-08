import pandas as pd
from django.db import transaction
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class ImportService:
    @staticmethod
    def import_from_excel(file, model_class, field_mapping, user):
        """Import data from Excel file"""
        try:
            # Read Excel file
            df = pd.read_excel(file)
            df = df.fillna('')  # Replace NaN with empty string
            
            results = {
                'success': 0,
                'errors': [],
                'total': len(df)
            }
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        data = {}
                        for excel_field, model_field in field_mapping.items():
                            if excel_field in row:
                                value = row[excel_field]
                                
                                # Handle boolean fields
                                if isinstance(value, str) and value.lower() in ['yes', 'no']:
                                    value = value.lower() == 'yes'
                                
                                data[model_field] = value
                        
                        # Add audit fields
                        data['created_by'] = user
                        data['modified_by'] = user
                        
                        # Create instance and validate
                        obj = model_class(**data)
                        obj.full_clean()
                        obj.save()
                        results['success'] += 1
                        
                    except ValidationError as e:
                        results['errors'].append({
                            'row': index + 2,  # Excel row number (1-indexed + header)
                            'errors': e.message_dict if hasattr(e, 'message_dict') else str(e)
                        })
                    except Exception as e:
                        results['errors'].append({
                            'row': index + 2,
                            'error': str(e)
                        })
            
            return results
            
        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            raise
    
    @staticmethod
    def validate_import_file(file, expected_columns):
        """Validate Excel file before import"""
        try:
            df = pd.read_excel(file)
            file_columns = list(df.columns)
            
            missing_columns = [col for col in expected_columns if col not in file_columns]
            extra_columns = [col for col in file_columns if col not in expected_columns]
            
            return {
                'valid': len(missing_columns) == 0,
                'missing_columns': missing_columns,
                'extra_columns': extra_columns,
                'total_rows': len(df)
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_import_template(model_class, fields, filename):
        """Generate import template"""
        df = pd.DataFrame(columns=fields)
        
        # Add sample data
        sample_data = {
            'Product Code': 'PROD-001',
            'Product Name': 'Sample Product',
            'Type': 'SINGLE',
            'Current Stock': 100,
            'Reorder Point': 20,
            # Add more sample data based on model
        }
        
        df = df.append(sample_data, ignore_index=True)
        
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response