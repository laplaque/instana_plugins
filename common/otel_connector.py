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

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.metrics import set_meter_provider, get_meter_provider

# Configure logging
setup_logging()  # Use the logging configuration from logging_config
logger = logging.getLogger(__name__)

class InstanaOTelConnector:
    """
    OpenTelemetry connector for Instana.
    
    This class provides functionality to send metrics and traces to Instana
    using the OpenTelemetry protocol.
    """
    
    def __init__(
        self,
        service_name: str,
        agent_host: str = "localhost",
        agent_port: int = 4317,
        resource_attributes: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the Instana OpenTelemetry connector.
        
        Args:
            service_name: Name of the service being monitored
            agent_host: Hostname of the Instana agent (default: localhost)
            agent_port: Port of the Instana agent's OTLP receiver (default: 4317)
            resource_attributes: Additional resource attributes to include
        """
        self.service_name = service_name
        self.agent_host = agent_host
        self.agent_port = agent_port
        
        # Set up resource attributes
        attributes = {
            "service.name": service_name,
            "service.namespace": "instana.plugins",
            "host.name": socket.gethostname(),
        }
        
        # Add custom resource attributes if provided
        if resource_attributes:
            attributes.update(resource_attributes)
            
        self.resource = Resource.create(attributes)
        
        # Initialize tracer
        self._setup_tracing()
        
        # Initialize metrics
        self._setup_metrics()
        
        logger.info(f"Initialized InstanaOTelConnector for service {service_name}")
        
    def _setup_tracing(self):
        """Set up the OpenTelemetry tracer provider and exporter."""
        try:
            # Create OTLP exporter for traces
            otlp_endpoint = f"{self.agent_host}:{self.agent_port}"
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
        try:
            # Create OTLP exporter for metrics
            otlp_endpoint = f"{self.agent_host}:{self.agent_port}"
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
                elif isinstance(value, str) and value.isdigit():
                    # Try to convert string numbers
                    gauge = self.meter.create_gauge(
                        name=name,
                        description=f"Gauge metric for {name}",
                        unit="1"
                    )
                    gauge.record(float(value))
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
            An OpenTelemetry span
        """
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
