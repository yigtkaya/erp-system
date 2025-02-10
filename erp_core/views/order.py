from rest_framework import viewsets
from sales.models import SalesOrder
from sales.serializers import SalesOrderSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer
    filterset_fields = ['status', 'customer']
    search_fields = ['order_number', 'customer__name'] 