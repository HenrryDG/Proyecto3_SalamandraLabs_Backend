from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response



def swagger_ui(request):
    return render(request, 'swagger.html')   