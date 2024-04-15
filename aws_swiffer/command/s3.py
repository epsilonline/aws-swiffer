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
