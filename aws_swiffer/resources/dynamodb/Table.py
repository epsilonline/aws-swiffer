import os

import botocore.exceptions
import botocore.errorfactory
from aws_swiffer.resources.IResource import IResource
from aws_swiffer.utils import get_client, get_resource
from aws_swiffer.utils import get_logger

logger = get_logger(os.path.basename(__file__))


class Table(IResource):

    def __init__(self, arn: str, name: str = None, tags: list = None, region: str = None):
        # arn:aws:dynamodb:eu-west-1:389003593287:table/aes-demo-dynamo-db
        if not name:
            name = arn.split('/')[-1]
        super().__init__(arn, name, tags, region)

    def remove(self):
        client = get_client('dynamodb', self.region)
        logger.info(f"Trying to delete resource: {self.arn}")
        try:
            response = client.delete_table(
                TableName=self.name,
            )
            logger.debug(response)
            logger.info(f"Resource deleted: {self.arn}")
        except botocore.exceptions.ClientError as e:
            logger.error(f"Cannot delete resource: {self.arn}")
            logger.debug(e)

    def clean(self):

        """Deletes all items from a DynamoDB table."""
        dynamodb = get_resource("dynamodb")
        table = dynamodb.Table(self.name)

        logger.info(f"Trying to delete resource: {self.arn}")

        # Scan the table to get all items
        response = table.scan()
        items = response.get("Items", [])

        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={k['AttributeName']: item[k['AttributeName']] for k in table.key_schema})

        print(f"Deleted {len(items)} items from {self.name}.")

        # Example usage:
        # clean_dynamodb_table("your_table_name")
