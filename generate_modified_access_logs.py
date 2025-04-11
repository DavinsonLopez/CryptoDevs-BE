import random
from datetime import datetime, timedelta
import os
from calendar import monthrange, weekday, SATURDAY, SUNDAY

# Function to check if a date is a weekend
def is_weekend(date):
    return date.weekday() >= 5  # 5 is Saturday, 6 is Sunday

# Open the file for writing
with open('database/ACCESS_LOGS.sql', 'w') as f:
    f.write('-- Access logs from January to April 2025\n')
    f.write('-- No weekend entries, with early/late arrivals and departures\n')
    f.write('INSERT INTO access_logs (person_type, person_id, access_type, access_time, workday_date)\nVALUES\n')
    
    records = []
    
    # Employee IDs to use
    employee_ids = [1, 2, 3, 4, 5, 6, 7]
    
    # Generate data for January through April 2025
    for month in range(1, 5):  # January (1) to April (4)
        # Get the number of days in the month
        num_days = monthrange(2025, month)[1]
        
        for day in range(1, num_days + 1):
            # Create date object
            current_date = datetime(2025, month, day)
            
            # Skip weekends
            if is_weekend(current_date):
                continue
                
            date_str = current_date.strftime('%Y-%m-%d')
            
            for emp_id in employee_ids:
                # Determine if this employee will arrive early, on time, or late
                arrival_status = random.choices(
                    ['early', 'on_time', 'late'], 
                    weights=[0.2, 0.6, 0.2], 
                    k=1
                )[0]
                
                # Determine if this employee will leave early, on time, or late
                departure_status = random.choices(
                    ['early', 'on_time', 'late'], 
                    weights=[0.2, 0.6, 0.2], 
                    k=1
                )[0]
                
                # Generate entry time based on status
                if arrival_status == 'early':
                    # 15-30 minutes early
                    entry_minutes_variation = random.randint(-30, -15)
                elif arrival_status == 'late':
                    # 5-20 minutes late
                    entry_minutes_variation = random.randint(5, 20)
                else:
                    # On time (±5 minutes)
                    entry_minutes_variation = random.randint(-5, 5)
                
                entry_time = current_date.replace(hour=8, minute=0) + timedelta(minutes=entry_minutes_variation)
                entry_time_str = entry_time.strftime('%Y-%m-%d %H:%M:%S')
                
                # Generate exit time based on status
                if departure_status == 'early':
                    # 10-30 minutes early
                    exit_minutes_variation = random.randint(-30, -10)
                elif departure_status == 'late':
                    # 10-40 minutes late
                    exit_minutes_variation = random.randint(10, 40)
                else:
                    # On time (±10 minutes)
                    exit_minutes_variation = random.randint(-10, 10)
                
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

print("Generated access log records from January to April 2025 successfully!")
