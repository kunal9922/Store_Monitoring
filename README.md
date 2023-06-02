# Store_Monitoring
A system that gives notification to the restaurant owner. building an backend APIs for monitoring the online status of restaurants, trigger report generation and return the status of the report

To read the data from the CSV files and store it in a database, you can follow these steps:
1.	Import the necessary libraries and modules for CSV handling and database interaction. For example, you can use the csv module for CSV parsing and a database library like SQLAlchemy for database operations.
2.	Set up the database connection and define the necessary models to represent the data in the database. You can create models for the store information, store status, store business hours, and timezones.
3.	Read the data from each CSV file and populate the corresponding tables in the database.
•	For the store status data (source 1), parse the CSV file and create records in the database table representing the store status. Use the store_id, timestamp_utc, and status columns to populate the respective fields in the table.
•	For the store business hours data (source 2), parse the CSV file and create records in the database table representing the store business hours. Use the store_id, dayOfWeek, start_time_local, and end_time_local columns to populate the respective fields in the table.
•	For the store timezones data (source 3), parse the CSV file and create records in the database table representing the store timezones. Use the store_id and timezone_str columns to populate the respective fields in the table.
To handle the timezone data for the stores and ensure that the data sources can be compared against each other, you can modify the previous implementation as follows:
4.	Import the pytz library to handle timezones.
5.	Modify the StoreTimezone model to set a default value of "America/Chicago" for the timezone_str column.
6.	When parsing the timezone data from the CSV file, check if the timezone_str value is missing. If it is missing, use the default value of "America/Chicag

7.	Save the changes to the database and close the connection

The `Report` class is a SQLAlchemy model representing a table named `'reports'` in a database. It contains several columns: `id`, `report_id`, `status`, `data`, `created_at`, and `completed_at`.

•	`id` is an auto-incrementing integer column and serves as the primary key for the table.
•	`report_id` is a string column of length 255 and is used to uniquely identify each report. It is marked as `nullable=False` and `unique=True`, meaning it must have a value and should be unique among all reports.
•	`status` is a string column of length 50 and represents the status of the report. It is marked as `nullable=False`, meaning it must have a value.
•	`data` is a text column that stores the report data. It is marked as `nullable=False`, meaning it must have a value.
•	`created_at` is a DateTime column that represents the timestamp when the report was created. It has a default value of the current UTC timestamp when a new report is inserted.
•	`completed_at` is a DateTime column that represents the timestamp when the report was completed. It is initially `NULL` but gets updated when the report generation process is finished.

The `Report` class also contains a `to_dict()` method, which returns a dictionary representation of the report object. The dictionary includes the `id`, `report_id`, `status`, `created_at`, and `completed_at` values in ISO 8601 format. The `completed_at` value is converted to a string if it exists, otherwise it is set to `None`.

The `generate_report()` method is the main functionality of the `Report` class. It performs the following steps:
1. Retrieves the maximum timestamp from the `StoreStatus` table using a database query.
2. Determines the current timestamp by getting the current UTC time if there is no maximum timestamp, otherwise uses the maximum timestamp.
3. Fetches the business hours for each store from the `StoreHours` table using a database query.
4. Calculates the uptime and downtime for each store based on the store's business hours and the store status records within the last week.
5. Stores the calculated report data in the `report_data` list.
6. Updates the `data` column of the report object with the `report_data`, sets the `status` to `'Complete'`, and sets the `completed_at` timestamp to the current UTC time.
7. Commits the changes to the database.



<h1>app/reports.py <h1>
The `Report` class is a SQLAlchemy model representing a table named `'reports'` in a database. It contains several columns: `id`, `report_id`, `status`, `data`, `created_at`, and `completed_at`.

•	`id` is an auto-incrementing integer column and serves as the primary key for the table.
•	`report_id` is a string column of length 255 and is used to uniquely identify each report. It is marked as `nullable=False` and `unique=True`, meaning it must have a value and should be unique among all reports.
•	`status` is a string column of length 50 and represents the status of the report. It is marked as `nullable=False`, meaning it must have a value.
•	`data` is a text column that stores the report data. It is marked as `nullable=False`, meaning it must have a value.
•	`created_at` is a DateTime column that represents the timestamp when the report was created. It has a default value of the current UTC timestamp when a new report is inserted.
•	`completed_at` is a DateTime column that represents the timestamp when the report was completed. It is initially `NULL` but gets updated when the report generation process is finished.

The `Report` class also contains a `to_dict()` method, which returns a dictionary representation of the report object. The dictionary includes the `id`, `report_id`, `status`, `created_at`, and `completed_at` values in ISO 8601 format. The `completed_at` value is converted to a string if it exists, otherwise it is set to `None`.

