from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import View, ListView, TemplateView
from django.contrib.auth import login, authenticate, logout 
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import permission_required
from . import models
from . import forms
import json

User = get_user_model()
# Create your views here.
class RegisterView(View):
    template_name = 'authentification/register.html'
    form_class = forms.SignupForm
    def get(self, request):
        form = self.form_class()
        message = ''
        return render(request, self.template_name, context={'form': form, 'message': message})

    def post(self, request):
        form = self.form_class(request.POST, request.FILES)

        if form.is_valid():
            # new_user = form.save(commit=False)
            if form.cleaned_data:
                user = form.save() 
                # user.save() 

                # login(request, user)# on connect l'utilisateur
                return redirect('login')
            else:
                message = 'erreur de données'
                return render(request,self.template_name, context={'form': form,'message': message})
        else:
            message = 'Formulaire invalide'
            # print(form.errors)
            return render(request, 'authentification/register.html', context={'form': form,'message': message})
        
def login_view(request):
    form = forms.LoginForm(data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        # messages.success(request, f"Bienvenue {user.nom} !")
        messages.info(request, "Vous êtes déconnecté.")
        
        """ if request.user.is_superuser:
            return redirect('user_list')
        else:
            return redirect('commande') """
        return redirect('produits')
    return render(request, 'authentification/login.html', {'form': form})

        
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Vous êtes déconnecté.")
    return redirect('login')

@login_required
def user_list_view(request):
    # users = User.objects.filter(is_active=True).order_by('-creat_at')
    users = User.objects.filter(is_active=True).order_by('-creat_at')
    return render(request, 'authentification/users.html', {'users': users})


@login_required
def user_detail_view(request, pk):
    profile_user = get_object_or_404(User, pk=pk)
    form = None
    form_class = forms.ProfileUpdateForm
        

    form = form_class(
        request.POST or None,
        request.FILES or None,
        instance=profile_user
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Profil mis à jour avec succès !")
        return redirect('user_detail', pk=pk)

    return render(request, 'authentification/profil.html', {
        'profile_user': profile_user,
        'form': form,
        'profil': profile_user,
    })