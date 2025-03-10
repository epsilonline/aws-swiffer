from typer import Typer
from aws_swiffer.factory.codebuild import ProjectFactory
from aws_swiffer.utils import get_logger, get_tags, callback_check_account

logger = get_logger('CODEBUILD')


def callback(profile: str = None, region: str = 'eu-west-1', skip_account_check: bool = False):
    """
    Clean CODEBUILD resources
    """
    callback_check_account(profile=profile, region=region, skip_account_check=skip_account_check)


codebuild_command = Typer(callback=callback)


@codebuild_command.command()
def remove_codebuild_projects_by_tags(tags: str = None):
    tags = get_tags(tags)
    logger.info(f"Search Codebuild projects by tags: \n{tags}")
    codepipeline_pipelines = ProjectFactory().create_by_tags(tags=tags)
    logger.info(f"Found {len(codepipeline_pipelines)} Codebuild projects")
    for e in codepipeline_pipelines:
        e.remove()


@codebuild_command.command()
def remove_codebuild_project_by_name(name: str):
    codepipeline_pipeline = ProjectFactory().create_by_name(name=name)
    codepipeline_pipeline.remove()
