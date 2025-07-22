from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.serializers import APIKeySerializer

class GenerateAPIKeyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = APIKeySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            api_key_instance, raw_api_key = serializer.save()
            return Response({
                "api_key": raw_api_key,
                "name": api_key_instance.name,
                "application": api_key_instance.application.name,
                "permissions": api_key_instance.permissions,
                "created": api_key_instance.created
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
