from typing import List, Optional, Dict, Union
import graphene
from graphene_django import DjangoObjectType
from graphene.types.generic import GenericScalar
from django.db.models import Count, Sum, Avg, F

from django.db.models.functions import Trunc
from election.outputs import *
from .models import (
    AcademicYear, InstitutionLevel, Institution, Position,
    Student, Election, ElectionPosition, Candidate,
    Vote, ElectionResult, Leader, Promise, PromiseUpdate,
    Rating, ElectionStatistics
)

# Helper Types
class CountType(graphene.ObjectType):
    total = graphene.Int()
    label = graphene.String()

class PercentageType(graphene.ObjectType):
    value = graphene.Float()
    label = graphene.String()

class TimeSeriesDataType(graphene.ObjectType):
    timestamp = graphene.DateTime()
    value = graphene.Int()

# Base Model Types
class AcademicYearType(DjangoObjectType):
    class Meta:
        model = AcademicYear
        fields = '__all__'

    is_active = graphene.Boolean()
    
    def resolve_is_active(self, info):
        return self.is_current

class InstitutionLevelType(DjangoObjectType):
    class Meta:
        model = InstitutionLevel
        fields = '__all__'

# class InstitutionType(DjangoObjectType):
#     class Meta:
#         model = Institution
#         fields = '__all__'

#     parent = graphene.Field(lambda: InstitutionType)
#     children = graphene.List(lambda: InstitutionType)
#     hierarchy = graphene.List(lambda: InstitutionType)
#     student_count = graphene.Int()
#     leader_count = graphene.Int()
    
#     def resolve_parent(self, info):
#         return self.parent
    
#     def resolve_children(self, info):
#         return self.institution_set.all()
    
#     def resolve_hierarchy(self, info):
#         def get_hierarchy(obj):
#             if obj.parent:
#                 return get_hierarchy(obj.parent) + [obj]
#             return [obj]
#         return get_hierarchy(self)
    
#     def resolve_student_count(self, info):
#         return self.student_set.count()
    
#     def resolve_leader_count(self, info):
#         return self.leader_set.count()

# class LeaderType(DjangoObjectType):
#     class Meta:
#         model = Leader
#         fields = '__all__'

class LeaderType(DjangoObjectType):
    class Meta:
        model = Leader
        fields = '__all__'

    full_name = graphene.String()
    position_name = graphene.String()
    institution_name = graphene.String()
    average_rating = graphene.Float()
    promises_completed = graphene.Int()
    promises_in_progress = graphene.Int()
    promises_total = graphene.Int()
    
    def resolve_full_name(self, info):
        return self.candidate.student.user.get_full_name()
    
    def resolve_position_name(self, info):
        return self.position.name
    
    def resolve_institution_name(self, info):
        return self.institution.name
    
    def resolve_average_rating(self, info):
        return (
            Rating.objects.filter(leader=self)
            .aggregate(avg_rating=Avg('score'))
            .get('avg_rating')
        )
    
    def resolve_promises_completed(self, info):
        return (
            Promise.objects.filter(candidate=self.candidate)
            .filter(promiseupdate__status='COMPLETED')
            .distinct()
            .count()
        )
    
    def resolve_promises_in_progress(self, info):
        return (
            Promise.objects.filter(candidate=self.candidate)
            .filter(promiseupdate__status='IN_PROGRESS')
            .distinct()
            .count()
        )
    
    def resolve_promises_total(self, info):
        return self.candidate.promise_set.count()

class VoteRateType(graphene.ObjectType):
    date = graphene.DateTime()  # Or use Date() if you want just the date part
    vote_count = graphene.Int()
    
