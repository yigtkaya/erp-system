from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Tool, ToolUsage, Holder, Fixture, ControlGauge # Added Tool, ToolUsage and uncommented others
# from django.contrib.auth.models import User # If using authentication
from django.contrib.auth import get_user_model # For creating test users

User = get_user_model()

class ToolAPITests(APITestCase):
    def setUp(self):
        # self.user = User.objects.create_user(username='testuser', password='testpassword')
        # self.client.login(username='testuser', password='testpassword')
        self.tool1 = Tool.objects.create(
            stock_code="TOOL001", supplier_name="SupplierA", product_code="P001", 
            unit_price_tl=100.00,
            tool_insert_code="ICODE01", tool_material="Carbide", tool_diameter=10.0,
            tool_length=50.0, tool_connection_diameter=8.0, tool_type="EndMill", quantity=10
        )
        self.list_url = reverse('inventory:tool-list') 
        self.detail_url = reverse('inventory:tool-detail', kwargs={'pk': str(self.tool1.pk)}) # pk is UUID

    def test_create_tool(self):
        data = {
            "stock_code": "TOOL002", "supplier_name": "SupplierB", "product_code": "P002",
            "unit_price_tl": 150.00,
            "tool_insert_code": "ICODE02", "tool_material": "HSS", "tool_diameter": 12.0,
            "tool_length": 60.0, "tool_connection_diameter": 10.0, "tool_type": "Drill", "quantity": 5
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Tool.objects.count(), 2)

    def test_get_tool_list(self):
        response = self.client.get(self.list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        # self.assertEqual(len(response.data), 1) # Default pagination might affect this

    def test_get_tool_detail(self):
        response = self.client.get(self.detail_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['stock_code'], self.tool1.stock_code)

    # Add tests for update (PUT/PATCH) and delete (DELETE)

class ToolUsageAPITests(APITestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(username='testuser_usage', password='password')
        # self.client.login(username='testuser_usage', password='password') # Uncomment if auth is required
        self.tool = Tool.objects.create(
            stock_code="TOOLSUP", supplier_name="SupplierTool", tool_type="TestType", quantity=5
        )
        self.list_url = reverse('inventory:toolusage-list') # Basename from router
        # self.detail_url = reverse('inventory:toolusage-detail', kwargs={'pk': str(some_tool_usage_pk)}) # For detail view tests

    def test_create_tool_usage(self):
        data = {
            "tool": str(self.tool.pk), # Pass UUID as string
            "issued_by": self.test_user.pk, # Pass user pk
            "usage_count": 1,
            "condition_before": "NEW",
            "notes": "Test usage entry"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(ToolUsage.objects.count(), 1)
        self.assertEqual(ToolUsage.objects.first().tool, self.tool)

    # Add more tests (GET list, GET detail, PUT, PATCH, DELETE)

class HolderAPITests(APITestCase):
    def setUp(self):
        self.holder1 = Holder.objects.create(
            stock_code="HOLD001", supplier_name="SupplierC", product_code="PH001",
            unit_price_tl=200.00, unit_price_euro=20.00, unit_price_usd=24.00,
            holder_type="BT40", pulley_type="Standard", tool_connection_diameter=20.0,
            holder_type_enum="COLLET_CHUCK"
        )
        self.list_url = reverse('inventory:holder-list')
        self.detail_url = reverse('inventory:holder-detail', kwargs={'pk': self.holder1.pk})

    def test_create_holder(self):
        data = {
            "stock_code": "HOLD002", "supplier_name": "SupplierD", "product_code": "PH002",
            "unit_price_tl": 250.00, "unit_price_euro": 25.00, "unit_price_usd": 30.00,
            "holder_type": "HSK63", "pulley_type": "HighSpeed", "water_cooling": True,
            "tool_connection_diameter": 16.0, "holder_type_enum": "MILLING_CHUCK"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # Add more tests (GET list, GET detail, PUT, PATCH, DELETE)

class FixtureAPITests(APITestCase):
    def setUp(self):
        self.fixture1 = Fixture.objects.create(code="FIX001", name="Main Assembly Fixture")
        self.list_url = reverse('inventory:fixture-list')
        self.detail_url = reverse('inventory:fixture-detail', kwargs={'pk': self.fixture1.pk})

    def test_create_fixture(self):
        data = {"code": "FIX002", "name": "Welding Fixture Alpha"}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    # Add more tests

class ControlGaugeAPITests(APITestCase):
    def setUp(self):
        self.gauge1 = ControlGauge.objects.create(
            stock_code="CG001", stock_name="Digital Caliper", status="UYGUN"
        )
        self.list_url = reverse('inventory:controlgauge-list') # Basename might be 'controlgauge'
        self.detail_url = reverse('inventory:controlgauge-detail', kwargs={'pk': self.gauge1.pk})

    def test_create_control_gauge(self):
        data = {"stock_code": "CG002", "stock_name": "Micrometer", "status": "KALIBRASYONDA"}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    # Add more tests
