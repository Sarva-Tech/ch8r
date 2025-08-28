from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import AppModel, Application
from core.serializers import AppModelCreateSerializer, AppModelViewSerializer, ConfigureAppModelSerializer, \
    LLMModelViewSerializer


class AppModelViewSet(viewsets.ModelViewSet):
    queryset = AppModel.objects.none()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AppModelCreateSerializer
        return AppModelViewSerializer

    def get_queryset(self):
        return AppModel.objects.filter(application__owner=self.request.user)

    def create(self, request, *args, **kwargs):
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        instance = create_serializer.save()

        view_serializer = AppModelViewSerializer(instance, context={'request': request})
        return Response(view_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT", detail="Use PATCH to update app model.")

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": "Deleted"},
            status=status.HTTP_200_OK
        )


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