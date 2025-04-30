# ElectionBackend
pg_restore -U your_username -d target_db -F c backup_file.dump
python3 manage.py populate_election_data --csv_file /media/tarxemo/TarXemo/GT/VS/ElectionBackend/election/Salaries.csv --students 20000

python3 manage.py randomize_vote_timestamps

python3 manage.py simulate_election --election_name="2024 General Election" --days=7
python3 manage.py simulate_election --election_name="2024 General Election"
python3 manage.py simulate_election --election_name="High Turnout Test" --days=5 --voter_turnout=0.9 --peak_day=3
python3 manage.py simulate_election --election_name="New Test Election" --force_new