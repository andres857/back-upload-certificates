from django.shortcuts import render

# Create your views here.
def uploadFile(request):
    return render(request, 'uploadfile.html')

def procesar_datos_excel(request):
    if "GET" == request.method:
       return render(request, 'uploadfile.html', {})
        