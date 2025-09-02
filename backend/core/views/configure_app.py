from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import AppModel, Application, AppIntegration
from core.serializers import ConfigureAppModelSerializer, LLMModelViewSerializer, ConfigureAppIntegrationSerializer, \
    IntegrationViewSerializer


class ConfigureAppModelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, app_uuid):
        application = get_object_or_404(Application, uuid=app_uuid, owner=request.user)

        serializer = ConfigureAppModelSerializer(data=request.data, context={'request': request, 'application': application})
        serializer.is_valid(raise_exception=True)

        llm_model = serializer.validated_data['llm_model']
        model_type = llm_model.model_type

        existing_app_model = AppModel.objects.filter(
            application=application,
            llm_model__model_type=model_type
        ).first()

        if existing_app_model:
            existing_app_model.llm_model = llm_model
            existing_app_model.save()
        else:
            AppModel.objects.create(application=application, llm_model=llm_model)

        llm_model_serializer = LLMModelViewSerializer(llm_model)
        return Response(llm_model_serializer.data, status=status.HTTP_200_OK)

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
            integration=integration,
        ).first()

        if existing_app_integration:
            if branch_name:
                existing_app_integration.metadata = {
                    **(existing_app_integration.metadata or {}),
                    "branch_name": branch_name
                }
            existing_app_integration.save()
        else:
            AppIntegration.objects.create(
                application=application,
                integration=integration,
                metadata={"branch_name": branch_name} if branch_name else {}
            )

        integration_serializer = IntegrationViewSerializer(integration)
        return Response(integration_serializer.data, status=status.HTTP_200_OK)