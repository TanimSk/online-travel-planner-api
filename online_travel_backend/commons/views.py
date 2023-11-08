from .serializers import CategorySerializer
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Category


class CategoriesAPI(APIView):
    serializer_class = CategorySerializer

    def get(self, request, format=None, *args, **kwargs):
        instance = Category.objects.all()
        serialized_data = CategorySerializer(instance, many=True)
        return Response(serialized_data.data)
