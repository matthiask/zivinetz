class UglynessMiddleware(object):
    def process_request(self, request):
        request.access = request.user  # XXX Uglyness
