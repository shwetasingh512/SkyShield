from django.urls import path
from . import views

app_name = 'risk_assessments'

urlpatterns = [
    path('matrix/', views.risk_matrix_view, name='matrix'),
    path('assess/<int:incident_id>/', views.risk_assessment_create_view, name='create'),
    path('thresholds/', views.threshold_list_view, name='threshold_list'),
    path('thresholds/<int:pk>/edit/', views.threshold_edit_view, name='threshold_edit'),
]
