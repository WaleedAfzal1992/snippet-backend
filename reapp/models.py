from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class CustomUserManager(BaseUserManager):
    def create_user(self, Email, name, password=None, **extra_fields):
        if not Email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(Email)
        user = self.model(Email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, Email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(Email, name, password, **extra_fields)


class RegisterBlog(AbstractBaseUser, PermissionsMixin):
    First_name = models.CharField(max_length=100)
    Last_name = models.CharField(max_length=100)
    name = models.CharField(max_length=100, unique=True)
    Email = models.EmailField(max_length=200, unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'Email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.name


class LoginBlog(models.Model):
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.username


class BlogArticle(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()

    def __str__(self):
        return self.title


class BlogContactUs(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=200)
    message = models.CharField(max_length=1000)

    def __str__(self):
        return self.name
