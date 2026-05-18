# GCP Setup

## Required GCP resources

| Resource | Name |
|---|---|
| Project | `rail-511` |
| BigQuery dataset | `rail_data` |
| GCS bucket | `rail_storage` |
| Service account | `rail-access@rail-511.iam.gserviceaccount.com` |

## Required IAM roles for the service account

| Role | Purpose |
|---|---|
| `BigQuery Data Editor` | Read and write BigQuery tables |
| `BigQuery Job User` | Run queries |
| `Storage Object Admin` | Upload Parquet files to GCS |

## Creating the service account key

```bash
gcloud iam service-accounts keys create service-account.json \
  --iam-account=rail-access@rail-511.iam.gserviceaccount.com \
  --project=rail-511
```

> **Security:** Rotate this key periodically. The file must never be committed — it is listed in `.gitignore`.

## Creating the BigQuery dataset

```bash
bq mk --dataset --location=EU rail-511:rail_data
```

## Creating the GCS bucket

```bash
gsutil mb -p rail-511 -l EU gs://rail_storage
```
