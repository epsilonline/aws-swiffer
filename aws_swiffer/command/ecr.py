from typer import Typer
from aws_swiffer.factory.ecr import EcrFactory
from aws_swiffer.utils import get_logger, get_tags

logger = get_logger('ECR')
ecr_command = Typer()


@ecr_command.command()
def remove_ecr_by_tags(tags: str = None):
    tags = get_tags(tags)
    logger.info(f"Search ECR repositories by tags: \n{tags}")
    ecr_repositories = EcrFactory().create_by_tags(tags=tags)
    logger.info(f"Found {len(ecr_repositories)} ECR repositories")
    for e in ecr_repositories:
        e.remove()


@ecr_command.command()
def remove_ecr_by_name(name: str):
    ecr = EcrFactory().create_by_name(name=name)
    ecr.remove()
