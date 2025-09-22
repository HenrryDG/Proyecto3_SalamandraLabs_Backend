from django.urls import path
from .views import HolaAPI

urlpatterns = [
    path('saludo/', HolaAPI.as_view(), name='saludo'),

]