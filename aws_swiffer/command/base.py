from abc import ABC
from typing import Type, Optional
import os

from aws_swiffer.factory.IFactory import IFactory
from aws_swiffer.resources.IResource import IResource
from aws_swiffer.utils import get_logger, ExecutionContext


class BaseCommand(ABC):
    """
    Base class for AWS service commands providing standardized operations.
    
    Attributes:
        factory: Factory instance for creating resources
        context: ExecutionContext for operation configuration
        logger: Logger instance for the command
    """
    
    def __init__(self, factory: Type[IFactory], logger_name: str = None):
        """
        Initialize BaseCommand with a factory.
        
        Args:
            factory: Factory class instance for creating resources
            logger_name: Optional name for logger (defaults to class name)
        """
        self.factory = factory
        self.context: Optional[ExecutionContext] = None
        self.logger = get_logger(logger_name or self.__class__.__name__)
    
    def setup_context(self, dry_run: bool = False, auto_approve: bool = False, 
                     region: str = None, profile: str = None) -> None:
        """
        Initialize ExecutionContext from CLI flags or environment.
        
        Args:
            dry_run: Enable dry-run mode
            auto_approve: Enable auto-approve mode
            region: AWS region
            profile: AWS profile
        """
        # Prefer explicit parameters, fall back to environment
        self.context = ExecutionContext(
            dry_run=dry_run or os.getenv('DRY_RUN', 'false').lower() == 'true',
            auto_approve=auto_approve or os.getenv('AUTO_APPROVE', 'false').lower() == 'true',
            region=region or os.getenv('AWS_REGION'),
            profile=profile or os.getenv('AWS_PROFILE')
        )
    
    def remove_by_name(self, name: str) -> None:
        """
        Remove a resource by name.
        
        Args:
            name: Resource name
        """
        resource = self.factory.create_by_name(name)
        self._execute_removal(resource)
    
    def remove_by_id(self, resource_id: str) -> None:
        """
        Remove a resource by ID.
        
        Args:
            resource_id: Resource identifier
        """
        resource = self.factory.create_by_id(resource_id)
        self._execute_removal(resource)
    
    def remove_by_tags(self, tags: dict) -> None:
        """
        Remove resources matching tags.
        
        Args:
            tags: Dictionary of tags to match
        """
        self.logger.info(f"Search resources by tags: {tags}")
        resources = self.factory.create_by_tags(tags)
        self.logger.info(f"Found {len(resources)} resources")
        self._execute_batch_removal(resources)
    
    def remove_by_file_list(self, file_path: str) -> None:
        """
        Remove resources listed in a file.
        
        Args:
            file_path: Path to file containing resource identifiers
        """
        self.logger.info(f"Loading resources from file: {file_path}")
        resources = self.factory.create_by_list_file(file_path)
        self.logger.info(f"Found {len(resources)} resources in file")
        self._execute_batch_removal(resources)
    
    def _execute_removal(self, resource: IResource) -> None:
        """
        Execute removal of a single resource with context-aware logging.
        
        Args:
            resource: Resource to remove
        """
        prefix = self.context.log_prefix() if self.context else ""
        self.logger.info(f"{prefix}Processing resource: {resource.arn}")
        
        try:
            resource.remove(context=self.context)
        except Exception as e:
            self.logger.error(f"Failed to remove resource {resource.arn}: {e}")
            raise
    
    def _execute_batch_removal(self, resources: list[Type[IResource]]) -> None:
        """
        Execute removal of multiple resources with error handling and summary.
        
        Args:
            resources: List of resources to remove
        """
        if not resources:
            self.logger.info("No resources to process")
            return
        
        prefix = self.context.log_prefix() if self.context else ""
        success_count = 0
        failure_count = 0
        
        for resource in resources:
            try:
                self.logger.info(f"{prefix}Processing resource: {resource.arn}")
                resource.remove(context=self.context)
                success_count += 1
            except Exception as e:
                self.logger.error(f"Failed to remove resource {resource.arn}: {e}")
                failure_count += 1
                # Continue processing remaining resources
        
        # Summary logging
        self.logger.info(f"{prefix}Batch operation complete: {success_count} succeeded, {failure_count} failed")
