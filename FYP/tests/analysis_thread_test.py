import pytest
import logging
from unittest.mock import MagicMock
from core.analysis_thread import QtLogHandler


def test_qtloghandler_emits_formatted_message():
    signal = MagicMock()
    handler = QtLogHandler(signal)
    
    logger = logging.getLogger("test_logger")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    logger.info("test message")
    
    assert signal.emit.called
    emitted = signal.emit.call_args[0][0]
    assert "test message" in emitted
    assert "INFO" in emitted
    logger.removeHandler(handler)


def test_qtloghandler_includes_logger_name():
    signal = MagicMock()
    handler = QtLogHandler(signal)
    record = logging.LogRecord(
        name="my.module",
        level=logging.WARNING,
        pathname="",
        lineno=0,
        msg="something happened",
        args=(),
        exc_info=None
    )
    handler.emit(record)
    emitted = signal.emit.call_args[0][0]
    assert "my.module" in emitted
    assert "something happened" in emitted