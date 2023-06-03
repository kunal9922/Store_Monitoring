import uuid
from datetime import datetime, timedelta
import csv
from flask import Flask, request, jsonify, send_file
from reports import Report
from io import StringIO

app = Flask(__name__)

# In-memory database to store reports
reports = {}


# Endpoint to trigger report generation
@app.route('/trigger_report', methods=['POST'])
def trigger_report():
    # Generate a random report_id
    report_id = str(uuid.uuid4())
    
    # Perform report generation logic and store the report in the in-memory database
    repo = Report()
    data = repo.generate_report()  # Replace with your actual report generation logic
    status = 'Complete'  # Assuming the report generation is complete at this point
    report = {'data': data, 'status': status}
    reports[report_id] = report

    return jsonify({'report_id': report_id, 'message': status})


# Endpoint to get report status or CSV
@app.route('/get_report', methods=['GET'])
def get_report():
    # Get the report_id from the request parameters
    report_id = request.args.get('report_id')

    # Retrieve the report based on the report_id from the in-memory database
    report = reports.get(report_id)

    if report is None:
        return jsonify({'message': 'Report not found'})

    if report['status'] == 'Running':
        return jsonify({'status': 'Running'})

    if report['status'] == 'Complete':
        # Extrapolate uptime and downtime based on the periodic polls
        extrapolated_data = extrapolate_data(report['data'])

        # Generate the CSV file
        csv_data = generate_csv(extrapolated_data)

        # Return the CSV file as the response
        return send_csv_file(csv_data, f'report_{report_id}.csv')


# Function to generate the CSV file from the extrapolated data
def generate_csv(data):
    # Create a list of dictionaries representing the report rows
    report_rows = []
    for row in data:
        uptime_last_hour = row['uptime']
        uptime_last_day = calculate_total_uptime(data, row['timestamp'], timedelta(hours=24))
        uptime_last_week = calculate_total_uptime(data, row['timestamp'], timedelta(days=7))
        downtime_last_hour = row['downtime']
        downtime_last_day = calculate_total_downtime(data, row['timestamp'], timedelta(hours=24))
        downtime_last_week = calculate_total_downtime(data, row['timestamp'], timedelta(days=7))

        report_rows.append({
            'store_id': row['store_id'],  # Replace with the actual store_id value
            'uptime_last_hour': uptime_last_hour,
            'uptime_last_day': uptime_last_day,
            'uptime_last_week': uptime_last_week,
            'downtime_last_hour': downtime_last_hour,
            'downtime_last_day': downtime_last_day,
            'downtime_last_week': downtime_last_week
        })

    # Generate the CSV file
    csv_data = StringIO()
    writer = csv.DictWriter(csv_data, fieldnames=report_rows[0].keys())
    writer.writeheader()
    writer.writerows(report_rows)

    return csv_data.getvalue()


# Function to calculate the total uptime within a time range
def calculate_total_uptime(data, current_time, time_range):
    uptime = sum(row['uptime'] for row in data if current_time - time_range <= row['timestamp'] <= current_time)
    if isinstance(time_range, timedelta):
        uptime = uptime.total_seconds() / 60 if time_range.total_seconds() >= 60 else uptime
    return uptime


# Function to calculate the total downtime within a time range
def calculate_total_downtime(data, current_time, time_range):
    downtime = sum(row['downtime'] for row in data if current_time - time_range <= row['timestamp'] <= current_time)
    if isinstance(time_range, timedelta):
        downtime = downtime.total_seconds() / 60 if time_range.total_seconds() >= 60 else downtime
    return downtime


# Function to extrapolate the uptime and downtime based on the periodic polls
def extrapolate_data(polls):
    # Sort the polls by timestamp in ascending order
    polls = sorted(polls, key=lambda x: x['timestamp'])

    # Determine the time interval between the first and last poll
    start_time = polls[0]['timestamp']
    end_time = polls[-1]['timestamp']
    time_interval = end_time - start_time

    # Calculate the average uptime and downtime values
    total_uptime = sum(poll['uptime'] for poll in polls)
    total_downtime = sum(poll['downtime'] for poll in polls)
    average_uptime = total_uptime / len(polls)
    average_downtime = total_downtime / len(polls)

    # Extrapolate the uptime and downtime values for the entire time interval
    extrapolated_data = []
    current_time = start_time
    while current_time <= end_time:
        extrapolated_data.append({
            'timestamp': current_time,
            'uptime': average_uptime,
            'downtime': average_downtime
        })
        current_time += timedelta(minutes=1)  # Assuming the polls are recorded at 1-minute intervals

    return extrapolated_data


# Function to send the CSV file as the response
def send_csv_file(csv_data, filename):
    # Set up the response headers
    headers = {
        'Content-Disposition': f'attachment; filename={filename}',
        'Content-Type': 'text/csv'
    }

    # Return the CSV file as the response
    return csv_data, 200, headers


if __name__ == '__main__':
    app.run()
