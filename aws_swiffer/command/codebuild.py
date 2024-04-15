from aws_swiffer.factory.codebuild import ProjectFactory
from aws_swiffer.utils import get_logger, get_tags

logger = get_logger('CODEBUILD')


def remove_codebuild_projects_by_tags(tags: str = None):
    tags = get_tags(tags)
    logger.info(f"Search Codebuild projects by tags: \n{tags}")
    codepipeline_pipelines = ProjectFactory().create_by_tags(tags=tags)
    logger.info(f"Found {len(codepipeline_pipelines)} Codebuild projects")
    for e in codepipeline_pipelines:
        e.remove()


def remove_codebuild_project_by_name(name: str):
    codepipeline_pipeline = ProjectFactory().create_by_name(name=name)
    codepipeline_pipeline.remove()
