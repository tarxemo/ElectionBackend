# resolvers.py
import graphene
from django.db.models import Count, Sum, F, Q
from election.models import (
    Candidate, Election, ElectionPosition, Vote, 
    ElectionResult, Leader, Rating, Promise
)
from datetime import datetime, timedelta
from collections import defaultdict

class VoteRateType(graphene.ObjectType):
    date = graphene.String()
    voteCount = graphene.Int()

class VoteDistributionType(graphene.ObjectType):
    candidate_id = graphene.ID()
    candidate_name = graphene.String()
    vote_count = graphene.Int()
    vote_percentage = graphene.Float()
    is_winner = graphene.Boolean()

class InstitutionalVoteType(graphene.ObjectType):
    institution_name = graphene.String()
    vote_count = graphene.Int()
    vote_percentage = graphene.Float()

class VoteStatistics(graphene.ObjectType):
    vote_time_series = graphene.List(VoteRateType)
    vote_distribution = graphene.List(VoteDistributionType)
    cumulative_votes = graphene.List(VoteRateType)
    institutional_breakdown = graphene.List(InstitutionalVoteType)

class CandidateDetails(graphene.ObjectType):
    candidate = graphene.Field('api.schema.CandidateType')
    election_details = graphene.Field('api.schema.ElectionType')
    position_details = graphene.Field('api.schema.PositionType')
    competitors = graphene.List('api.schema.CandidateType')
    election_results = graphene.Field('api.schema.ElectionResultType')
    vote_statistics = graphene.Field(VoteStatistics)
    leader_info = graphene.Field('api.schema.LeaderType')
    ratings = graphene.List('api.schema.RatingType')
    promises = graphene.List('api.schema.PromiseType')

class CandidateQuery(graphene.ObjectType):
    candidate_details = graphene.Field(
        CandidateDetails,
        candidate_id=graphene.ID(required=True)
    )

    def resolve_candidate_details(self, info, candidate_id):
        try:
            candidate = Candidate.objects.select_related(
                'student__user',
                'student__institution',
                'student__academic_year',
                'election_position__election',
                'election_position__position'
            ).get(id=candidate_id)
        except Candidate.DoesNotExist:
            return None

        # Basic data
        election_position = candidate.election_position
        election = election_position.election
        position = election_position.position

        # Competitors
        competitors = Candidate.objects.filter(
            election_position=election_position
        ).exclude(id=candidate.id).select_related(
            'student__user',
            'student__institution'
        )

        # Election results
        election_results = ElectionResult.objects.filter(
            election=election,
            candidate=candidate
        ).first()

        # Vote statistics
        vote_statistics = self._get_vote_statistics(candidate, election_position)

        # Leader info (if won)
        leader_info = None
        ratings = []
        promises = []
        if election_results and election_results.is_winner:
            leader_info = Leader.objects.filter(
                candidate=candidate,
                position=position
            ).first()
            
            ratings = Rating.objects.filter(
                leader__candidate=candidate
            ).select_related('student__user')
            
            promises = Promise.objects.filter(
                candidate=candidate
            ).prefetch_related('promiseupdate_set')

        return CandidateDetails(
            candidate=candidate,
            election_details=election,
            position_details=position,
            competitors=competitors,
            election_results=election_results,
            vote_statistics=vote_statistics,
            leader_info=leader_info,
            ratings=ratings,
            promises=promises
        )

    def _get_vote_statistics(self, candidate, election_position):
        # Time series data (last 30 days)
        time_series_data = self._get_time_series_data(candidate, election_position)
        
        # Vote distribution among competitors
        vote_distribution = self._get_vote_distribution(candidate, election_position)
        
        # Cumulative votes
        cumulative_votes = self._get_cumulative_votes(time_series_data)
        
        # Institutional breakdown
        institutional_breakdown = self._get_institutional_breakdown(candidate, election_position)
        
        return VoteStatistics(
            vote_time_series=time_series_data,
            vote_distribution=vote_distribution,
            cumulative_votes=cumulative_votes,
            institutional_breakdown=institutional_breakdown
        )

    def _get_time_series_data(self, candidate, election_position):
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        votes = Vote.objects.filter(
            candidate=candidate,
            timestamp__gte=thirty_days_ago
        ).extra({
            'date': "date(timestamp)"
        }).values('date').annotate(
            vote_count=Count('id')
        ).order_by('date')
        
        return [
            VoteRateType(
                date=vote['date'],
                voteCount=vote['vote_count']
            ) for vote in votes
        ]

    def _get_vote_distribution(self, candidate, election_position):
        candidates = Candidate.objects.filter(
            election_position=election_position
        ).annotate(
            vote_count=Count('votes'),
            total_votes=Count('votes', filter=Q(votes__election=election_position.election))
        )
        
        total_votes = sum(c.vote_count for c in candidates) or 1  # Avoid division by zero
        
        return [
            VoteDistributionType(
                candidate_id=c.id,
                candidate_name=f"{c.student.user.first_name} {c.student.user.last_name}",
                vote_count=c.vote_count,
                vote_percentage=(c.vote_count / total_votes) * 100,
                is_winner=c.id == candidate.id and election_position.election.status == 'COMPLETED'
            ) for c in candidates
        ]

    def _get_cumulative_votes(self, time_series_data):
        cumulative = 0
        cumulative_votes = []
        
        for day in sorted(time_series_data, key=lambda x: x.date):
            cumulative += day.voteCount
            cumulative_votes.append(
                VoteRateType(
                    date=day.date,
                    voteCount=cumulative
                )
            )
            
        return cumulative_votes

    def _get_institutional_breakdown(self, candidate, election_position):
        votes = Vote.objects.filter(
            candidate=candidate,
            election=election_position.election
        ).values(
            'voter__institution__name'
        ).annotate(
            vote_count=Count('id'),
            total_votes=Count('id', filter=Q(election=election_position.election))
        )
        
        total_votes = votes.aggregate(total=Sum('vote_count'))['total'] or 1
        
        return [
            InstitutionalVoteType(
                institution_name=vote['voter__institution__name'],
                vote_count=vote['vote_count'],
                vote_percentage=(vote['vote_count'] / total_votes) * 100
            ) for vote in votes
        ]