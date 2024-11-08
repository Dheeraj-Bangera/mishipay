from app import db
from models import UserAnalytics
from datetime import datetime, timedelta

# Sample data
data = {
    "username": "brainyHeron5",
    "mac_address": "74:73:4E:09:DE:6F",
    "start_time": "2022-11-04 15:43:33",
    "usage_time": "4:50:20",  # 4 hours, 50 minutes, 20 seconds
    "upload": 3512752.28,
    "download": 7462017.97
}

# Parse usage_time into a timedelta object
hours, minutes, seconds = map(int, data["usage_time"].split(":"))
usage_duration = timedelta(hours=hours, minutes=minutes, seconds=seconds)

# Parse start_time into datetime
start_time = datetime.strptime(data["start_time"], "%Y-%m-%d %H:%M:%S")

# Create a new record
new_record = UserAnalytics(
    username=data["username"],
    mac_address=data["mac_address"],
    start_time=start_time,
    usage_time=usage_duration,
    upload=data["upload"],
    download=data["download"]
)

# Add to the database
db.session.add(new_record)
db.session.commit()
print("Data ingested successfully!")
