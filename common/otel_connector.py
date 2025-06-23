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

# Import TOML utilities for metric definitions
try:
    from common.toml_utils import get_expanded_metrics
except ImportError as e:
    logger.error(f"TOML utilities not found: {e}")
    get_expanded_metrics = None

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
            "service.name": getattr(self, 'display_name', service_name),  # Use self.display_name with fallback to self.service_name
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
    
    def _handle_connection_error(self, error, component_name):
        """
        Handle ConnectionError consistently across tracing and metrics setup.
        
        Args:
            error: The ConnectionError that occurred
            component_name: Name of the component ("tracing" or "metrics")
            
        Returns:
            MagicMock: A mock exporter for testing/fallback scenarios
        """
        logger.error(f"Error setting up {component_name}: {error}")
        logger.warning(f"Using mock exporter for {component_name} (likely in test environment)")
        
        # Import MagicMock here to avoid import at module level
        from unittest.mock import MagicMock
        return MagicMock()

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
                    span_exporter = self._handle_connection_error(e, "tracing")
                    return
            else:
                # Use standard non-TLS endpoint
                otlp_endpoint = f"{self.agent_host}:{self.agent_port}"
                logger.debug(f"Using non-TLS endpoint: {otlp_endpoint}")
                try:
                    span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
                except ConnectionError as e:
                    span_exporter = self._handle_connection_error(e, "tracing")
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
            decimal_places: Number of decimal places to round to (from manifest.toml)
            display_name: Optional display name for logging

        Returns:
            A generator callback function that yields Observation objects for the observable gauge
        """
        def callback(options):
            try:
                if metric_name in self._metrics_state:
                    raw_value = self._metrics_state[metric_name]
                    
                    # Format the value according to manifest.toml specifications
                    if is_counter or decimal_places == 0:
                        # For counters and metrics with 0 decimals, show as integers
                        value = int(float(raw_value))
                    else:
                        # For other metrics, use the decimal places from manifest.toml
                        value = round(float(raw_value), decimal_places)
                    
                    # Yield an Observation object as required by OpenTelemetry API
                    yield Observation(value)
                    
                    # Use the provided display name or the metric name for logging
                    log_name = display_name or metric_name
                    logger.debug(f"Observed metric {log_name}={value}")
            except Exception as e:
                logger.error(f"Error in metric callback for {metric_name}: {e}")
        return callback
    
    def create_observable(self, name, otel_type, unit=None, decimals=2, is_percentage=False, 
                         is_counter=False, description=None, pattern_type=None, 
                         pattern_source=None, pattern_range=None, display_name=None):
        """
        Create an observable metric based on TOML configuration parameters.
        
        Args:
            name: Metric name from TOML
            otel_type: OpenTelemetry metric type ("Gauge", "Counter", "UpDownCounter")  
            unit: Unit from TOML (e.g., "%", "bytes", "threads")
            decimals: Number of decimal places from TOML
            is_percentage: Whether metric is a percentage from TOML
            is_counter: Whether metric is a counter from TOML
            description: Description from TOML
            pattern_type: Pattern type from TOML (e.g., "indexed")
            pattern_source: Pattern source from TOML (e.g., "cpu_count")
            pattern_range: Pattern range from TOML (e.g., "0-auto")
            display_name: Display name from metadata store
            
        Returns:
            The created observable metric
        """
        if not hasattr(self, 'meter') or not self.meter:
            logger.error(f"Cannot create observable metric {name}: Meter not initialized")
            return None
            
        # Convert TOML otel_type to OpenTelemetry method name
        if otel_type == "UpDownCounter":
            method_name = "create_observable_up_down_counter"
        else:
            # For "Gauge", "Counter", or any other type
            method_name = f"create_observable_{otel_type.lower()}"
        
        # Get the method dynamically, with fallback to gauge
        create_method = getattr(self.meter, method_name, self.meter.create_observable_gauge)
        
        # Use simple metric name from metadata store
        simple_name = self._metadata_store.get_simple_metric_name(name)
        
        # Create callback with all TOML parameters
        callback = self._create_metric_callback(
            metric_name=name,
            is_percentage=is_percentage,
            is_counter=is_counter,
            decimal_places=decimals,
            display_name=display_name
        )
        
        # Log creation with TOML type
        logger.debug(f"Creating observable {otel_type} metric: {name} -> {simple_name}")
        
        # Create and return the metric using the dynamically obtained method
        return create_method(
            name=simple_name,
            description=description or f"Metric for {name}",
            unit=unit or ("%" if is_percentage else ""),
            callbacks=[callback]
        )
    
    def _sync_toml_to_database(self):
        """
        Sync TOML metric definitions to database registry.
        Check if TOML has changed since last sync and update database accordingly.
        """
        try:
            # Load current metric definitions from TOML
            if not get_expanded_metrics:
                logger.error("TOML utilities not available. Cannot sync metrics to database.")
                return False
            
            metric_definitions = get_expanded_metrics()
            logger.info(f"Syncing {len(metric_definitions)} TOML metric definitions to database")
            
            # Sync each metric definition to database
            for metric_def in metric_definitions:
                name = metric_def['name']
                
                # Sync metric to database with all TOML parameters
                metric_id, display_name = self._metadata_store.sync_metric_from_toml(
                    service_id=self.service_id,
                    name=name,
                    unit=metric_def.get('unit', ""),
                    otel_type=metric_def.get('otel_type', 'Gauge'),
                    decimals=metric_def.get('decimals', 2),
                    is_percentage=metric_def.get('is_percentage', False),
                    is_counter=metric_def.get('is_counter', False),
                    description=metric_def.get('description', f"Metric for {name}"),
                    pattern_type=metric_def.get('pattern_type'),
                    pattern_source=metric_def.get('pattern_source'),
                    pattern_range=metric_def.get('pattern_range')
                )
                
            # Remove metrics from database that are no longer in TOML
            current_metric_names = {metric_def['name'] for metric_def in metric_definitions}
            self._metadata_store.remove_obsolete_metrics(self.service_id, current_metric_names)
            
            logger.info("Successfully synced TOML metrics to database")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing TOML to database: {e}")
            return False

    def _register_observable_metrics(self):
        """
        Register individual observable metrics with OpenTelemetry using database registry.
        At startup: sync TOML changes to database, then use database as single source of truth.
        """
        if not hasattr(self, 'meter') or not self.meter:
            logger.error("Cannot register metrics: Meter not initialized")
            return
            
        try:
            # Step 1: Sync TOML changes to database (register once)
            if not self._sync_toml_to_database():
                logger.error("Failed to sync TOML to database. Cannot proceed with metric registration.")
                return
                
            # Step 2: Load metrics from database registry (read many)
            database_metrics = self._metadata_store.get_service_metrics(self.service_id)
            logger.info(f"Loaded {len(database_metrics)} metrics from database registry")
            
            # Step 3: Register metrics with OpenTelemetry using database definitions
            for metric_record in database_metrics:
                try:
                    metric_name = metric_record['name']
                    otel_type = metric_record['otel_type']
                    unit = metric_record['unit']
                    decimals = metric_record['decimal_places']
                    is_percentage = metric_record['is_percentage']
                    is_counter = metric_record['is_counter']
                    description = metric_record['description']
                    display_name = metric_record['display_name']
                    
                    # Create the observable metric using database configuration
                    metric = self.create_observable(
                        name=metric_name,
                        otel_type=otel_type,
                        unit=unit,
                        decimals=decimals,
                        is_percentage=is_percentage,
                        is_counter=is_counter,
                        description=description,
                        display_name=display_name
                    )
                    
                    # Add to registry for tracking
                    self._metrics_registry.add(metric_name)
                    logger.debug(f"Registered observable metric from database: {metric_name} ({otel_type})")
                    
                except Exception as e:
                    logger.error(f"Error registering metric {metric_record.get('name', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Registered {len(self._metrics_registry)} observable metrics from database for {self.service_name}")
        except Exception as e:
            logger.error(f"Error registering observable metrics: {e}")
        
    def record_metrics(self, metrics: Dict[str, Any]):
        """
        Update the metrics state with new values.
        Only accepts metrics that are defined in TOML configuration.
        
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
            # Update the metrics state dictionary with new values
            metrics_updated = 0
            metrics_rejected = 0
            
            for name, value in metrics.items():
                # Only process metrics that are registered (defined in TOML)
                if name not in self._metrics_registry:
                    logger.warning(f"Metric '{name}' not defined in TOML configuration, rejecting")
                    metrics_rejected += 1
                    continue
                    
                if isinstance(value, (int, float)):
                    # Store the raw value - formatting happens in the callback
                    self._metrics_state[name] = value
                    metrics_updated += 1
                    logger.debug(f"Updated metric state {name}={value}")
                elif isinstance(value, str):
                    # Try to convert string numbers (handles both integers and decimals)
                    try:
                        numeric_value = float(value)
                        self._metrics_state[name] = numeric_value
                        metrics_updated += 1
                        logger.debug(f"Updated metric state {name}={value} (converted from string)")
                    except ValueError:
                        # Skip non-numeric string values
                        logger.debug(f"Skipping non-numeric string metric: {name}={value}")
                else:
                    # Skip non-numeric metrics
                    logger.debug(f"Skipping non-numeric metric: {name}={value}")
            
            logger.debug(f"Updated {metrics_updated} metrics, rejected {metrics_rejected} undefined metrics for {self.service_name}")
        except Exception as e:
            logger.error(f"Error recording metrics: {e}")
            
            
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
