from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return redirect('accounts:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('incidents/', include('incidents.urls')),
    path('investigations/', include('investigations.urls')),
    path('risk/', include('risk_assessments.urls')),
    path('actions/', include('corrective_actions.urls')),
    path('reports/', include('reports.urls')),
    path('audit/', include('audit.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler403 = 'accounts.views.error_403'
handler404 = 'accounts.views.error_404'
handler500 = 'accounts.views.error_500'
