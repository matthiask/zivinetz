from django.views.generic import ListView
from django.utils.translation import gettext_lazy as _


class BaseView(ListView):
    """
    Base view class that provides common functionality for list views.
    """

    def get_queryset(self):
        """
        Get the queryset based on search parameters.
        """
        queryset = super().get_queryset()

        # Apply search filters if any
        if self.request.GET.get("s"):
            for key, value in self.request.GET.items():
                if key != "s" and value:
                    if hasattr(self, f"filter_{key}"):
                        queryset = getattr(self, f"filter_{key}")(queryset, value)

        return queryset
