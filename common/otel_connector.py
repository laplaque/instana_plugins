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
from typing import Dict, Any, Optional
import socket

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
    from opentelemetry.metrics import set_meter_provider, get_meter_provider
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    logger.error("OpenTelemetry packages not found. Please install required dependencies.")
    logger.error("Run: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp")
    OPENTELEMETRY_AVAILABLE = False

class InstanaOTelConnector:
    """
    OpenTelemetry connector for Instana.
    
    This class provides functionality to send metrics and traces to Instana
    using the OpenTelemetry protocol.
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
        client_key_path: Optional[str] = None
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
        
        # Store attributes for later use
        self.attributes = {
            "service.name": service_name,
            "service.namespace": "instana.plugins",
            "host.name": socket.gethostname(),
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
                
                span_exporter = OTLPSpanExporter(
                    endpoint=otlp_endpoint,
                    insecure=False,
                    credentials=None,
                    headers=None,
                    timeout=None,
                    compression=None,
                    **tls_config
                )
            else:
                # Use standard non-TLS endpoint
                otlp_endpoint = f"{self.agent_host}:{self.agent_port}"
                logger.debug(f"Using non-TLS endpoint: {otlp_endpoint}")
                span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            
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
            raise
        
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
            logger.debug(f"Metrics setup completed for {self.service_name}")
        except Exception as e:
            logger.error(f"Error setting up metrics: {e}")
            raise
        
    def record_metrics(self, metrics: Dict[str, Any]):
        """
        Record metrics using OpenTelemetry.
        
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
            # Create counters and gauges for each metric
            for name, value in metrics.items():
                if isinstance(value, (int, float)):
                    # Use gauge for numeric values
                    gauge = self.meter.create_gauge(
                        name=name,
                        description=f"Gauge metric for {name}",
                        unit="1"
                    )
                    gauge.record(value)
                    logger.debug(f"Recorded metric {name}={value}")
                elif isinstance(value, str) and value.isdigit():
                    # Try to convert string numbers
                    gauge = self.meter.create_gauge(
                        name=name,
                        description=f"Gauge metric for {name}",
                        unit="1"
                    )
                    gauge.record(float(value))
                    logger.debug(f"Recorded metric {name}={value}")
                else:
                    # Skip non-numeric metrics
                    logger.debug(f"Skipping non-numeric metric: {name}={value}")
                    
            logger.debug(f"Recorded {len(metrics)} metrics for {self.service_name}")
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
