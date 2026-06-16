from functools import wraps
from django.http import JsonResponse


def login_required_api(view_fn):
    @wraps(view_fn)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("employee_id"):
            return JsonResponse({"error": "Необхідна авторизація"}, status=401)
        return view_fn(request, *args, **kwargs)
    return wrapper


def manager_required(view_fn):
    @wraps(view_fn)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("employee_id"):
            return JsonResponse({"error": "Необхідна авторизація"}, status=401)
        if request.session.get("role") != "Manager":
            return JsonResponse({"error": "Доступ лише для менеджерів"}, status=403)
        return view_fn(request, *args, **kwargs)
    return wrapper
