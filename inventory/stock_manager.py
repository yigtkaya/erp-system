# inventory/stock_manager.py
from django.db import transaction, models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum, F, Q, Case, When, Value, FloatField, ExpressionWrapper, OuterRef, Subquery
from django.db.models.functions import Coalesce
from decimal import Decimal
from .models import Product, StockMovement, ProductStock, StockTransaction, StockTransactionType, InventoryCategory

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

    @staticmethod
    def get_stock_levels(product=None, category=None, location=None, threshold=None):
        """
        Get current stock levels, optionally filtered by product, category or location
        Equivalent to vw_product_stock view in SQL
        """
        # Base query for products with their stock
        query = ProductStock.objects.select_related('product', 'category')
        
        # Apply filters if provided
        if product:
            query = query.filter(product=product)
        if category:
            query = query.filter(category=category)
        if location:
            query = query.filter(location=location)
        if threshold is not None:
            # Filter products that are below their reorder threshold
            query = query.annotate(
                threshold_diff=ExpressionWrapper(
                    F('quantity') - F('product__reorder_point'),
                    output_field=FloatField()
                )
            ).filter(threshold_diff__lte=threshold)
            
        return query
    
    @staticmethod
    def get_reorder_alerts():
        """
        Get products that need to be reordered based on reorder point
        Equivalent to vw_inventory_reorder_alert view in SQL
        """
        return ProductStock.objects.select_related('product', 'category').filter(
            ~Q(product__purchase_order_items__purchase_order__status='OPEN'),  # Exclude products with existing purchase orders
            quantity__lte=F('product__reorder_point'),
            product__is_active=True  # Only include active products
        ).annotate(
            quantity_to_order=ExpressionWrapper(
                F('product__reorder_quantity') - F('quantity'),
                output_field=FloatField()
            ),
            days_until_stockout=Case(
                # Calculate days until stockout based on usage rate
                When(
                    product__average_daily_usage__gt=0,
                    then=ExpressionWrapper(
                        F('quantity') / F('product__average_daily_usage'),
                        output_field=FloatField()
                    )
                ),
                default=Value(None),
                output_field=FloatField()
            )
        ).order_by(
            # Order by days until stockout (most urgent first)
            Case(
                When(days_until_stockout=None, then=Value(999999)),
                default=F('days_until_stockout'),
                output_field=FloatField()
            )
        )
    
    @staticmethod
    def get_product_stock_history(product, start_date=None, end_date=None):
        """
        Get stock history for a product
        Equivalent to fn_product_stock_history function in SQL
        """
        if not start_date:
            # Default to last 30 days
            start_date = timezone.now().date() - timezone.timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date() + timezone.timedelta(days=1)  # Include today
            
        return StockTransaction.objects.filter(
            product=product,
            transaction_date__range=(start_date, end_date)
        ).select_related(
            'product', 'category', 'work_order', 'purchase_order'
        ).order_by('transaction_date')
    
    @staticmethod
    def get_product_movement_summary(start_date=None, end_date=None, product=None, category=None):
        """
        Get summary of product movements
        Equivalent to vw_inventory_movement_summary view in SQL
        """
        if not start_date:
            # Default to last 30 days
            start_date = timezone.now().date() - timezone.timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date() + timezone.timedelta(days=1)  # Include today
            
        # Start building the query
        query = Product.objects.all()
        
        # Apply filters
        if product:
            query = query.filter(id=product.id)
        if category:
            query = query.filter(category=category)
            
        # Get beginning balance
        beginning_query = StockTransaction.objects.filter(
            transaction_date__lt=start_date,
            product=OuterRef('pk')
        ).values('product').annotate(
            total=Sum('quantity')
        ).values('total')
        
        # Get transactions in the period
        incoming_query = StockTransaction.objects.filter(
            transaction_date__range=(start_date, end_date),
            product=OuterRef('pk'),
            transaction_type__in=[
                StockTransactionType.PURCHASE_RECEIPT,
                StockTransactionType.PRODUCTION_RECEIPT,
                StockTransactionType.RETURN_RECEIPT,
                StockTransactionType.ADJUSTMENT_IN
            ]
        ).values('product').annotate(
            total=Sum('quantity')
        ).values('total')
        
        outgoing_query = StockTransaction.objects.filter(
            transaction_date__range=(start_date, end_date),
            product=OuterRef('pk'),
            transaction_type__in=[
                StockTransactionType.SALES_ISSUE,
                StockTransactionType.PRODUCTION_ISSUE,
                StockTransactionType.SCRAP,
                StockTransactionType.ADJUSTMENT_OUT
            ]
        ).values('product').annotate(
            total=Sum('quantity')
        ).values('total')
        
        # Annotate the products with the calculated values
        return query.annotate(
            beginning_balance=Coalesce(Subquery(beginning_query), Decimal('0')),
            incoming=Coalesce(Subquery(incoming_query), Decimal('0')),
            outgoing=Coalesce(Subquery(outgoing_query), Decimal('0')),
            ending_balance=Coalesce(Subquery(beginning_query), Decimal('0')) + 
                           Coalesce(Subquery(incoming_query), Decimal('0')) - 
                           Coalesce(Subquery(outgoing_query), Decimal('0'))
        )
    
    @staticmethod
    def get_slow_moving_inventory(days_threshold=90, min_value=1000):
        """
        Get slow moving inventory
        Equivalent to vw_slow_moving_inventory view in SQL
        """
        threshold_date = timezone.now().date() - timezone.timedelta(days=days_threshold)
        
        # Get the most recent transaction date for each product
        last_movement_subquery = StockTransaction.objects.filter(
            product=OuterRef('product'),
            transaction_type__in=[
                StockTransactionType.SALES_ISSUE,
                StockTransactionType.PRODUCTION_ISSUE
            ]
        ).values('product').annotate(
            last_date=models.Max('transaction_date')
        ).values('last_date')
        
        # Get products with stock and filter for slow moving ones
        return ProductStock.objects.select_related('product').filter(
            quantity__gt=0  # Only include products with stock
        ).annotate(
            last_movement_date=Subquery(last_movement_subquery),
            days_since_last_movement=Case(
                When(
                    last_movement_date__isnull=False,
                    then=ExpressionWrapper(
                        timezone.now().date() - F('last_movement_date'),
                        output_field=models.IntegerField()
                    )
                ),
                default=Value(days_threshold + 1),  # If never moved, consider as exceeding threshold
                output_field=models.IntegerField()
            ),
            stock_value=ExpressionWrapper(
                F('quantity') * F('product__standard_cost'),
                output_field=models.DecimalField(max_digits=12, decimal_places=2)
            )
        ).filter(
            Q(days_since_last_movement__gt=days_threshold) | Q(last_movement_date__isnull=True),  # Either exceeds days threshold or has no movement
            stock_value__gt=min_value  # Only include items with value above threshold
        ).order_by('-stock_value')  # Highest value first
    
    @staticmethod
    def get_inventory_aging_report(age_brackets=None):
        """
        Get inventory aging report
        Equivalent to vw_inventory_aging view in SQL
        """
        if age_brackets is None:
            # Default age brackets in days
            age_brackets = [30, 60, 90, 180, 365]
            
        today = timezone.now().date()
        
        # Start with all stock
        query = ProductStock.objects.select_related('product', 'category').filter(
            quantity__gt=0  # Only include products with stock
        )
        
        # Create annotations for each age bracket
        annotations = {
            f'age_bracket_{i}': Case(
                When(
                    Q(receipt_date__gt=today - timezone.timedelta(days=bracket)) &
                    Q(receipt_date__lte=today - timezone.timedelta(days=prev_bracket if i > 0 else 0)),
                    then=F('quantity')
                ),
                default=Value(0),
                output_field=models.DecimalField(max_digits=10, decimal_places=2)
            ) for i, (prev_bracket, bracket) in enumerate(zip([0] + age_brackets[:-1], age_brackets))
        }
        
        # Add a final bracket for items older than the last bracket
        annotations[f'age_bracket_{len(age_brackets)}'] = Case(
            When(
                receipt_date__lte=today - timezone.timedelta(days=age_brackets[-1]),
                then=F('quantity')
            ),
            default=Value(0),
            output_field=models.DecimalField(max_digits=10, decimal_places=2)
        )
        
        # Add value calculations
        for i in range(len(age_brackets) + 1):
            annotations[f'value_bracket_{i}'] = ExpressionWrapper(
                F(f'age_bracket_{i}') * F('product__standard_cost'),
                output_field=models.DecimalField(max_digits=12, decimal_places=2)
            )
        
        return query.annotate(**annotations)

    @staticmethod
    @transaction.atomic
    def transfer_stock(product, from_category, to_category, quantity, reference=None, notes=None, user=None):
        """
        Transfer stock from one category to another
        Equivalent to fn_transfer_stock function in SQL
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
            
        # Check if source has enough stock
        source_stock = ProductStock.objects.select_for_update().get(
            product=product, 
            category=from_category
        )
        
        if source_stock.quantity < quantity:
            raise ValueError(f"Insufficient stock. Only {source_stock.quantity} available.")
            
        # Get or create target stock record
        target_stock, created = ProductStock.objects.select_for_update().get_or_create(
            product=product,
            category=to_category,
            defaults={'quantity': 0}
        )
        
        # Update source and target
        source_stock.quantity -= quantity
        source_stock.save()
        
        target_stock.quantity += quantity
        if created:
            target_stock.receipt_date = timezone.now().date()
        target_stock.save()
        
        # Create transaction records
        timestamp = timezone.now()
        
        # Record the stock issue transaction
        StockTransaction.objects.create(
            product=product,
            transaction_type=StockTransactionType.TRANSFER_OUT,
            transaction_date=timestamp,
            quantity=-quantity,  # Negative for outgoing
            category=from_category,
            reference=reference,
            notes=notes,
            created_by=user
        )
        
        # Record the stock receipt transaction
        StockTransaction.objects.create(
            product=product,
            transaction_type=StockTransactionType.TRANSFER_IN,
            transaction_date=timestamp,
            quantity=quantity,  # Positive for incoming
            category=to_category,
            reference=reference,
            notes=notes,
            created_by=user
        )
        
        return {
            'from_stock': source_stock,
            'to_stock': target_stock,
            'quantity': quantity,
            'transaction_date': timestamp
        }
    
    @staticmethod
    def get_inventory_value_by_category():
        """
        Get total inventory value by category
        Equivalent to vw_inventory_value_by_category view in SQL
        """
        return InventoryCategory.objects.annotate(
            total_value=Coalesce(
                Subquery(
                    ProductStock.objects.filter(
                        category=OuterRef('pk')
                    ).values('category').annotate(
                        value=Sum(
                            F('quantity') * F('product__standard_cost'),
                            output_field=models.DecimalField(max_digits=12, decimal_places=2)
                        )
                    ).values('value')
                ),
                Decimal('0')
            ),
            item_count=Coalesce(
                Subquery(
                    ProductStock.objects.filter(
                        category=OuterRef('pk'),
                        quantity__gt=0
                    ).values('category').annotate(
                        count=models.Count('product', distinct=True)
                    ).values('count')
                ),
                0
            )
        ).order_by('-total_value')