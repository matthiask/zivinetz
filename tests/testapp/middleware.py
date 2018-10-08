def UglynessMiddleware(get_response):
    def fn(request):
        request.access = request.user  # XXX Uglyness
        return get_response(request)

    return fn
