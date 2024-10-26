# Maaldar database setup

## Database
To get started, you'll need a PostgreSQL database. You can set up a free PostgreSQL database on a platform like [Neon](https://neon.tech/)  
After setting it up, obtain the connection string, which you'll add to `config.json`. The connection string should look something like this:
```
postgresql://alex:AbC123dEf@ep-cool-darkness-123456.us-east-2.aws.neon.tech/dbname?sslmode=require
             ^    ^         ^                                               ^
       role -|    |         |- hostname                                     |- database
                  |
                  |- password
```

## Tables
The following tables are required for the application to function:
```
1. maaldar
2. maaldarduration
3. maaldarroles
```

### 1. `maaldar`
**Purpose**: Stores all the roles for boosting members.
**Schema**: The required column names and their types are:
```
user_id: text
role_id: text
```

### 2. `maaldarduration`
**Purpose**: Tracks the duration that server members have been boosting.
**Schema**: The required columns and their types are:
```
user_id: text
boosting_since: integer
```

### 3. `maaldarroles`
**Purpose**: Stores the roles for members who have been boosting for 180 days.
**Schema**: The required columns and their types are:
```
user_id: text
role_name: text
role_color: text
```

Create each of the tables above with the specified columns and types.

## Finishing up
If you encounter this warning in the logs after setting up the application:
```
HINT:  No function matches the given name and argument types. You might need to add explicit type casts.
STATEMENT:  SELECT delete_expired_sessions();
```
You can resolve it by running the query in `maaldar_session.sql` located in this directory.
