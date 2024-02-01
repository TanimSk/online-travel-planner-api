from django.urls import path
from .views import CategoriesAPI, QueryServicesAPI, SuggestionAPI, CheckHotelAPI


urlpatterns = [
    path("available_categories/", CategoriesAPI.as_view(), name="categories"),
    # suggestion API
    path("suggestions/", SuggestionAPI.as_view(), name="suggestions"),
    # Query Services
    path("query_services/", QueryServicesAPI.as_view(), name="query_services"),
    path("check_hotel/", CheckHotelAPI.as_view(), name="check_hotel"),
    path(
        "view_service/<int:service_id>", QueryServicesAPI.as_view(), name="view_service"
    ),
]
