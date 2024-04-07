from django.contrib import admin
from django.urls import path, include
from balance.views import custom_login

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ge/', include('balance.urls')),
    path('login/', custom_login, name='custom_login'),
]
