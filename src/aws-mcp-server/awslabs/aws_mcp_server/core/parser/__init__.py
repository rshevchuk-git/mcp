"""Parser functionality for AWS CLI commands."""

from .classifier import classify_operation
from .interpretation import interpret

__all__ = ['classify_operation', 'interpret']
