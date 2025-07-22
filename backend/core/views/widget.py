from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from core.models import Application, ApplicationWidgetToken
from core.permissions import HasAPIKeyPermission

class WidgetView(APIView):
    permission_classes = [IsAuthenticated | HasAPIKeyPermission]

    def post(self, request, application_uuid):
        app = get_object_or_404(Application, uuid=application_uuid, owner=request.user)

        ApplicationWidgetToken.objects.filter(application=app).delete()

        token_obj = ApplicationWidgetToken.objects.create(application=app)

        return Response({
            "token": token_obj.key,
            "embed_url": f"https://ch8r.com/widget.js?token={token_obj.key}&app={app.uuid}"
        })
