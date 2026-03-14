from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django.shortcuts import get_object_or_404

from core.models.application import Application
from core.widget_auth import WidgetTokenAuthentication, IsAuthenticatedOrWidget
from core.permissions import HasAPIKeyPermission
from core.consts import REGISTERED_USER_ID_PREFIX


class HumanAgentInfoView(APIView):
    """
    Returns the human agent (app owner) info for the widget's Agent tab.
    The owner's user_identifier is `reg:{user.id}` — stable and unique per user.
    """
    authentication_classes = [WidgetTokenAuthentication, SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticatedOrWidget | HasAPIKeyPermission]

    def get(self, request, application_uuid):
        if request.user and request.user.is_authenticated:
            app = get_object_or_404(Application, uuid=application_uuid, owner=request.user)
        else:
            app = getattr(request, 'application', None)
            if not app or str(app.uuid) != str(application_uuid):
                return Response({'detail': 'Invalid or unauthorized widget token'}, status=403)

        owner = app.owner
        return Response({
            'user_identifier': f"{REGISTERED_USER_ID_PREFIX}:{owner.id}",
            'name': owner.get_full_name() or owner.username,
            'email': owner.email,
            'is_online': True,  # always online for now; can be extended with presence tracking
        })
