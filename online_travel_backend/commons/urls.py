from django.urls import path
from .views import CategoriesAPI, QueryServicesAPI, SuggestionAPI


urlpatterns = [
    path("available_categories/", CategoriesAPI.as_view(), name="categories"),
    # suggestion API
    path("suggestions/", SuggestionAPI.as_view(), name="suggestions"),
    # Query Services
    path("query_services/", QueryServicesAPI.as_view(), name="query_services"),
    path(
        "view_service/<int:service_id>", QueryServicesAPI.as_view(), name="view_service"
    ),
]
