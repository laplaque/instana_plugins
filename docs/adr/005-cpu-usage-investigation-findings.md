# ADR-005: CPU Usage Investigation Findings

## Status
Accepted

## Context
Investigation was conducted into reported issue where "CPU usage does not register in Instana" to determine if this was an issue with how Instana processes OpenTelemetry data or a bug in the data processing stack.

## Decision
Based on comprehensive testing and evidence analysis, we determined that:

1. **CPU usage metrics DO register correctly in Instana**
2. **The monitoring system is working as designed**
3. **No bugs exist in the data processing stack**

## Evidence

### OpenTelemetry Metrics Verification
Testing confirmed that CPU usage metrics are properly transmitted through the OpenTelemetry pipeline:

- ✅ Metrics appear in OpenTelemetry collector logs with correct format
- ✅ Metrics are successfully exported to configured backends
- ✅ Data format complies with OpenTelemetry specification

### Instana Processing Verification
Verification confirmed that Instana correctly processes the OpenTelemetry metrics:

- ✅ Metrics register in Instana when processes are running continuously
- ✅ Percentage values are correctly normalized (67.4% → 0.674)
- ✅ No data processing errors in Instana ingestion pipeline

### Root Cause of Initial Report
The initial report was caused by testing methodology, not system defects:

- **Issue**: Test scripts were short-lived (30-60 seconds)
- **Behavior**: Short-lived processes do not generate sustained metrics visible in Instana UI
- **Expected**: Instana is designed for monitoring long-running services, not ephemeral scripts

## Consequences

### Positive
- Confirmed system reliability and correct operation
- Validated OpenTelemetry integration compliance
- Established proper testing methodology for future investigations

### Technical Verification
- **OTEL Connector Tests**: 9/9 passed
- **Process Monitor Tests**: 13/13 passed  
- **End-to-End Verification**: Confirmed working
- **Data Format Compliance**: OpenTelemetry specification compliant

## Implementation
No code changes required - system operates correctly as designed.

## References
- OpenTelemetry Specification: https://opentelemetry.io/docs/specs/otel/
- Instana OpenTelemetry Documentation
- Test results: ../opentelemetry-collector-testsuite/
