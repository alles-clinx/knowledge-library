# Aegis / ORBIT-7

Aegis is the control-plane layer for Nova. Its internal release codename is **ORBIT-7**.

The purpose is to make Nova a source-grounded AI copilot for facility managers without turning the public Knowledge library into an opaque training dump.

## What Aegis controls

- which Alle's ClinX Knowledge records are admitted to a Nova candidate;
- Nova's facility-manager reasoning and evidence policy;
- facility-operations evaluation cases;
- candidate manifests and content hashes;
- a gated promotion adapter for the Nova backend.

## Source of truth

Only article IDs present in `production/live.json` are admitted. English and available Hindi variants are packaged from the canonical `articles/` source tree. Draft or future canonical records are excluded automatically.

## Release path

```
Knowledge source
   ↓
production/live.json gate
   ↓
Aegis candidate builder
   ↓
ORBIT-7 integrity + facility-manager gates
   ↓
GitHub artifact
   ↓
manual nova-production promotion
   ↓
Nova backend
```

## Security boundary

This repository is public. Therefore **Aegis and ORBIT-7 are codenames, not security controls**. Do not commit API keys, tokens, private endpoints, customer data, credentials, or confidential model configuration here.

The promotion workflow reads `NOVA_CONTROL_ENDPOINT` and `NOVA_CONTROL_TOKEN` only from GitHub environment secrets. The actual Nova backend is not configured by this repository yet.

## Design principle

Aegis is retrieval-first. Fine-tuning is disabled by policy until evaluations show a specific behavior problem that retrieval, prompting, or tool design cannot solve. This keeps operational answers traceable to approved Knowledge and makes rollbacks straightforward.
