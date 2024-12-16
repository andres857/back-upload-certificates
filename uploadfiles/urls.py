from django.urls import path
from . import views

app_name = 'upload_files'  # Esto define el espacio de nombres

urlpatterns = [
    path('', views.procesar_datos_excel, name='upload'),
    path('test', views.example_upload_do, name='test'),
]