The `generate_report()` method is the main functionality of the `Report` class. It performs the following steps:

1. Retrieves the maximum timestamp from the `StoreStatus` table using a database query.
2. Determines the current timestamp by getting the current UTC time if there is no maximum timestamp, otherwise uses the maximum timestamp.
3. Fetches the business hours for each store from the `StoreHours` table using a database query.
4. Calculates the uptime and downtime for each store based on the store's business hours and the store status records within the last week.
5. Stores the calculated report data in the `report_data` list.
6. Updates the `data` column of the report object with the `report_data`, sets the `status` to `'Complete'`, and sets the `completed_at` timestamp to the current UTC time.
7. Commits the changes to the database.



The `interpolate_store_status_records` function performs interpolation on store status records to fill in missing timestamps within a given time range. Here's how it works:

1. It takes the following parameters:
   - `records`: A list of store status records.
   - `start_time_local`: The start time of the desired time range.
   - `end_time_local`: The end time of the desired time range.
   - `current_timestamp`: The current timestamp (used for reference).
2. It initializes an empty list called `interpolated_records` to store the interpolated records.
3. It calculates the `interval` by subtracting the `start_time_local` from the `end_time_local`.
4. It checks if there are any records available for interpolation.
5. It iterates over each day within the `interval` using the `range` function.
6. For each day, it calculates the `current_day_start_time` and `current_day_end_time` by adding the corresponding number of days to the `start_time_local`.
7. It filters the `records` to get the records that fall within the current day.
8. If no records are available for the current day, it assumes that the store was inactive for the entire day and adds a record with the `timestamp_utc` set to the `current_day_start_time` and the `status` set to 'inactive' to the `interpolated_records` list.
9. If there are records available for the current day, it iterates over each record.
10. It adds the current record to the `interpolated_records` list.
11. If there is a previous record available, it calculates the time difference (`time_diff`) between the current record and the previous record.
12. It calculates the number of intervals (`num_intervals`) within the time difference by dividing the time difference in seconds by 3600 (since each interval represents one hour).
13. It then iterates over the range from 1 to `num_intervals` (excluding the endpoints).
14. For each interval, it calculates the interpolated timestamp (`interpolated_timestamp`) by adding `k` hours to the previous record's timestamp.
15. It calculates the interpolated status by calling the `interpolate_status` function with the previous record's status, current record's status, `k`, and `num_intervals`.
16. It adds a new record to the `interpolated_records` list with the `interpolated_timestamp` and the interpolated status.
17. Finally, it sets the `previous_record` to the current record for the next iteration.
18. The function continues iterating over the remaining records and days.
19. Once all records and days have been processed, it returns the `interpolated_records` list.

The `interpolate_store_status_records` function helps to fill in gaps in the store status records by interpolating the status for missing timestamps within the given time range.



These functions calculate the total uptime and downtime based on a given set of status records and a current timestamp. Here's how they work:

1. `calculate_uptime_last_hour(records, current_timestamp)`
   - It takes a list of status records (`records`) and the current timestamp (`current_timestamp`) as input.
   - It initializes a variable `uptime` to keep track of the total uptime.
   - It calculates the timestamp of one hour ago by subtracting one hour from the current timestamp.
   - It iterates over the records and checks if each record falls within the last hour and has an 'active' status.
   - If a record satisfies both conditions, it increments the `uptime` counter by 1.
   - Finally, it multiplies the `uptime` value by 60 to convert it from hours to minutes and returns the result.

2. `calculate_downtime_last_hour(records, current_timestamp)`
   - It takes a list of status records (`records`) and the current timestamp (`current_timestamp`) as input.
   - It follows a similar process as the `calculate_uptime_last_hour` function, but instead calculates the total downtime within the last hour.
   - It initializes a variable `downtime` to keep track of the total downtime.
   - It calculates the timestamp of one hour ago by subtracting one hour from the current timestamp.
   - It iterates over the records and checks if each record falls within the last hour and has an 'inactive' status.
   - If a record satisfies both conditions, it increments the `downtime` counter by 1.
   - Finally, it multiplies the `downtime` value by 60 to convert it from hours to minutes and returns the result.

The remaining four functions (`calculate_uptime_last_day`, `calculate_downtime_last_day`, `calculate_uptime_last_week`, `calculate_downtime_last_week`) follow a similar logic but calculate the uptime and downtime for the last day and last week respectively. The only difference is the time window used for filtering the records.

These functions provide a convenient way to analyze the uptime and downtime trends over different time periods based on the provided records and current timestamp.
