from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import EdgeView

router = SimpleRouter()
router.register('', EdgeView, basename='')

urlpatterns = [
    path('Edge/', include(router.urls)),
]
