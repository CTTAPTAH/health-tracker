from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
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

    def get_queryset(self):
        return WeightEntry.objects.filter(user=self.request.user)