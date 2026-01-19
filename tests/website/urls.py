from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth.decorators import login_required
from django.urls import path, re_path
from django.views.generic import TemplateView

urlpatterns = [
    *i18n_patterns(path('', TemplateView.as_view(template_name='index.html'), name='index')),
    path('accounts/login/', TemplateView.as_view(template_name='login.html'), name='login'),
    re_path(
        r'^internal/(?:(?P<parameter>[^/]+)/)?$',
        login_required(TemplateView.as_view(template_name='internal.html')),
        name='internal',
    ),
]
