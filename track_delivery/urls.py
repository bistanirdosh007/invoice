from django.urls import path
from . import views

app_name = 'track_delivery'

urlpatterns = [
    path('', views.track_deliveries, name='track_deliveries'),
]
