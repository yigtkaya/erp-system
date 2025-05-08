# core/utils.py
from django.db import models, transaction
from django.utils import timezone

class SequenceGenerator:
    """Generate sequential numbers for documents"""
    
    @staticmethod
    def get_next_number(prefix, model_class, field_name='number', year_based=True):
        with transaction.atomic():
            current_year = timezone.now().year
            
            if year_based:
                prefix_with_year = f"{prefix}-{current_year}"
                last_record = model_class.objects.filter(
                    **{f"{field_name}__startswith": prefix_with_year}
                ).order_by(f'-{field_name}').first()
                
                if last_record:
                    last_number = getattr(last_record, field_name)
                    sequence = int(last_number.split('-')[-1]) + 1
                else:
                    sequence = 1
                
                return f"{prefix_with_year}-{sequence:05d}"
            else:
                last_record = model_class.objects.filter(
                    **{f"{field_name}__startswith": prefix}
                ).order_by(f'-{field_name}').first()
                
                if last_record:
                    last_number = getattr(last_record, field_name)
                    sequence = int(last_number.split('-')[-1]) + 1
                else:
                    sequence = 1
                
                return f"{prefix}-{sequence:05d}"

# Example usage in models
class WorkOrder(BaseModel):
    def save(self, *args, **kwargs):
        if not self.work_order_number:
            self.work_order_number = SequenceGenerator.get_next_number('WO', WorkOrder, 'work_order_number')
        super().save(*args, **kwargs)