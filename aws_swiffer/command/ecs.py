from typer import Typer
from aws_swiffer.factory.ecs import TaskDefinitionFactory, ServiceFactory, ClusterFactory
from aws_swiffer.utils import get_logger, get_tags

logger = get_logger('ECS')
ecs_command = Typer()


@ecs_command.command()
def remove_task_definitions_by_tags(tags: str = None):
    tags = get_tags(tags)

    logger.info(f"Search task definitions by tags: \n{tags}")
    task_definitions = TaskDefinitionFactory().create_by_tags(tags=tags)
    logger.info(f"Found {len(task_definitions)} task definitions")
    for td in task_definitions:
        td.remove()


@ecs_command.command()
def remove_service_by_tags(tags: str = None):
    tags = get_tags(tags)

    logger.info(f"Search ECS services by tags: \n{tags}")
    ecs_services = ServiceFactory().create_by_tags(tags=tags)
    logger.info(f"Found {len(ecs_services)} services")
    for s in ecs_services:
        s.remove()


@ecs_command.command()
def remove_service_by_arn(arn: str):
    service = ServiceFactory().create_by_arn(arn=arn)
    service.remove()


@ecs_command.command()
def remove_service_by_arns(arn: str):
    arn = arn.split(' ')
    print(arn)
    for arn in arn:
        service = ServiceFactory().create_by_arn(arn=arn)
        service.remove()


@ecs_command.command()
def remove_ecs_cluster_by_tags(tags: str = None):
    tags = get_tags(tags)
    logger.info(f"Search ECS Clusters by tags: \n{tags}")
    ecs_clusters = ClusterFactory().create_by_tags(tags=tags)
    logger.info(f"Found {len(ecs_clusters)} clusters")
    for s in ecs_clusters:
        s.remove()
