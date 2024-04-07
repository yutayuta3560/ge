from django.urls import path
from . import views


urlpatterns = [
    path('all_list', views.entry_list, name='all_list'),
    path('all_graph/', views.all_users_graph, name='all_graph'),
    path('', views.my_list, name='my_list'),
    path('my_graph/', views.my_graph, name='my_graph'),
    path('create/', views.create_entry, name='create_entry'),
    path('update/<int:pk>/', views.update_entry, name='update_entry'),
    path('delete/<int:pk>/', views.delete_entry, name='delete_entry'),
]
