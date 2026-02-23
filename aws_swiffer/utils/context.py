import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionContext:
    """
    Execution context for AWS Swiffer operations.
    
    Attributes:
        dry_run: If True, simulate operations without making actual AWS API calls
        auto_approve: If True, skip confirmation prompts for destructive operations
        region: AWS region for operations
        profile: AWS profile to use for authentication
    """
    dry_run: bool = False
    auto_approve: bool = False
    region: Optional[str] = None
    profile: Optional[str] = None
    context: 'ExecutionContext' = None
    
    @classmethod
    def get_context(self) -> 'ExecutionContext':
        if self.context:
            return self.context
        else:
            context = self.from_environment()
            self.context = context
            return context

    def log_prefix(self) -> str:
        """
        Returns appropriate log prefix based on execution mode.
        
        Returns:
            String prefix to prepend to log messages
        """
        if self.dry_run:
            return "[DRY-RUN] "
        elif self.auto_approve:
            return "[AUTO-APPROVE] "
        return ""
    
    @classmethod
    def from_environment(cls) -> 'ExecutionContext':
        """
        Create ExecutionContext from environment variables.
        
        Returns:
            ExecutionContext instance populated from environment
        """
        return cls(
            dry_run=os.getenv('DRY_RUN', 'false').lower() == 'true',
            auto_approve=os.getenv('AUTO_APPROVE', 'false').lower() == 'true',
            region=os.getenv('AWS_REGION'),
            profile=os.getenv('AWS_PROFILE')
        )
    