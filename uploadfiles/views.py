import zipfile,os
from django.shortcuts import render
from django.http import JsonResponse

def procesar_datos_excel(request):
    if request.method == "GET":
        return render(request, 'uploadfile.html')
    elif request.method == "POST":
        
        archivo_zip = request.FILES.get('archivo')  # Asegúrate que este nombre coincida con tu input file
        if archivo_zip and archivo_zip.name.endswith('.zip'):
            
            # Creamos un diccionario para almacenar la estructura
            estructura = {
                'carpetas': set(),  # Usamos set para evitar duplicados
                'archivos': []
            }
            
            # Leemos el archivo ZIP
            with zipfile.ZipFile(archivo_zip, 'r') as zip_ref:
                certificate_name = ''
                for elemento in zip_ref.namelist():
                    if elemento.endswith('/'):
                        certificate_name = elemento
                        print("carpeta : ", elemento)
                        estructura['carpetas'].add(elemento)

                    # Si el elemento no termina en /, es un archivo
                    else:
                        nombre_archivo = os.path.basename(elemento)  # Extrae solo el nombre del archivo
                        print("nombre certificado",certificate_name ,"certificado : ", nombre_archivo)
                        estructura['archivos'].append(nombre_archivo)
            
            # Convertimos el set a lista para poder serializarlo
            estructura['carpetas'] = list(estructura['carpetas'])
            
            return JsonResponse({
                'success': True,
                'estructura': estructura
            })
        
        return JsonResponse({
            'success': False,
            'error': 'Por favor sube un archivo ZIP válido'
        })
        