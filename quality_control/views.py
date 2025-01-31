from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.filters import DjangoFilterBackend, SearchFilter
from rest_framework.permissions import IsAuthenticated

# Create your views here.

class ChecklistViewSet(viewsets.ModelViewSet):
    queryset = QualityChecklist.objects.select_related('process')
    serializer_class = ChecklistSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['process__machine_type']
    search_fields = ['name', 'description']
