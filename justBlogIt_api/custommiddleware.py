def print_cookies_middleware(get_response):
    def print_cookies(request):
        return get_response(request)
    return print_cookies