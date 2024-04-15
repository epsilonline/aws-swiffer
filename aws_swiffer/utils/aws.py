import boto3
from botocore.config import Config

import os

clients = {}
resources = {}


def get_client(service_name: str, region: str = None):
    if not region:
        region = os.getenv('AWS_REGION', 'eu-west-1')

    my_config = Config(region_name=region)
    key = service_name + '_' + region

    if service_name not in clients:
        clients[key] = boto3.client(service_name, config=my_config)

    return clients[key]


def get_resource(service_name: str, region: str = None):
    if not region:
        region = os.getenv('AWS_REGION', 'eu-west-1')

    my_config = Config(region_name=region)
    key = service_name + '_' + region

    if key not in resources:
        resources[key] = boto3.resource(service_name, config=my_config)

    return resources[key]


def get_account_info(region: str = None):
    sts = get_client('sts', region=region)
    iam = get_client('iam', region=region)
    caller_identity = sts.get_caller_identity()
    caller_identity['region'] = sts.meta.region_name
    caller_identity['AccountAliases'] = iam.list_account_aliases().get('AccountAliases')
    return caller_identity


def get_base_arn(service_name: str, region: str = None, with_region: bool = True, with_account_id: bool = True):
    account_id = ''
    if with_region or with_account_id:
        caller_identity = get_account_info()
        account_id = caller_identity.get('Account', '')
        region = caller_identity.get('region', None) if with_region else ''

    return f'arn:aws:{service_name}:{region}:{account_id}:'
