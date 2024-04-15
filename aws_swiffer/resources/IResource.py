import abc
import os


class IResource(abc.ABC):
    def __init__(self, arn: str, name: str, tags: list = None, region: str = None):
        if not arn and not name:
            raise Exception("Resource name or ARN is required")
        self.arn = arn
        self.name = name if name else arn.split('/')[-1]
        self.tags = tags
        self.region = os.getenv('AWS_REGION', region) or arn.split(':')[3]

    def __str__(self):
        return f'{self.arn}'

    def remove(self):
        raise NotImplementedError

