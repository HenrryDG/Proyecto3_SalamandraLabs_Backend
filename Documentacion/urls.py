from django.urls import path
from .views import  swagger_ui

urlpatterns = [
    path('swagger/', swagger_ui, name='swagger-ui'),

]