from django.urls import path
from . import views

app_name = 'investigations'

urlpatterns = [
    path('workspace/<int:incident_id>/', views.investigation_workspace_view, name='workspace'),
    path('start/<int:incident_id>/', views.investigation_start_view, name='start'),
    path('edit/<int:incident_id>/', views.investigation_edit_view, name='edit'),
    path('submit/<int:incident_id>/', views.investigation_submit_view, name='submit'),
    path('review/<int:incident_id>/', views.investigation_review_view, name='review'),
    path('rca/<int:incident_id>/', views.rca_edit_view, name='rca'),
    path('factors/create/<int:incident_id>/', views.contributing_factor_create_view, name='create_factor'),
    path('factors/delete/<int:factor_id>/', views.contributing_factor_delete_view, name='delete_factor'),
]
