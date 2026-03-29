from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import json
import requests as http_requests

from core.models import Integration, AppIntegration, Application
from core.serializers.integration import IntegrationSerializer, IntegrationCreateSerializer
from core.serializers.app_integration import AppIntegrationSerializer, AppIntegrationCreateSerializer
from core.consts import SUPPORTED_INTEGRATIONS


class IntegrationViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return Integration.objects.filter(creator=self.request.user)

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return IntegrationCreateSerializer
        return IntegrationSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict):
            response.data['supported_integrations'] = SUPPORTED_INTEGRATIONS
        else:
            response.data = {
                'results': response.data,
                'supported_integrations': SUPPORTED_INTEGRATIONS,
            }
        return response

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if hasattr(serializer, '_credential_error'):
            return Response(
                {'error': 'Failed to validate integration credentials', 'details': serializer._credential_error},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance = serializer.save()
        return Response(IntegrationSerializer(instance).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if hasattr(serializer, '_credential_error'):
            return Response(
                {'error': 'Failed to validate integration credentials', 'details': serializer._credential_error},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance = serializer.save()
        return Response(IntegrationSerializer(instance).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"detail": "deleted"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='repos')
    def repos(self, request, uuid=None):
        integration = self.get_object()
        try:
            credentials = json.loads(integration.credentials or '{}')
            token = credentials.get('token', '')
        except (json.JSONDecodeError, AttributeError):
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

        if not token:
            return Response({'error': 'No token configured'}, status=status.HTTP_400_BAD_REQUEST)

        repos = []
        page = 1
        while True:
            resp = http_requests.get(
                'https://api.github.com/user/repos',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Accept': 'application/vnd.github+json',
                },
                params={'per_page': 100, 'page': page, 'sort': 'updated'},
                timeout=15,
            )
            if resp.status_code != 200:
                return Response(
                    {'error': f'Failed to fetch repositories: {resp.status_code}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            data = resp.json()
            if not data:
                break
            repos.extend([{'full_name': r['full_name'], 'private': r['private']} for r in data])
            if len(data) < 100:
                break
            page += 1

        return Response({'repos': repos})


class AppIntegrationViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        application = get_object_or_404(
            Application,
            uuid=self.kwargs['application_uuid'],
            owner=self.request.user,
        )
        return AppIntegration.objects.filter(application=application)

    def get_serializer_class(self):
        if self.action == 'create':
            return AppIntegrationCreateSerializer
        return AppIntegrationSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['application'] = get_object_or_404(
            Application,
            uuid=self.kwargs['application_uuid'],
            owner=self.request.user,
        )
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(AppIntegrationSerializer(instance, context=self.get_serializer_context()).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"detail": "deleted"}, status=status.HTTP_200_OK)
