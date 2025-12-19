"""GUI service layer"""

from .job_manager import JobManager

__all__ = ['JobManager']

# Global job manager instance
job_manager = JobManager()
