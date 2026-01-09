"""Application state management for the desktop GUI."""

from enum import Enum
from typing import Optional


class AppState(Enum):
    """Application state enumeration."""

    IDLE = "idle"                    # No file loaded, ready to start
    LOADING = "loading"              # File being loaded/validated
    READY = "ready"                  # File loaded, ready to process
    PROCESSING = "processing"        # Currently processing URLs
    PAUSED = "paused"                # Processing paused
    COMPLETED = "completed"          # Processing completed successfully
    ERROR = "error"                  # Error occurred


class StateManager:
    """Manages application state transitions and validation."""

    def __init__(self):
        self._current_state = AppState.IDLE
        self._callbacks = []

    @property
    def current(self) -> AppState:
        """Get current application state."""
        return self._current_state

    def set_state(self, new_state: AppState, message: Optional[str] = None):
        """
        Set new application state and notify callbacks.

        Args:
            new_state: The new state to transition to
            message: Optional message describing the state change
        """
        if not self._is_valid_transition(self._current_state, new_state):
            raise ValueError(
                f"Invalid state transition: {self._current_state.value} -> {new_state.value}"
            )

        old_state = self._current_state
        self._current_state = new_state

        # Notify all registered callbacks
        for callback in self._callbacks:
            callback(old_state, new_state, message)

    def register_callback(self, callback):
        """
        Register a callback to be notified of state changes.

        Args:
            callback: Function with signature (old_state, new_state, message)
        """
        self._callbacks.append(callback)

    def _is_valid_transition(self, from_state: AppState, to_state: AppState) -> bool:
        """
        Validate state transition.

        Args:
            from_state: Current state
            to_state: Desired new state

        Returns:
            True if transition is valid
        """
        # Define valid state transitions
        valid_transitions = {
            AppState.IDLE: {AppState.LOADING, AppState.ERROR},
            AppState.LOADING: {AppState.READY, AppState.ERROR, AppState.IDLE},
            AppState.READY: {AppState.PROCESSING, AppState.IDLE, AppState.ERROR},
            AppState.PROCESSING: {AppState.PAUSED, AppState.COMPLETED, AppState.ERROR, AppState.IDLE},
            AppState.PAUSED: {AppState.PROCESSING, AppState.IDLE, AppState.ERROR},
            AppState.COMPLETED: {AppState.IDLE, AppState.READY},
            AppState.ERROR: {AppState.IDLE},
        }

        return to_state in valid_transitions.get(from_state, set())

    def can_start_processing(self) -> bool:
        """Check if processing can be started."""
        return self._current_state == AppState.READY

    def can_pause_processing(self) -> bool:
        """Check if processing can be paused."""
        return self._current_state == AppState.PROCESSING

    def can_resume_processing(self) -> bool:
        """Check if processing can be resumed."""
        return self._current_state == AppState.PAUSED

    def can_stop_processing(self) -> bool:
        """Check if processing can be stopped."""
        return self._current_state in {AppState.PROCESSING, AppState.PAUSED}

    def is_processing(self) -> bool:
        """Check if currently processing."""
        return self._current_state in {AppState.PROCESSING, AppState.PAUSED}
