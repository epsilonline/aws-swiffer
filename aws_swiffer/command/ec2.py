from aws_swiffer.factory.ec2 import InstanceFactory


def remove_instance_by_id(resource_id: str):
    instance = InstanceFactory().create_by_id(resource_id)
    instance.remove()
