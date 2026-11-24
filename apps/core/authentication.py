from rest_framework import authentication
from rest_framework.request import Request


class SessionAuthentication(authentication.SessionAuthentication):
    def authenticate_header(self, request: Request) -> str:
        return "Session"
