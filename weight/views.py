from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsOwner
from .models import WeightEntry
from .serializers import WeightEntrySerializer

class WeightEntryListCreateView(ListCreateAPIView):
    serializer_class = WeightEntrySerializer

    def get_queryset(self):
        return WeightEntry.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class WeightEntryDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = WeightEntrySerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return WeightEntry.objects.filter(user=self.request.user)