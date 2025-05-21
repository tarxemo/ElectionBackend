import random
from django.core.management.base import BaseCommand
from django.db.models import Count

from election.models import Candidate

class Command(BaseCommand):
    help = 'Removes excess candidates so that no election position has more than 5 candidates.'

    def handle(self, *args, **kwargs):
        overfilled_positions = (
            Candidate.objects.values('election_position')
            .annotate(candidate_count=Count('id'))
            .filter(candidate_count__gt=5)
        )

        total_deleted = 0
        total_positions_trimmed = 0

        for entry in overfilled_positions:
            ep_id = entry['election_position']
            candidates = list(Candidate.objects.filter(election_position_id=ep_id))

            if len(candidates) > 5:
                random.shuffle(candidates)
                to_keep = candidates[:5]
                to_delete = [c for c in candidates if c not in to_keep]

                Candidate.objects.filter(id__in=[c.id for c in to_delete]).delete()

                self.stdout.write(self.style.WARNING(
                    f"Trimmed {len(to_delete)} candidates from election_position ID {ep_id}"
                ))

                total_deleted += len(to_delete)
                total_positions_trimmed += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Trimmed {total_deleted} candidates across {total_positions_trimmed} positions."
        ))
