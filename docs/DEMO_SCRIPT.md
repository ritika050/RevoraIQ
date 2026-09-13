# RevoralQ demo script

Use this when recording or presenting. Total live click-path is about two minutes; Demo Mode itself runs roughly 60–120 seconds.

## Before you start

1. Run `run.bat` (Windows) or `./run.sh`.
2. Wait until both windows stay up.
3. Open [http://localhost:5173](http://localhost:5173).
4. Confirm the sidebar says **Live stream connected**.
5. No login is required. No API key is required.

## Path A — Demo Mode (preferred for the pitch)

1. On **RevoralQ Intelligence Dashboard**, click **DEMO MODE**.
2. Call out the status line as it changes:
   - Ingesting event...
   - Validating...
   - Running anomaly detection...
   - Analyzing behavior...
   - Calculating risk...
   - RevoralQ AI reasoning...
   - Decision generated...
   - Action triggered...
3. Point at the live feed: first four rows are normal USR-102 amounts (₹500 / ₹800 / ₹1,200 / ₹700).
4. When the ₹75,000 row appears, point at Anomaly = YES, high risk, CRITICAL/HIGH, decision BLOCK or FLAG.
5. Point at the alert card on the right.
6. If Demo Mode already auto-executed the block, show the **ACTION EXECUTED** JSON.
7. Otherwise click **Execute Action**.
8. Open **View Details**. Walk the timeline: EVENT → VALIDATED → PROCESSED → ANOMALY → RISK → AI → DECISION → ACTION.
9. Optionally visit **Search & Analysis** and filter severity CRITICAL.
10. Optionally visit **Admin / Ops** and show API / database / processor / AI engine status.

## Path B — Manual buttons (if you want full control)

1. Click **Generate Normal Event** two or three times. Rows should stay LOW / ALLOW.
2. Click **Generate Suspicious Event**. A ₹75,000 Delhi / new-device event should appear.
3. Click **Generate Burst of Events** to show frequency pressure.
4. Click **Run Demo Scenario** for the scripted 500→75000 sequence without the long pacing.
5. From the alert card, use **Execute Action**, **View Details**, and **Dismiss**. Every button changes state.

## Talking points while it runs

- Isolation Forest plus rules, not a fake score.
- Behavior comparison: normal ₹500–₹2,000 range versus ₹75,000.
- Risk math is on screen in the event detail breakdown.
- Actions are simulated on purpose: the log is the proof, not a live bank call.

## If something looks idle

- Refresh the page and confirm the API at [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).
- If Demo Mode says `already_running`, wait for it to finish.
- Restart `run.bat` if the live indicator stays disconnected.
