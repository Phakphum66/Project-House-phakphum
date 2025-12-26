from django.utils import translation


class ForceThaiLocaleMiddleware:
    """Force Thai locale for all requests, overriding browser Accept-Language.

    Place after LocaleMiddleware to ensure activation applies consistently.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        translation.activate('th')
        request.LANGUAGE_CODE = 'th'
        response = self.get_response(request)
        translation.deactivate()
        return response
