"""
Vues web pour l'authentification et le profil utilisateur.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator

from .forms import RegisterForm, LoginForm, ProfileForm


class RegisterView(View):
    """Vue d'inscription — crée un nouveau compte joueur."""
    template_name = 'users/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        form = RegisterForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Bienvenue, {user.display_name} ! Votre aventure commence.')
            return redirect('home')
        return render(request, self.template_name, {'form': form})


class LoginView(View):
    """Vue de connexion."""
    template_name = 'users/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bon retour, {user.display_name} !')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    """Vue de déconnexion."""
    def post(self, request):
        logout(request)
        messages.info(request, 'Vous avez été déconnecté.')
        return redirect('home')

    def get(self, request):
        logout(request)
        return redirect('home')


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    """Vue profil — affiche les histoires en cours et terminées."""
    template_name = 'users/profile.html'

    def get(self, request):
        from apps.sessions.models import GameSession
        # Histoires en cours (non terminées)
        active_sessions = GameSession.objects.filter(
            user=request.user,
            is_completed=False
        ).select_related('story', 'current_scene').order_by('-last_played')

        # Histoires terminées
        completed_sessions = GameSession.objects.filter(
            user=request.user,
            is_completed=True
        ).select_related('story').order_by('-last_played')

        form = ProfileForm(instance=request.user)
        context = {
            'form': form,
            'active_sessions': active_sessions,
            'completed_sessions': completed_sessions,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour avec succès.')
            return redirect('profile')

        from apps.sessions.models import GameSession
        active_sessions = GameSession.objects.filter(user=request.user, is_completed=False)
        completed_sessions = GameSession.objects.filter(user=request.user, is_completed=True)

        context = {
            'form': form,
            'active_sessions': active_sessions,
            'completed_sessions': completed_sessions,
        }
        return render(request, self.template_name, context)
