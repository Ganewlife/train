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

    def create_user(self, email, password=None, **extra_fields):
        if not email or email is None:
            raise ValueError(_("L'email est obligatoire"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        
        if not password or password is None:
            raise TypeError("Mot de passe est obligatoire.")
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        if email is None:
            raise TypeError("Superusers exige un email.")
        if password is None:
            raise TypeError("Mot de passe est obligatoire.")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
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
    REQUIRED_FIELDS = ["nom", "prenoms"] 
    
    objects = UserManager()

    @property
    def full_name(self):
        return f"{self.nom} {self.prenoms}"
    
    def __str__(self) -> str:
        return self.nom+" "+self.prenoms