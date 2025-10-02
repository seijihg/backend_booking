from django.urls import path

from .views import CustomerDetailUpdateDeleteView, CustomerListCreateAPIView

urlpatterns = [
    path("", CustomerListCreateAPIView.as_view(), name="customer-list-create"),
    path(
        "<int:pk>/",
        CustomerDetailUpdateDeleteView.as_view(),
        name="customer-detail-update-delete",
    ),
]
