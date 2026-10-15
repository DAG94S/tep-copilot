# Tennessee Eastman Process: plant description

Reference description of the Tennessee Eastman Process (TEP), a public benchmark simulation of an industrial chemical plant (Downs & Vogel, 1993). Tag names and units follow the benchmark.

## Overview

The plant converts four gaseous reactants (components A, C, D, E) into two liquid products (components G, H). The feeds also carry an inert (component B), and side reactions form a byproduct (component F). Components A to E are gases, F, G and H are liquids at process conditions.

Reactions (irreversible, exothermic; rates increase with temperature):

- A(g) + C(g) + D(g) -> G(liq)
- A(g) + C(g) + E(g) -> H(liq)
- A(g) + E(g) -> F(liq)
- 3 D(g) -> 2 F(liq)

## Process units

- Reactor: gaseous feeds react here. An internal cooling water bundle removes the heat of reaction.
- Condenser: cools the reactor effluent (stream 7) with cooling water.
- Vapor-liquid separator: receives the condensed effluent. Vapor goes back to the reactor feed, liquid goes to the stripper.
- Recycle compressor: returns separator vapor (stream 8) to the reactor feed. A recycle valve (XMV(5)) acts around it.
- Purge: a part of the recycle gas leaves as stream 9 to remove the inert and the byproduct.
- Stripper: stream 4 (components A and C) strips remaining reactants from the separator liquid (stream 10). Steam heats the stripper. The stripped vapor joins the reactor feed through stream 5. Products G and H leave the stripper base as stream 11.

## Streams

| Stream | Content |
|---|---|
| 1 | Component A feed |
| 2 | Component D feed |
| 3 | Component E feed |
| 4 | Component A and C feed (to the stripper) |
| 5 | Stripper overhead vapor to the reactor feed |
| 6 | Combined reactor feed |
| 7 | Reactor effluent |
| 8 | Recycle gas from the separator through the compressor |
| 9 | Purge |
| 10 | Separator liquid (underflow) to the stripper |
| 11 | Product (G and H) from the stripper base |

## Measured variables (XMEAS 1-41)

| Tag | Description | Unit |
|---|---|---|
| XMEAS(1) | component A feed (stream 1) | kscmh |
| XMEAS(2) | component D feed (stream 2) | kg/h |
| XMEAS(3) | component E feed (stream 3) | kg/h |
| XMEAS(4) | component A and component C feed (stream 4) | kscmh |
| XMEAS(5) | recycle flow (stream 8) | kscmh |
| XMEAS(6) | reactor feed rate (stream 6) | kscmh |
| XMEAS(7) | reactor pressure | kPa gauge |
| XMEAS(8) | reactor level | % |
| XMEAS(9) | reactor temperature | °C |
| XMEAS(10) | purge rate (stream 9) | kscmh |
| XMEAS(11) | separator temperature | °C |
| XMEAS(12) | separator level | % |
| XMEAS(13) | separator pressure | kPa gauge |
| XMEAS(14) | separator underflow (stream 10) | m3/h |
| XMEAS(15) | stripper level | % |
| XMEAS(16) | stripper pressure | kPa gauge |
| XMEAS(17) | stripper underflow (stream 11) | m3/h |
| XMEAS(18) | stripper temperature | °C |
| XMEAS(19) | stripper steam flow | kg/h |
| XMEAS(20) | compressor work | kW |
| XMEAS(21) | reactor cooling water outlet temperature | °C |
| XMEAS(22) | separator cooling water outlet temperature | °C |
| XMEAS(23) | component A in reactor feed (stream 6) | mol% |
| XMEAS(24) | component B in reactor feed (stream 6) | mol% |
| XMEAS(25) | component C in reactor feed (stream 6) | mol% |
| XMEAS(26) | component D in reactor feed (stream 6) | mol% |
| XMEAS(27) | component E in reactor feed (stream 6) | mol% |
| XMEAS(28) | component F in reactor feed (stream 6) | mol% |
| XMEAS(29) | component A in purge gas (stream 9) | mol% |
| XMEAS(30) | component B in purge gas (stream 9) | mol% |
| XMEAS(31) | component C in purge gas (stream 9) | mol% |
| XMEAS(32) | component D in purge gas (stream 9) | mol% |
| XMEAS(33) | component E in purge gas (stream 9) | mol% |
| XMEAS(34) | component F in purge gas (stream 9) | mol% |
| XMEAS(35) | component G in purge gas (stream 9) | mol% |
| XMEAS(36) | component H in purge gas (stream 9) | mol% |
| XMEAS(37) | component D in product (stream 11) | mol% |
| XMEAS(38) | component E in product (stream 11) | mol% |
| XMEAS(39) | component F in product (stream 11) | mol% |
| XMEAS(40) | component G in product (stream 11) | mol% |
| XMEAS(41) | component H in product (stream 11) | mol% |

