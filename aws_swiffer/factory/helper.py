from aws_swiffer.utils import get_client
from aws_swiffer.resources import IResource
from typing import Union, Type


def get_resources_by_tags(tags, resource_type_filters: Union[str, list[str]],
                          resource_class: Type[IResource]):
    client = get_client('resourcegroupstaggingapi')
    paginator = client.get_paginator('get_resources')

    resources = []

    tag_filters = []

    if type(resource_type_filters) is str:
        resource_type_filters = [resource_type_filters]
    elif type(resource_type_filters) is list:
        resource_type_filters = resource_type_filters
    else:
        raise ValueError('Invalid resource type')

    for k, v in tags.items():
        if type(v) is str:
            tag_filters.append({'Key': k, 'Values': [v]})
        elif type(v) is list:
            tag_filters.append({'Key': k, 'Values': v})
        else:
            raise ValueError('Invalid tag value')

    response_iterator = paginator.paginate(TagFilters=tag_filters, ResourceTypeFilters=resource_type_filters)

    for page in response_iterator:
        resource_tag_mapping_list = page['ResourceTagMappingList']
        for resource in resource_tag_mapping_list:
            r = resource_class(name='', arn=resource['ResourceARN'], tags=resource['Tags'])
            resources.append(r)
    return resources

