from typer import Typer
from aws_swiffer.factory.ec2 import InstanceFactory
from aws_swiffer.utils import callback_check_account


def callback(profile: str = None, region: str = 'eu-west-1', skip_account_check: bool = False):
    """
    Clean EC2 resources
    """
    callback_check_account(profile=profile, region=region, skip_account_check=skip_account_check)


ec2_command = Typer(callback=callback)


@ec2_command.command()
def remove_instance_by_id(resource_id: str):
    instance = InstanceFactory().create_by_id(resource_id)
    instance.remove()
