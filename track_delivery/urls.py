from django.urls import path
from . import views

urlpatterns = [
    path('', views.track_deliveries, name='track_deliveries'),
]
