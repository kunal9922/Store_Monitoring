import csv
from datetime import datetime, time
import pytz
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

class Config:
    #contain the sqlite database url
    SQLALCHEMY_DATABASE_URI = 'sqlite:///restaurant_monitoring.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

config = Config()
# Set up the database connection
engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


# Define the models
class StoreStatus(Base):
    __tablename__ = 'store_status'

    id = Column(Integer, primary_key=True)
    store_id = Column(String(255), nullable=False)
    timestamp_utc = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False)


class StoreHours(Base):
    __tablename__ = 'store_hours'

    id = Column(Integer, primary_key=True)
    store_id = Column(String(255), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_time_local = Column(String(50))
    end_time_local = Column(String(50))


class StoreTimezone(Base):
    __tablename__ = 'store_timezone'

    id = Column(Integer, primary_key=True)
    store_id = Column(String(255), nullable=False)
    timezone_str = Column(String(255), default='America/Chicago')

# Drop existing tables
Base.metadata.drop_all(bind=engine)

# Create the tables
Base.metadata.create_all(bind=engine)

# Read data from CSV files and store in the database
def read_and_store_data():
    count = 0
    # Read and store store status data
    with open(r'C:\Users\HP\Downloads\store status.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            store_id, status, timestamp_utc = row
            if count == 30:
                break
            # skipping the header of csv file to store in DB
            if store_id in ['store_id', 'status', 'timestamp_utc']:
                continue
            # Process the timestamp and status values accordingly
            try:
                timestamp_utc = datetime.strptime(timestamp_utc, '%Y-%m-%d %H:%M:%S')
            except ValueError as v:
                # Removing the unconverted data for the timestamp_utc
                if len(v.args) > 0 and v.args[0].startswith('unconverted data remains: '):
                    line = timestamp_utc[:-(len(v.args[0]) - 26)]
                    timestamp_utc = datetime.strptime(line, '%Y-%m-%d %H:%M:%S')
                else:
                    raise
            store_status = StoreStatus(store_id=store_id, timestamp_utc=timestamp_utc, status=status)
            session.add(store_status)
            count += 1

    # Read and store store hours data
    with open(r"C:\Users\HP\Downloads\Menu hours.csv", 'r') as file:
        reader = csv.reader(file)
        count = 0
        for row in reader:
            store_id, day_of_week, start_time_local, end_time_local = row
            # skipping the header of csv file to store in DB
            if store_id in ["store_id", "day", "start_time_local", "end_time_local"]:
                continue
            if not start_time_local or not end_time_local:
                # Store is assumed to be open 24/7 if missing data
                start_time_local = time(0, 0)
                end_time_local = time(23, 59)
            else:
                start_time_local = datetime.strptime(start_time_local, '%H:%M:%S').time().strftime('%H:%M:%S')
                end_time_local = datetime.strptime(end_time_local, '%H:%M:%S').time().strftime('%H:%M:%S')

            store_hours = StoreHours(
                store_id=store_id,
                day_of_week=int(day_of_week),
                start_time_local=start_time_local,
                end_time_local=end_time_local
            )
            session.add(store_hours)       

    # Read and store store timezone data
    with open(r"C:\Users\HP\Downloads\store_timezone.csv", 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            store_id, timezone_str = row
            # skipping the header of csv file to store in DB
            if store_id in ["store_id", "timezone_str"]:
                continue
            if not timezone_str:
                timezone_str = 'America/Chicago'
            store_timezone = StoreTimezone(store_id=store_id, timezone_str=timezone_str)
            session.add(store_timezone)

    # Save changes to the database
    session.commit()


if __name__ == '__main__':
    read_and_store_data()
