"""
Mock implementation of OpenTelemetry modules for testing.
This allows tests to run without requiring the actual OpenTelemetry dependencies.
"""
from unittest.mock import MagicMock

# Create mock classes and functions
class MockTrace:
    def __init__(self):
        self.get_tracer = MagicMock(return_value=MagicMock())
        self.set_tracer_provider = MagicMock()

class MockMetrics:
    def __init__(self):
        self.get_meter_provider = MagicMock(return_value=MagicMock())
        self.set_meter_provider = MagicMock()

# Create mock modules
trace = MockTrace()
metrics = MockMetrics()

# Mock classes
class Resource:
    @staticmethod
    def create(attributes):
        return MagicMock()

class TracerProvider:
    def __init__(self, resource=None):
        self.resource = resource
        self.add_span_processor = MagicMock()
        self.force_flush = MagicMock()

class BatchSpanProcessor:
    def __init__(self, exporter):
        self.exporter = exporter

class OTLPSpanExporter:
    def __init__(self, endpoint=None, insecure=True):
        self.endpoint = endpoint
        self.insecure = insecure

class MeterProvider:
    def __init__(self, resource=None, metric_readers=None):
        self.resource = resource
        self.metric_readers = metric_readers or []
        self.force_flush = MagicMock()

class PeriodicExportingMetricReader:
    def __init__(self, exporter, export_interval_millis=60000):
        self.exporter = exporter
        self.export_interval_millis = export_interval_millis

class OTLPMetricExporter:
    def __init__(self, endpoint=None, insecure=True):
        self.endpoint = endpoint
        self.insecure = insecure

# Create mock semantic conventions
class SemanticConventions:
    pass
