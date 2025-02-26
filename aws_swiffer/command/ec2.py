from typer import Typer
from aws_swiffer.factory.ec2 import InstanceFactory

ec2_command = Typer()


@ec2_command.command()
def remove_instance_by_id(resource_id: str):
    instance = InstanceFactory().create_by_id(resource_id)
    instance.remove()
