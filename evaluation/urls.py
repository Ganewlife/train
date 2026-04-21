"""
URL configuration for evaluation project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings 
from django.urls import path
from django.conf.urls.static import static
from django.urls import path, include
import eshop.views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', eshop.views.ProduitsView.as_view(), name='produits'),
    path('produits/<uuid:pk>/modifier/', eshop.views.ProduitModifierView.as_view(), name='produit_modifier'),
    path('produits/<uuid:pk>/supprimer/', eshop.views.ProduitSupprimerView.as_view(), name='produit_supprimer'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
