# MongoDB Index Auto-Deployment

Automated GitHub Actions pipeline for deploying MongoDB indexes using mongosh-compatible JavaScript files. All operations are properly logged with comprehensive error handling.

## Features

- **Automated Deployment**: Automatically deploys index changes when pushed to the main branch
- **Mongosh Compatible**: Uses MongoDB Shell (mongosh) JavaScript files for full flexibility
- **Comprehensive Logging**: Detailed logs for all operations and errors stored in `deployment_logs/`
- **Secure Credentials**: Connection string stored as GitHub secret
- **Validation**: JavaScript syntax validation before deployment
- **Manual Trigger**: Option to manually trigger deployments from GitHub Actions
- **Log Artifacts**: Deployment logs uploaded as artifacts for 30 days

## Architecture

```
indexes_to_deploy/
  ├── 01_users_indexes.js      # Executed first (alphabetical order)
  ├── 02_products_indexes.js   # Executed second
  └── 03_orders_indexes.js     # Executed third
```

Scripts are executed in alphabetical order using `mongosh`, allowing you to control execution sequence by naming your files appropriately.

## Setup

### 1. Add MongoDB Connection String Secret

1. Go to your GitHub repository settings
2. Navigate to **Settings > Secrets and variables > Actions**
3. Click **New repository secret**
4. Add a secret with:
   - **Name**: `MONGODB_CONNECTION_STRING`
   - **Value**: Your MongoDB connection string
     ```
     mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
     ```

### 2. Create Your Index Scripts

Create JavaScript files in the `indexes_to_deploy/` directory. These files are standard mongosh scripts:

**Example: `indexes_to_deploy/users_indexes.js`**

```javascript
// Switch to your database
db = db.getSiblingDB('myapp_db');

// Create indexes on users collection
print('Creating indexes for users collection...');

db.users.createIndex(
  { email: 1 },
  {
    name: 'email_1',
    unique: true,
    background: true
  }
);
print('✓ Created email_1 index on users');

db.users.createIndex(
  { status: 1, createdAt: -1 },
  {
    name: 'status_1_createdAt_-1',
    background: true
  }
);
print('✓ Created status_1_createdAt_-1 compound index on users');

print('User indexes deployed successfully!');
```

### 3. Push Changes

```bash
git add indexes_to_deploy/
git commit -m "Add user indexes"
git push origin main
```

The GitHub Action will automatically deploy the changes to your MongoDB cluster.

## Mongosh Script Examples

### Create a Simple Index

```javascript
db = db.getSiblingDB('myapp_db');

db.products.createIndex(
  { sku: 1 },
  { name: 'sku_1', unique: true, background: true }
);
```

### Create a Compound Index

```javascript
db = db.getSiblingDB('myapp_db');

db.orders.createIndex(
  { userId: 1, createdAt: -1 },
  { name: 'userId_1_createdAt_-1', background: true }
);
```

### Create a Text Search Index

```javascript
db = db.getSiblingDB('myapp_db');

db.products.createIndex(
  { name: 'text', description: 'text' },
  {
    name: 'product_text_search',
    background: true,
    weights: { name: 2, description: 1 }
  }
);
```

### Create a TTL Index

```javascript
db = db.getSiblingDB('myapp_db');

// Documents will be automatically deleted after 30 days
db.sessions.createIndex(
  { createdAt: 1 },
  {
    name: 'createdAt_ttl',
    expireAfterSeconds: 2592000,  // 30 days
    background: true
  }
);
```

### Create a Partial Index

```javascript
db = db.getSiblingDB('myapp_db');

db.users.createIndex(
  { email: 1 },
  {
    name: 'active_users_email',
    unique: true,
    background: true,
    partialFilterExpression: { status: 'active' }
  }
);
```

### Drop an Index

```javascript
db = db.getSiblingDB('myapp_db');

try {
  db.users.dropIndex('old_index_name');
  print('✓ Dropped old_index_name from users');
} catch (e) {
  print('Note: old_index_name does not exist or already dropped');
}
```

### Create Geospatial Index

```javascript
db = db.getSiblingDB('myapp_db');

db.locations.createIndex(
  { coordinates: '2dsphere' },
  { name: 'coordinates_2dsphere', background: true }
);
```

