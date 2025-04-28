# schema.py
import graphene
from graphene_django import DjangoObjectType
from election.models import Candidate, ElectionResult, InstitutionLevel, Position, Institution, AcademicYear, Election, Promise, Rating, Student, Vote
from django.db.models import Q
import datetime
from django.db.models import Avg
from django.contrib.auth.models import User  # Assuming you're using the default User model
from django.db.models import Count, DateTimeField
from django.db.models.functions import TruncHour
from collections import defaultdict
from django.db.models.functions import TruncDay 

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'full_name')  # Customize the fields as needed

    full_name = graphene.String()

    # Custom resolver for full_name
    def resolve_full_name(self, info):
        return self.get_full_name()

class InstitutionLevelType(DjangoObjectType):
    class Meta:
        model = InstitutionLevel
        fields = '__all__'

class AcademicYearType(DjangoObjectType):
    class Meta:
        model = AcademicYear
        fields = '__all__'


class InstitutionType(DjangoObjectType):
    class Meta:
        model = Institution
        fields = '__all__'

    parent = graphene.Field(lambda: InstitutionType)
    children = graphene.List(lambda: InstitutionType)
    hierarchy = graphene.List(lambda: InstitutionType)
    student_count = graphene.Int()
    leader_count = graphene.Int()
    
    def resolve_parent(self, info):
        return self.parent
    
    def resolve_children(self, info):
        return self.institution_set.all()
    
    def resolve_hierarchy(self, info):
        def get_hierarchy(obj):
            if obj.parent:
                return get_hierarchy(obj.parent) + [obj]
            return [obj]
        return get_hierarchy(self)
    
    def resolve_student_count(self, info):
        return self.student_set.count()
    
    def resolve_leader_count(self, info):
        return self.leader_set.count()
    
class PositionType(DjangoObjectType):
    class Meta:
        model = Position
        fields = '__all__'
    
    election_count = graphene.Int()
    candidate_count = graphene.Int()
    
    def resolve_election_count(self, info):
        return self.elections.count()
    
    def resolve_candidate_count(self, info):
        # Correct path: Position -> ElectionPosition -> Candidate
        return Candidate.objects.filter(election_position__position=self).count()

class StudentType(DjangoObjectType):
    class Meta:
        model = Student
        fields = '__all__'  # You can specify the fields you want to expose, or just use '__all__' to expose everything
    
    # Optionally, you can add custom fields if needed
    full_name = graphene.String()
    academic_year = graphene.Field(AcademicYearType)
    institution = graphene.Field(InstitutionType)
    user = graphene.Field(UserType)

    # Optionally, a custom resolver for the full name
    def resolve_full_name(self, info):
        return self.user.get_full_name()  # Assuming 'user' is a ForeignKey to a User model
    
    def resolve_academic_year(self, info):
        return self.academic_year

    def resolve_institution(self, info):
        return self.institution
    
    def resolve_user(self, info):
        return self.user 
     # Changed from TruncHour

class VoteRateType(graphene.ObjectType):
    day = graphene.Date()  # Changed from hour to day
    vote_count = graphene.Int()
    
class CandidateType(DjangoObjectType):
    class Meta:
        model = Candidate
        fields = '__all__'

    # Define the student field explicitly
    student = graphene.Field(StudentType)  # Assuming you have a StudentType for the Student model

    # Add a resolver for the student field
    def resolve_student(self, info):
        return self.student  # Return the related Student object

    vote_count = graphene.Int()
    vote_percentage = graphene.Float()
    is_winner = graphene.Boolean()
    promises_count = graphene.Int()
    rating = graphene.Float()
    daily_vote_rates = graphene.List(VoteRateType)

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
    
    def resolve_daily_vote_rates(self, info):
        # Query to get vote counts per day for this candidate
        vote_rates = (
            self.votes.annotate(
                day=TruncDay('timestamp')  # Changed to TruncDay
            )
            .values('day')
            .annotate(vote_count=Count('id'))
            .order_by('day')
        )
        
        return [
            VoteRateType(day=rate['day'], vote_count=rate['vote_count'])
            for rate in vote_rates
        ]

class VoteTimeSeriesType(graphene.ObjectType):
    timestamp = graphene.DateTime()
    count = graphene.Int()
    candidate_id = graphene.ID()

class PositionDetailsType(graphene.ObjectType):
    position = graphene.Field(PositionType)
    candidates = graphene.List(CandidateType)
    vote_time_series = graphene.List(VoteTimeSeriesType)
    total_voters = graphene.Int()
    total_votes = graphene.Int()
    is_election_active = graphene.Boolean()
    winner = graphene.Field(CandidateType)

class PositionFilterInput(graphene.InputObjectType):
    search = graphene.String()
    level = graphene.String()
    institution_id = graphene.ID()
    academic_year_id = graphene.ID()
    has_elections = graphene.Boolean()
    has_candidates = graphene.Boolean()

class PositionStatsType(graphene.ObjectType):
    level = graphene.String()
    count = graphene.Int()
    with_elections = graphene.Int()
    with_candidates = graphene.Int()

