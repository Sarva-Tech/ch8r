from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models.app_model import AppModel
from core.models.application import Application
from core.serializers.llm_model import LLMModelViewSerializer
from core.serializers.app_model import ConfigureAppModelsSerializer


class ConfigureAppModelsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, app_uuid):
        application = get_object_or_404(Application, uuid=app_uuid, owner=request.user)

        serializer = ConfigureAppModelsSerializer(
            data=request.data, context={"request": request, "application": application}
        )
        serializer.is_valid(raise_exception=True)

        updated_models = []
        for item in serializer.validated_data["models"]:
            llm_model = item["llm_model"]
            model_type = llm_model.model_type

            existing_app_model = AppModel.objects.filter(
                application=application, llm_model__model_type=model_type
            ).first()

            if existing_app_model:
                existing_app_model.llm_model = llm_model
                existing_app_model.save()
            else:
                AppModel.objects.create(
                    application=application, llm_model=llm_model
                )

            updated_models.append(LLMModelViewSerializer(llm_model).data)

        return Response(updated_models, status=status.HTTP_200_OK)
