# ElectionBackend
pg_restore -U your_username -d target_db -F c backup_file.dump
python manage.py populate_election_data --csv_file /media/tarxemo/TarXemo/GT/VS/ElectionBackend/election/Salaries.csv --students 20