#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║  Azure Infrastructure Setup — Retail Intelligence Platform      ║
# ║  Run once to provision all Azure resources                      ║
# ╚══════════════════════════════════════════════════════════════════╝
# Usage: bash azure/provision.sh

set -e

# ── CONFIG ────────────────────────────────────────────────────────────────────
RESOURCE_GROUP="retail-intel-rg"
LOCATION="eastus"
APP_NAME="retail-intelligence-platform"
APP_SERVICE_PLAN="retail-intel-plan"
SQL_SERVER="retail-intel-sql"
SQL_DB="retaildb"
STORAGE_ACCOUNT="retailintelstorage$(date +%s | tail -c 6)"
KEY_VAULT="retail-intel-kv"
LOG_ANALYTICS="retail-intel-logs"

echo "🚀 Provisioning Azure infrastructure..."
echo "   Resource Group : $RESOURCE_GROUP"
echo "   Location       : $LOCATION"
echo ""

# ── 1. RESOURCE GROUP ─────────────────────────────────────────────────────────
echo "📦 Creating resource group..."
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --tags project="retail-intel" environment="production" owner="data-team"

# ── 2. LOG ANALYTICS (monitoring) ─────────────────────────────────────────────
echo "📊 Setting up Log Analytics workspace..."
az monitor log-analytics workspace create \
  --resource-group "$RESOURCE_GROUP" \
  --workspace-name "$LOG_ANALYTICS" \
  --location "$LOCATION" \
  --sku PerGB2018

WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group "$RESOURCE_GROUP" \
  --workspace-name "$LOG_ANALYTICS" \
  --query customerId -o tsv)

# ── 3. KEY VAULT ──────────────────────────────────────────────────────────────
echo "🔑 Creating Key Vault..."
az keyvault create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$KEY_VAULT" \
  --location "$LOCATION" \
  --sku standard \
  --enable-rbac-authorization true

# ── 4. AZURE SQL DATABASE ─────────────────────────────────────────────────────
echo "🗄️  Provisioning Azure SQL..."
SQL_ADMIN="retailadmin"
SQL_PASSWORD=$(openssl rand -base64 24)

az sql server create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$SQL_SERVER" \
  --location "$LOCATION" \
  --admin-user "$SQL_ADMIN" \
  --admin-password "$SQL_PASSWORD"

# Allow Azure services
az sql server firewall-rule create \
  --resource-group "$RESOURCE_GROUP" \
  --server "$SQL_SERVER" \
  --name "AllowAzureServices" \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

az sql db create \
  --resource-group "$RESOURCE_GROUP" \
  --server "$SQL_SERVER" \
  --name "$SQL_DB" \
  --service-objective S2 \
  --backup-storage-redundancy Local

# Store connection string in Key Vault
SQL_CONN="Driver={ODBC Driver 18 for SQL Server};Server=tcp:${SQL_SERVER}.database.windows.net;Database=${SQL_DB};Uid=${SQL_ADMIN};Pwd=${SQL_PASSWORD};Encrypt=yes;TrustServerCertificate=no;"
az keyvault secret set \
  --vault-name "$KEY_VAULT" \
  --name "azure-sql-connection" \
  --value "$SQL_CONN"

echo "   ✓ SQL Server : ${SQL_SERVER}.database.windows.net"
echo "   ✓ Database   : $SQL_DB"

# ── 5. AZURE BLOB STORAGE (Power BI data source) ──────────────────────────────
echo "💾 Creating Storage Account for Power BI..."
az storage account create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$STORAGE_ACCOUNT" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --kind StorageV2

az storage container create \
  --name "powerbi-data" \
  --account-name "$STORAGE_ACCOUNT" \
  --public-access off

az storage container create \
  --name "analytics-cache" \
  --account-name "$STORAGE_ACCOUNT" \
  --public-access off

STORAGE_CONN=$(az storage account show-connection-string \
  --resource-group "$RESOURCE_GROUP" \
  --name "$STORAGE_ACCOUNT" \
  --query connectionString -o tsv)

az keyvault secret set \
  --vault-name "$KEY_VAULT" \
  --name "azure-storage-connection" \
  --value "$STORAGE_CONN"

echo "   ✓ Storage    : $STORAGE_ACCOUNT"

# ── 6. APP SERVICE PLAN ───────────────────────────────────────────────────────
echo "⚙️  Creating App Service Plan..."
az appservice plan create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_SERVICE_PLAN" \
  --location "$LOCATION" \
  --sku B2 \
  --is-linux

# ── 7. AZURE APP SERVICE (Web App for Containers) ────────────────────────────
echo "🌐 Deploying App Service..."
az webapp create \
  --resource-group "$RESOURCE_GROUP" \
  --plan "$APP_SERVICE_PLAN" \
  --name "$APP_NAME" \
  --deployment-container-image-name "mcr.microsoft.com/appsvc/staticsite:latest"

# Configure app settings
az webapp config appsettings set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --settings \
    WEBSITES_PORT=8000 \
    ENVIRONMENT=production \
    KEY_VAULT_URI="https://${KEY_VAULT}.vault.azure.net/"

# Enable managed identity for Key Vault access
IDENTITY=$(az webapp identity assign \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --query principalId -o tsv)

# Grant Key Vault access to managed identity
az keyvault set-policy \
  --name "$KEY_VAULT" \
  --object-id "$IDENTITY" \
  --secret-permissions get list

# Enable logging
az webapp log config \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --docker-container-logging filesystem \
  --level information

echo ""
echo "✅ Azure infrastructure provisioned!"
echo ""
echo "📋 Summary:"
echo "   App URL      : https://${APP_NAME}.azurewebsites.net"
echo "   SQL Server   : ${SQL_SERVER}.database.windows.net"
echo "   Storage      : ${STORAGE_ACCOUNT}.blob.core.windows.net"
echo "   Key Vault    : ${KEY_VAULT}.vault.azure.net"
echo ""
echo "🔐 Next steps:"
echo "   1. Add AZURE_CREDENTIALS to GitHub Secrets"
echo "   2. Add POWER_BI_WORKSPACE_ID and POWER_BI_REPORT_ID to GitHub Secrets"
echo "   3. Push to main branch to trigger deployment"
echo "   4. Connect Power BI Desktop to Azure SQL using the connection string"
echo ""
echo "💡 Power BI connection string saved in Key Vault: azure-sql-connection"
