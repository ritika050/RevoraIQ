# RevoralQ 5-minute pitch script

Speak this naturally. Pause at the dashboard. Do not read the timestamps out loud unless you are rehearsing to a clock.

## 0:00 – 0:30 · Problem

Fraud and operational risk no longer look like a single obvious spike. They hide in ordinary customer journeys: a familiar user, a familiar app, then one payment that is just different enough to matter.

By the time a traditional SOC notice fires, the money has often already moved. Teams are staring at dashboards that say *something* broke, but not *why this user, why this device, why now*.

## 0:30 – 1:00 · Why existing monitoring is insufficient

Most stacks are good at collection and terrible at judgment.

Thresholds fire too late or too often. SIEM tools drown analysts in events. Fraud rules are brittle. Machine-learning scores show up as a number with no explanation, so nobody trusts them enough to block in real time.

What’s missing is a closed loop: ingest, understand behavior, explain the risk, decide, and act — while the operator can still see every step.

## 1:00 – 1:30 · RevoralQ

RevoralQ is real-time AI monitoring and intelligence.

It watches activity as it happens, compares it with how that user normally behaves, and when something looks wrong it does three things humans actually need:

1. It scores the risk in a way you can audit.
2. It explains the event in plain language.
3. It recommends — and can execute — a concrete action.

This is not a slide. The system behind me is running locally, with no API key required.

## 1:30 – 2:15 · Architecture / technical approach

Data comes in from activities, transactions, logs, APIs, devices. An ingestion layer validates it and puts it on a stream. In this prototype the stream is an in-memory broker with a Kafka-shaped interface, so production can drop Kafka in without rewriting the pipeline.

Processing extracts features, updates a behavior profile, and runs anomaly detection — Isolation Forest plus rules for amount, frequency, new device, new location, new beneficiary.

A transparent risk model turns those signals into a 0–100 score. Then the RevoralQ AI engine writes the story: why it happened, what patterns fired, what to do next. A decision engine maps LOW to allow, MEDIUM to monitor, HIGH to flag, CRITICAL to block.

Everything lands in SQLite, shows up on the dashboard over a live event stream, and actions are logged so you can defend the decision later.

## 2:15 – 3:45 · Live demo

Open the Intelligence Dashboard.

You are looking at Ananya Rao, user `USR-102`. Her normal world is a few hundred to about twelve hundred rupees, same device, Mumbai, known beneficiaries.

Click **DEMO MODE**.

Watch the pipeline strip at the top. Events are ingested, validated, queued, processed. The live feed fills with ordinary payments: ₹500, ₹800, ₹1,200, ₹700. Charts move. Risk stays low. This is the baseline.

Then the spike arrives: ₹75,000, new device `DEV-NEW-91`, Delhi, new beneficiary. Anomaly detection lights up. Risk climbs into the high / critical band. The AI panel explains it the way an analyst would: amount far above history, unseen device, new payee, compressed frequency.

An alert appears. The decision is not a mystery number — it is FLAG or BLOCK, with a reason.

## 3:45 – 4:20 · AI reasoning + automated decision

Click through into the event.

You get the raw payload, the features, the historical range versus the current amount, the pattern list, and a paragraph you could paste into a case file. If an LLM key is configured, that paragraph can be model-authored. If not, the local engine still produces a consistent, human-readable explanation.

Then execute the recommended action. You should see a success record: transaction id, action type, reason, timestamp. In this prototype we do not send SMS or call a bank. We prove the control path works, and we keep an audit trail.

## 4:20 – 4:45 · Business impact

This is how you cut time-to-judgment. Analysts stop reconstructing context from five tools. Compliance gets a written why. Operations get a button that actually does something.

The same loop applies beyond payments: account takeover, insider misuse, API abuse, device fleets. The product is a decision fabric, not a single fraud rule.

## 4:45 – 5:00 · Scale and close

The broker, cache, and raw store are already abstracted. Kafka, Redis, and object storage are the next mechanical upgrades, not a rewrite. Models can be swapped. The reasoning layer can sit on whatever LLM your security policy allows.

RevoralQ turns noisy event streams into explained decisions, fast enough to act. That’s the system. I’m happy to walk through the code or a second scenario next.
