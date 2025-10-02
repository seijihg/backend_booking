from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from .models import Customer
from .serializers import CustomerSerializer


# Create your views here.
class CustomerListCreateAPIView(ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class CustomerDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
