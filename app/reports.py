import json
import csv
from datetime import datetime, timedelta
from pytz import timezone
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from models import Config
from models import StoreStatus, StoreHours, StoreTimezone

# Set up the database connection

config = Config()
# Create an SQLite engine
engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
Base = declarative_base()
# Create a session factory
Session = sessionmaker(bind=engine)

# Create a session
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
          # Get the maximum timestamp from the StoreStatus table
        latest_record = session.query(StoreStatus).order_by(StoreStatus.timestamp_utc.desc()).first()
        max_timestamp = None
        if latest_record is not None:
            max_timestamp = latest_record.timestamp_utc
            min_timestamp = max_timestamp - timedelta(hours=24)
            
            # Query the records within the specified time range
            records = session.query(StoreStatus).filter(StoreStatus.timestamp_utc >= min_timestamp, 
                                                        StoreStatus.timestamp_utc <= max_timestamp).all()

            # Generate the report based on the retrieved records
            # ...
        else:
            # Handle the case when no records are found in the StoreStatus table
            print("No records found in the StoreStatus table.")
            # Get the current timestamp
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
        # Convert the report data to JSON
        report_data_json = json.dumps(report_data)
        # Update the report data and mark the report as complete
        self.data = report_data_json
        self.status = 'Complete'
        self.completed_at = datetime.utcnow()
        
        session.commit()
        return report_data
    
 # Create the reports table if it doesn't exist
Base.metadata.create_all(engine)       

def interpolate_store_status_records(records, start_time_local, end_time_local, current_timestamp):
    interpolated_records = []
    # giving the date format
    date_format = '%H:%M:%S'

    start_time_local = datetime.strptime(start_time_local, date_format)
    end_time_local = datetime.strptime(end_time_local, date_format)
    interval = end_time_local - start_time_local

    # Check if there are any records available for interpolation
    if records:
        for i in range(interval.days + 1):
            # Get the start and end time for the current day
            current_day_start_time = start_time_local + timedelta(days=i)
            current_day_end_time = current_day_start_time + timedelta(days=1)

            # Filter records within the current day
            current_day_records = [record for record in records if
                                   current_day_start_time <= record.timestamp_utc < current_day_end_time]

            # If no records are available for the current day, assume the store was inactive for the entire day
            if not current_day_records:
                interpolated_records.append({
                    'timestamp_utc': current_day_start_time,
                    'status': 'inactive'
                })
            else:
                # Interpolate the status for the missing timestamps within the current day
                previous_record = None
                for j in range(len(current_day_records)):
                    record = current_day_records[j]

                    # Add the current record to the interpolated records
                    interpolated_records.append({
                        'timestamp_utc': record.timestamp_utc,
                        'status': record.status
                    })

                    # Interpolate the status for the missing timestamps between the current and previous record
                    if previous_record:
                        time_diff = record.timestamp_utc - previous_record.timestamp_utc
                        num_intervals = int(time_diff.total_seconds() / 3600)

                        for k in range(1, num_intervals):
                            interpolated_timestamp = previous_record.timestamp_utc + timedelta(hours=k)
                            interpolated_records.append({
                                'timestamp_utc': interpolated_timestamp,
                                'status': interpolate_status(previous_record.status, record.status, k, num_intervals)
                            })

                    previous_record = record

    # If no records are available, assume the store was inactive for the entire time interval
    else:
        for i in range(interval.days + 1):
            current_day_start_time = start_time_local + timedelta(days=i)
            interpolated_records.append({
                'timestamp_utc': current_day_start_time,
                'status': 'inactive'
            })

    # Sort the interpolated records based on timestamp
    interpolated_records.sort(key=lambda x: x['timestamp_utc'])

    # Add the current timestamp as the last record for extrapolation
    interpolated_records.append({
        'timestamp_utc': current_timestamp,
        'status': interpolated_records[-1]['status']
    })

    return interpolated_records

