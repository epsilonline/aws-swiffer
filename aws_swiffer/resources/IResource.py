import abc
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aws_swiffer.utils.context import ExecutionContext


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

    def remove(self, context: 'ExecutionContext' = None):
        """
        Remove resource.
        
        Args:
            context: Optional ExecutionContext for dry-run and auto-approve modes
        """
        raise NotImplementedError

    def clean(self, context: 'ExecutionContext' = None):
        """
        Remove all relations between resources and other things that avoid deletions,
        such as objects in s3 bucket.
        
        Args:
            context: Optional ExecutionContext for dry-run and auto-approve modes
        """
        raise NotImplementedError
    
    def _should_proceed(self, context: 'ExecutionContext', operation_description: str) -> bool:
        """
        Check if operation should proceed based on context and user confirmation.
        
        Args:
            context: ExecutionContext with dry_run and auto_approve settings
            operation_description: Description of the operation for confirmation prompt
            
        Returns:
            True if operation should proceed, False otherwise
        """
        from aws_swiffer.utils import ask_delete_confirm, get_logger
        
        logger = get_logger(self.__class__.__name__)
        
        if context:
            prefix = context.log_prefix()
            
            if context.dry_run:
                logger.info(f"{prefix}Would {operation_description}: {self.name}")
                return False
            
            if context.auto_approve:
                logger.info(f"{prefix}Auto-approving {operation_description}: {self.name}")
                return True
        
        # Interactive confirmation
        return ask_delete_confirm(self.name, context)
