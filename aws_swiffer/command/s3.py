from aws_swiffer.factory.s3.BucketFactory import BucketFactory
from aws_swiffer.utils import get_logger, get_tags

logger = get_logger('s3')


def remove_bucket_by_name(name: str):
    s3 = BucketFactory().create_by_name(name=name)
    s3.remove()


def remove_bucket_by_tags(tags: str = None):
    tags = get_tags(tags)

    logger.info(f"Search S3 buckets by tags: \n{tags}")
    buckets = BucketFactory().create_by_tags(tags=tags)
    logger.info(f"Found {len(buckets)} Buckets")
    for s in buckets:
        s.remove()

def clear_bucket_by_list_file(file_path: str):
    logger.info(f"Taking S3 buckets from file...")
    buckets = BucketFactory().create_by_list_file(file_path = file_path)
    for bucket in buckets:
        bucket.remove(clear_only=True)