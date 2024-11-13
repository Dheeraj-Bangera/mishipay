# User Analytics System

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
