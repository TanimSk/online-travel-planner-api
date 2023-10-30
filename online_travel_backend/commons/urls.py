from django.urls import path
from .views import CategoriesAPI

urlpatterns = [
    path("available_categories/", CategoriesAPI.as_view(), name="categories"),
]
