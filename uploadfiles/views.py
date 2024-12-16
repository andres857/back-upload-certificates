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
        # Set the ACL based on whether the file should be public
        acl = 'public-read' if is_public else 'private'
        
        # Upload the file
        client.put_object(
            Bucket=bucket_name,
            Key=file_path,
            Body=file_content,
            ACL=acl
        )
        
        # If the upload was successful and the file is public, return its URL
        if is_public:
            return f"https://{bucket_name}.nyc3.digitaloceanspaces.com/{file_path}"
        return f"File uploaded successfully to {file_path}"
        
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

async def upload_file(client):
    # Step 3: Call the put_object command and specify the file to upload.
    client.put_object(Bucket='example-space-name', # The path to the directory you want to upload the object to, starting with your Space name.
        Key='folder-path/hello-world.txt', # Object key, referenced whenever you want to access this file later.
        Body=b'Hello, World!', # The object's contents.
        ACL='private', # Defines Access-control List (ACL) permissions, such as private or public.
        Metadata={ # Defines metadata tags.
            'x-amz-meta-my-key': 'your-value'
        }
    )

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
        