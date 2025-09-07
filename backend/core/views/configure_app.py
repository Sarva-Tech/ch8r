from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.integrations import SUPPORTED_INTEGRATIONS, SUPPORTED_PROVIDERS, INTEGRATION_TOOLS
from core.models.application import Application
from core.models.app_integration import AppIntegration
from core.serializers import AppIntegrationViewSerializer

from core.serializers.configure_app import ConfigureAppIntegrationSerializer, LoadAppConfigurationSerializer
from core.serializers.llm_model import LLMModelViewSerializer
from core.serializers.integration import IntegrationViewSerializer
from core.views import LLMModelViewSet, IntegrationViewSet


class LoadAvailableConfigurationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        llm_viewset = LLMModelViewSet()
        llm_viewset.request = request
        llm_queryset = llm_viewset.get_queryset()
        llm_serializer = LLMModelViewSerializer(llm_queryset, many=True)

        integration_viewset = IntegrationViewSet()
        integration_viewset.request = request
        integration_queryset = integration_viewset.get_queryset()
        integration_serializer = IntegrationViewSerializer(integration_queryset, many=True)

        supported_data = {
            "supported_integrations": SUPPORTED_INTEGRATIONS,
            "supported_providers": SUPPORTED_PROVIDERS,
            "integration_tools": INTEGRATION_TOOLS,
        }

        return Response({
            "llm_models": llm_serializer.data,
            "integrations": integration_serializer.data,
            **supported_data
        })


class LoadAppConfigurationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, app_uuid):
        application = get_object_or_404(Application, uuid=app_uuid, owner=request.user)
        serializer = LoadAppConfigurationSerializer(application)
        return Response(serializer.data)


class ConfigureAppIntegrationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, app_uuid):
        application = get_object_or_404(Application, uuid=app_uuid, owner=request.user)

        serializer = ConfigureAppIntegrationSerializer(
            data=request.data,
            context={'request': request, 'application': application}
        )
        serializer.is_valid(raise_exception=True)

        integration = serializer.validated_data['integration']
        branch_name = serializer.validated_data.get("branch_name")

        existing_app_integration = AppIntegration.objects.filter(
            application=application,
            integration__type=integration.type
        ).first()

        if existing_app_integration:
            if existing_app_integration.integration_id == integration.id:
                if branch_name:
                    existing_app_integration.metadata = {
                        **(existing_app_integration.metadata or {}),
                        "branch_name": branch_name
                    }
            else:
                existing_app_integration.integration = integration
                existing_app_integration.metadata = {"branch_name": branch_name} if branch_name else {}
            existing_app_integration.save()
            app_integration_instance = existing_app_integration
        else:
            app_integration_instance = AppIntegration.objects.create(
                application=application,
                integration=integration,
                metadata={"branch_name": branch_name} if branch_name else {}
            )

        response_serializer = AppIntegrationViewSerializer(app_integration_instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)