class CandidateType(DjangoObjectType):
    class Meta:
        model = Candidate
        fields = '__all__'

    is_predicted_winner = graphene.Boolean()
    # Define the student field explicitly
    student = graphene.Field(lambda: StudentType)  # Assuming you have a StudentType for the Student model

    # Add a resolver for the student field
    def resolve_student(self, info):
        return self.student  # Return the related Student object

    vote_count = graphene.Int()
    vote_percentage = graphene.Float()
    is_winner = graphene.Boolean()
    promises_count = graphene.Int()
    rating = graphene.Float()
    vote_rates = graphene.List(
        VoteRateType,
        granularity=graphene.String(),
        limit=graphene.Int()
        )

    def resolve_vote_count(self, info):
        # Use reverse relationship to count votes for this candidate
        return Vote.objects.filter(candidate=self).count()

    def resolve_vote_percentage(self, info):
        total_votes = Vote.objects.filter(
            election=self.election_position.election,
            candidate__election_position=self.election_position
        ).count()
        if total_votes > 0:
            return (Vote.objects.filter(candidate=self).count() / total_votes) * 100
        return 0

    def resolve_is_winner(self, info):
        return ElectionResult.objects.filter(
            candidate=self,
            is_winner=True
        ).exists()

    def resolve_promises_count(self, info):
        return Promise.objects.filter(candidate=self).count()

    def resolve_rating(self, info):
        if hasattr(self, 'leader'):
            return Rating.objects.filter(
                leader=self.leader
            ).aggregate(Avg('score'))['score__avg']
        return None
      # New field for daily rates
    
    def resolve_vote_rates(self, info, granularity="day", limit=50):
        # Determine the truncation based on granularity
        trunc_kind = {
            'minute': 'minute',
            'hour': 'hour',
            'day': 'day'
        }.get(granularity, 'day')  # default to day
        
        # Query to get vote counts with the specified granularity
        vote_rates = (
            self.votes.annotate(
                time_period=Trunc('timestamp', trunc_kind)
            )
            .values('time_period')
            .annotate(vote_count=Count('id'))
            .order_by('-time_period')[:limit]  # Get most recent N periods
        )

        return [
            VoteRateType(date=rate['time_period'], vote_count=rate['vote_count'])
            for rate in vote_rates
        ]
          
# class ElectionStatisticsType(DjangoObjectType):
#     class Meta:
#         model = ElectionStatistics
#         fields = '__all__'
 
class ElectionTrendType(graphene.ObjectType):
    year = graphene.String()
    elections = graphene.Int()
    voters = graphene.Int()
    turnout = graphene.Float()
           
class InstitutionType(DjangoObjectType):
    class Meta:
        model = Institution
        fields = "__all__"

    children = graphene.List(lambda: InstitutionType)
    leaders = graphene.List(LeaderType)
    election_stats = graphene.Field(lambda: ElectionStatisticsType)
    vote_distribution = graphene.JSONString()
    voter_turnout_history = graphene.JSONString()
    position_breakdown = graphene.JSONString()

    def resolve_children(self, info):
        return Institution.objects.filter(parent=self)

    def resolve_leaders(self, info):
        return Leader.objects.filter(
            institution=self,
            is_active=True
        ).select_related('candidate__student__user', 'position')

    def resolve_election_stats(self, info):
        return ElectionStatistics.objects.filter(
            election__institution=self
        ).order_by('-election__start_datetime').first()

    def resolve_vote_distribution(self, info):
        elections = Election.objects.filter(institution=self, status='COMPLETED')
        data = []
        
        for election in elections:
            results = ElectionResult.objects.filter(
                election=election
            ).select_related('candidate__student__user')
            
            for result in results:
                data.append({
                    'election': election.name,
                    'candidate': f"{result.candidate.student.user.firstName} {result.candidate.student.user.lastName}",
                    'votes': result.total_votes,
                    'percentage': float(result.percentage),
                    'isWinner': result.is_winner
                })
        
        return data

    def resolve_voter_turnout_history(self, info):
        stats = ElectionStatistics.objects.filter(
            election__institution=self
        ).order_by('election__start_datetime')
        
        return [{
            'election': stat.election.name,
            'year': stat.election.academic_year.name,
            'turnout': float(stat.voter_turnout),
            'totalVoters': stat.total_voters,
            'votesCast': stat.total_votes_cast
        } for stat in stats]

    def resolve_position_breakdown(self, info):
        positions = Position.objects.filter(institution=self)
        data = []
        
        for position in positions:
            leaders = Leader.objects.filter(position=position).count()
            elections = ElectionPosition.objects.filter(position=position).count()
            data.append({
                'position': position.name,
                'leadersCount': leaders,
                'electionsCount': elections,
                'description': position.description
            })
        
        return data

