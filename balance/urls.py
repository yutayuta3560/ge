from django.urls import path
from . import views
from django.views.generic import RedirectView
from balance.views import user_login, signup
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('signup/', signup, name='signup2'),
    path('login/', user_login, name='custom_login2'),
    path('login2/', user_login, name='custom_login3'),
    path('all_list', views.entry_list, name='all_list'),
    path('report/', views.report, name='report'),
    path('group_report/', views.group_report, name='group_report'),
    path('', views.my_list, name='my_list'),
    path('my_graph/', views.my_graph, name='my_graph'),
    path('create/', views.create_entry, name='create_entry'),
    path('detail/<int:pk>/', views.entry_detail, name='entry_detail'),
    path('update/<int:pk>/', views.update_entry, name='update_entry'),
    path('delete/<int:pk>/', views.delete_entry, name='delete_entry'),
    path('get_hotels', views.get_hotels, name='get_hotels'),
    path('logout/', LogoutView.as_view(next_page='custom_login2'), name='logout'),

]
