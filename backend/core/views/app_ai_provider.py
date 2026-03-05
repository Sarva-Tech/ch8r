from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from core.models.app_ai_provider import AppAIProvider
from core.models.application import Application
from core.serializers.app_ai_provider import (
    AppAIProviderSerializer,
    AppAIProviderCreateSerializer,
    AppAIProviderUpdateSerializer
)

class AppAIProviderViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_queryset(self):
        application = get_object_or_404(
            Application,
            uuid=self.kwargs['application_uuid'],
            owner=self.request.user
        )

        queryset = AppAIProvider.objects.filter(application=application)

        context = self.request.query_params.get('context')
        capability = self.request.query_params.get('capability')

        if context:
            queryset = queryset.filter(context=context)
        if capability:
            queryset = queryset.filter(capability=capability)

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return AppAIProviderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AppAIProviderUpdateSerializer
        return AppAIProviderSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        application = get_object_or_404(
            Application,
            uuid=self.kwargs['application_uuid'],
            owner=self.request.user
        )
        context['application'] = application
        return context

    def perform_create(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": "deleted"},
            status=status.HTTP_200_OK
        )
