from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    JobViewSet, JobSkillViewSet, JobRequirementViewSet,
    MatchingResultViewSet
)


router = DefaultRouter()
router.register(r'', JobViewSet, basename='job')
router.register(r'requirements', JobRequirementViewSet, basename='job-requirement')
router.register(r'skills', JobSkillViewSet, basename='job-skill')
router.register(r'matching-results', MatchingResultViewSet, basename='matching-result')

app_name = 'jobs'

urlpatterns = [
    path('', include(router.urls)),
]
