from django.urls import path
from . import views

urlpatterns = [
    # post view
    path('login/',views.user_login,name='login')
]