def interpolate_status(previous_status, current_status, interval, num_intervals):
    if previous_status == 'inactive' and current_status == 'active':
        return 'active'
    elif previous_status == 'active' and current_status == 'inactive':
        return 'inactive'
    else:
        # Interpolate the status based on the interval and the number of intervals
        interpolation = interval / num_intervals
        if interpolation <= 0.5:
            return previous_status
        else:
            return current_status


def calculate_uptime_last_hour(records, current_timestamp):
    """
    Calculates the total uptime in minutes for the last hour based on the provided records.

    Parameters:
    - records: List of dictionaries containing status records.
    - current_timestamp: Current timestamp.

    Returns:
    - Total uptime in minutes.
    """
    uptime = 0
    hour_ago = current_timestamp - timedelta(hours=1)

    for record in records:
        if record['timestamp_utc'] > hour_ago and record['timestamp_utc'] <= current_timestamp and record[
            'status'] == 'active':
            uptime += 1

    return uptime * 60


def calculate_downtime_last_hour(records, current_timestamp):
    """
    Calculates the total downtime in minutes for the last hour based on the provided records.

    Parameters:
    - records: List of dictionaries containing status records.
    - current_timestamp: Current timestamp.

    Returns:
    - Total downtime in minutes.
    """
    downtime = 0
    hour_ago = current_timestamp - timedelta(hours=1)

    for record in records:
        if record['timestamp_utc'] > hour_ago and record['timestamp_utc'] <= current_timestamp and record[
            'status'] == 'inactive':
            downtime += 1

    return downtime * 60


def calculate_uptime_last_day(records, current_timestamp):
    """
    Calculates the total uptime in minutes for the last day based on the provided records.

    Parameters:
    - records: List of dictionaries containing status records.
    - current_timestamp: Current timestamp.

    Returns:
    - Total uptime in minutes.
    """
    uptime = 0
    day_ago = current_timestamp - timedelta(days=1)

    for record in records:
        if record['timestamp_utc'] > day_ago and record['timestamp_utc'] <= current_timestamp and record[
            'status'] == 'active':
            uptime += 1

    return uptime * 60 * 24


def calculate_downtime_last_day(records, current_timestamp):
    """
    Calculates the total downtime in minutes for the last day based on the provided records.

    Parameters:
    - records: List of dictionaries containing status records.
    - current_timestamp: Current timestamp.

    Returns:
    - Total downtime in minutes.
    """
    downtime = 0
    day_ago = current_timestamp - timedelta(days=1)

    for record in records:
        if record['timestamp_utc'] > day_ago and record['timestamp_utc'] <= current_timestamp and record[
            'status'] == 'inactive':
            downtime += 1

    return downtime * 60 * 24


def calculate_uptime_last_week(records, current_timestamp):
    """
    Calculates the total uptime in minutes for the last week based on the provided records.

    Parameters:
    - records: List of dictionaries containing status records.
    - current_timestamp: Current timestamp.

    Returns:
    - Total uptime in minutes.
    """
    uptime = 0
    week_ago = current_timestamp - timedelta(days=7)

    for record in records:
        if record['timestamp_utc'] > week_ago and record['timestamp_utc'] <= current_timestamp and record[
            'status'] == 'active':
            uptime += 1

    return uptime * 60 * 24 * 7


def calculate_downtime_last_week(records, current_timestamp):
    """
    Calculates the total downtime in minutes for the last week based on the provided records.

    Parameters:
    - records: List of dictionaries containing status records.
    - current_timestamp: Current timestamp.

    Returns:
    - Total downtime in minutes.
    """
    downtime = 0
    week_ago = current_timestamp - timedelta(days=7)

    for record in records:
        if record['timestamp_utc'] > week_ago and record['timestamp_utc'] <= current_timestamp and record[
            'status'] == 'inactive':
            downtime += 1

    return downtime * 60 * 24 * 7

