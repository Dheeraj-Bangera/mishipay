from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from extensions import db,redis_client
from config import Config
import csv
import json
from io import StringIO

def create_app(config_class=Config):

    app = Flask(__name__)
    

    app.config.from_object(config_class)


    db.init_app(app)


    @app.route('/', methods=['GET'])
    def home():
        return jsonify({"message": "Hello, world!"})

    @app.route('/ingest', methods=['POST'])
    def ingest_data():
        if 'file' not in request.files:
            return jsonify({"ok": False, "error": {"message": "No file provided"}}), 400

        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({"ok": False, "error": {"message": "Invalid file format. Please upload a CSV file."}}), 400

        file_stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(file_stream)
        

        reader.fieldnames = [header.strip() for header in reader.fieldnames]
        
        required_headers = ["username", "mac_address", "start_time", "usage_time", "upload", "download"]
        if not all(header in reader.fieldnames for header in required_headers):
            return jsonify({"ok": False, "error": {"message": "Missing required headers"}}), 400

        from models import UserAnalytics 
        
        records = []
        for row in reader:
            try:
                record = UserAnalytics(
                    username=row['username'].strip(),
                    mac_address=row['mac_address'].strip(),
                    start_time=datetime.strptime(row['start_time'].strip(), '%Y-%m-%d %H:%M:%S'),
                    usage_time=timedelta(hours=int(row['usage_time'].split(":")[0]),
                                       minutes=int(row['usage_time'].split(":")[1]),
                                       seconds=int(row['usage_time'].split(":")[2])),
                    upload=float(row['upload'].strip()),
                    download=float(row['download'].strip())
                )
                records.append(record)
            except Exception as e:
                return jsonify({"ok": False, "error": {"message": f"Data format issue: {str(e)}"}}), 400

        try:
            db.session.bulk_save_objects(records)
            db.session.commit()
            return jsonify({"ok": True, "message": "Data ingested successfully!"}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"ok": False, "error": {"message": f"Database error: {str(e)}"}}), 500


    def format_time_duration(seconds):
        if seconds is None:
            return "0s"
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s" if hours > 0 else f"{minutes}m {seconds}s"

    @app.route('/analytics', methods=['GET'])
    def get_top_users():
        try:
            date_str = request.args.get('date')
            if not date_str:
                return jsonify({"ok": False, "error": {"message": "date parameter is required"}}), 400
                    
            try:
                date = datetime.strptime(date_str, '%d%m%Y')
                if date > datetime.now():
                    return jsonify({"ok": False, "error": {"message": "invalid date"}}), 422
            except ValueError:
                return jsonify({"ok": False, "error": {"message": "invalid date format"}}), 400

            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('pageSize', 100))

            # Check Redis cache first
            cache_key = f"analytics:{date_str}:{page}:{page_size}"
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return jsonify(json.loads(cached_data))

            from models import UserAnalytics 

            day_start = date - timedelta(days=1)
            week_start = date - timedelta(days=7)
            month_start = date - timedelta(days=30)

            results = db.session.query(
                UserAnalytics.username,
                db.func.sum(
                    db.case(
                        (UserAnalytics.start_time >= day_start, 
                        db.func.extract('epoch', UserAnalytics.usage_time)),
                        else_=0
                    )
                ).label('day_time'),
                db.func.sum(
                    db.case(
                        (UserAnalytics.start_time >= week_start, 
                        db.func.extract('epoch', UserAnalytics.usage_time)),
                        else_=0
                    )
                ).label('week_time'),
                db.func.sum(
                    db.case(
                        (UserAnalytics.start_time >= month_start, 
                        db.func.extract('epoch', UserAnalytics.usage_time)),
                        else_=0
                    )
                ).label('month_time')
            ).filter(
                UserAnalytics.start_time >= month_start
            ).group_by(
                UserAnalytics.username
            ).order_by(
                db.desc('month_time')
            ).paginate(page=page, per_page=page_size, error_out=False)

            response_data = []
            for result in results.items:
                response_data.append({
                    "username": result.username,
                    "lastDayUsage": format_time_duration(result.day_time),
                    "last7DayUsage": format_time_duration(result.week_time),
                    "last30DayUsage": format_time_duration(result.month_time)
                })

            response = {
                "ok": True,
                "data": response_data,
                "pageSize": page_size,
                "page": page,
                "totalPages": results.pages
            }

            redis_client.set(cache_key, json.dumps(response), ex=3600)  # Cache for 1 hour

            return jsonify(response)

        except Exception as e:
            return jsonify({"ok": False, "error": {"message": str(e)}}), 500

    @app.route('/user/search', methods=['GET'])
    def get_user_details():
        try:
            from models import UserAnalytics
            username = request.args.get('username')
            datetime_str = request.args.get('datetime')

            if not username or not datetime_str:
                return jsonify({"ok": False, "error": {"message": "username and datetime are required"}}), 400

            try:
                datetime_obj = datetime.strptime(datetime_str, '%Y%m%dT%H%M')
            except ValueError:
                return jsonify({"ok": False, "error": {"message": "Invalid datetime format"}}), 400

            cache_key = f"user:{username}:search:{datetime_str}"
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return jsonify(json.loads(cached_data))

            hour_ago = datetime_obj - timedelta(hours=1)
            six_hours_ago = datetime_obj - timedelta(hours=6)
            day_ago = datetime_obj - timedelta(hours=24)

            # Query the database using the datetime object
            result = db.session.query(
                UserAnalytics.username,
                db.func.sum(
                    db.case(
                        (UserAnalytics.start_time >= hour_ago, UserAnalytics.usage_time),
                        else_=timedelta(0)
                    )
                ).label('hour_time'),
                db.func.sum(
                    db.case(
                        (UserAnalytics.start_time >= hour_ago, UserAnalytics.upload),
                        else_=0
                    )
                ).label('hour_upload'),
                db.func.sum(
                    db.case(
                        (UserAnalytics.start_time >= hour_ago, UserAnalytics.download),
                        else_=0
                    )
                ).label('hour_download'),
                db.func.sum(
                    db.case(
                        (UserAnalytics.start_time >= six_hours_ago, UserAnalytics.usage_time),
                        else_=timedelta(0)
                    )
                ).label('six_hour_time'),
                db.func.sum(
                    db.case(
                        (UserAnalytics.start_time >= six_hours_ago, UserAnalytics.upload),
                        else_=0
                    )
                ).label('six_hour_upload'),
                db.func.sum(
                    db.case(
                        (UserAnalytics.start_time >= six_hours_ago, UserAnalytics.download),
                        else_=0
                    )
                ).label('six_hour_download'),
                db.func.sum(
                    db.case(
                        (UserAnalytics.start_time >= day_ago, UserAnalytics.usage_time),
                        else_=timedelta(0)
                    )
                ).label('day_time'),
                db.func.sum(
                    db.case(
                        (UserAnalytics.start_time >= day_ago, UserAnalytics.upload),
                        else_=0
                    )
                ).label('day_upload'),
                db.func.sum(
                    db.case(
                        (UserAnalytics.start_time >= day_ago, UserAnalytics.download),
                        else_=0
                    )
                ).label('day_download')
            ).filter(
                UserAnalytics.username == username
            ).group_by(
                UserAnalytics.username
            ).first()

            if not result:
                return jsonify({"ok": False, "error": {"message": "user not found"}}), 404

            def format_data_size(size):
                if size is None:
                    return "0B"
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if size < 1024.0:
                        return f"{size:.2f}{unit}"
                    size /= 1024.0

            response = {
                "ok": True,
                "data": {
                    "username": username,
                    "lastHourUsage": {
                        "time": format_time_duration(result.hour_time.total_seconds() if result.hour_time else 0),
                        "upload": format_data_size(result.hour_upload),
                        "download": format_data_size(result.hour_download)
                    },
                    "last6HourUsage": {
                        "time": format_time_duration(result.six_hour_time.total_seconds() if result.six_hour_time else 0),
                        "upload": format_data_size(result.six_hour_upload),
                        "download": format_data_size(result.six_hour_download)
                    },
                    "last24HourUsage": {
                        "time": format_time_duration(result.day_time.total_seconds() if result.day_time else 0),
                        "upload": format_data_size(result.day_upload),
                        "download": format_data_size(result.day_download)
                    }
                }
            }

            # Cache the result in Redis for future requests
            redis_client.set(cache_key, json.dumps(response), ex=3600)  # Cache for 1 hour

            return jsonify(response)

        except Exception as e:
            return jsonify({"ok": False, "error": {"message": str(e)}}), 500

    return app
