from typer import Typer
from aws_swiffer.factory.codepipeline import CodepipelineFactory
from aws_swiffer.utils import get_logger, get_tags, callback_check_account

logger = get_logger('CODEPIPELINE')


def callback(profile: str = None, region: str = 'eu-west-1', skip_account_check: bool = False):
    """
    Clean CODEPIPELINE resources
    """
    callback_check_account(profile=profile, region=region, skip_account_check=skip_account_check)


codepipeline_command = Typer(callback=callback)


@codepipeline_command.command()
def remove_codepipeline_by_tags(tags: str = None):
    tags = get_tags(tags)
    logger.info(f"Search Codepipeline pipeline by tags: \n{tags}")
    codepipeline_pipelines = CodepipelineFactory().create_by_tags(tags=tags)
    logger.info(f"Found {len(codepipeline_pipelines)} Codepipeline pipelines")
    for e in codepipeline_pipelines:
        e.remove()


@codepipeline_command.command()
def remove_codepipeline_by_name(name: str):
    codepipeline_pipeline = CodepipelineFactory().create_by_name(name=name)
    codepipeline_pipeline.remove()
