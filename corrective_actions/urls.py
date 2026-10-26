from django.urls import path
from . import views

app_name = 'corrective_actions'

urlpatterns = [
    path('', views.capa_list_view, name='list'),
    path('create/<int:incident_id>/', views.capa_create_view, name='create'),
    path('<int:action_id>/', views.capa_detail_view, name='detail'),
    path('<int:action_id>/progress/', views.capa_update_progress_view, name='update_progress'),
    path('<int:action_id>/verify/', views.capa_verify_view, name='verify'),
]
