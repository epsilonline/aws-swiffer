from typer import Typer
from aws_swiffer.factory.codepipeline import CodepipelineFactory
from aws_swiffer.utils import get_logger, get_tags

logger = get_logger('CODEPIPELINE')
codepipeline_command = Typer()


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
