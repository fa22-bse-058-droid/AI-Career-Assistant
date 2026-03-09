"""
Permission classes for RBAC.
"""
from rest_framework.permissions import BasePermission

from .models import CustomUser


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == CustomUser.Role.STUDENT
        )


class IsEmployer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == CustomUser.Role.EMPLOYER
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == CustomUser.Role.ADMIN
        )


class IsStudentOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            CustomUser.Role.STUDENT,
            CustomUser.Role.ADMIN,
        )
