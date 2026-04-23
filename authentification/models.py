from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):

    """ def create_user(self, telephone, password=None, **extra_fields):
        if not telephone:
            raise ValueError("Le téléphone est obligatoire")

        user = self.model(telephone=telephone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user """

    """ def create_superuser(self, telephone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(telephone, password, **extra_fields) """

class User(AbstractUser):
    # username = models.CharField(max_length=60 , blank=True, null=True, unique=False)
    email = models.EmailField(max_length=100 , blank=True, null=True, unique=True)
    nom = models.CharField(max_length=50, blank=False, null=False)
    prenoms = models.CharField(max_length=65, blank=False, null=False)
    photo_url = models.ImageField(upload_to='photo/')
    
    creat_at = models.DateTimeField(auto_now_add=True, editable=False)
    update_at = models.DateTimeField(auto_now=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, auto_created=True)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email' 
    REQUIRED_FIELDS = [] 
    
    objects = UserManager()