from typer import Typer
from aws_swiffer.factory.iam import GroupFactory, UserFactory, PolicyFactory
from aws_swiffer.utils import get_logger, get_tags

logger = get_logger('IAM')
iam_command = Typer()


@iam_command.command()
def remove_iam_group_by_name(name: str):
    group = GroupFactory().create_by_name(name=name)
    group.remove()


@iam_command.command()
def remove_iam_user_by_name(name: str):
    user = UserFactory().create_by_name(name=name)
    user.remove()


@iam_command.command()
def remove_iam_policy_by_name(name: str):
    policy = PolicyFactory().create_by_name(name=name)
    policy.remove()


@iam_command.command()
def remove_iam_policy_by_tags(tags: str = None):

    tags = get_tags(tags)

    logger.info(f"Search IAM policies by tags: \n{tags}")
    policies = PolicyFactory().create_by_tags(tags=tags)
    logger.info(f"Found {len(policies)} policies")
    for s in policies:
        s.remove()
