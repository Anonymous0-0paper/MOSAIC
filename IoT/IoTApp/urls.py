from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import IoTView

router = SimpleRouter()
router.register('', IoTView, basename='')

urlpatterns = [
    path('IoT/', include(router.urls)),
]
