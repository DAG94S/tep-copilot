# Inspection guide by disturbance IDV(1)-IDV(15)

Illustrative guide for maintenance: what to inspect or measure to confirm or rule out each candidate disturbance of the Tennessee Eastman benchmark. It is not a real plant procedure. Findings are reported to the operator, who decides any control action under the plant procedures.

Stream numbers refer to the plant description: stream 1 component A feed, stream 2 component D feed, stream 4 component A and C feed.

## Step disturbances

### IDV(1): A/C feed ratio change in stream 4 (B composition constant)
- Check the stream 4 flow measurement and its transmitter calibration.
- Sample the stream 4 feed and verify the A/C ratio against the analyzer reading.
- Inspect the stream 4 feed control valve and the upstream supply of A and C.

### IDV(2): B composition change in stream 4 (A/C ratio constant)
- Sample the stream 4 feed and verify the inert B content.
- Check the feed analyzer and its sampling line.
- Verify the composition at the supplier or upstream header.

### IDV(3): D feed temperature step (stream 2)
- Measure the stream 2 temperature at the field and compare with the indication.
- Inspect the feed heater or heat exchanger on stream 2.
- Check the temperature transmitter and its thermowell.

### IDV(4): Reactor cooling water inlet temperature step
- Measure the cooling water supply temperature at the reactor inlet.
- Check the cooling water supply header and the cooling tower or chiller outlet.
- Verify the reactor cooling water outlet temperature transmitter.

### IDV(5): Condenser cooling water inlet temperature step
- Measure the cooling water supply temperature at the condenser inlet.
- Check the cooling water supply header and the upstream heat rejection system.
- Verify the separator cooling water outlet temperature transmitter.

### IDV(6): A feed loss (stream 1)
- Check the stream 1 supply: upstream isolation valves, header pressure, and supplier status.
- Inspect the stream 1 flow transmitter and the feed valve.
- Verify the stream 1 line for blockage or leakage.

### IDV(7): C header pressure loss (stream 4)
- Measure the C header pressure at the field gauge.
- Check the supply source and the pressure regulator on the C header.
- Inspect the stream 4 feed valve and the flow transmitter.

## Random variations

### IDV(8): A, B, C feed composition variation (stream 4)
- Sample the stream 4 feed over time and verify the composition variability.
- Check the feed analyzer and the upstream mixing or blending point.
- Verify the stream 4 flow transmitter for noise.

### IDV(9): D feed temperature variation (stream 2)
- Measure the stream 2 temperature repeatedly at the field.
- Inspect the temperature control loop on the D feed heater.
- Check the temperature transmitter for noise or a loose connection.

### IDV(10): C feed temperature variation (stream 4)
- Measure the stream 4 temperature repeatedly at the field.
- Inspect the heat exchanger or heater on the C feed.
- Check the temperature transmitter for noise.

### IDV(11): Reactor cooling water inlet temperature variation
- Measure the supply temperature at the reactor cooling water inlet over time.
- Check the cooling water source for temperature swings.
- Verify the reactor cooling water outlet temperature transmitter.

### IDV(12): Condenser cooling water inlet temperature variation
- Measure the supply temperature at the condenser cooling water inlet over time.
- Check the cooling water source for temperature swings.
- Verify the separator cooling water outlet temperature transmitter.

## Slow drift

### IDV(13): Reaction kinetics drift
- Sample the reactor product and verify the composition trend against laboratory analysis.
- Inspect the catalyst or reaction conditions records, and check the reactor temperature transmitter for drift.
- Verify the analyzers on the product stream for calibration drift.

## Sticking valves

### IDV(14): Reactor cooling water valve sticking
- Inspect the valve stem, packing and positioner for friction.
- Check the valve response by comparing the commanded position with the measured flow.
- Verify the air supply and the positioner feedback.

### IDV(15): Condenser cooling water valve sticking
- Inspect the valve stem, packing and positioner for friction.
- Check the valve response by comparing the commanded position with the measured flow.
- Verify the air supply and the positioner feedback.

## Sources

- Downs, J. J. and Vogel, E. F. (1993). A plant-wide industrial process control problem. Computers & Chemical Engineering, 17(3), 245-255 (disturbance definitions).
- Khan, A. et al. (2025). FaultExplainer. Computers & Chemical Engineering (candidate cause catalogue). Code: github.com/li-group/FaultExplainer (MIT).
- Inspection items are generic maintenance practice written for this demonstration, not taken from a real plant.
