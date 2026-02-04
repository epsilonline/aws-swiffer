from typer import Typer, Argument
from aws_swiffer.factory.s3.BucketFactory import BucketFactory
from aws_swiffer.utils import get_logger, get_tags, callback_check_account
from typing_extensions import Annotated

logger = get_logger('s3')


def callback(profile: str = None, region: str = 'eu-west-1', skip_account_check: bool = False,
            dry_run: bool = False, auto_approve: bool = False):
    """
    Clean S3 resources
    """
    callback_check_account(profile=profile, region=region, skip_account_check=skip_account_check,
                          dry_run=dry_run, auto_approve=auto_approve)


s3_command = Typer(callback=callback)


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
    buckets = BucketFactory().create_by_file_list(file_path=file_path)
    for bucket in buckets:
        bucket.remove()


@s3_command.command()
def remove_bucket_by_tags(tags: Annotated[str, Argument(help="You can provide JSON tag list or use GUI for choose "
                                                             "selection tags.")] = None):
    """
    Find bucket by tags, and for each bucket empty and delete it.
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
def clean_bucket_by_tags(tags: Annotated[str, Argument(help="You can provide JSON tag list or use GUI for choose "
                                                             "selection tags.")] = None):
    """
    Find bucket by tags, and for each bucket empty it
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
    buckets = BucketFactory().create_by_file_list(file_path=file_path)
    for s in buckets:
        s.clean()
