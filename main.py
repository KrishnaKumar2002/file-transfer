from uuid import uuid4
import boto3
from botocore.exceptions import ClientError
import magic
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi import FastAPI, HTTPException, Response, UploadFile, status
from pydantic import BaseModel
from loguru import logger

# AWS S3 configuration
session = boto3.Session(
    aws_access_key_id='',
    aws_secret_access_key='',
    region_name='us-east-1'  # Ensure you specify the correct region
)

s3 = boto3.resource('s3')
AWS_BUCKET = 'creya-proctoring'  # Replace with your actual bucket name
bucket = s3.Bucket(AWS_BUCKET)

KB = 1024
MB = 1024 * KB

SUPPORTED_FILE_TYPES = {
    'image/png': 'png',
    'image/jpeg': 'jpg',
    'application/pdf': 'pdf',
    'video/mp4': 'mp4',
    'video/webm': 'webm',
}

class UploadResponse(BaseModel):
    file_name: str
    bucket: str
    key: str

class UploadURLResponse(BaseModel):
    upload_url: str
    bucket: str
    key: str

async def s3_upload(contents: bytes, key: str):
    logger.info(f'Uploading {key} to s3')
    bucket.put_object(Key=key, Body=contents)

async def s3_download(key: str):
    try:
        return s3.Object(bucket_name=AWS_BUCKET, key=key).get()['Body'].read()
    except ClientError as err:
        logger.error(str(err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error downloading file")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this to restrict to specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],  # Update this to restrict to specific methods if needed
    allow_headers=["*"],  # Update this to restrict to specific headers if needed
)

@app.get('/')
async def home():
    return {'message': 'Hello from file-upload 😄👋'}

@app.post('/upload', response_model=UploadResponse)
async def upload(file: UploadFile | None = None):
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No file found!!'
        )

    contents = await file.read()
    size = len(contents)

    if not 0 < size <= 100 * MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Supported file size is 0 - 100 MB'
        )

    file_type = magic.from_buffer(buffer=contents, mime=True)
    if file_type not in SUPPORTED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Unsupported file type: {file_type}. Supported types are {SUPPORTED_FILE_TYPES}'
        )
    
    file_name = f'{uuid4()}.{SUPPORTED_FILE_TYPES[file_type]}'
    key = f'{file_name}'
    
    await s3_upload(contents=contents, key=key)
    
    return UploadResponse(
        file_name=file_name,
        bucket=AWS_BUCKET,
        key=key
    )

@app.get('/get-upload-url', response_model=UploadURLResponse)
async def get_upload_url():
    file_key = f'videos/{uuid4()}.mp4'  # Adjust file key as needed

    params = {
        'Bucket': AWS_BUCKET,
        'Key': file_key,
        'Expires': 60,  # URL expires in 60 seconds
        'ContentType': 'video/mp4'
    }

    try:
        upload_url = s3.meta.client.generate_presigned_url('put_object', Params=params, ExpiresIn=60)
        return UploadURLResponse(
            upload_url=upload_url,
            bucket=AWS_BUCKET,
            key=file_key
        )
    except ClientError as e:
        logger.error(str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error generating upload URL")

@app.get('/download')
async def download(file_name: str | None = None):
    if not file_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No file name provided'
        )

    contents = await s3_download(key=file_name)
    return Response(
        content=contents,
        headers={
            'Content-Disposition': f'attachment;filename={file_name}',
            'Content-Type': 'application/octet-stream',
        }
    )

if __name__ == '__main__':
    uvicorn.run(app='main:app', reload=True)





# from uuid import uuid4
# import boto3
# from botocore.exceptions import ClientError
# import magic
# import uvicorn
# from fastapi import FastAPI, HTTPException, Response, UploadFile, status
# from loguru import logger

# # AWS S3 configuration
# session = boto3.Session(
#       aws_access_key_id='',
#       aws_secret_access_key='',
# )

# KB = 1024
# MB = 1024 * KB

# SUPPORTED_FILE_TYPES = {
#     'image/png': 'png',
#     'image/jpeg': 'jpg',
#     'application/pdf': 'pdf',
#     'video/mp4': 'mp4',
#     'video/webm': 'webm',
# }

# AWS_BUCKET = 'creya-proctoring'  # Correct bucket name
# s3 = boto3.resource('s3')
# bucket = s3.Bucket(AWS_BUCKET)

# async def s3_upload(contents: bytes, key: str):
#     logger.info(f'Uploading {key} to s3')
#     bucket.put_object(Key=key, Body=contents)

# async def s3_download(key: str):
#     try:
#         return s3.Object(bucket_name=AWS_BUCKET, key=key).get()['Body'].read()
#     except ClientError as err:
#         logger.error(str(err))

# app = FastAPI()

# @app.get('/')
# async def home():
#     return {'message': 'Hello from file-upload 😄👋'}

# @app.post('/upload')
# async def upload(file: UploadFile | None = None):
#     if not file:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail='No file found!!'
#         )

#     contents = await file.read()
#     size = len(contents)

#     if not 0 < size <= 100 * MB:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail='Supported file size is 0 - 100 MB'
#         )

#     file_type = magic.from_buffer(buffer=contents, mime=True)
#     if file_type not in SUPPORTED_FILE_TYPES:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f'Unsupported file type: {file_type}. Supported types are {SUPPORTED_FILE_TYPES}'
#         )
#     file_name = f'{uuid4()}.{SUPPORTED_FILE_TYPES[file_type]}'
#     await s3_upload(contents=contents, key=file_name)
#     return {'file_name': file_name}

# @app.get('/download')
# async def download(file_name: str | None = None):
#     if not file_name:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail='No file name provided'
#         )

#     contents = await s3_download(key=file_name)
#     return Response(
#         content=contents,
#         headers={
#             'Content-Disposition': f'attachment;filename={file_name}',
#             'Content-Type': 'application/octet-stream',
#         }
#     )

# if __name__ == '__main__':
#     uvicorn.run(app='main:app', reload=True)