class InstitutionDetails(graphene.ObjectType):
    institution = graphene.Field(InstitutionType)
    parent_institution = graphene.Field(InstitutionType)
    child_institutions = graphene.List(InstitutionType)
    hierarchy = graphene.JSONString()

class PositionType(DjangoObjectType):
    class Meta:
        model = Position
        fields = '__all__'

    current_holder = graphene.Field(lambda: LeaderType)
    candidates_count = graphene.Int()
    
    def resolve_current_holder(self, info):
        return Leader.objects.filter(
            position=self,
            is_active=True
        ).first()
    
    def resolve_candidates_count(self, info):
        return self.candidate_set.count()

class StudentType(DjangoObjectType):
    class Meta:
        model = Student
        fields = '__all__'
        # exclude = ('user',)

    full_name = graphene.String()
    email = graphene.String()
    is_eligible_to_vote = graphene.Boolean(election_id=graphene.ID())
    is_eligible_to_candidate = graphene.Boolean(position_id=graphene.ID())
    votes_cast = graphene.Int(election_id=graphene.ID())
    
    def resolve_full_name(self, info):
        return self.user.get_full_name()
    
    def resolve_email(self, info):
        return self.user.email
    
    def resolve_is_eligible_to_vote(self, info, election_id=None):
        # Implement eligibility logic based on election rules
        return True  # Placeholder
    
    def resolve_is_eligible_to_candidate(self, info, position_id=None):
        # Implement eligibility logic based on position requirements
        return True  # Placeholder
    
    def resolve_votes_cast(self, info, election_id=None):
        if election_id:
            return self.votes.filter(election_id=election_id).count()
        return self.votes.count()

# class StudentType(DjangoObjectType):
#     class Meta:
#         model = Student
#         fields = '__all__'  # You can specify the fields you want to expose, or just use '__all__' to expose everything
    
#     # Optionally, you can add custom fields if needed
#     full_name = graphene.String()
#     academic_year = graphene.Field(AcademicYearType)
#     institution = graphene.Field(InstitutionType)
#     user = graphene.Field(UserType)

#     # Optionally, a custom resolver for the full name
#     def resolve_full_name(self, info):
#         return self.user.get_full_name()  # Assuming 'user' is a ForeignKey to a User model
    
#     def resolve_academic_year(self, info):
#         return self.academic_year

#     def resolve_institution(self, info):
#         return self.institution
    
#     def resolve_user(self, info):
#         return self.user 
#      # Changed from TruncHour


# Election Related Types
class ElectionStatusType(graphene.ObjectType):
    code = graphene.String()
    display = graphene.String()

class ElectionType(DjangoObjectType):
    class Meta:
        model = Election
        fields = '__all__'

    status_display = graphene.String()
    time_remaining = graphene.String()
    voter_turnout = graphene.Float()
    positions_count = graphene.Int()
    candidates_count = graphene.Int()
    votes_count = graphene.Int()
    is_active = graphene.Boolean()
    results = graphene.List(lambda: ElectionResultType)
    statistics = graphene.Field(lambda: ElectionStatisticsType)
    vote_distribution = graphene.List(CountType)
    time_series_data = graphene.List(TimeSeriesDataType)
    
    def resolve_status_display(self, info):
        return self.get_status_display()
    
    def resolve_time_remaining(self, info):
        from django.utils import timezone
        if self.status == 'ACTIVE':
            remaining = self.end_datetime - timezone.now()
            return str(remaining)
        return None
    
    def resolve_voter_turnout(self, info):
        if hasattr(self, 'electionstatistics'):
            return self.electionstatistics.voter_turnout
        return None
    
    def resolve_positions_count(self, info):
        return self.positions.count()
    
    def resolve_candidates_count(self, info):
        return Candidate.objects.filter(election_position__election=self).count()
    
    def resolve_votes_count(self, info):
        return Vote.objects.filter(election=self).count()
    
    def resolve_is_active(self, info):
        return self.status == 'ACTIVE'
    
    def resolve_results(self, info):
        return self.electionresult_set.all().order_by('position_rank')
    
    def resolve_statistics(self, info):
        return getattr(self, 'electionstatistics', None)
    
    def resolve_vote_distribution(self, info):
        return (
            Candidate.objects.filter(election_position__election=self)
            .annotate(vote_count=Count('votes'))
            .values('vote_count')
            .annotate(total=Count('id'))
            .order_by('-vote_count')
        )
    
    def resolve_time_series_data(self, info):
        return (
            Vote.objects.filter(election=self)
            .extra({'hour': "date_trunc('hour', timestamp)"})
            .values('hour')
            .annotate(value=Count('id'))
            .order_by('hour')
        )

