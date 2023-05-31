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
