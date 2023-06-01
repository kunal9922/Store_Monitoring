import csv
from datetime import datetime, timedelta
from pytz import timezone
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from models import Config
from models import StoreStatus, StoreHours, StoreTimezone

# Set up the database connection
config = Config()
engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

class Report(Base):
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True)
    report_id = Column(String(255), nullable=False, unique=True)
    status = Column(String(50), nullable=False)
    data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() + 'Z',
            'completed_at': self.completed_at.isoformat() + 'Z' if self.completed_at else None
        }

    def generate_report(self):
        # Get the current timestamp
        max_timestamp = session.query(StoreStatus).order_by(StoreStatus.timestamp_utc.desc()).first().timestamp_utc
        current_timestamp = datetime.now(tz=timezone('UTC')) if not max_timestamp else max_timestamp

        # Get the business hours for each store
        store_hours = session.query(StoreHours).all()

        # Calculate uptime and downtime for each store
        report_data = []
        for store_hour in store_hours:
            store_id = store_hour.store_id
            day_of_week = store_hour.day_of_week
            start_time_local = store_hour.start_time_local
            end_time_local = store_hour.end_time_local

            # Filter store status records within business hours
            store_status_records = session.query(StoreStatus).filter(
                StoreStatus.store_id == store_id,
                StoreStatus.timestamp_utc >= current_timestamp - timedelta(days=7),  # Consider last week's data
                StoreStatus.status.in_(['active', 'inactive'])
            ).all()

            # Interpolate uptime and downtime based on available observations
            interpolated_records = interpolate_store_status_records(store_status_records, start_time_local,
                                                                    end_time_local, current_timestamp)

            # Calculate uptime and downtime for the last hour, last day, and last week
            uptime_last_hour = calculate_uptime_last_hour(interpolated_records, current_timestamp)
            downtime_last_hour = calculate_downtime_last_hour(interpolated_records, current_timestamp)
            uptime_last_day = calculate_uptime_last_day(interpolated_records, current_timestamp)
            downtime_last_day = calculate_downtime_last_day(interpolated_records, current_timestamp)
            uptime_last_week = calculate_uptime_last_week(interpolated_records, current_timestamp)
            downtime_last_week = calculate_downtime_last_week(interpolated_records, current_timestamp)

            # Append the store data to the report
            report_data.append({
                'store_id': store_id,
                'uptime_last_hour': uptime_last_hour,
                'downtime_last_hour': downtime_last_hour,
                'uptime_last_day': uptime_last_day,
                'downtime_last_day': downtime_last_day,
                'uptime_last_week': uptime_last_week,
                'downtime_last_week': downtime_last_week
            })

        # Update the report data and mark the report as complete
        self.data = report_data
        self.status = 'Complete'
        self.completed_at = datetime.utcnow()
        session.commit()


