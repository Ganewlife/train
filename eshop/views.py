from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import View, ListView, TemplateView
from django.shortcuts import render, redirect, redirect, get_object_or_404
from django.contrib import messages
from . import models
from . import forms
from django.db.models import Sum, Count

import json

# Create your views here.
class ProduitsView(View):
    template_name = 'eshop/produits.html'
    form_class = forms.ProduitsForm

    def get(self, request):
        form = self.form_class()
        produits = models.Produits.objects.filter(is_active=True).order_by('-date_ajout')
        
        stats = produits.aggregate(
            total_produits=Count('id'),
            montant_total=Sum('prix')
        )
        
        return render(request, self.template_name, context={
            'form': form,
            'produits': produits,
            'total_produits': stats['total_produits'],
            'montant_total': stats['montant_total'] or 0,
        })

    def post(self, request):
        form = forms.ProduitsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('produits')
        return render(request, self.template_name, context={'form': form, 'produits': models.Produits.objects.filter(is_active=True).order_by('-date_ajout')})
            


class ProduitModifierView(View):
    template_name = 'eshop/produit_modifier.html'
    form_class = forms.ProduitsForm

    def get(self, request, pk):
        produit = get_object_or_404(models.Produits, pk=pk)
        form = self.form_class(instance=produit)
        return render(request, self.template_name, context={'form': form, 'produit': produit})

    def post(self, request, pk):
        produit = get_object_or_404(models.Produits, pk=pk)
        form = self.form_class(request.POST, request.FILES, instance=produit)
        if form.is_valid():
            form.save()
            return redirect('produits')
        return render(request, self.template_name, context={'form': form, 'produit': produit})


class ProduitSupprimerView(View):

    def post(self, request, pk):
        produit = get_object_or_404(models.Produits, pk=pk)
        produit.delete()  # ou produit.is_active = False; produit.save() pour soft delete
        return redirect('produits')