from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from .models import Customer
from .serializers import CustomerSerializer

ALLOWED_SORT_FIELDS = ['id', 'full_name', 'phone_number', 'created', 'modified']
DEFAULT_SORT_FIELD = 'created'
DEFAULT_SORT_ORDER = 'desc'


class CustomerListCreateAPIView(ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by salon
        salon_id = self.request.query_params.get('salon')
        if salon_id:
            queryset = queryset.filter(salons__id=salon_id)

        # Sorting
        sort_by = self.request.query_params.get('sort_by', DEFAULT_SORT_FIELD)
        order = self.request.query_params.get('order', DEFAULT_SORT_ORDER)

        # Validate sort field
        if sort_by not in ALLOWED_SORT_FIELDS:
            sort_by = DEFAULT_SORT_FIELD

        # Validate order direction
        if order not in ['asc', 'desc']:
            order = DEFAULT_SORT_ORDER

        # Apply ordering
        order_prefix = '-' if order == 'desc' else ''
        queryset = queryset.order_by(f'{order_prefix}{sort_by}')

        return queryset


class CustomerDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
