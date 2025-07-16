"""
URL configuration for project_run project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from app_run.views import company_info, UserViewSet, RunStartAPIView, RunStopAPIView
from rest_framework.routers import DefaultRouter
from app_run.views import RunViewSet
from athlete_info.views import AthleteViewSet, ChallengeViewSet
from latitudelongitude.views import PositionViewSet

router = DefaultRouter()
router.register('api/runs', RunViewSet)
router.register('api/users', UserViewSet)
router.register('api/athlete_info', AthleteViewSet, basename='athlete-info')
router.register('api/challenges', ChallengeViewSet, basename='challenges')
router.register(r'positions', PositionViewSet, basename='position')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/company_details/', company_info),
    path('api/runs/<int:run_id>/start/', RunStartAPIView.as_view(), name='run-start'),
    path('api/runs/<int:run_id>/stop/', RunStopAPIView.as_view(), name='run-stop'),
    path('', include(router.urls)),
]