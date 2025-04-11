import random
from datetime import datetime, timedelta
import os

# Start date for the records
start_date = datetime(2025, 4, 5)
# Number of employees
num_employees = 10
# Number of days to generate records for
num_days = 18  # This will generate 180 records (10 employees * 18 days)

# Open the file for writing
with open('database/ACCESS_LOGS.sql', 'a') as f:
    f.write('\n\n-- Additional 180 records with time variations\n')
    f.write('INSERT INTO access_logs (person_type, person_id, access_type, access_time, workday_date)\nVALUES\n')
    
    records = []
    
    for day in range(num_days):
        current_date = start_date + timedelta(days=day)
        date_str = current_date.strftime('%Y-%m-%d')
        
        for emp_id in range(1, num_employees + 1):
            # Generate entry time around 8:00 AM with ±15 minutes variation
            entry_minutes_variation = random.randint(-15, 15)
            entry_time = current_date.replace(hour=8, minute=0) + timedelta(minutes=entry_minutes_variation)
            entry_time_str = entry_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Generate exit time around 5:00 PM with ±20 minutes variation
            exit_minutes_variation = random.randint(-20, 20)
            exit_time = current_date.replace(hour=17, minute=0) + timedelta(minutes=exit_minutes_variation)
            exit_time_str = exit_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Add entry record
            entry_record = f"    ('employee', {emp_id}, 'entry', '{entry_time_str}', '{date_str}')"
            records.append(entry_record)
            
            # Add exit record
            exit_record = f"    ('employee', {emp_id}, 'exit', '{exit_time_str}', '{date_str}')"
            records.append(exit_record)
    
    # Join all records with commas
    sql_values = ',\n'.join(records)
    f.write(sql_values)
    f.write(';')

print("Generated 180 access log records successfully!")
