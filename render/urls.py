from django.urls import path

from . import views

urlpatterns = [
	path('', views.index, name='index'),
	path('readings/', views.readings_list, name='readings_list'),
]
