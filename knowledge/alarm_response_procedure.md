# Alarm response procedure (ILLUSTRATIVE)

**ILLUSTRATIVE ONLY. This is not a real plant SOP.** It is a generic example written for a research demonstration on the Tennessee Eastman benchmark. A real plant must follow its own approved procedures, operating limits and management of change.

## Golden rule

The copilot and the documentation agent never operate the process. They do not hold write access to the plant and do not issue control commands. Every control action is decided and carried out by the licensed operator under the plant procedures. The copilot only detects, proposes a diagnosis, and drafts documentation after a human has approved it.

## Principles (general alignment)

The structure follows the general philosophy of alarm management in ISA-18.2 and EEMUA 191: an alarm must be relevant, unique, timely, prioritised, understandable, diagnostic, advisory and focused. Each alarm needs a defined operator response. This document does not claim compliance with either standard.

## Response steps for the control room operator

1. Acknowledge the alarm and note the time.
2. Identify the alarm priority and the affected unit (reactor, condenser, separator, compressor, stripper).
3. Check whether other alarms started at the same time. Several related alarms usually point to a single upstream cause.
4. Verify the measurement: compare redundant or related indications (for example flow against valve position, temperature against cooling water outlet temperature) to rule out an instrument fault.
5. Review the copilot diagnosis as a proposal. Check that the evidence it cites (sensor tags and directions) matches what you see on the trends. Evidence marked as rejected by the deterministic gate must not be used as support.
6. Decide the response according to the plant procedure. The operator is the only one who decides control actions.
7. Escalate to the shift supervisor when the situation is not covered by procedure, when the diagnosis is marked uncertain, or when the process approaches a safety limit.
8. Request maintenance inspection when a field cause is suspected. Use the inspection guide for the suspected disturbance.
9. Record in the shift log: alarm time, approved diagnosis, evidence, actions decided by the operator, and open items.
10. Hand over: tell the next shift what is pending and what was rejected.

## Roles

| Role | Responsibility |
|---|---|
| Operator | Decides and executes control actions. Approves or rejects the diagnosis. |
| Shift supervisor | Receives escalations and authorises exceptions. |
| Maintenance | Inspects and measures in the field to confirm or rule out a cause. |
| Copilot (statistics + language model + gate) | Detects, proposes, verifies evidence. Never acts. |
| Documentation agent | Drafts the work order and shift handover from an approved diagnosis. Never acts. |

## Sources

- ANSI/ISA-18.2-2016, Management of Alarm Systems for the Process Industries.
- EEMUA Publication 191, Alarm Systems: A Guide to Design, Management and Procurement (3rd ed., 2013).
- Downs, J. J. and Vogel, E. F. (1993). A plant-wide industrial process control problem. Computers & Chemical Engineering, 17(3), 245-255 (benchmark context only).
