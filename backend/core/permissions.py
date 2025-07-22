from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed
from core.models import ApplicationAPIKey, Application

class HasAPIKeyPermission(BasePermission):
    def has_permission(self, request, view):
        try:
            application_uuid = request.resolver_match.kwargs['application_uuid']
        except KeyError:
            raise AuthenticationFailed('Application UUID not found in URL')

        api_key = request.headers.get('X-Api-Key')

        if not api_key:
            raise AuthenticationFailed('API Key not provided')

        try:
            application = Application.objects.get(uuid=application_uuid)

            api_keys = ApplicationAPIKey.objects.filter(application=application)

            for api_key_instance in api_keys:
                if api_key_instance.check_api_key(api_key):
                    self.check_permissions(request, api_key_instance)
                    return True

            raise AuthenticationFailed('Invalid API Key for the provided application')

        except Application.DoesNotExist:
            raise AuthenticationFailed('Application not found')
        except ApplicationAPIKey.DoesNotExist:
            raise AuthenticationFailed('API Key not found')

    def check_permissions(self, request, api_key_instance):
        action = self.get_action_from_request(request)

        if action not in api_key_instance.permissions:
            raise AuthenticationFailed(f"API Key does not have {action} permission")

    def get_action_from_request(self, request):
        if request.method == "GET":
            return "read"
        elif request.method in ["POST", "PUT", "PATCH"]:
            return "write"
        elif request.method == "DELETE":
            return "delete"
        else:
            raise AuthenticationFailed("Unsupported HTTP method")
