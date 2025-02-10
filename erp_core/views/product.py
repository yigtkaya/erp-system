from rest_framework import viewsets
from inventory.models import Product
from erp_core.serializers import ProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filterset_fields = ['product_type', 'inventory_category']
    search_fields = ['product_code', 'product_name'] 