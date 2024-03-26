# middleware.py
from django.conf import settings


class NgrokMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.headers.get('Host', '')
        if '.ngrok.io' in host:
            settings.ALLOWED_HOSTS.append(host)

        response = self.get_response(request)

        return response
