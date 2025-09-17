from rest_framework.throttling import SimpleRateThrottle
from core.models.application import Application
from core.models import LLMModel
from django.core.exceptions import ObjectDoesNotExist


class UserApplicationRateThrottle(SimpleRateThrottle):
    scope = "user_application"

    def get_cache_key(self, request, view):
        application_uuid = view.kwargs.get("application_uuid")
        if not application_uuid:
            return None

        return self.cache_format % {
            "scope": self.scope,
            "ident": str(application_uuid),
        }

    def get_rate(self):
        application_uuid = self.view.kwargs.get("application_uuid")

        if not application_uuid:
            return None

        try:
            app = Application.objects.get(uuid=application_uuid)
            text_model = app.get_model_by_type(LLMModel.ModelType.TEXT)

            if text_model.is_default:
                return "10/minute"
            else:
                return app.custom_model_rate_limit_per_model or "10/minute"
        except ObjectDoesNotExist:
            return "10/minute"