class ElectionPositionType(DjangoObjectType):
    class Meta:
        model = ElectionPosition
        fields = '__all__'

    candidates = graphene.List(lambda: CandidateType)
    votes_count = graphene.Int()
    
    def resolve_candidates(self, info):
        return self.candidate_set.all()
    
    def resolve_votes_count(self, info):
        return (
            Vote.objects.filter(candidate__election_position=self)
            .count()
        )

# class CandidateType(DjangoObjectType):
#     class Meta:
#         model = Candidate
#         fields = '__all__'

#     full_name = graphene.String()
#     votes_count = graphene.Int()
#     vote_percentage = graphene.Float()
#     is_leading = graphene.Boolean()
#     promises = graphene.List(lambda: PromiseType)
#     current_rating = graphene.Float()
    
#     def resolve_full_name(self, info):
#         return self.student.user.get_full_name()
    
#     def resolve_votes_count(self, info):
#         return self.votes.count()
    
#     def resolve_vote_percentage(self, info):
#         total_votes = (
#             Vote.objects.filter(
#                 election=self.election_position.election,
#                 candidate__election_position=self.election_position
#             ).count()
#         )
#         if total_votes > 0:
#             return (self.votes.count() / total_votes) * 100
#         return 0
    
#     def resolve_is_leading(self, info):
#         return (
#             ElectionResult.objects.filter(
#                 election=self.election_position.election,
#                 position_rank=1,
#                 candidate=self
#             ).exists()
#         )
    
#     def resolve_promises(self, info):
#         return self.promise_set.all()
    
#     def resolve_current_rating(self, info):
#         return (
#             Rating.objects.filter(leader__candidate=self)
#             .aggregate(avg_rating=Avg('score'))
#             .get('avg_rating')
#         )

class VoteType(DjangoObjectType):
    class Meta:
        model = Vote
        fields = '__all__'

    voter_name = graphene.String()
    
    def resolve_voter_name(self, info):
        return self.voter.user.get_full_name()

class ElectionResultType(DjangoObjectType):
    class Meta:
        model = ElectionResult
        fields = '__all__'

# class ElectionStatisticsType(DjangoObjectType):
#     class Meta:
#         model = ElectionStatistics
#         fields = '__all__'

# Leadership Types


class PromiseType(DjangoObjectType):
    class Meta:
        model = Promise
        fields = '__all__'

    status = graphene.String()
    updates = graphene.List(lambda: PromiseUpdateType)
    
    def resolve_status(self, info):
        latest_update = self.promiseupdate_set.order_by('-timestamp').first()
        return latest_update.status if latest_update else 'NOT_STARTED'
    
    def resolve_updates(self, info):
        return self.promiseupdate_set.all().order_by('-timestamp')

class PromiseUpdateType(DjangoObjectType):
    class Meta:
        model = PromiseUpdate
        fields = '__all__'

    status_display = graphene.String()
    
    def resolve_status_display(self, info):
        return self.get_status_display()

class RatingType(DjangoObjectType):
    class Meta:
        model = Rating
        fields = '__all__'

    voter_name = graphene.String()
    
    def resolve_voter_name(self, info):
        return self.student.user.get_full_name()

# Aggregation Types
class ElectionSummaryType(graphene.ObjectType):
    upcoming = graphene.Int()
    active = graphene.Int()
    completed = graphene.Int()
    total = graphene.Int()

