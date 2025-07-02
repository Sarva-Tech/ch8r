from django.contrib import admin
from django.urls import path, include

from core.views.dummy_view import DummyView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('dummy/<uuid:application_uuid>', DummyView.as_view(), name='dummy'),
]
