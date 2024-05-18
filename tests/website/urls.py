from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html')),
    path('accounts/login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path(
        'internal/',
        login_required(TemplateView.as_view(template_name='internal.html')),
        name='internal',
    ),
]
