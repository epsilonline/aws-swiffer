from typer import Typer
from aws_swiffer.factory.s3.BucketFactory import BucketFactory
from aws_swiffer.utils import get_logger, get_tags

logger = get_logger('s3')
s3_command = Typer()


@s3_command.command()
def remove_bucket_by_name(name: str):
    """
    Empty and delete bucket
    :param name: bucket name
    :return:
    """
    s3 = BucketFactory().create_by_name(name=name)
    s3.remove()


@s3_command.command()
def remove_bucket_by_file_list(file_path: str):
    """
    Empty and delete bucket in file list
    :param file_path:
    :return:
    """
    logger.info(f"Taking S3 buckets from file")
    buckets = BucketFactory().create_by_list_file(file_path=file_path)
    for bucket in buckets:
        bucket.remove()


@s3_command.command()
def remove_bucket_by_tags(tags: str = None):
    """
    Find bucket by tags, and for each bucket empty and delete it
    :param tags:
    :return:
    tags = get_tags(tags)
    """
    tags = get_tags(tags)
    logger.info(f"Search S3 buckets by tags: \n{tags}")
    buckets = BucketFactory().create_by_tags(tags=tags)
    logger.info(f"Found {len(buckets)} Buckets")
    for s in buckets:
        s.remove()


@s3_command.command()
def clean_bucket_by_name(name: str):
    """
    Empty bucket
    :param name: bucket name
    :return:
    """
    s3 = BucketFactory().create_by_name(name=name)
    s3.remove()


@s3_command.command()
def clean_bucket_by_tags(tags: str = None):
    """
    Find bucket by tags, and for each bucket empty it
    :param tags:
    :return:
    tags = get_tags(tags)
    """
    tags = get_tags(tags)
    logger.info(f"Search S3 buckets by tags: \n{tags}")
    buckets = BucketFactory().create_by_tags(tags=tags)
    logger.info(f"Found {len(buckets)} Buckets")
    for s in buckets:
        s.clean()


@s3_command.command()
def clean_bucket_by_file_list(file_path: str):
    """
    Empty bucket in file list
    :param file_path:
    :return:
    """
    logger.info(f"Taking S3 buckets from file")
    buckets = BucketFactory().create_by_list_file(file_path=file_path)
    for s in buckets:
        s.clean()
