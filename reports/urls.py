from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_index_view, name='index'),
    path('incidents/csv/', views.export_incidents_csv, name='incidents_csv'),
    path('capa/csv/', views.export_capa_csv, name='capa_csv'),
    path('audit/csv/', views.export_audit_csv, name='audit_csv'),
    path('incident/<int:incident_id>/pdf/', views.export_incident_pdf, name='incident_pdf'),
]
