import os
import boto3

def upload_pdf(**kwargs):
    """
    Resolves a PDF from local upload folder or downloads from S3.
    Pushes the local path to XCom.
    """

    # Example context variable you might pass to Airflow params
    file_source = kwargs.get("params", {}).get("file_source", "local")  # or "s3"
    file_name = kwargs.get("params", {}).get("file_name", "sample.pdf")

    local_upload_dir = "/usr/local/airflow/uploads"
    s3_bucket = "your-s3-bucket"
    s3_key_prefix = "uploads/"

    if file_source == "local":
        local_path = os.path.join(local_upload_dir, file_name)

        if not os.path.exists(local_path):
            raise FileNotFoundError(f"File not found in web upload folder: {local_path}")
        print(f"Found file locally at: {local_path}")

    elif file_source == "s3":
        local_path = f"/tmp/{file_name}"
        s3 = boto3.client("s3")

        s3_key = f"{s3_key_prefix}{file_name}"
        print(f"Downloading from S3: {s3_bucket}/{s3_key} to {local_path}")
        s3.download_file(s3_bucket, s3_key, local_path)

    else:
        raise ValueError("Invalid file_source. Expected 'local' or 's3'.")

    kwargs['ti'].xcom_push(key='pdf_path', value=local_path)
