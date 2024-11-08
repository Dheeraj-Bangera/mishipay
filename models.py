from extensions import db

class UserAnalytics(db.Model):
    __tablename__ = 'user_analytics'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    mac_address = db.Column(db.String, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    usage_time = db.Column(db.Interval, nullable=False)   
    upload = db.Column(db.Float, nullable=False)          
    download = db.Column(db.Float, nullable=False)        
