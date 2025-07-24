from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.serializers import APIKeySerializer
from core.models import ApplicationAPIKey

class GenerateAPIKeyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = APIKeySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            api_key_instance, raw_api_key = serializer.save()
            return Response({
                "id": api_key_instance.id,
                "api_key": raw_api_key,
                "name": api_key_instance.name,
                "application": api_key_instance.application.id,
                "permissions": api_key_instance.permissions,
                "created": api_key_instance.created
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, api_key_id=None):
        if api_key_id is None:
            return Response({"detail": "API key ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            api_key_instance = ApplicationAPIKey.objects.get(id=api_key_id)
        except ApplicationAPIKey.DoesNotExist:
            return Response({"detail": "API key not found."}, status=status.HTTP_404_NOT_FOUND)

        if api_key_instance.owner != request.user:
            return Response({"detail": "You do not have permission to delete this API key."}, status=status.HTTP_403_FORBIDDEN)

        api_key_instance.delete()
        return Response({"detail": "API key deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

    def get(self, request):
        api_keys = ApplicationAPIKey.objects.filter(owner=request.user)

        if not api_keys:
            return Response([], status=status.HTTP_200_OK)

        serializer = APIKeySerializer(api_keys, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
