from django.urls import path
from . import views

app_name = 'invoicing'

urlpatterns = [
    path('', views.render_upload_excel, name='render_upload_excel'),  # View to render the HTML form
    path('process_excel/', views.process_excel, name='process_excel'),  # View to process the form and send PDFs
]
