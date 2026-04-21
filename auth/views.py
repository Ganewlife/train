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

# Create your views here.
class RegisterView(View):
    template_name = 'auth/register.html'
    form_class = forms.SignupForm
    def get(self, request):
        form = self.form_class()
        message = ''
        return render(request, self.template_name, context={'form': form, 'message': message})

    def post(self, request):
        form = self.form_class(request.POST)

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
            return render(request, 'auth/register.html', context={'form': form,'message': message})