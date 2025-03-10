from typer import Typer, Argument
from aws_swiffer.factory.dynamodb.TableFactory import TableFactory
from aws_swiffer.utils import get_logger, get_tags, callback_check_account
from typing_extensions import Annotated

logger = get_logger('DYNAMODB')


def callback(profile: str = None, region: str = 'eu-west-1', skip_account_check: bool = False):
    """
    Clean DYNAMODB resources
    """
    callback_check_account(profile=profile, region=region, skip_account_check=skip_account_check)


dynamodb_command = Typer(callback=callback)


@dynamodb_command.command()
def remove_table_by_name(name: str):
    """
    Empty and delete dynamodb table
    """
    table = TableFactory().create_by_name(name=name)
    table.remove()


@dynamodb_command.command()
def remove_table_by_file_list(file_path: str):
    """
    Empty and delete dynamodb tables in file list
    """
    logger.info(f"Taking DYNAMODB tables tables from file")
    tables = TableFactory().create_by_list_file(file_path=file_path)
    for table in tables:
        table.remove()


@dynamodb_command.command()
def remove_table_by_tags(tags: Annotated[str, Argument(help="You can provide JSON tag list or use GUI for choose "
                                                             "selection tags.")] = None):
    """
    Find dynamodb tables by tags, and for each dynamodb empty and delete it.
    """
    tags = get_tags(tags)
    logger.info(f"Search DYNAMODB tables by tags: \n{tags}")
    tables = TableFactory().create_by_tags(tags=tags)
    logger.info(f"Found {len(tables)} Tables")
    for t in tables:
        t.remove()


@dynamodb_command.command()
def clean_table_by_name(name: str):
    """
    Clean dynamodb tables by name
    """
    table = TableFactory().create_by_name(name=name)
    table.clean()


@dynamodb_command.command()
def clean_table_by_tags(tags: Annotated[str, Argument(help="You can provide JSON tag list or use GUI for choose "
                                                             "selection tags.")] = None):
    """
    Clean dynamodb tables select by tags
    """
    tags = get_tags(tags)
    logger.info(f"Search DYNAMODB tables by tags: \n{tags}")
    tables = TableFactory().create_by_tags(tags=tags)
    logger.info(f"Found {len(tables)} Buckets")
    for t in tables:
        t.clean()


@dynamodb_command.command()
def clean_table_by_file_list(file_path: str):
    """
    Clean dynamodb tables select by file list
    """
    logger.info(f"Taking DYNAMODB tables from file")
    tables = TableFactory().create_by_list_file(file_path=file_path)
    for t in tables:
        t.clean()
