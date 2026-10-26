from django.urls import path
from . import views

app_name = 'incidents'

urlpatterns = [
    path('', views.incident_list_view, name='list'),
    path('report/', views.incident_create_view, name='report'),
    path('<int:incident_id>/', views.incident_detail_view, name='detail'),
    path('<int:incident_id>/edit/', views.incident_edit_view, name='edit'),
    path('<int:incident_id>/transition/', views.incident_transition_view, name='transition'),
    path('<int:incident_id>/assign/', views.incident_assign_investigator_view, name='assign_investigator'),
    path('<int:incident_id>/attach/', views.attachment_upload_view, name='upload_attachment'),
    path('attachment/<int:attachment_id>/download/', views.attachment_download_view, name='download_attachment'),
    path('attachment/<int:attachment_id>/delete/', views.attachment_delete_view, name='delete_attachment'),
]