### Create Wildcard Index

```javascript
db = db.getSiblingDB('myapp_db');

db.products.createIndex(
  { 'attributes.$**': 1 },
  { name: 'attributes_wildcard', background: true }
);
```

## Index Options Reference

| Option | Type | Description |
|--------|------|-------------|
| `name` | string | Name of the index (required) |
| `unique` | boolean | Ensure unique values |
| `background` | boolean | Build index in background (recommended) |
| `sparse` | boolean | Only index documents with the field |
| `expireAfterSeconds` | integer | TTL for automatic document deletion |
| `partialFilterExpression` | object | Partial index filter |
| `weights` | object | Text search field weights |
| `collation` | object | Collation specification |

Full reference: [MongoDB Index Options](https://www.mongodb.com/docs/manual/reference/method/db.collection.createIndex/#options)

## Workflow Triggers

The deployment workflow is triggered **ONLY** by changes in the `indexes_to_deploy/` folder:

1. **Push to main**: Automatically deploys when any file in `indexes_to_deploy/` is modified
2. **Manual Dispatch**: Trigger manually from GitHub Actions tab

**Note**: Changes to `deploy_indexes.py`, `README.md`, or other files will NOT trigger the workflow automatically.

## Workflow Jobs

### 1. Validate

Validates the JavaScript files:
- Checks that `indexes_to_deploy/` directory exists
- Verifies `.js` files are present
- Validates JavaScript syntax using Node.js
- Runs before deployment

### 2. Deploy

Deploys indexes to MongoDB:
- Installs MongoDB Shell (mongosh)
- Connects to MongoDB using the secret connection string
- Executes all `.js` files in alphabetical order
- Uploads deployment logs as artifacts (30 days retention)

## Local Testing

### Prerequisites

Install MongoDB Shell (mongosh):

**macOS (Homebrew)**
```bash
brew install mongosh
```

**Linux (Ubuntu/Debian)**
```bash
wget -qO- https://www.mongodb.org/static/pgp/server-7.0.asc | sudo tee /etc/apt/trusted.gpg.d/server-7.0.asc
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-mongosh
```

**Windows**
Download from: https://www.mongodb.com/try/download/shell

### Set Environment Variables

```bash
export MONGODB_CONNECTION_STRING="mongodb+srv://username:password@cluster.mongodb.net/"
export INDEXES_DIRECTORY="indexes_to_deploy"
```

### Run the Script

```bash
python deploy_indexes.py
```

### Test Individual Script

You can also test individual scripts directly with mongosh:

```bash
mongosh "your-connection-string" --file indexes_to_deploy/your_script.js
```

### Check Logs

Deployment logs are saved to `deployment_logs/index_deployment_YYYYMMDD_HHMMSS.log`

## Script Execution Order

Scripts in `indexes_to_deploy/` are executed in **alphabetical order**. Use prefixes to control execution sequence:

```
indexes_to_deploy/
  ├── 01_create_base_indexes.js
  ├── 02_create_search_indexes.js
  ├── 03_create_analytics_indexes.js
  └── 99_cleanup_old_indexes.js
```

## Error Handling

The deployment script provides comprehensive error handling:

- **Connection Failures**: Logs connection errors and exits with status code 1
- **Syntax Errors**: JavaScript syntax validated before execution
- **Execution Errors**: Each script's errors are logged; deployment continues
- **Timeouts**: Scripts timeout after 5 minutes to prevent hanging
- **Summary Report**: Shows count of successful and failed scripts

## Monitoring and Troubleshooting

### View Workflow Runs

1. Go to the **Actions** tab in your GitHub repository
2. Click on the latest workflow run
3. Review logs for each job

### Download Logs

Deployment logs are uploaded as artifacts:

1. Go to the workflow run
2. Scroll to the **Artifacts** section
3. Download `deployment-logs-{run_number}`

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `MONGODB_CONNECTION_STRING environment variable is not set` | Secret not configured | Add the secret in repository settings |
| `Failed to connect to MongoDB` | Invalid connection string or network issue | Verify connection string and cluster accessibility |
| `indexes_to_deploy directory not found` | Missing directory | Create the directory and add `.js` files |
| `No .js files found` | No scripts in directory | Add at least one `.js` file |
| `mongosh is not installed` | MongoDB Shell not found | Install mongosh (done automatically in GitHub Actions) |

### Debug Mode

To see detailed debug information, modify the logging level in [deploy_indexes.py:26](deploy_indexes.py#L26):

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    # ...
)
```

### Log Files

All deployment logs are automatically saved to the `deployment_logs/` directory:
- Local deployments: `deployment_logs/index_deployment_YYYYMMDD_HHMMSS.log`
- GitHub Actions: Uploaded as workflow artifacts

## Security Best Practices

1. **Never commit credentials**: Always use GitHub secrets for connection strings
2. **Use read-write user**: Ensure MongoDB user has appropriate permissions for index operations
3. **Restrict network access**: Configure MongoDB network access lists
4. **Review changes carefully**: Always review index changes before merging to main
5. **Monitor deployments**: Check logs after each deployment
6. **Use TLS/SSL**: Ensure connection string uses `mongodb+srv://` or has TLS enabled
7. **Principle of least privilege**: MongoDB user should only have index creation permissions

## Manual Deployment

To manually trigger a deployment:

1. Go to **Actions** tab
2. Select **Deploy MongoDB Indexes** workflow
3. Click **Run workflow**
4. Choose branch
5. Click **Run workflow** button

## Rollback Strategy

To rollback index changes:

1. Create a new script to drop the problematic indexes
2. Commit and push to main, or
3. Connect directly to MongoDB and drop indexes manually:

```javascript
db = db.getSiblingDB('myapp_db');
db.collection.dropIndex('index_name');
```

## Best Practices

1. **Use background indexes**: Always include `background: true` to avoid blocking operations
2. **Test locally first**: Run scripts locally before committing
3. **Name your indexes**: Always specify explicit `name` option
4. **Add logging**: Include `print()` statements for visibility
5. **Handle errors**: Use try-catch blocks for drop operations
6. **Sequential naming**: Use numeric prefixes (01_, 02_, etc.) to control execution order
7. **One concern per file**: Separate indexes by collection or feature
8. **Document your indexes**: Add comments explaining why indexes exist

## Example: Complete Deployment Script

```javascript
// File: indexes_to_deploy/01_users_and_products.js
// Purpose: Create core indexes for users and products collections
// Author: DevOps Team
// Date: 2025-01-15

// Switch to production database
db = db.getSiblingDB('production_db');

print('========================================');
print('Deploying indexes for production_db');
print('========================================');

// Users Collection
print('\n[Users Collection]');

try {
  db.users.createIndex(
    { email: 1 },
    { name: 'email_1', unique: true, background: true }
  );
  print('✓ Created email_1 index');
} catch (e) {
  print('✗ Failed to create email_1 index:', e.message);
}

try {
  db.users.createIndex(
    { status: 1, lastLoginAt: -1 },
    { name: 'status_1_lastLoginAt_-1', background: true }
  );
  print('✓ Created status_1_lastLoginAt_-1 index');
} catch (e) {
  print('✗ Failed to create status_1_lastLoginAt_-1 index:', e.message);
}

// Products Collection
print('\n[Products Collection]');

try {
  db.products.createIndex(
    { sku: 1 },
    { name: 'sku_1', unique: true, background: true }
  );
  print('✓ Created sku_1 index');
} catch (e) {
  print('✗ Failed to create sku_1 index:', e.message);
}

try {
  db.products.createIndex(
    { category: 1, price: -1 },
    { name: 'category_1_price_-1', background: true }
  );
  print('✓ Created category_1_price_-1 index');
} catch (e) {
  print('✗ Failed to create category_1_price_-1 index:', e.message);
}

print('\n========================================');
print('Index deployment completed');
print('========================================');
```

## Contributing

1. Create a feature branch
2. Add or modify scripts in `indexes_to_deploy/`
3. Test locally with your MongoDB connection
4. Create a pull request
5. Merge to main to deploy

## License

See [LICENSE](LICENSE) file for details.

## Support

For issues or questions:
- Check the [troubleshooting section](#monitoring-and-troubleshooting)
- Review deployment logs in GitHub Actions artifacts
- Open an issue in this repository
