from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from extensions import db  # Import db from extensions
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialize SQLAlchemy with the app
db.init_app(app)

# Import models after db is initialized to avoid circular import
with app.app_context():
    from models import UserAnalytics

# Route for analytics data (list top users)
@app.route('/analytics', methods=['GET'])
def get_top_users():
    date_str = request.args.get('date')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 10))
    
    date = datetime.strptime(date_str, '%d%m%Y')
    day_start = date - timedelta(days=1)
    week_start = date - timedelta(days=7)
    month_start = date - timedelta(days=30)

    users = db.session.query(
        UserAnalytics.username,
        db.func.sum(UserAnalytics.upload + UserAnalytics.download).label('last30DayUsage'),
        db.func.sum(db.case([(UserAnalytics.start_time >= day_start, UserAnalytics.upload + UserAnalytics.download)], else_=0)).label('lastDayUsage'),
        db.func.sum(db.case([(UserAnalytics.start_time >= week_start, UserAnalytics.upload + UserAnalytics.download)], else_=0)).label('last7DayUsage')
    ).filter(UserAnalytics.start_time >= month_start).group_by(UserAnalytics.username).order_by(db.desc('last30DayUsage')).paginate(page, page_size, False)

    response = {
        "ok": True,
        "data": [
            {
                "username": user.username,
                "lastDayUsage": user.lastDayUsage,
                "last7DayUsage": user.last7DayUsage,
                "last30DayUsage": user.last30DayUsage
            }
            for user in users.items
        ],
        "pageSize": page_size,
        "page": page,
        "totalPages": users.pages
    }
    return jsonify(response)

# Route to get user details by username and time
@app.route('/user/search', methods=['GET'])
def get_user_details():
    username = request.args.get('username')
    datetime_str = request.args.get('datetime')
    datetime_obj = datetime.strptime(datetime_str, '%Y%m%dT%H%M')

    user_data = db.session.query(
        db.func.sum(UserAnalytics.upload + UserAnalytics.download).label('totalUsage'),
        db.func.sum(db.case([(UserAnalytics.start_time >= datetime_obj - timedelta(hours=1), UserAnalytics.upload)], else_=0)).label('lastHourUpload'),
        db.func.sum(db.case([(UserAnalytics.start_time >= datetime_obj - timedelta(hours=6), UserAnalytics.upload)], else_=0)).label('last6HoursUpload')
    ).filter(UserAnalytics.username == username).one_or_none()

    if not user_data:
        return jsonify({"ok": False, "error": {"message": "user not found"}}), 404

    return jsonify({
        "ok": True,
        "data": {
            "username": username,
            "lastHourUsage": {
                "upload": user_data.lastHourUpload,
            },
            "last6HourUsage": {
                "upload": user_data.last6HoursUpload,
            }
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
