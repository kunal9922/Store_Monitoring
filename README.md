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
