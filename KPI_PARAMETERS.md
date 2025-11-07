# KPI Parameters Analyzed

This document lists all the parameters (KPIs) that the LTE Band 41 RCA application analyzes.

## Primary KPI Parameters with Thresholds

The application monitors and analyzes the following KPIs with specific thresholds:

### Connection Management KPIs

1. **RRC_Setup_Success_Rate**
   - Threshold: ≥ 95%
   - Unit: Percentage
   - Description: Radio Resource Control connection setup success rate
   - Used for: Connection establishment monitoring, parameter validation

2. **ERAB_Setup_Success_Rate**
   - Threshold: ≥ 98%
   - Unit: Percentage
   - Description: E-UTRAN Radio Access Bearer setup success rate
   - Used for: Bearer establishment monitoring, QoS validation

3. **RRC_Setup_Attempts**
   - Description: Number of RRC connection establishment attempts
   - Used for: Traffic analysis, connection load monitoring

4. **RRC_Setup_Success**
   - Description: Number of successful RRC connection establishments
   - Used for: Success rate calculation, performance trending

5. **RRC_Connections**
   - Description: Current number of RRC connections
   - Used for: Capacity monitoring, load analysis

6. **ERAB_Setup_Attempts**
   - Description: Number of ERAB establishment attempts
   - Used for: Bearer load analysis

7. **ERAB_Setup_Success**
   - Description: Number of successful ERAB establishments
   - Used for: Bearer success rate calculation

8. **ERAB_Connections**
   - Description: Current number of active ERAB connections
   - Used for: Bearer capacity monitoring

### Resource Utilization KPIs

1. **PRB_Utilization_Avg**
   - Threshold: < 70%
   - Unit: Percentage
   - Description: Average Physical Resource Block utilization
   - Used for: Congestion detection, capacity planning

2. **PRB_Utilization_P95**
   - Threshold: < 85%
   - Unit: Percentage
   - Description: 95th percentile PRB utilization
   - Used for: Peak load analysis, congestion signatures

### Radio Quality KPIs

1. **SINR_Avg**
   - Threshold: > 5 dB
   - Unit: Decibels (dB)
   - Description: Average Signal-to-Interference-plus-Noise Ratio
   - Used for: RF quality assessment, interference detection

2. **SINR_P10**
   - Threshold: > 0 dB
   - Unit: Decibels (dB)
   - Description: 10th percentile SINR (worst-case coverage)
   - Used for: Coverage edge analysis, interference hotspots

3. **SINR_PUSCH**
   - Description: SINR on Physical Uplink Shared Channel
   - Used for: Uplink quality assessment

### Error Rate KPIs

1. **BLER_P95**
   - Threshold: < 10%
   - Unit: Percentage
   - Description: 95th percentile Block Error Rate
   - Used for: Link quality degradation detection

2. **BLER_DL**
   - Description: Downlink Block Error Rate
   - Used for: Downlink quality monitoring

### Throughput KPIs

1. **Downlink_Throughput**
   - Description: Downlink data throughput (bits per second)
   - Used for: Performance validation, capacity analysis

2. **Uplink_Throughput**
   - Description: Uplink data throughput (bits per second)
   - Used for: Uplink performance monitoring

### Mobility KPIs

1. **Handover_Success_Rate**
   - Description: Success rate of handover procedures
   - Used for: Mobility performance, neighbor optimization

### Core Network KPIs

1. **S1_Setup_Failure_Rate**
   - Threshold: < 1%
   - Unit: Percentage
   - Description: S1 interface setup failure rate
   - Used for: Transport/TIMING fault detection, backhaul monitoring

2. **Paging_Success_Rate**
   - Threshold: ≥ 95%
   - Unit: Percentage
   - Description: Paging procedure success rate
   - Used for: New-site integration validation, paging configuration

### Availability KPIs

1. **Cell_Availability**
   - Threshold: ≥ 99%
   - Unit: Percentage
   - Description: Cell availability percentage
   - Used for: Site health monitoring, outage detection

## Analysis Features

### Statistical Analysis

For each KPI, the application calculates:

- **Mean**: Average value
- **Min**: Minimum value observed
- **Max**: Maximum value observed
- **Median**: Median value (if multiple samples)
- **Standard Deviation**: Variability measure (if multiple samples)
- **Count**: Number of measurement samples

### Anomaly Detection

- Threshold-based anomaly detection
- ML-based anomaly detection (IsolationForest)
- Severity classification (low, medium, high)

### Root Cause Analysis

The application uses these KPIs to identify:

- Transport/TIMING faults
- Microwave ACM fade
- TDD frame misalignment
- RF interference / sector overshoot
- Congestion
- RF quality degradation
- Parameter mismatches
- New-site integration issues
- CPE-specific issues

### Parameter Drift Detection

- Baseline comparison for all KPIs
- Drift score calculation
- Parameter change identification

## Ericsson Counter Name Mappings

The parser automatically maps Ericsson PM counter names to standard KPI names:

| Ericsson Counter | Standard KPI Name |
|-----------------|------------------|
| pmRrcConnEstabAtt | RRC_Setup_Attempts |
| pmRrcConnEstabSucc | RRC_Setup_Success |
| pmRrcConnEstab | RRC_Setup_Success_Rate |
| pmErabEstabAtt | ERAB_Setup_Attempts |
| pmErabEstabSucc | ERAB_Setup_Success |
| pmErabEstab | ERAB_Setup_Success_Rate |
| pmPrbUsedDlAvg | PRB_Utilization_Avg |
| pmPrbUsedDl | PRB_Utilization_Avg |
| pmSinrAvg | SINR_Avg |
| pmSinrP10 | SINR_P10 |
| pmSinrPusch | SINR_PUSCH |
| pmBlerP95 | BLER_P95 |
| pmBlerDl | BLER_DL |
| pmPagingSucc | Paging_Success_Rate |
| pmS1EstabFail | S1_Setup_Failure_Rate |
| pmCellAvail | Cell_Availability |
| pmPdcpVolDlDrb | Downlink_Throughput |

## Data Sources

KPIs are extracted from:

- Ericsson ENM PM counter XML files
- Multiple XML formats supported:
  - `measCollecFile` structure
  - `mdc` structure (with namespaces)
  - `pmContainer` structure
- Time-series data with timestamps
- Site/cell identifiers

## Usage

All KPIs are automatically:

1. Parsed from uploaded XML files
2. Analyzed for threshold violations
3. Used in root cause analysis
4. Monitored for anomalies
5. Tracked for parameter drift
6. Visualized in dashboards
