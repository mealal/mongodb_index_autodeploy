// User Collection Indexes
// Database: production_db
// Collection: users

db = db.getSiblingDB('production_db');

print('========================================');
print('Deploying indexes for users collection');
print('========================================');

// Email index - unique for user authentication
try {
  db.users.createIndex(
    { email: 1 },
    {
      name: 'email_unique_idx',
      unique: true,
      background: true
    }
  );
  print('✓ Created email_unique_idx');
} catch (e) {
  print('Note: email_unique_idx - ' + e.message);
}

// Username index - unique for user profiles
try {
  db.users.createIndex(
    { username: 1 },
    {
      name: 'username_unique_idx',
      unique: true,
      background: true
    }
  );
  print('✓ Created username_unique_idx');
} catch (e) {
  print('Note: username_unique_idx - ' + e.message);
}

// Created date index - for sorting users by registration date
try {
  db.users.createIndex(
    { createdAt: -1 },
    {
      name: 'createdAt_desc_idx',
      background: true
    }
  );
  print('✓ Created createdAt_desc_idx');
} catch (e) {
  print('Note: createdAt_desc_idx - ' + e.message);
}

// Status + LastLogin compound index - for active user queries
try {
  db.users.createIndex(
    { status: 1, lastLoginAt: -1 },
    {
      name: 'status_lastLogin_idx',
      background: true
    }
  );
  print('✓ Created status_lastLogin_idx');
} catch (e) {
  print('Note: status_lastLogin_idx - ' + e.message);
}

print('\n========================================');
print('Users collection indexes deployed');
print('========================================');
