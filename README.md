# User Analytics System
# Optimized Approach

### 1.Pre-Aggregated Data Approach (Not Scalable)
This approach is based on pre-aggregating user data, specifically the top user statistics for any given date. For each user, we calculate their usage for the past 30 days, 7 days, and 1 day before a given day. This meant storing aggregated values for each user and each date, which would require creating a record for every day.

For example, with 998 users, storing pre-aggregated data for one year would require `998 * 365 = 364,270` rows. This number jumps up to `1,059,960` in our case since the oldest data is of 2022.
### 2.Redis Caching for Efficient Query Handling
To overcome the inefficiency of storing pre-aggregated data, I have  implemented Redis caching to store the results of frequently requested queries and return them directly without the need for re-computation. Redis, being an in-memory data store, allows fast access to frequently used data, improving response times significantly.

For analytics data, we store the results as a key-value pair in Redis using the format:
```bash
analytics:{date_str}:{page}:{page_size}
```
Where date_str is the specific date of the query, page refers to the page number for pagination, and page_size is the number of results to return per page. This allows us to quickly retrieve the cached result for any given analytics query.

For user search queries, we use the following cache key format:
```bash
user:{username}:search:{datetime_str}
```
Here, username refers to the user's name and datetime_str represents the timestamp when the search was performed. By caching these results, we can quickly return the search results for the user, improving both the user experience and system performance.



## Setup Steps
1. Clone the repository:
```bash
git clone https://github.com/your-repo/user-analytics.git
cd user-analytics
```

2. Start the application:
```bash
docker-compose up --build
```

The application will be available at `http://localhost:5001`
## Testing the API

To run tests and ensure the API is functioning correctly, use the following command to execute the test suite in a Docker container.

### Run Tests
```bash
docker-compose run test
```
# User Analytics System
# Optimized Approach

### 1.Pre-Aggregated Data Approach (Not Scalable)
This approach is based on pre-aggregating user data, specifically the top user statistics for any given date. For each user, we calculate their usage for the past 30 days, 7 days, and 1 day before a given day. This meant storing aggregated values for each user and each date, which would require creating a record for every day.

For example, with 998 users, storing pre-aggregated data for one year would require `998 * 365 = 364,270` rows. This number jumps up to `1,059,960` in our case since the oldest data is of 2022.
### 2.Redis Caching for Efficient Query Handling
To overcome the inefficiency of storing pre-aggregated data, I have  implemented Redis caching to store the results of frequently requested queries and return them directly without the need for re-computation. Redis, being an in-memory data store, allows fast access to frequently used data, improving response times significantly.

For analytics data, we store the results as a key-value pair in Redis using the format:
```bash
analytics:{date_str}:{page}:{page_size}
```
Where date_str is the specific date of the query, page refers to the page number for pagination, and page_size is the number of results to return per page. This allows us to quickly retrieve the cached result for any given analytics query.

For user search queries, we use the following cache key format:
```bash
user:{username}:search:{datetime_str}
```
Here, username refers to the user's name and datetime_str represents the timestamp when the search was performed. By caching these results, we can quickly return the search results for the user, improving both the user experience and system performance.



## Setup Steps
1. Clone the repository:
```bash
git clone https://github.com/your-repo/user-analytics.git
cd user-analytics
```

2. Start the application:
```bash
docker-compose up --build
```

The application will be available at `http://localhost:5001`
## Testing the API

To run tests and ensure the API is functioning correctly, use the following command to execute the test suite in a Docker container.

### Run Tests
```bash
docker-compose run test
```
This command will execute the tests defined for the API written in the `test.py` inside tests directory