## Manipulated variables (XMV 1-11)

The twelfth manipulated variable of the original model (agitator speed) is not present in the public datasets used here.

| Tag | Description | Unit |
|---|---|---|
| XMV(1) | component D feed flow (stream 2) | % open |
| XMV(2) | component E feed flow (stream 3) | % open |
| XMV(3) | component A feed flow (stream 1) | % open |
| XMV(4) | component A and component C feed flow (stream 4) | % open |
| XMV(5) | compressor recycle valve | % open |
| XMV(6) | purge valve (stream 9) | % open |
| XMV(7) | separator pot liquid flow (stream 10) | % open |
| XMV(8) | stripper liquid product flow (stream 11) | % open |
| XMV(9) | stripper steam valve | % open |
| XMV(10) | reactor cooling water flow | % open |
| XMV(11) | condenser cooling water flow | % open |

## Process disturbances IDV(1)-IDV(15)

The benchmark defines 15 programmable disturbances. IDV(1) to IDV(7) are step changes, IDV(8) to IDV(12) are random variations, IDV(13) is a slow drift in the reaction kinetics, and IDV(14) and IDV(15) are valves that stick. The cooling water "inlet temperature" disturbances apply to the reactor cooling water (IDV(4), IDV(11)) and the condenser cooling water (IDV(5), IDV(12)).

| IDV | Description | Type |
|---|---|---|
| IDV(1) | component A/component C feed ratio, component B composition constant (stream 4) | step |
| IDV(2) | component B composition, component A/component C ratio constant (stream 4) | step |
| IDV(3) | component D feed temperature (stream 2) | step |
| IDV(4) | reactor cooling water inlet temperature | step |
| IDV(5) | condenser cooling water inlet temperature | step |
| IDV(6) | component A feed loss (stream 1) | step |
| IDV(7) | component C header pressure loss, reduced availability (stream 4) | step |
| IDV(8) | component A, component B, component C feed composition (stream 4) | random variation |
| IDV(9) | component D feed temperature (stream 2) | random variation |
| IDV(10) | component C feed temperature (stream 4) | random variation |
| IDV(11) | reactor cooling water inlet temperature | random variation |
| IDV(12) | condenser cooling water inlet temperature | random variation |
| IDV(13) | reaction kinetics | slow drift |
| IDV(14) | reactor cooling water valve | sticking |
| IDV(15) | condenser cooling water valve | sticking |

Note: depending on the dataset, a fault number "k" corresponds to IDV(k). Some disturbances (for example IDV(3), IDV(9), IDV(15)) are known to be very hard to detect from the measurements because their effect is small.

## Sources

- Downs, J. J. and Vogel, E. F. (1993). A plant-wide industrial process control problem. Computers & Chemical Engineering, 17(3), 245-255.
- Rieth, C. A., Amsel, B. D., Tran, R. and Cook, M. B. (2017). Additional Tennessee Eastman Process Simulation Data for Anomaly Detection Evaluation. Harvard Dataverse, https://doi.org/10.7910/DVN/6C3JR1.
- Khan, A. et al. (2025). FaultExplainer. Computers & Chemical Engineering (cause catalogue of 15 candidate disturbances). Code: github.com/li-group/FaultExplainer (MIT).
