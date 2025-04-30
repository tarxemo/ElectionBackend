def get_vote_statistics(candidate, election_position):
    return VoteStatistics(
        vote_time_series=get_time_series_data(candidate, election_position),
        vote_distribution=get_vote_distribution(candidate, election_position),
        cumulative_votes=get_cumulative_votes(candidate, election_position),
        institutional_breakdown=get_institutional_breakdown(candidate, election_position)
    )
    
def get_vote_statistics(self, candidate, election_position):
    return VoteStatistics(
        vote_time_series=self._get_time_series_data(candidate, election_position),
        vote_distribution=self._get_vote_distribution(candidate, election_position),
        cumulative_votes=self._get_cumulative_votes(candidate, election_position),
        institutional_breakdown=self._get_institutional_breakdown(candidate, election_position)
    )

def get_time_series_data(self, candidate, election_position):
    thirty_days_ago = datetime.now() - timedelta(days=30)
    votes = (
        candidate.votes
        .filter(timestamp__gte=thirty_days_ago)
        .annotate(date=TruncDate('timestamp'))
        .values('date')
        .annotate(vote_count=Count('id'))
        .order_by('date')
    )
    return [
        VoteRateType(date=vote['date'], vote_count=vote['vote_count'])
        for vote in votes
    ]

def get_vote_distribution(self, candidate, election_position):
    candidates = (
        Candidate.objects
        .filter(election_position=election_position)
        .annotate(vote_count=Count('votes'))
    )
    total_votes = sum(c.vote_count for c in candidates) or 1
    
    return [
        VoteDistributionType(
            candidate_id=c.id,
            candidate_name=f"{c.student.user.first_name} {c.student.user.last_name}",
            vote_count=c.vote_count,
            vote_percentage=(c.vote_count / total_votes) * 100,
            is_winner=c.id == candidate.id and election_position.election.status == 'COMPLETED'
        ) for c in candidates
    ]

def get_cumulative_votes(self, candidate, election_position):
    votes = (
        candidate.votes
        .annotate(date=TruncDate('timestamp'))
        .values('date')
        .annotate(vote_count=Count('id'))
        .order_by('date')
    )
    
    cumulative = 0
    cumulative_votes = []
    for vote in votes:
        cumulative += vote['vote_count']
        cumulative_votes.append(
            VoteRateType(
                date=vote['date'],
                vote_count=cumulative
            )
        )
    return cumulative_votes

def get_institutional_breakdown(self, candidate, election_position):
    votes = (
        candidate.votes
        .filter(election=election_position.election)
        .values('voter__institution__name')
        .annotate(
            vote_count=Count('id'),
            total_votes=Count('id', filter=Q(election=election_position.election))
        )
    )
    total_votes = votes.aggregate(total=Sum('vote_count'))['total'] or 1
    
    return [
        InstitutionalVoteType(
            institution_name=vote['voter__institution__name'],
            vote_count=vote['vote_count'],
            vote_percentage=(vote['vote_count'] / total_votes) * 100
        ) for vote in votes
    ]

