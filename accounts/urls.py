from django.urls import path
from .views import CustomLoginView, CustomLogoutView, SignUpView, confirm_account

urlpatterns = [
    path('', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('confirm/', confirm_account, name='confirm'),
]