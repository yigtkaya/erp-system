from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'documents', views.QualityDocumentViewSet)
router.register(r'checklists', views.ChecklistViewSet)
router.register(r'calibrations', views.CalibrationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('work-orders/<int:pk>/quality-checks/', views.WorkOrderQualityView.as_view()),
]
