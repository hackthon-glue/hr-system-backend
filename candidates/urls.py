from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SkillViewSet, CandidateViewSet, CandidateSkillViewSet,
    EducationViewSet, WorkExperienceViewSet,
    ApplicationViewSet, InterviewViewSet
)

router = DefaultRouter()
router.register(r'skills', SkillViewSet, basename='skill')
router.register(r'candidates', CandidateViewSet, basename='candidate')
router.register(r'candidate-skills', CandidateSkillViewSet, basename='candidate-skill')
router.register(r'educations', EducationViewSet, basename='education')
router.register(r'work-experiences', WorkExperienceViewSet, basename='work-experience')
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'interviews', InterviewViewSet, basename='interview')

app_name = 'candidates'

urlpatterns = [
    path('', include(router.urls)),
]
