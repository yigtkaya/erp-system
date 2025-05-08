import pandas as pd
from django.http import HttpResponse
from io import BytesIO
import xlsxwriter
from datetime import datetime

class ExportService:
    @staticmethod
    def export_to_excel(queryset, filename, fields, headers=None):
        """Export queryset to Excel"""
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1
        })
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
        
        # Write headers
        headers = headers or fields
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Set column widths
        for col in range(len(headers)):
            worksheet.set_column(col, col, 15)
        
        # Write data
        for row_num, obj in enumerate(queryset, 1):
            for col, field in enumerate(fields):
                value = getattr(obj, field)
                
                # Handle different field types
                if hasattr(value, 'strftime'):
                    worksheet.write_datetime(row_num, col, value, date_format)
                elif isinstance(value, bool):
                    worksheet.write(row_num, col, 'Yes' if value else 'No')
                elif value is None:
                    worksheet.write(row_num, col, '')
                else:
                    # Handle related fields
                    if '.' in field:
                        parts = field.split('.')
                        for part in parts:
                            value = getattr(value, part) if value else None
                    worksheet.write(row_num, col, str(value))
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
    
    @staticmethod
    def export_to_csv(queryset, filename, fields, headers=None):
        """Export queryset to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        
        # Create DataFrame
        data = []
        for obj in queryset:
            row = {}
            for field in fields:
                value = getattr(obj, field)
                if hasattr(value, 'strftime'):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, bool):
                    value = 'Yes' if value else 'No'
                elif '.' in field:
                    parts = field.split('.')
                    for part in parts:
                        value = getattr(value, part) if value else None
                row[field] = value
            data.append(row)
        
        df = pd.DataFrame(data)
        if headers:
            df.columns = headers
        
        df.to_csv(response, index=False)
        return response
    
    @staticmethod
    def export_report(report_type, data, filename):
        """Export various reports"""
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # Add a worksheet for each section of the report
        for sheet_name, sheet_data in data.items():
            worksheet = workbook.add_worksheet(sheet_name[:31])  # Excel sheet name limit
            
            # Add headers
            if sheet_data:
                headers = list(sheet_data[0].keys())
                for col, header in enumerate(headers):
                    worksheet.write(0, col, header)
                
                # Add data
                for row_num, row_data in enumerate(sheet_data, 1):
                    for col, header in enumerate(headers):
                        worksheet.write(row_num, col, row_data[header])
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response