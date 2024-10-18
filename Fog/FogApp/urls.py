from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import FogView

router = SimpleRouter()
router.register('', FogView, basename='')

urlpatterns = [
    path('Fog/', include(router.urls)),
]
