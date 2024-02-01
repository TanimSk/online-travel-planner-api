from .models import Category
from rest_framework import serializers
from agent.models import RfqService
from agent.serializers import QueryServiceSerializer


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Category


class CheckHotelSerializer(QueryServiceSerializer):
    service_id = serializers.IntegerField(required=True)
