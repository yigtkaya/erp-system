# inventory/stock_manager.py
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Product, StockMovement

class StockManager:
    @staticmethod
    @transaction.atomic
    def reserve_stock(product, quantity, reference_type, reference_id):
        """Reserve stock for orders"""
        if product.available_stock < quantity:
            raise ValidationError(f"Insufficient stock. Available: {product.available_stock}")
        
        product.reserved_stock += quantity
        product.save()
        
        StockMovement.objects.create(
            product=product,
            movement_type='RESERVATION',
            quantity=quantity,
            reference_type=reference_type,
            reference_id=reference_id
        )
    
    @staticmethod
    @transaction.atomic
    def consume_stock(product, quantity, reference_type, reference_id):
        """Consume stock for production"""
        if product.current_stock < quantity:
            raise ValidationError(f"Insufficient stock. Current: {product.current_stock}")
        
        product.current_stock -= quantity
        if product.reserved_stock >= quantity:
            product.reserved_stock -= quantity
        product.save()
        
        StockMovement.objects.create(
            product=product,
            movement_type='CONSUMPTION',
            quantity=-quantity,
            reference_type=reference_type,
            reference_id=reference_id
        )
    
    @staticmethod
    @transaction.atomic
    def receive_stock(product, quantity, reference_type, reference_id):
        """Receive stock from purchases or production"""
        product.current_stock += quantity
        product.save()
        
        StockMovement.objects.create(
            product=product,
            movement_type='RECEIPT',
            quantity=quantity,
            reference_type=reference_type,
            reference_id=reference_id
        )