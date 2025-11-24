from django.urls import path
from . import views

urlpatterns = [
    path('', views.school_import_view, name='school_import'),
]