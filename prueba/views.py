from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response

class HolaAPI(APIView):
    @extend_schema(tags=['Prueba'])
    def get(self, request):
        return Response({"mensaje": "Hola desde la API"})
    

