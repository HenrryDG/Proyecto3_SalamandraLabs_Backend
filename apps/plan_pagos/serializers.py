from rest_framework import serializers
from .models import PlanPago

class PlanPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanPago
        fields = '_all_'