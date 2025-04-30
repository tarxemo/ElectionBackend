import random
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from election.models import Vote  # <-- Replace `your_app` with your actual app name


class Command(BaseCommand):
    help = 'Randomizes the timestamps of votes based on their election year.'

    def handle(self, *args, **kwargs):
        votes = Vote.objects.select_related('election').all()
        updated_count = 0

        for vote in votes:
            election_name = vote.election.name  # e.g., "2021-2022"
            try:
                start_year = int(election_name.split('-')[0])  # Extract the first year
            except (ValueError, IndexError):
                self.stdout.write(self.style.WARNING(
                    f"Skipping vote with invalid election name: {election_name}"
                ))
                continue

            # Random date between December 1 and December 20 of start_year
            random_day = random.randint(1, 20)
            random_hour = random.randint(0, 23)
            random_minute = random.randint(0, 59)
            random_second = random.randint(0, 59)

            naive_random_date = datetime(
                year=start_year,
                month=12,
                day=random_day,
                hour=random_hour,
                minute=random_minute,
                second=random_second,
            )

            # Make timezone-aware
            aware_random_date = timezone.make_aware(naive_random_date)

            # Update the timestamp
            vote.timestamp = aware_random_date
            vote.save(update_fields=['timestamp'])
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully randomized timestamps for {updated_count} votes."
        ))
