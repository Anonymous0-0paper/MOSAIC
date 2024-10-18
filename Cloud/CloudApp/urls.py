from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import CloudView

router = SimpleRouter()
router.register('', CloudView, basename='')

urlpatterns = [
    path('Cloud/', include(router.urls)),
]
