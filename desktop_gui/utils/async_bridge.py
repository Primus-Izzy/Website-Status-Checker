"""Async/sync bridge utilities for running async code from tkinter."""

import asyncio
import threading
from typing import Callable, Any, Optional


def run_async_in_thread(
    coro_func: Callable,
    *args,
    callback: Optional[Callable[[Any], None]] = None,
    error_callback: Optional[Callable[[Exception], None]] = None,
    **kwargs
):
    """
    Run an async function in a background thread.

    Args:
        coro_func: Async function to run
        *args: Positional arguments for the function
        callback: Optional callback to call with the result
        error_callback: Optional callback to call with exceptions
        **kwargs: Keyword arguments for the function

    Returns:
        The thread object
    """

    def run_in_thread():
        """Run the async function in this thread's event loop."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Run the coroutine
            result = loop.run_until_complete(coro_func(*args, **kwargs))

            # Call success callback if provided
            if callback:
                callback(result)

        except Exception as e:
            # Call error callback if provided
            if error_callback:
                error_callback(e)
            else:
                print(f"Error in async thread: {e}")

        finally:
            # Clean up the loop
            loop.close()

    # Create and start the thread
    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()

    return thread


class AsyncRunner:
    """Helper class for running async code with more control."""

    def __init__(self):
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        """Start the event loop in a background thread."""
        if self._running:
            return

        def run_loop():
            """Run event loop in this thread."""
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self._running = True

            try:
                self.loop.run_forever()
            finally:
                self.loop.close()
                self._running = False

        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()

    def run_coro(
        self,
        coro,
        callback: Optional[Callable[[Any], None]] = None,
        error_callback: Optional[Callable[[Exception], None]] = None
    ):
        """
        Schedule a coroutine on the event loop.

        Args:
            coro: Coroutine to run
            callback: Optional callback for result
            error_callback: Optional callback for exceptions
        """
        if not self._running or not self.loop:
            raise RuntimeError("AsyncRunner not started")

        def done_callback(future):
            """Handle completed future."""
            try:
                result = future.result()
                if callback:
                    callback(result)
            except Exception as e:
                if error_callback:
                    error_callback(e)
                else:
                    print(f"Error in coroutine: {e}")

        # Schedule coroutine on the loop
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        future.add_done_callback(done_callback)

        return future

    def stop(self):
        """Stop the event loop."""
        if self.loop and self._running:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self._running = False

    def is_running(self) -> bool:
        """Check if the event loop is running."""
        return self._running
