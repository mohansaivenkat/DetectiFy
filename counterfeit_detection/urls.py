from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('admin/reports/', views.admin_report_queue, name='admin_report_queue'),
    path('admin/reports/<int:pk>/approve/', views.approve_report, name='approve_report'),
    path('admin/reports/<int:pk>/reject/', views.reject_report, name='reject_report'),

    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)