from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver

@receiver(pre_save, sender=CalibrationRecord)
def validate_calibration_dates(sender, instance, **kwargs):
    if instance.next_calibration_date <= instance.calibration_date:
        raise ValidationError("Next calibration date must be after calibration date") 