class LeaderboardType(graphene.ObjectType):
    candidate = graphene.Field(CandidateType)
    votes = graphene.Int()
    position = graphene.String()
    election = graphene.String()

class InstitutionStatsType(graphene.ObjectType):
    institution = graphene.Field(InstitutionType)
    elections_count = graphene.Int()
    voters_count = graphene.Int()
    average_turnout = graphene.Float()
    current_leaders = graphene.List(LeaderType)

# Query Filters
class ElectionFilterInput(graphene.InputObjectType):
    status = graphene.String()
    level = graphene.String()
    institution_id = graphene.ID()
    academic_year_id = graphene.ID()
    is_active = graphene.Boolean()

class CandidateFilterInput(graphene.InputObjectType):
    election_id = graphene.ID()
    position_id = graphene.ID()
    institution_id = graphene.ID()
    is_approved = graphene.Boolean()

# Pagination Types
class PaginationType(graphene.ObjectType):
    total = graphene.Int()
    page = graphene.Int()
    pages = graphene.Int()
    has_next = graphene.Boolean()
    has_prev = graphene.Boolean()

class PaginatedElectionType(graphene.ObjectType):
    items = graphene.List(ElectionType)
    pagination = graphene.Field(PaginationType)

class PaginatedCandidateType(graphene.ObjectType):
    items = graphene.List(CandidateType)
    pagination = graphene.Field(PaginationType)
    
    
class ElectionStatisticsType(graphene.ObjectType):
    total_voters = graphene.Int()
    total_votes_cast = graphene.Int()
    voter_turnout = graphene.Float()
    leading_candidate = graphene.Field(CandidateOutput)
    calculated_at = graphene.DateTime()

    def resolve_total_voters(self, info):
        return self.total_voters

    def resolve_total_votes_cast(self, info):
        return self.total_votes_cast

    def resolve_voter_turnout(self, info):
        return self.voter_turnout

    def resolve_leading_candidate(self, info):
        return self.leading_candidate

    def resolve_calculated_at(self, info):
        return self.calculated_at


class PositionStatsType(graphene.ObjectType):
    position = graphene.Field(PositionOutput)
    election_count = graphene.Int()
    candidate_count = graphene.Int()
    average_votes_per_election = graphene.Float()
    most_contested_election = graphene.Field(ElectionOutput)

    def resolve_position(self, info):
        return self.position

    def resolve_election_count(self, info):
        return self.election_count

    def resolve_candidate_count(self, info):
        return self.candidate_count

    def resolve_average_votes_per_election(self, info):
        return self.average_votes_per_election

    def resolve_most_contested_election(self, info):
        return self.most_contested_election


class InstitutionStatsType(graphene.ObjectType):
    institution = graphene.Field(InstitutionOutput)
    election_count = graphene.Int()
    vote_count = graphene.Int()
    average_turnout = graphene.Float()
    most_active_election = graphene.Field(ElectionOutput)

    def resolve_institution(self, info):
        return self.institution

    def resolve_election_count(self, info):
        return self.election_count

    def resolve_vote_count(self, info):
        return self.vote_count

    def resolve_average_turnout(self, info):
        return self.average_turnout

    def resolve_most_active_election(self, info):
        return self.most_active_election
    
class ElectionWithStatsType(graphene.ObjectType):
    election = graphene.Field(ElectionOutput)
    stats = graphene.Field(ElectionStatisticsType)
    leading_candidates = graphene.List(CandidateOutput)
    
class DashboardStatsType(graphene.ObjectType):
    total_elections = graphene.Int()
    active_elections = graphene.Int()
    completed_elections = graphene.Int()
    upcoming_elections = graphene.Int()
    total_voters = graphene.Int()
    total_votes_cast = graphene.Int()
    voter_turnout = graphene.Float()
    recent_elections = graphene.List(ElectionOutput)
    active_elections_with_stats = graphene.List(ElectionWithStatsType)
    positions_with_most_contests = graphene.List(PositionStatsType)
    institutions_with_most_activity = graphene.List(InstitutionStatsType)
