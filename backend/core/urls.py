from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from core.views import (
    UserRegisterView, VerifyEmailView, KnowledgeBaseViewSet, ChatRoomMessagesView,
    MeView, GenerateAPIKeyView,
    AppNotificationProfileCreateView, IntegrationViewSet, WidgetView, LoadAvailableConfigurationView
)
from core.views.application import ApplicationViewSet, ApplicationChatRoomsPreviewView
from core.views.chatroom import ChatRoomDetailView
from core.views.configure_app import ConfigureAppIntegrationView, LoadAppConfigurationView
from core.views.integration import supported_integrations
from core.views.llm_model import LLMModelViewSet
from core.views.message import SendMessageView
from core.views.ingestion import IngestApplicationKBView
from core.views.notification_profile import NotificationProfileViewSet
from core.views.app_model import ConfigureAppModelsView

router = DefaultRouter()
router.register(r'applications', ApplicationViewSet, basename='applications')
router.register(r'notification-profiles', NotificationProfileViewSet, basename='notificationprofile')
router.register(r'models', LLMModelViewSet, basename='model'),
router.register(r'integrations', IntegrationViewSet, basename='integration'),

nested_router = NestedDefaultRouter(router, r'applications', lookup='application')
nested_router.register(r'knowledge-bases', KnowledgeBaseViewSet, basename='application-knowledge-bases')

urlpatterns = [
    path('login/', obtain_auth_token, name='api_login'),
    path('register/', UserRegisterView.as_view(), name='api_register'),
    path('applications/<uuid:application_uuid>/api-keys/', GenerateAPIKeyView.as_view(), name='generate-api-key'),
    path('applications/<uuid:application_uuid>/api-keys/<int:api_key_id>/', GenerateAPIKeyView.as_view(), name='delete-api-key'),
    path('me/', MeView.as_view(), name='api_me'),
    path('verify-email/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),

    path(
        'applications/<uuid:application_uuid>/chatrooms/send-message/',
        SendMessageView.as_view(),
        name='send-message'
    ),

    path(
        'applications/<uuid:application_uuid>/chatrooms/<uuid:chatroom_uuid>/messages/',
        ChatRoomMessagesView.as_view(),
        name='chatroom-messages'
    ),

    path('applications/<uuid:application_uuid>/chatrooms/', ApplicationChatRoomsPreviewView.as_view(),
         name='application-chatroom-previews'),
    path('chatrooms/<uuid:chatroom_uuid>/', ChatRoomDetailView.as_view(), name='chatroom-detail'),

    path('applications/<uuid:application_uuid>/ingests/', IngestApplicationKBView.as_view(), name='application-ingest'),

    path('notification-profiles/bulk-upload/',
         NotificationProfileViewSet.as_view({'post': 'bulk_upload'}),
         name='notificationprofile-bulk-upload'),

    path('app-notification-profiles/',
         AppNotificationProfileCreateView.as_view()),

    path('applications/<uuid:app_uuid>/configure-app-models/', ConfigureAppModelsView.as_view(), name='configure-app-models'),

    path('applications/<uuid:app_uuid>/configure-integration/', ConfigureAppIntegrationView.as_view(), name='configure-app-integration'),

    path(
        "applications/<uuid:application_uuid>/widget/",
        WidgetView.as_view(),
        name="widget"
    ),

    path(
        'applications/<uuid:app_uuid>/load-app-configurations/',
        LoadAppConfigurationView.as_view(),
        name='app-configurations',
    ),

    path(
        'available-configurations/',
        LoadAvailableConfigurationView.as_view(),
        name='available-configurations',
    ),

    path('supported-integrations/', supported_integrations, name='supported-integrations'),

    path('', include(router.urls)),
    path('', include(nested_router.urls)),
]
