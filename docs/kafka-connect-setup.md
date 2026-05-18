# Kafka Connect — BigQuery Sink Setup

The WePay BigQuery Sink connector is used to stream typed Kafka topics into BigQuery. The connector JAR is not tracked in git (it's too large). Follow these steps to install it.

## 1. Download the connector JAR

Download version **2.5.7** of the WePay BigQuery Connector from the [Confluent Hub](https://www.confluent.io/hub/wepay/kafka-connect-bigquery) or directly from the [GitHub releases](https://github.com/confluentinc/kafka-connect-bigquery).

Extract the contents so your directory looks like:

```
connect-plugins/
└── wepay-kafka-connect-bigquery-2.5.7/
    ├── manifest.json
    └── lib/
        └── *.jar
```

The `docker-compose.yml` mounts this directory into the Kafka Connect container at `/etc/kafka-connect/jars`.

## 2. Place your service account key

The connector authenticates to BigQuery using the service account key:

```bash
cp /path/to/your/service-account.json ./service-account.json
```

This is mounted read-only into the connect container at `/etc/kafka-connect/service-account.json`.

## 3. Start Kafka Connect

```bash
docker compose up -d broker connect
```

Wait for Connect to be ready (check `docker logs connect`).

## 4. Deploy all sink connectors

```bash
python kafka/deploy_connectors.py
```

This script reads every JSON file in `kafka/sink_config/` and POSTs it to the Kafka Connect REST API.

## 5. Verify

```bash
curl http://localhost:8083/connectors | python -m json.tool
```

All 8 connectors should appear:
- `rail_activation_sink`
- `rail_cancellation_sink`
- `rail_change_identity_sink`
- `rail_change_location_sink`
- `rail_change_origin_sink`
- `rail_movement_sink`
- `rail_reinstatement_sink`
- `rail_td_sink`

## Troubleshooting

| Symptom | Check |
|---|---|
| `ConnectException: No class found` | JAR not mounted — verify `connect-plugins/` path in docker-compose volume |
| `BigQueryConnectException: Access Denied` | Service account key missing or lacks BigQuery Data Editor role |
| Connector stuck in `FAILED` state | Check offset topic — may need to delete and re-register the connector |
