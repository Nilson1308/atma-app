from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    """
    Um gerenciador de modelo de usuário personalizado onde o email é o identificador
    único para autenticação em vez de nomes de usuário.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Cria e salva um usuário com o email e a senha fornecidos.
        """
        if not email:
            raise ValueError('O Email deve ser definido')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Cria e salva um Superusuário com o email e a senha fornecidos.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('O Superusuário deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('O Superusuário deve ter is_superuser=True.')

        return self.create_user(email, password, **extra_fields)
