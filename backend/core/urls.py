from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from core.views import UserRegisterView, KnowledgeBaseViewSet, ChatRoomMessagesView, MeView, WidgetView, GenerateAPIKeyView
from core.views.application import ApplicationViewSet, ApplicationChatRoomsPreviewView
from core.views.chatroom import ChatRoomDetailView
from core.views.message import SendMessageView
from core.views.ingestion import IngestApplicationKBView

router = DefaultRouter()
router.register(r'applications', ApplicationViewSet, basename='applications')
nested_router = NestedDefaultRouter(router, r'applications', lookup='application')
nested_router.register(r'knowledge-bases', KnowledgeBaseViewSet, basename='application-knowledge-bases')

urlpatterns = [
    path('login/', obtain_auth_token, name='api_login'),
    path('register/', UserRegisterView.as_view(), name='api_register'),
    path('api-keys/', GenerateAPIKeyView.as_view(), name='generate-api-key'),
    path('api-keys/<int:api_key_id>/', GenerateAPIKeyView.as_view(), name='delete-api-key'),
    path('me/', MeView.as_view(), name='api_me'),

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

    path('applications/<uuid:application_uuid>/widget/', WidgetView.as_view(), name='enable-widget'),

    path('', include(router.urls)),
    path('', include(nested_router.urls)),
]
