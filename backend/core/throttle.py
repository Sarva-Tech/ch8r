from rest_framework.throttling import SimpleRateThrottle

class UserApplicationRateThrottle(SimpleRateThrottle):
    scope = "user_application"

    def get_cache_key(self, request, view):
        application_uuid = view.kwargs.get("application_uuid")
        user = request.user

        if not user or not user.is_authenticated or not application_uuid:
            return None

        return self.cache_format % {
            "scope": self.scope,
            "ident": f"user:{user.id}-app:{application_uuid}",
        }
