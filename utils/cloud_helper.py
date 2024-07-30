import boto3
import os
from werkzeug.utils import secure_filename
from decimal import Decimal
from botocore.exceptions import ClientError
import json
import uuid
BUCKET_NAME = 'mytelecomfyp'
from decimal import Decimal
from datetime import datetime
import os

import boto3
from botocore.exceptions import ClientError



# Initialize S3 and DynamoDB clients
aws_access_key_id = os.getenv('AWS_ACCESS_KEY')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = 'eu-north-1'






s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)

dynamodb = boto3.client(
    'dynamodb',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)

dynamodb_resource = boto3.resource(
    'dynamodb',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)



def upload_bdf_file_to_s3(file, folder_name):
    filename = secure_filename(file.filename)
    file_path = os.path.join(folder_name, filename)
    print("This is file path", file_path)
    try:
        s3.upload_fileobj(
            file,
            BUCKET_NAME,
            f"{folder_name}/{filename}".replace("\\", "/"),  
        )
        # Construct and return the URL
        s3_image_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{folder_name}/{filename}"
        return s3_image_url
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def upload_file_to_s3(file, folder_name):
    filename = secure_filename(file.filename)
    file_path = os.path.join(folder_name, filename)
    print("This is file path", file_path)
    try:
        s3.upload_fileobj(
            file,
            BUCKET_NAME,
            f"{folder_name}/{filename}".replace("\\", "/"),  
        )
        return True
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


# Example function to upload a file to S3
def upload_generated_file_to_s3(file_path, folder_name):
    try:
        # Extract filename from file path
        filename = os.path.basename(file_path)

        # Upload the file to S3
        s3.upload_file(
            file_path,
            BUCKET_NAME,
            f"{folder_name}/{filename}".replace("\\", "/")
        )

        # Construct and return the URL
        s3_image_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{folder_name}/{filename}"
        return s3_image_url

    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        return None

def get_data_for_arduino(table_name):
    table = dynamodb_resource.Table(table_name)
    try:
        # Scan the table and get all items
        response = table.scan()
        items = response.get('Items', [])
        
        # Check if the items list is empty
        if not items:
            return None
        
        # Sort items by timestamp and get the last one
        last_item = sorted(items, key=lambda x: x['timestamp'], reverse=True)[0]
        
        return last_item
    except Exception as e:
        print(f"Error fetching data from DynamoDB: {e}")
        return None

# Custom JSON Encoder that handles Decimal
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

# Function to convert floats to Decimal, suitable for DynamoDB
def convert_floats(obj):
    if isinstance(obj, list):
        return [convert_floats(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_floats(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj



def save_summary_to_dynamodb(summary_report, table_name):

    summary_report = convert_floats(summary_report)
    timestamp = datetime.utcnow().isoformat()
    # Prepare the item for DynamoDB
    item = {
        'id': {'N': str(int(uuid.uuid4().int >> 64))},
        'timestamp': {'S': timestamp},
        'accuracy': {'N': str(summary_report['accuracy'])},
        'precision': {'N': str(summary_report['precision'])},
        'recall': {'N': str(summary_report['recall'])},
        'f1_score': {'N': str(summary_report['f1_score'])},
        'confusion_matrix_image_url': {'S': summary_report['confusion_matrix_image_url']},
        'roc_auc': {'S': summary_report['roc_auc']},
        'classification_report': {'S': json.dumps(summary_report['classification_report'],cls=DecimalEncoder)}, 
        'class_distribution': {'S': json.dumps(summary_report['class_distribution'], cls=DecimalEncoder)}
    }

    try:
        response = dynamodb.put_item(TableName=table_name, Item=item)
        return response
    except boto3.exceptions.ClientError as e:
        print(e.response['Error']['Message'])
        return None