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
        """
        Remove resource
        :return:
        """
        raise NotImplementedError

    def clean(self):
        """
        Remove al relations between resources and other things that avoid deletions, such as object in s3 bucket
        :return:
        """
        raise NotImplementedError
