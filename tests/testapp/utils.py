from datetime import date, datetime

from django.forms.models import model_to_dict
from testapp import factories

from zivinetz.models import UserProfile


def model_to_postable_dict(instance):
    data = model_to_dict(instance)
    for key in list(data.keys()):
        if data[key] is None:
            data[key] = ""
        elif isinstance(data[key], (date, datetime)):
            data[key] = data[key].strftime("%Y-%m-%d")
    return data


def get_messages(response):
    return [m.message for m in response.context["messages"]]


def admin_login(testcase):
    if not getattr(testcase, "admin", None):
        testcase.admin = factories.UserFactory.create(is_staff=True, is_superuser=True)
        # Create UserProfile with admin type
        UserProfile.objects.create(user=testcase.admin, user_type="admin")
    testcase.client.force_login(testcase.admin)
