#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

This file is part of the Instana Plugins collection.
"""
from common.logging_config import setup_logging

setup_logging()  # Configure logging at the start of the module
import os
import json
import logging
import re
from typing import Dict, Any, Optional, List
import socket
import sys

# Custom implementation of strtobool to replace distutils.util.strtobool
def strtobool(val):
    """Convert a string representation of truth to True or False.
    
    True values are 'y', 'yes', 't', 'true', 'on', and '1';
    False values are 'n', 'no', 'f', 'false', 'off', and '0'.
    Raises ValueError if 'val' is anything else.
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise ValueError(f"Invalid truth value: {val}")

# Configure logging
logger = logging.getLogger(__name__)

# Import metadata store - this is required
try:
    from common.metadata_store import MetadataStore
except ImportError as e:
    logger.error("MetadataStore module not found. This is a required component.")
    logger.error(f"Error: {e}")
    logger.error("Please ensure common/metadata_store.py exists and is importable.")
    sys.exit(1)

# OpenTelemetry imports
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.metrics import set_meter_provider, get_meter_provider, Observation
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    logger.error("OpenTelemetry packages not found. Please install required dependencies.")
    logger.error("Run: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp")
    OPENTELEMETRY_AVAILABLE = False

class InstanaOTelConnector:
    """
    OpenTelemetry connector for Instana.
    
    This class provides functionality to send metrics and traces to Instana
    using the OpenTelemetry protocol with proper metric formatting.
    """
    
    def __init__(
        self,
        service_name: str,
        agent_host: str = None,
        agent_port: int = None,
        resource_attributes: Optional[Dict[str, str]] = None,
        use_tls: bool = None,
        ca_cert_path: Optional[str] = None,
        client_cert_path: Optional[str] = None,
        client_key_path: Optional[str] = None,
        metadata_db_path: Optional[str] = None,
        service_namespace: str = "Unknown"
    ):
        """
        Initialize the Instana OpenTelemetry connector.
        
        Args:
            service_name: Name of the service being monitored
            agent_host: Hostname of the Instana agent (default: localhost)
            agent_port: Port of the Instana agent's OTLP receiver (default: 4317)
            resource_attributes: Additional resource attributes to include
            use_tls: Whether to use TLS encryption for the connection (default: False)
            ca_cert_path: Path to CA certificate file for TLS verification (optional)
            client_cert_path: Path to client certificate file for TLS authentication (optional)
            client_key_path: Path to client key file for TLS authentication (optional)
        """
        # Add a metrics state dictionary to store current metric values
        self._metrics_state = {}
        
        # Add a registry to track registered metrics
        self._metrics_registry = set()
        
        # Initialize metadata store - this is required
        try:
            self._metadata_store = MetadataStore(db_path=metadata_db_path)
            logger.info(f"Initialized metadata store at: {self._metadata_store.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize metadata store: {e}")
            logger.error("A working metadata store is required for proper operation.")
            raise RuntimeError(f"Failed to initialize metadata store: {e}")
        # Get configuration from environment variables or use provided values
        self.service_name = service_name
        self.agent_host = agent_host or os.environ.get('INSTANA_AGENT_HOST', 'localhost')
        
        # Parse port from environment or use default
        try:
            self.agent_port = int(os.environ.get('INSTANA_AGENT_PORT', agent_port or 4317))
        except (ValueError, TypeError):
            self.agent_port = 4317
            logger.warning(f"Invalid port specified, using default: {self.agent_port}")
        
        # Parse TLS settings from environment or use provided values
        try:
            env_use_tls = os.environ.get('USE_TLS')
            self.use_tls = bool(strtobool(env_use_tls)) if env_use_tls is not None else (use_tls or False)
        except (ValueError, AttributeError):
            self.use_tls = use_tls or False
            logger.warning(f"Invalid USE_TLS value, using: {self.use_tls}")
        
        # Get certificate paths from environment or use provided values
        self.ca_cert_path = os.environ.get('CA_CERT_PATH', ca_cert_path)
        self.client_cert_path = os.environ.get('CLIENT_CERT_PATH', client_cert_path)
        self.client_key_path = os.environ.get('CLIENT_KEY_PATH', client_key_path)
        
        # Log TLS configuration
        if self.use_tls:
            logger.info(f"TLS encryption enabled for OpenTelemetry connection to {self.agent_host}:{self.agent_port}")
            if self.ca_cert_path:
                logger.info(f"Using CA certificate: {self.ca_cert_path}")
            if self.client_cert_path and self.client_key_path:
                logger.info(f"Using client certificate for mutual TLS")
        
        # Get service ID and display name from metadata store
        try:
            hostname = socket.gethostname()
            self.service_id, self.display_name = self._metadata_store.get_or_create_service(
                service_name, 
                hostname=hostname, 
                service_namespace=service_namespace
            )
            
            # Get host ID from metadata store for OpenTelemetry standard compliance
            self.host_id = self._metadata_store.get_or_create_host(hostname)
            
            logger.info(f"Using service ID: {self.service_id} with display name: {self.display_name}")
            logger.info(f"Using host ID: {self.host_id} for hostname: {hostname}")
        except Exception as e:
            logger.error(f"Error getting service ID from metadata store: {e}")
            logger.error("Cannot continue without a valid service ID.")
            raise RuntimeError(f"Failed to get service ID: {e}")
        
        # Store OpenTelemetry standard resource attributes
        self.attributes = {
            "service.name": service_name,
            "service.namespace": service_namespace,
            "service.instance.id": self.service_id,  # OpenTelemetry standard attribute
            "host.id": self.host_id,                 # OpenTelemetry standard attribute  
            "host.name": hostname,
        }
        
        # Add custom resource attributes if provided
        if resource_attributes:
            self.attributes.update(resource_attributes)
        
        # Only proceed with OpenTelemetry setup if it's available
        if OPENTELEMETRY_AVAILABLE:
            self.resource = Resource.create(self.attributes)
            
            # Initialize tracer
            self._setup_tracing()
            
            # Initialize metrics
            self._setup_metrics()
            
            logger.info(f"Initialized InstanaOTelConnector for service {service_name}")
        else:
            logger.warning(f"OpenTelemetry is not available. Metrics and traces will not be sent.")
            logger.warning(f"To enable OpenTelemetry, install required packages:")
            logger.warning(f"pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp")
        
    def _setup_tracing(self):
        """Set up the OpenTelemetry tracer provider and exporter."""
        if not OPENTELEMETRY_AVAILABLE:
            logger.error("Cannot set up tracing: OpenTelemetry packages not installed")
            return
            
        try:
            # Create OTLP exporter for traces
            if self.use_tls:
                # Use HTTPS endpoint with TLS
                protocol = "https://" if self.use_tls else "http://"
                otlp_endpoint = f"{protocol}{self.agent_host}:{self.agent_port}"
                logger.debug(f"Using TLS endpoint: {otlp_endpoint}")
                
                # Configure TLS options
                tls_config = {}
                if self.ca_cert_path:
                    tls_config["ca_file"] = self.ca_cert_path
                    logger.debug(f"Using CA certificate: {self.ca_cert_path}")
                if self.client_cert_path and self.client_key_path:
                    tls_config["cert_file"] = self.client_cert_path
                    tls_config["key_file"] = self.client_key_path
                    logger.debug("Using client certificate for mutual TLS")
                
                try:
                    span_exporter = OTLPSpanExporter(
                        endpoint=otlp_endpoint,
                        insecure=False,
                        credentials=None,
                        headers=None,
                        timeout=None,
                        compression=None,
                        **tls_config
                    )
                except ConnectionError as e:
                    logger.error(f"Error setting up tracing: {e}")
                    # Create a dummy exporter for tests
                    span_exporter = MagicMock()
                    return
            else:
                # Use standard non-TLS endpoint
                otlp_endpoint = f"{self.agent_host}:{self.agent_port}"
                logger.debug(f"Using non-TLS endpoint: {otlp_endpoint}")
                try:
                    span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
                except ConnectionError as e:
                    logger.error(f"Error setting up tracing: {e}")
                    # Create a dummy exporter for tests
                    span_exporter = MagicMock()
                    return
            
            # Create and set the tracer provider
            tracer_provider = TracerProvider(resource=self.resource)
            span_processor = BatchSpanProcessor(span_exporter)
            tracer_provider.add_span_processor(span_processor)
            trace.set_tracer_provider(tracer_provider)
            
            # Store provider for cleanup
            self._tracer_provider = tracer_provider
            
            # Get a tracer
            self.tracer = trace.get_tracer(
                self.service_name,
                schema_url="https://opentelemetry.io/schemas/1.11.0"
            )
            logger.debug(f"Tracing setup completed for {self.service_name}")
        except Exception as e:
            logger.error(f"Error setting up tracing: {e}")
            # Make sure we don't propagate errors in the constructor
        
    def _setup_metrics(self):
        """Set up the OpenTelemetry meter provider and exporter."""
        if not OPENTELEMETRY_AVAILABLE:
            logger.error("Cannot set up metrics: OpenTelemetry packages not installed")
            return
            
        try:
            # Create OTLP exporter for metrics
            if self.use_tls:
                # Use HTTPS endpoint with TLS
                protocol = "https://" if self.use_tls else "http://"
                otlp_endpoint = f"{protocol}{self.agent_host}:{self.agent_port}"
                logger.debug(f"Using TLS endpoint for metrics: {otlp_endpoint}")
                
                # Configure TLS options
                tls_config = {}
                if self.ca_cert_path:
                    tls_config["ca_file"] = self.ca_cert_path
                if self.client_cert_path and self.client_key_path:
                    tls_config["cert_file"] = self.client_cert_path
                    tls_config["key_file"] = self.client_key_path
                
                metric_exporter = OTLPMetricExporter(
                    endpoint=otlp_endpoint,
                    insecure=False,
                    headers=None,
                    timeout=None,
                    compression=None,
                    **tls_config
                )
            else:
                # Use standard non-TLS endpoint
                otlp_endpoint = f"{self.agent_host}:{self.agent_port}"
                logger.debug(f"Using non-TLS endpoint for metrics: {otlp_endpoint}")
                metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
            
            # Create metric reader
            reader = PeriodicExportingMetricReader(
                metric_exporter,
                export_interval_millis=60000  # Export every 60 seconds
            )
            
            # Create and set meter provider
            meter_provider = MeterProvider(resource=self.resource, metric_readers=[reader])
            set_meter_provider(meter_provider)
            
            # Store provider for cleanup
            self._meter_provider = meter_provider
            
            # Get a meter
            self.meter = get_meter_provider().get_meter(
                self.service_name,
                schema_url="https://opentelemetry.io/schemas/1.11.0"
            )
            
            # Register the metrics callback
            self._register_observable_metrics()
            
            logger.debug(f"Metrics setup completed for {self.service_name}")
        except Exception as e:
            logger.error(f"Error setting up metrics: {e}")
            raise
            
    def _create_metric_callback(self, metric_name, is_percentage=False, is_counter=False, 
                               decimal_places=2, display_name=None):
        """Create a generator callback function for a specific metric.

        Args:
            metric_name: The name of the metric this callback will observe
            is_percentage: Whether the metric is a percentage
            is_counter: Whether the metric is a counter
            decimal_places: Number of decimal places to round to
            display_name: Optional display name for logging

        Returns:
            A generator callback function that yields Observation objects for the observable gauge
        """
        def callback(options):
            try:
                if metric_name in self._metrics_state:
                    value = self._metrics_state[metric_name]
                    
                    # Format the value if formatting parameters are provided
                    if any([is_percentage, is_counter, decimal_places != 2]):
                        value = self._metadata_store.format_metric_value(
                            value, 
                            is_percentage=is_percentage, 
                            is_counter=is_counter,
                            decimal_places=decimal_places
                        )
                    
                    # Yield an Observation object as required by OpenTelemetry API
                    yield Observation(value)
                    
                    # Use the provided display name or the metric name for logging
                    log_name = display_name or metric_name
                    logger.debug(f"Observed metric {log_name}={value}")
            except Exception as e:
                logger.error(f"Error in metric callback for {metric_name}: {e}")
        return callback
    
    def _register_observable_metrics(self):
        """Register individual observable metrics with OpenTelemetry."""
        if not hasattr(self, 'meter') or not self.meter:
            logger.error("Cannot register metrics: Meter not initialized")
            return
            
        try:
            # Define the metrics we expect to collect
            expected_metrics = [
                "cpu_usage", "memory_usage", "process_count", "disk_read_bytes", 
                "disk_write_bytes", "open_file_descriptors", "thread_count",
                "voluntary_ctx_switches", "nonvoluntary_ctx_switches"
            ]
            
            # Compute the CPU core count once and reuse it throughout the function
            cpu_core_count = os.cpu_count() or 1  # Get the number of CPU cores, fallback to 1 if None
            
            # Add CPU core metrics to expected metrics
            for i in range(cpu_core_count):  # Support up to the actual number of cores
                expected_metrics.append(f"cpu_core_{i}")
            
            # Define which metrics should be displayed as percentages
            percentage_metrics = {
                "cpu_usage": True,
                "memory_usage": True
            }
            
            # Define which metrics are counters (should be displayed as integers)
            counter_metrics = {
                "process_count": True,
                "disk_read_bytes": True,
                "disk_write_bytes": True,
                "open_file_descriptors": True,
                "thread_count": True,
                "voluntary_ctx_switches": True,
                "nonvoluntary_ctx_switches": True,
                "max_threads_per_process": True,
                "min_threads_per_process": True
            }
            
            # Add CPU core metrics to percentage metrics - reuse the same CPU count from above
            for i in range(cpu_core_count):  # Use actual CPU count instead of hardcoded value
                percentage_metrics[f"cpu_core_{i}"] = True
            
            # Add any metric-specific descriptions
            metric_descriptions = {
                "cpu_usage": "CPU usage as percentage",
                "memory_usage": "Memory usage as percentage",
                "process_count": "Number of processes",
                "disk_read_bytes": "Bytes read from disk",
                "disk_write_bytes": "Bytes written to disk",
                "open_file_descriptors": "Number of open file descriptors",
                "thread_count": "Number of threads",
                "voluntary_ctx_switches": "Number of voluntary context switches",
                "nonvoluntary_ctx_switches": "Number of non-voluntary context switches"
            }
            
            # In newer OpenTelemetry versions, we need to use callbacks differently
            for metric_name in expected_metrics:
                # Get metric ID and display name from metadata store
                is_percentage = percentage_metrics.get(metric_name, False)
                
                try:
                    # Check if this metric is a counter
                    is_counter = counter_metrics.get(metric_name, False)
                    
                    # Set decimal places to 0 for counters
                    decimal_places = 0 if is_counter else 2
                    
                    metric_id, display_name = self._metadata_store.get_or_create_metric(
                        service_id=self.service_id,
                        name=metric_name,
                        unit="%" if is_percentage else "",
                        format_type="counter" if is_counter else ("percentage" if is_percentage else "number"),
                        decimal_places=decimal_places,
                        is_percentage=is_percentage,
                        is_counter=is_counter
                    )
                    
                    # Use specific description if available, otherwise use generic
                    description = metric_descriptions.get(
                        metric_name, f"Metric for {display_name or metric_name}"
                    )
                    
                    # Create the observable gauge with the callback and proper naming
                    # Use the simple name from metadata store for better display in Instana
                    gauge = self.meter.create_observable_gauge(
                        name=self._metadata_store.get_simple_metric_name(metric_name),
                        description=description,
                        unit="%" if is_percentage else "1",
                        callbacks=[self._create_metric_callback(
                            metric_name, 
                            is_percentage, 
                            is_counter, 
                            decimal_places, 
                            display_name
                        )]
                    )
                except Exception as e:
                    logger.error(f"Error registering metric {metric_name}: {e}")
                    continue
                
                # Add to registry for tracking
                self._metrics_registry.add(metric_name)
                logger.debug(f"Registered observable metric: {metric_name}")
                
            # Also create a general callback for any metrics not in the expected list
            # This allows handling of dynamic or unexpected metrics
            def general_callback(options):
                for name, value in self._metrics_state.items():
                    if name not in expected_metrics and isinstance(value, (int, float)):
                        # Yield Observation with metric metadata for dynamic metrics
                        # The "metric_name" attribute helps identify the source in Instana
                        # This metadata structure is used by Instana to correlate metrics with their source
                        # and is required for proper identification of dynamic metrics in the Instana UI
                        yield Observation(value, {"metric_name": name})
                        logger.debug(f"Observed general metric {name}={value}")
            
            # Register a general observable gauge for unexpected metrics
            general_gauge = self.meter.create_observable_gauge(
                name=f"{self.service_name}.general_metrics",
                description=f"General metrics for {self.service_name}",
                unit="1",
                callbacks=[general_callback]
            )
            
            # Add the general gauge name to the metrics registry
            self._metrics_registry.add(f"{self.service_name}.general_metrics")
            
            logger.info(f"Registered {len(expected_metrics)} individual observable metrics for {self.service_name}")
        except Exception as e:
            logger.error(f"Error registering observable metrics: {e}")
        
    def _register_metric_if_new(self, name: str, percentage_metrics: Dict[str, bool]):
        """
        Register a metric if it's not already registered.
        
        Args:
            name: Name of the metric to register
            percentage_metrics: Dictionary mapping metric names to boolean indicating if they are percentages
        """
        if name not in self._metrics_registry and name != "monitored_pids":
            # Register the new metric for observation
            self._register_new_metric(name, percentage_metrics.get(name, False))

    def record_metrics(self, metrics: Dict[str, Any]):
        """
        Update the metrics state with new values.
        
        Args:
            metrics: Dictionary of metrics to record
        """
        if not OPENTELEMETRY_AVAILABLE:
            logger.error("Cannot record metrics: OpenTelemetry packages not installed")
            return
            
        if not metrics:
            logger.warning("No metrics to record")
            return
            
        try:
            # Define which metrics should be displayed as percentages
            percentage_metrics = {
                "cpu_usage": True,
                "memory_usage": True
            }
            
            # Add CPU core metrics to percentage metrics
            cpu_core_count = os.cpu_count() or 1  # Get the number of CPU cores, fallback to 1 if None
            for i in range(cpu_core_count):
                percentage_metrics[f"cpu_core_{i}"] = True
                
            # Update the metrics state dictionary with new values
            metrics_updated = 0
            for name, value in metrics.items():
                if isinstance(value, (int, float)):
                    # Store the raw value - formatting happens in the callback
                    self._metrics_state[name] = value
                    metrics_updated += 1
                    
                    # Check if this is a new metric that needs to be registered
                    self._register_metric_if_new(name, percentage_metrics)
                    
                    logger.debug(f"Updated metric state {name}={value}")
                elif isinstance(value, str) and value.isdigit():
                    # Try to convert string numbers
                    self._metrics_state[name] = float(value)
                    metrics_updated += 1
                    
                    # Check if this is a new metric that needs to be registered
                    self._register_metric_if_new(name, percentage_metrics)
                    
                    logger.debug(f"Updated metric state {name}={value}")
                else:
                    # Skip non-numeric metrics
                    logger.debug(f"Skipping non-numeric metric: {name}={value}")
            
            logger.debug(f"Updated {metrics_updated} metrics for {self.service_name}")
        except Exception as e:
            logger.error(f"Error recording metrics: {e}")
            
    def _register_new_metric(self, name: str, is_percentage: bool = False):
        """
        Register a new metric that was not in the initial expected metrics list.
        
        Args:
            name: Name of the metric to register
            is_percentage: Whether this metric should be displayed as a percentage
        """
        if not hasattr(self, 'meter') or not self.meter:
            logger.error(f"Cannot register new metric {name}: Meter not initialized")
            return
            
        # Define which metrics are counters
        counter_metrics = {
            "process_count": True,
            "disk_read_bytes": True,
            "disk_write_bytes": True,
            "open_file_descriptors": True,
            "thread_count": True,
            "voluntary_ctx_switches": True,
            "nonvoluntary_ctx_switches": True,
            "max_threads_per_process": True,
            "min_threads_per_process": True
        }
            
        try:
            # Check if this metric is a counter
            is_counter = counter_metrics.get(name, False)
            
            # Set decimal places to 0 for counters
            decimal_places = 0 if is_counter else 2
            
            # Get metric ID and display name from metadata store
            metric_id, display_name = self._metadata_store.get_or_create_metric(
                service_id=self.service_id,
                name=name,
                unit="%" if is_percentage else "",
                format_type="counter" if is_counter else ("percentage" if is_percentage else "number"),
                decimal_places=decimal_places,
                is_percentage=is_percentage,
                is_counter=is_counter
            )
            
            # Create the observable gauge with the callback
            gauge = self.meter.create_observable_gauge(
                # Use simple metric name from metadata store for display in Instana
                name=self._metadata_store.get_simple_metric_name(name),
                description=f"Metric for {display_name}",
                unit="%" if is_percentage else "1",
                callbacks=[self._create_metric_callback(
                    name, 
                    is_percentage, 
                    is_counter, 
                    decimal_places, 
                    display_name
                )]
            )
            
            # Add to registry
            self._metrics_registry.add(name)
            logger.info(f"Registered new observable metric: {name} (display: {display_name})")
            
        except Exception as e:
            logger.error(f"Error registering new metric {name}: {e}")
            
    def create_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Create a new span.
        
        Args:
            name: Name of the span
            attributes: Span attributes
            
        Returns:
            An OpenTelemetry span or a dummy context manager if OpenTelemetry is not available
        """
        if not OPENTELEMETRY_AVAILABLE:
            logger.error(f"Cannot create span '{name}': OpenTelemetry packages not installed")
            # Return a dummy context manager
            class DummyContextManager:
                def __enter__(self):
                    return self
                def __exit__(self, exc_type, exc_val, exc_tb):
                    pass
            return DummyContextManager()
            
        logger.debug(f"Creating span: {name}")
        return self.tracer.start_as_current_span(name, attributes=attributes)
        
    def shutdown(self):
        """
        Shutdown the OpenTelemetry providers and exporters.
        This ensures all pending spans and metrics are exported.
        """
        try:
            # Force flush any pending spans
            if hasattr(self, '_tracer_provider'):
                self._tracer_provider.force_flush()
                
            # Force flush any pending metrics
            if hasattr(self, '_meter_provider'):
                self._meter_provider.force_flush()
                
            logger.info(f"Successfully shut down OTel connector for {self.service_name}")
        except Exception as e:
            logger.error(f"Error during OTel connector shutdown: {e}")
