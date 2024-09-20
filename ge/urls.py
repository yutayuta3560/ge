from django.contrib import admin
from django.urls import path, include
from balance.views import user_login, signup
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/ge/', permanent=False)),
    path('admin/', admin.site.urls),
    path('ge/', include('balance.urls')),
    path('login/', user_login, name='custom_login'),
    path('signup/', signup, name='signup'),
]