class PositionQuery(graphene.ObjectType):
    all_institutions = graphene.List(InstitutionType)
    academic_years = graphene.List(AcademicYearType)
    all_positions = graphene.List(
        PositionType,
        filters=PositionFilterInput(),
        first=graphene.Int(),
        skip=graphene.Int()
    )
    position_stats = graphene.List(PositionStatsType)
    position_details = graphene.Field(
        PositionDetailsType,
        position_id=graphene.ID(required=True),
        election_id=graphene.ID(required=False),
        academic_year_id=graphene.ID(required=False)  # Add academic_year_id parameter
    )
    
    def resolve_all_positions(self, info, filters=None, first=None, skip=None, **kwargs):
        qs = Position.objects.all()
        
        if filters:
            if filters.search:
                qs = qs.filter(
                    Q(name__icontains=filters.search) |
                    Q(description__icontains=filters.search)
                )
            
            if filters.level:
                qs = qs.filter(level__level=filters.level)
            
            if filters.institution_id:
                qs = qs.filter(institution__id=filters.institution_id)
            
            if filters.academic_year_id:
                qs = qs.filter(elections__academic_year__id=filters.academic_year_id).distinct()
            
            if filters.has_elections:
                qs = qs.filter(elections__isnull=not filters.has_elections).distinct()
            
            if filters.has_candidates:
                qs = qs.filter(candidates__isnull=not filters.has_candidates).distinct()
        
        if skip:
            qs = qs[skip:]
        if first:
            qs = qs[:first]
        
        return qs
    
    def resolve_position_stats(self, info, **kwargs):
        stats = []
        
        # Prefetch related elections and candidates to minimize queries
        levels = InstitutionLevel.objects.all()
        
        for level in levels:
            positions = Position.objects.filter(level=level).prefetch_related(
                'elections',  # Prefetch related elections for each position
                'electionposition__candidate'  # Prefetch related candidates
            )

            total_positions = positions.count()
            positions_with_elections = positions.filter(elections__isnull=False).distinct().count()
            positions_with_candidates = positions.filter(
                electionposition__candidate__isnull=False
            ).distinct().count()

            stats.append({
                'level': level.get_level_display(),
                'count': total_positions,
                'with_elections': positions_with_elections,
                'with_candidates': positions_with_candidates
            })
        
        return stats


    def resolve_all_institutions(self, info):
        return Institution.objects.filter(parent__isnull=True)

    def resolve_academic_years(self, info):
        return AcademicYear.objects.all()
        

    def resolve_position_details(self, info, position_id, election_id=None, academic_year_id=None):
        # Fetch the position object
        position = Position.objects.get(id=position_id)

        # Build the base query for election position
        election_position_query = position.electionposition_set.all()
        
        # Filter by election_id if provided
        if election_id:
            election_position_query = election_position_query.filter(election_id=election_id)
        
        # Filter by academic_year_id if provided
        if academic_year_id:
            election_position_query = election_position_query.filter(
                election__academic_year__id=academic_year_id
            )
        
        election_position = election_position_query.first()
        
        if not election_position:
            return None

        # Fetch candidates
        candidates = election_position.candidate_set.all()

        # Define time range
        now = datetime.datetime.now()
        if election_position.election.status == 'ACTIVE':
            time_threshold = now - datetime.timedelta(hours=24)
            time_window = datetime.timedelta(hours=1)
        else:
            time_threshold = election_position.election.start_datetime
            time_window = datetime.timedelta(hours=6)

        # Fetch votes for this election position
        votes = Vote.objects.filter(
            election=election_position.election,
            candidate__election_position=election_position,
            timestamp__gte=time_threshold
        ).order_by('timestamp')

        # Set up time buckets
        current_window_start = time_threshold
        vote_counts = {candidate.id: 0 for candidate in candidates}
        vote_time_series = []

        for vote in votes:
            # Advance time window if needed
            while vote.timestamp >= current_window_start + time_window:
                for candidate in candidates:
                    # Calculate rate: votes per hour
                    hours = time_window.total_seconds() / 3600
                    vote_rate = vote_counts[candidate.id] / hours
                    vote_time_series.append({
                        'timestamp': current_window_start,
                        'candidate_id': candidate.id,
                        'vote_count': vote_counts[candidate.id],
                        'vote_rate_per_hour': vote_rate
                    })
                current_window_start += time_window
                vote_counts = {candidate.id: 0 for candidate in candidates}
            
            # Tally vote
            vote_counts[vote.candidate.id] += 1

        # Final window
        for candidate in candidates:
            hours = time_window.total_seconds() / 3600
            vote_rate = vote_counts[candidate.id] / hours
            vote_time_series.append({
                'timestamp': current_window_start,
                'candidate_id': candidate.id,
                'vote_count': vote_counts[candidate.id],
                'vote_rate_per_hour': vote_rate
            })

        # Total voters
        if position.level.level == 'HOSTEL':
            total_voters = Student.objects.filter(
                institution=position.institution.parent
            ).count()
        elif position.level.level == 'COLLEGE':
            total_voters = Student.objects.filter(
                institution=position.institution
            ).count()
        else:  # UNIVERSITY
            total_voters = Student.objects.count()
        
        # Total votes
        total_votes = Vote.objects.filter(
            election=election_position.election,
            candidate__election_position=election_position
        ).count()
        
        # Winner
        winner_result = ElectionResult.objects.filter(
            election=election_position.election,
            candidate__election_position=election_position,
            is_winner=True
        ).first()
        winner = winner_result.candidate if winner_result else None

        return {
            'position': position,
            'candidates': candidates,
            'vote_time_series': vote_time_series,
            'total_voters': total_voters,
            'total_votes': total_votes,
            'is_election_active': election_position.election.status == 'ACTIVE',
            'winner': winner
        }
