from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from erp_core.models import Customer
from inventory.models import Product
from .models import SalesOrder, SalesOrderItem
import json

User = get_user_model()

class BatchUpdateSalesOrderItemsTest(APITestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create a test customer
        self.customer = Customer.objects.create(
            name='Test Customer',
            email='customer@example.com',
            phone='1234567890'
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            name='Product 1',
            sku='P1',
            unit_price=100.00
        )
        
        self.product2 = Product.objects.create(
            name='Product 2',
            sku='P2',
            unit_price=200.00
        )
        
        # Create a test sales order
        self.sales_order = SalesOrder.objects.create(
            order_number='SO-TEST-001',
            customer=self.customer,
            created_by=self.user
        )
        
        # Create test sales order items
        self.item1 = SalesOrderItem.objects.create(
            sales_order=self.sales_order,
            product=self.product1,
            ordered_quantity=10
        )
        
        self.item2 = SalesOrderItem.objects.create(
            sales_order=self.sales_order,
            product=self.product2,
            ordered_quantity=5
        )
        
        # URL for batch update
        self.batch_update_url = reverse(
            'sales:order-items-batch-update',
            kwargs={'order_pk': self.sales_order.id}
        )
    
    def test_batch_update_success(self):
        """Test successful batch update of multiple sales order items"""
        data = {
            'items': [
                {
                    'id': self.item1.id,
                    'ordered_quantity': 15,
                    'deadline_date': '2023-12-31'
                },
                {
                    'id': self.item2.id,
                    'ordered_quantity': 8,
                    'deadline_date': '2023-12-25'
                }
            ]
        }
        
        response = self.client.patch(
            self.batch_update_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Refresh items from database
        self.item1.refresh_from_db()
        self.item2.refresh_from_db()
        
        # Check that items were updated correctly
        self.assertEqual(self.item1.ordered_quantity, 15)
        self.assertEqual(str(self.item1.deadline_date), '2023-12-31')
        self.assertEqual(self.item2.ordered_quantity, 8)
        self.assertEqual(str(self.item2.deadline_date), '2023-12-25')
    
    def test_batch_update_invalid_item_id(self):
        """Test batch update with an invalid item ID"""
        data = {
            'items': [
                {
                    'id': 9999,  # Non-existent ID
                    'ordered_quantity': 15
                },
                {
                    'id': self.item2.id,
                    'ordered_quantity': 8
                }
            ]
        }
        
        response = self.client.patch(
            self.batch_update_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check that no items were updated
        self.item1.refresh_from_db()
        self.item2.refresh_from_db()
        self.assertEqual(self.item1.ordered_quantity, 10)
        self.assertEqual(self.item2.ordered_quantity, 5)
    
    def test_batch_update_closed_order(self):
        """Test batch update on a closed order"""
        # Close the order
        self.sales_order.status = 'CLOSED'
        self.sales_order.save()
        
        data = {
            'items': [
                {
                    'id': self.item1.id,
                    'ordered_quantity': 15
                }
            ]
        }
        
        response = self.client.patch(
            self.batch_update_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot update items in a closed order', response.data['detail'])
        
        # Check that no items were updated
        self.item1.refresh_from_db()
        self.assertEqual(self.item1.ordered_quantity, 10)
    
    def test_batch_update_validation_error(self):
        """Test batch update with validation errors"""
        # Set fulfilled_quantity to 10
        self.item1.fulfilled_quantity = 10
        self.item1.save()
        
        # Try to update ordered_quantity to less than fulfilled_quantity
        data = {
            'items': [
                {
                    'id': self.item1.id,
                    'ordered_quantity': 5  # Less than fulfilled_quantity
                }
            ]
        }
        
        response = self.client.patch(
            self.batch_update_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check that no items were updated
        self.item1.refresh_from_db()
        self.assertEqual(self.item1.ordered_quantity, 10)


class BatchCreateSalesOrderItemsTest(APITestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create a test customer
        self.customer = Customer.objects.create(
            name='Test Customer',
            email='customer@example.com',
            phone='1234567890'
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            name='Product 1',
            sku='P1',
            unit_price=100.00
        )
        
        self.product2 = Product.objects.create(
            name='Product 2',
            sku='P2',
            unit_price=200.00
        )
        
        self.product3 = Product.objects.create(
            name='Product 3',
            sku='P3',
            unit_price=300.00
        )
        
        # Create a test sales order
        self.sales_order = SalesOrder.objects.create(
            order_number='SO-TEST-001',
            customer=self.customer,
            created_by=self.user
        )
        
        # URL for batch create
        self.batch_create_url = reverse(
            'sales:order-items-batch-create',
            kwargs={'order_pk': self.sales_order.id}
        )
    
    def test_batch_create_success(self):
        """Test successful batch creation of multiple sales order items"""
        data = {
            'items': [
                {
                    'product': self.product1.id,
                    'ordered_quantity': 15,
                    'deadline_date': '2023-12-31'
                },
                {
                    'product': self.product2.id,
                    'ordered_quantity': 8,
                    'deadline_date': '2023-12-25'
                },
                {
                    'product': self.product3.id,
                    'ordered_quantity': 12,
                    'receiving_date': '2023-11-15',
                    'deadline_date': '2023-12-20'
                }
            ]
        }
        
        response = self.client.post(
            self.batch_create_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 3)
        
        # Check that items were created correctly
        self.assertEqual(SalesOrderItem.objects.count(), 3)
        
        # Check first item
        item1 = SalesOrderItem.objects.get(product=self.product1)
        self.assertEqual(item1.ordered_quantity, 15)
        self.assertEqual(str(item1.deadline_date), '2023-12-31')
        
        # Check second item
        item2 = SalesOrderItem.objects.get(product=self.product2)
        self.assertEqual(item2.ordered_quantity, 8)
        self.assertEqual(str(item2.deadline_date), '2023-12-25')
        
        # Check third item
        item3 = SalesOrderItem.objects.get(product=self.product3)
        self.assertEqual(item3.ordered_quantity, 12)
        self.assertEqual(str(item3.receiving_date), '2023-11-15')
        self.assertEqual(str(item3.deadline_date), '2023-12-20')
    
    def test_batch_create_missing_required_fields(self):
        """Test batch create with missing required fields"""
        data = {
            'items': [
                {
                    'product': self.product1.id,
                    # Missing ordered_quantity
                    'deadline_date': '2023-12-31'
                },
                {
                    # Missing product
                    'ordered_quantity': 8,
                    'deadline_date': '2023-12-25'
                }
            ]
        }
        
        response = self.client.post(
            self.batch_create_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check that no items were created
        self.assertEqual(SalesOrderItem.objects.count(), 0)
    
    def test_batch_create_closed_order(self):
        """Test batch create on a closed order"""
        # Close the order
        self.sales_order.status = 'CLOSED'
        self.sales_order.save()
        
        data = {
            'items': [
                {
                    'product': self.product1.id,
                    'ordered_quantity': 15,
                    'deadline_date': '2023-12-31'
                }
            ]
        }
        
        response = self.client.post(
            self.batch_create_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot add items to a closed order', response.data['detail'])
        
        # Check that no items were created
        self.assertEqual(SalesOrderItem.objects.count(), 0)
    
    def test_batch_create_validation_error(self):
        """Test batch create with validation errors"""
        data = {
            'items': [
                {
                    'product': self.product1.id,
                    'ordered_quantity': -5,  # Negative quantity, should fail validation
                    'deadline_date': '2023-12-31'
                }
            ]
        }
        
        response = self.client.post(
            self.batch_create_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check that no items were created
        self.assertEqual(SalesOrderItem.objects.count(), 0)
