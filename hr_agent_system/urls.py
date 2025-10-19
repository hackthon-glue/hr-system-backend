"""
URL configuration for hr_agent_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger/OpenAPI設定
schema_view = get_schema_view(
    openapi.Info(
        title="HR Agent System API",
        default_version='v1',
        description="HR採用支援システムのAPI",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Endpoints
    path('api/auth/', include('authz.urls')),
    path('api/candidates/', include('candidates.urls')),
    path('api/jobs/', include('jobs.urls')),
    path('api/agents/', include('services.urls')),

    # Swagger/OpenAPI Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Health Check (with and without trailing slash)
    path('health/', lambda request: JsonResponse({'status': 'healthy'})),
    path('health', lambda request: JsonResponse({'status': 'healthy'})),
]

# Media files (development only)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
