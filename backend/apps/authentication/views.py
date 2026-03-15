"""
Views for authentication app.
"""
from django.conf import settings
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .models import CustomUser, UserProfile
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    UserProfileSerializer,
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
)

_REFRESH_COOKIE = "refresh_token"
_REFRESH_MAX_AGE = int(jwt_settings.REFRESH_TOKEN_LIFETIME.total_seconds())


def _set_refresh_cookie(response, token_str):
    """Attach the refresh token as an httpOnly cookie."""
    response.set_cookie(
        _REFRESH_COOKIE,
        token_str,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        path="/",
        max_age=_REFRESH_MAX_AGE,
    )


@method_decorator(ratelimit(key="ip", rate="3/m", method="POST", block=True), name="post")
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response = Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )
        _set_refresh_cookie(response, str(refresh))
        return response


@method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True), name="post")
class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            refresh_token = response.data.pop("refresh", None)
            if refresh_token:
                _set_refresh_cookie(response, refresh_token)
        return response


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get(_REFRESH_COOKIE) or request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token not provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
            )
        response = Response({"detail": "Logout successful."}, status=status.HTTP_200_OK)
        response.delete_cookie(_REFRESH_COOKIE, path="/", samesite="Lax")
        return response


class CookieTokenRefreshView(APIView):
    """Token refresh view that reads the refresh token from an httpOnly cookie."""

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token_str = request.COOKIES.get(_REFRESH_COOKIE)
        if not refresh_token_str:
            return Response(
                {"detail": "Refresh token not found."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            refresh = RefreshToken(refresh_token_str)
        except TokenError as e:
            return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        response = Response({"access": str(refresh.access_token)})

        if jwt_settings.ROTATE_REFRESH_TOKENS:
            if jwt_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    refresh.blacklist()
                except AttributeError:
                    pass
            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()
            _set_refresh_cookie(response, str(refresh))

        return response


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"detail": "Password changed successfully."})