### Expected Output
Upon successful execution, the test suite should complete without errors. 
![image](https://github.com/user-attachments/assets/6152cb2d-11dc-48ec-8f86-0d56b8817635)

## API Documentation
### Postman Collection
[![Run in Postman](https://run.pstmn.io/button.svg)](https://documenter.getpostman.com/view/27028215/2sAY52eLXd)
### 1. Ingest User Data
Upload CSV file containing user analytics data.

**Endpoint:** `/ingest`  
**Method:** POST  
**Content-Type:** multipart/form-data

#### CSV Requirements
Headers:
- username
- mac_address
- start_time (format: YYYY-MM-DD HH:MM:SS)
- usage_time (format: HH:MM:SS)
- upload (kilobits)
- download (kilobits)

#### Request Example
```bash
curl -X POST -F "file=@data.csv" http://localhost:5001/ingest
```

#### Success Response
```json
{
    "ok": true,
    "message": "Data ingested successfully!"
}
```

#### Error Response
```json
{
    "ok": false,
    "error": {
        "message": "Error description"
    }
}
```

### 2. Get User Analytics
Get usage statistics for all users.

**Endpoint:** `/analytics`  
**Method:** GET  

#### Parameters
- date (required): DDMMYYYY
- page (optional): Integer, default 1
- pageSize (optional): Integer, default 100

#### Request Example
```bash
curl "http://localhost:5001/analytics?date=11112024&page=1&pageSize=100"
```

#### Success Response
```json
{
    "ok": true,
    "data": [
        {
            "username": "user1",
            "lastDayUsage": "05h30m",
            "last7DayUsage": "35h45m",
            "last30DayUsage": "125h20m"
        }
    ],
    "pageSize": 100,
    "page": 1,
    "totalPages": 5
}
```

### 3. Search User Details
Get detailed usage statistics for a specific user.

**Endpoint:** `/user/search`  
**Method:** GET  

#### Parameters
- username (required): String
- datetime (required): YYYYMMDDTHHmm

#### Request Example
```bash
curl "http://localhost:5001/user/search?username=user1&datetime=202401011200"
```

#### Success Response
```json
{
    "ok": true,
    "data": {
        "username": "user1",
        "lastHourUsage": {
            "time": "00h45m",
            "upload": "1.2GB",
            "download": "2.5GB"
        },
        "last6HourUsage": {
            "time": "03h15m",
            "upload": "5.8GB",
            "download": "12.3GB"
        },
        "last24HourUsage": {
            "time": "08h30m",
            "upload": "15.2GB",
            "download": "45.7GB"
        }
    }
}
```

## Response Formats

### Time Duration Format
Times are shown as "HHhMMm":
- HH: Hours (two digits)
- MM: Minutes (two digits)
Example: "05h30m" = 5 hours and 30 minutes

### Data Size Format
Data sizes automatically use appropriate units:
- MB: < 1 GB
- GB: 1 GB to 1 TB
- TB: ≥ 1 TB
Example: "1.2GB", "800.0MB", "2.3TB"

## Error Codes
- 200: Success
- 201: Created (successful ingestion)
- 400: Bad Request
- 404: Not Found
- 422: Invalid date
- 500: Internal Server Error

All errors follow this format:
```json
{
    "ok": false,
    "error": {
        "message": "Error description"
    }
}
```

## API Documentation
### Postman Collection
[![Run in Postman](https://run.pstmn.io/button.svg)](https://documenter.getpostman.com/view/27028215/2sAY52eLXd)
### 1. Ingest User Data
Upload CSV file containing user analytics data.

**Endpoint:** `/ingest`  
**Method:** POST  
**Content-Type:** multipart/form-data

#### CSV Requirements
Headers:
- username
- mac_address
- start_time (format: YYYY-MM-DD HH:MM:SS)
- usage_time (format: HH:MM:SS)
- upload (kilobits)
- download (kilobits)

#### Request Example
```bash
curl -X POST -F "file=@data.csv" http://localhost:5001/ingest
```

#### Success Response
```json
{
    "ok": true,
    "message": "Data ingested successfully!"
}
```

#### Error Response
```json
{
    "ok": false,
    "error": {
        "message": "Error description"
    }
}
```

### 2. Get User Analytics
Get usage statistics for all users.

**Endpoint:** `/analytics`  
**Method:** GET  

#### Parameters
- date (required): DDMMYYYY
- page (optional): Integer, default 1
- pageSize (optional): Integer, default 100

#### Request Example
```bash
curl "http://localhost:5001/analytics?date=11112024&page=1&pageSize=100"
```

#### Success Response
```json
{
    "ok": true,
    "data": [
        {
            "username": "user1",
            "lastDayUsage": "05h30m",
            "last7DayUsage": "35h45m",
            "last30DayUsage": "125h20m"
        }
    ],
    "pageSize": 100,
    "page": 1,
    "totalPages": 5
}
```

### 3. Search User Details
Get detailed usage statistics for a specific user.

**Endpoint:** `/user/search`  
**Method:** GET  

#### Parameters
- username (required): String
- datetime (required): YYYYMMDDTHHmm

#### Request Example
```bash
curl "http://localhost:5001/user/search?username=user1&datetime=202401011200"
```

#### Success Response
```json
{
    "ok": true,
    "data": {
        "username": "user1",
        "lastHourUsage": {
            "time": "00h45m",
            "upload": "1.2GB",
            "download": "2.5GB"
        },
        "last6HourUsage": {
            "time": "03h15m",
            "upload": "5.8GB",
            "download": "12.3GB"
        },
        "last24HourUsage": {
            "time": "08h30m",
            "upload": "15.2GB",
            "download": "45.7GB"
        }
    }
}
```

## Response Formats

### Time Duration Format
Times are shown as "HHhMMm":
- HH: Hours (two digits)
- MM: Minutes (two digits)
Example: "05h30m" = 5 hours and 30 minutes

### Data Size Format
Data sizes automatically use appropriate units:
- MB: < 1 GB
- GB: 1 GB to 1 TB
- TB: ≥ 1 TB
Example: "1.2GB", "800.0MB", "2.3TB"

## Error Codes
- 200: Success
- 201: Created (successful ingestion)
- 400: Bad Request
- 404: Not Found
- 422: Invalid date
- 500: Internal Server Error

All errors follow this format:
```json
{
    "ok": false,
    "error": {
        "message": "Error description"
    }
}
```
