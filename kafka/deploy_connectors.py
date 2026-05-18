import os
import json
import requests

# Configuration
CONNECT_URL = os.getenv("KAFKA_CONNECT_URL", "http://localhost:8083/connectors")
CONFIG_DIR = os.getenv("KAFKA_CONNECTOR_CONFIG_DIR", "./kafka/sink_config/")

def deploy_connector(config_path):
    with open(config_path, 'r') as f:
        config_data = json.load(f)

    connector_name = config_data.get("name", os.path.basename(config_path))
    response = requests.post(
        CONNECT_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(config_data)
    )

    if response.status_code in [200, 201]:
        print(f"✅ Deployed: {connector_name}")
    elif response.status_code == 409:
        print(f"⚠️ Already exists: {connector_name}")
    else:
        print(f"❌ Failed to deploy: {connector_name} ({response.status_code})")
        print(response.text)

def main():
    if not os.path.exists(CONFIG_DIR):
        print(f"Config directory '{CONFIG_DIR}' does not exist.")
        return

    for file_name in os.listdir(CONFIG_DIR):
        if file_name.endswith("_sink_config.json"):
            config_path = os.path.join(CONFIG_DIR, file_name)
            print(f"Deploying connector: {file_name}")
            deploy_connector(config_path)

if __name__ == "__main__":
    main()
