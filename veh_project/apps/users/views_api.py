"""
Vues REST API pour la gestion des utilisateurs (Flutter).
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import UserRegisterSerializer, UserProfileSerializer


class RegisterAPIView(APIView):
    """
    POST /api/auth/register/
    Crée un nouveau compte utilisateur, retourne les données du profil.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            profile_serializer = UserProfileSerializer(user)
            return Response(
                {
                    'message': 'Compte créé avec succès.',
                    'user': profile_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileAPIView(APIView):
    """
    GET  /api/auth/me/  → retourne le profil de l'utilisateur connecté
    PATCH /api/auth/me/ → met à jour le profil
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
