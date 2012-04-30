from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class ModelBackend(ModelBackend):
    """
    Authentication backend which knows how to handle e-mails or usernames
    """

    def authenticate(self, username=None, password=None):
        for user in User.objects.filter(
                Q(username__iexact=username)
                | Q(email__iexact=username)
                | Q(drudge__zdp_no__iexact=username)
                ):
            if user.check_password(password):
                return user

        return None
