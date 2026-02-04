"""Base VPC Resource class for AWS Swiffer VPC resources."""

import os
from typing import TYPE_CHECKING, List, Optional
from abc import abstractmethod

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.utils import get_logger

if TYPE_CHECKING:
    from aws_swiffer.utils.context import ExecutionContext

logger = get_logger(os.path.basename(__file__))


class VPCResource(IResource):
    """
    Base class for VPC-related resources.
    
    This class extends IResource to provide VPC-specific functionality including
    dependency tracking, default resource protection, and VPC-scoped operations.
    """
    
    def __init__(self, arn: str, name: str, vpc_id: str, resource_type: str, 
                 tags: list = None, region: str = None):
        """
        Initialize VPC resource.
        
        Args:
            arn: AWS Resource Name
            name: Resource name
            vpc_id: VPC ID this resource belongs to
            resource_type: Type of VPC resource (subnet, security-group, etc.)
            tags: Resource tags
            region: AWS region
        """
        super().__init__(arn=arn, name=name, tags=tags, region=region)
        self.vpc_id = vpc_id
        self.resource_type = resource_type
        self.dependencies: List['VPCResource'] = []
        self.dependents: List['VPCResource'] = []
    
    def is_default_resource(self) -> bool:
        """
        Check if this is a default AWS resource that shouldn't be deleted.
        
        Default resources include:
        - Default VPC
        - Default security groups
        - Main route tables
        - Default network ACLs
        
        Returns:
            True if this is a default resource, False otherwise
        """
        # Base implementation - subclasses should override for specific logic
        return False
    
    def get_dependencies(self) -> List['VPCResource']:
        """
        Get resources this resource depends on.
        
        Returns:
            List of VPC resources this resource depends on
        """
        return self.dependencies.copy()
    
    def add_dependency(self, dependency: 'VPCResource') -> None:
        """
        Add a dependency relationship.
        
        Args:
            dependency: Resource this resource depends on
        """
        if dependency not in self.dependencies:
            self.dependencies.append(dependency)
            if self not in dependency.dependents:
                dependency.dependents.append(self)
    
    def can_delete(self) -> bool:
        """
        Check if resource can be safely deleted.
        
        Returns:
            True if resource can be deleted, False otherwise
        """
        if self.is_default_resource():
            logger.warning(f"Cannot delete default resource: {self.arn}")
            return False
        
        # Check if any dependencies still exist
        for dependency in self.dependencies:
            if dependency.exists():
                logger.debug(f"Cannot delete {self.arn} - dependency exists: {dependency.arn}")
                return False
        
        return True
    
    def exists(self) -> bool:
        """
        Check if the resource still exists in AWS.
        
        Returns:
            True if resource exists, False otherwise
        """
        # Base implementation - subclasses should override
        return True
    
    @abstractmethod
    def remove(self, context: 'ExecutionContext' = None) -> None:
        """
        Remove the VPC resource.
        
        Args:
            context: ExecutionContext for dry-run and auto-approve modes
        """
        raise NotImplementedError("Subclasses must implement remove method")
    
    def __str__(self) -> str:
        """String representation of the VPC resource."""
        return f"{self.resource_type}:{self.name}({self.arn})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the VPC resource."""
        return (f"VPCResource(type={self.resource_type}, name={self.name}, "
                f"vpc_id={self.vpc_id}, arn={self.arn})")