import zipfile,os
import botocore.config
from django.shortcuts import render
from django.http import JsonResponse
import boto3
from typing import Optional
from functools import lru_cache

@lru_cache(maxsize=1)
def get_spaces_client():
    """
    Creates and returns a singleton instance of the DigitalOcean Spaces client.
    Uses environment variables for sensitive credentials.
    """
    try:
        session = boto3.session.Session()
        client = session.client('s3',
        endpoint_url='https://nyc3.digitaloceanspaces.com', # Find your endpoint in the control panel, under Settings. Prepend "https://".
        config=botocore.config.Config(s3={'addressing_style': 'virtual'}), # Configures to use subdomain/virtual calling format.
        region_name='nyc3', # Use the region in your endpoint.
        aws_access_key_id= os.environ.get('aws_access_key_id'), # Access key pair. You can create access key pairs using the control panel or API.
        aws_secret_access_key=os.environ.get('aws_secret_access_key')) # Secret access key defined through an environment variable.
        return client
    except Exception as e:
        print(f"Error connecting to Spaces: {str(e)}")
        return None

async def upload_to_spaces(
    file_content: bytes,
    file_path: str,
    bucket_name: str,
    is_public: bool = True
) -> Optional[str]:
    """
    Uploads a file to DigitalOcean Spaces.
    
    Args:
        file_content: The content to upload
        file_path: The path/name for the file in Spaces
        bucket_name: The name of your Space
        is_public: Whether the file should be publicly accessible
    
    Returns:
        The URL of the uploaded file if successful, None if failed
    """
    client = get_spaces_client()
    if not client:
        return None
    
    try:
        # Determinamos el Content-Type basado en la extensión del archivo
        content_type = None
        if file_path.lower().endswith('.pdf'):
            content_type = 'application/pdf'
        elif file_path.lower().endswith('.png'):
            content_type = 'image/png'
        elif file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
            content_type = 'image/jpeg'
        
        # Set the ACL based on whether the file should be public
        acl = 'public-read' if is_public else 'private'
        
        upload_args = {
            'Bucket': bucket_name,
            'Key': file_path,
            'Body': file_content,
            'ACL': acl
        }
        # Añadimos el Content-Type solo si se detectó uno válido
        if content_type:
            upload_args['ContentType'] = content_type
        
        # Upload the file with all parameters
        client.put_object(**upload_args)

        return f"https://{bucket_name}.nyc3.digitaloceanspaces.com/{file_path}"
        
    except Exception as e:
        print(f"Error uploading to Spaces: {str(e)}")
        return None
    
async def example_upload_do(request):
    # Upload a text file
    folder_name = request.GET.get('folder_name', 'itsme1')
    result = await upload_to_spaces(
        file_content=b'Hello, World!',
        file_path=f"{folder_name}/hello.txt",
        bucket_name='certificates-private-zones',
        is_public=True
    )    
    if result:
        print(f"File uploaded successfully: {result}")
        return JsonResponse({'message': 'File uploaded successfully', 'url': result})
    else:
        print("Upload failed")
        return JsonResponse({'error': 'Upload failed'}, status=500)

async def procesar_datos_excel(request):
    if request.method == "GET":
        return render(request, 'uploadfile.html')
    elif request.method == "POST":
        archivo_zip = request.FILES.get('archivo')
        
        if archivo_zip and archivo_zip.name.endswith('.zip'):
            estructura = {
                'carpetas': set(),
                'archivos': [],
                'urls_archivos': []
            }
            
            try:
                with zipfile.ZipFile(archivo_zip, 'r') as zip_ref:
                    certificate_name = ''
                    
                    for certificate in zip_ref.namelist():
                        if certificate.endswith('/'):
                            certificate_name = certificate
                            estructura['carpetas'].add(certificate)
                        else:
                            granted_to = os.path.basename(certificate)
                            try:
                                # Leemos el contenido del archivo
                                contenido = zip_ref.read(certificate)
                                
                                # Construimos la ruta en Spaces usando la estructura de carpetas
                                ruta_spaces = f"{certificate_name}{granted_to}"
                                
                                # Subimos el archivo a Spaces
                                result = await upload_to_spaces(
                                    file_content=contenido,
                                    file_path=ruta_spaces,
                                    bucket_name='certificates-private-zones',
                                    is_public=True
                                )
                                
                                if result:
                                    # Si la subida fue exitosa, guardamos la información
                                    estructura['urls_archivos'].append({
                                        'nombre': granted_to,
                                        'carpeta': certificate_name,
                                        'url': result
                                    })
                                    print (f"Success: file upload success, certificate: {granted_to}, name: {certificate_name}")
                                else:
                                    print(f"Error: No se pudo obtener URL para {granted_to}")
                                    
                            except Exception as e:
                                print(f"Error al procesar archivo {granted_to}: {str(e)}")
                                
                            estructura['archivos'].append(granted_to)
                
                # Convertimos el set a lista para poder serializarlo
                estructura['carpetas'] = list(estructura['carpetas'])
                print(estructura)
                
                return JsonResponse({
                    'success': True,
                    'estructura': estructura,
                    'mensaje': f"Se subieron {len(estructura['urls_archivos'])} archivos correctamente"
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Error al procesar el archivo ZIP: {str(e)}'
                })
        
        return JsonResponse({
            'success': False,
            'error': 'Por favor sube un archivo ZIP válido'
        })
        