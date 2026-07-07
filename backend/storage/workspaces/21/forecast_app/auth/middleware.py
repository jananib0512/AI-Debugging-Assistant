class AuthMiddleware:
    def __init__(self, app=None): self.app = app
    def process_request(self): return True
