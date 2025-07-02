from rest_framework import generics
from django.contrib.auth.models import User
from core.serializers import UserSerializer

class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
