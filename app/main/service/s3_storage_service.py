import os

import boto3


class S3Storage:
    def __init__(self):
        session = boto3.session.Session()
        self.s3 = session.client(
            service_name='s3',
            endpoint_url='https://storage.yandexcloud.net',
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        )
        self.__bucket_name = os.getenv("AWS_BUCKET_NAME")
        self.__root_dir = os.getenv("AWS_ROOT_DIR")

    def upload(self, file, name):
        self.s3.put_object(
            Bucket=self.__bucket_name,
            Key=f'{self.__root_dir}/{name}',
            Body=file
        )

    def get(self, name):
        try:
            response = self.s3.get_object(
                Bucket=self.__bucket_name,
                Key=f'{self.__root_dir}/{name}'
            )
            file_bytes = response['Body'].read()
            return file_bytes
        except Exception:
            return None

    def delete(self, name):
        return self.s3.delete_objects(
            Bucket=self.__bucket_name,
            Delete={'Objects': [{'Key': f'{self.__root_dir}/{name}'}]}
        )
