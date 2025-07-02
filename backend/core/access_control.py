from core.models import ApplicationPermission


def token_has_access(token, app, action):
    if token.is_root:
        return True
    try:
        perm = token.app_permissions.get(application=app)
        return perm.has_permission(action)
    except ApplicationPermission.DoesNotExist:
        return False
