from datetime import timezone
from election.outputs import *
import graphene
from graphene_django.types import DjangoObjectType
from django.db.models import Count, Avg, F
from .models import *
from django.db.models import Count, Q

from graphene import Field, List, Int, String, ID, InputObjectType, ObjectType

from django.db.models import Q, Count, Avg, Case, When, FloatField

# GraphQL Types
class VoteType(DjangoObjectType):
    class Meta:
        model = Vote


class ElectionType(DjangoObjectType):
    class Meta:
        model = Election

class CollegeType(DjangoObjectType):
    class Meta:
        model = College

class HostelType(DjangoObjectType):
    class Meta:
        model = Hostel

class UniversityType(DjangoObjectType):
    class Meta:
        model = University

class LeaderRatingType(DjangoObjectType):
    class Meta:
        model = LeaderRating

class PromiseImplementationType(DjangoObjectType):
    class Meta:
        model = PromiseImplementation

class PositionType(DjangoObjectType):
    class Meta:
        model = Position

class VoterTurnoutType(graphene.ObjectType):
    name = graphene.String()
    total_voters = graphene.Int()
    total_votes = graphene.Int()

class AverageRatingType(graphene.ObjectType):
    student_username = graphene.String()
    average_rating = graphene.Float()

class VoteDistributionType(graphene.ObjectType):
    name = graphene.String()
    total_votes = graphene.Int()

class VotesComparisonType(graphene.ObjectType):
    name = graphene.String()
    total_votes = graphene.Int()

class VoterTurnoutByHostelType(graphene.ObjectType):
    name = graphene.String()
    total_voters = graphene.Int()
    total_votes = graphene.Int()

class HostelVoteComparisonType(graphene.ObjectType):
    name = graphene.String()
    total_votes = graphene.Int()

class TopCandidateType(graphene.ObjectType):
    student_username = graphene.String()
    total_votes = graphene.Int()


class PromiseImplementationComparisonType(graphene.ObjectType):
    student_username = graphene.String()
    completed_promises = graphene.Int()
    pending_promises = graphene.Int()

class VoterTurnoutByUniversityType(graphene.ObjectType):
    name = graphene.String()
    total_voters = graphene.Int()
    total_votes = graphene.Int()

class VotesTrendForPositionType(graphene.ObjectType):
    election_name = graphene.String()
    total_votes = graphene.Int()
    

class VoteTrendType(graphene.ObjectType):
    timestamp = graphene.String()
    total_votes = graphene.Int()
        
class RatingsComparisonType(graphene.ObjectType):
    student_username = graphene.String()
    average_rating = graphene.Float()

# Input types for filtering
class LeaderFilters(graphene.InputObjectType):
    position = graphene.String()
    college = graphene.String()
    level = graphene.String()
    search = graphene.String()
    limit = graphene.Int()
    offset = graphene.Int()
    sort_by = graphene.String()
    sort_order = graphene.String()

class LeaderStatsType(graphene.ObjectType):
    totalLeaders = graphene.Int()
    avgRating = graphene.Float()
    avgPromiseCompletion = graphene.Float()
    totalPositions = graphene.Int()
    
class UserType(graphene.ObjectType):
    username = graphene.String()
    last_name = graphene.String()
    full_name = graphene.String()
    first_name = graphene.String()

    def resolve_username(self, info):
        return self.username

    def resolve_full_name(self, info):
        return self.get_full_name()

class LeaderListType(graphene.ObjectType):
    leaders = graphene.List(lambda: CandidateType)
    total_count = graphene.Int()
    
class StudentType(DjangoObjectType):
    class Meta:
        model = Student
        fields = ('id', 'hostel', 'college', 'university')

    user = graphene.Field(UserType)

    def resolve_user(self, info):
        return self.user
    
class CandidateType(DjangoObjectType):
    class Meta:
        model = Candidate
        fields = ('id', 'manifesto', 'position')

    student = graphene.Field(StudentType)
    vote_count = graphene.Int()
    rating = graphene.Float()
    promises_completed = graphene.Float()

    def resolve_student(self, info):
        return self.student

    def resolve_vote_count(self, info):
        return getattr(self, 'vote_count', self.votes.count())

    def resolve_rating(self, info):
        return getattr(self, 'rating', None)

    def resolve_promises_completed(self, info):
        return getattr(self, 'promises_completed', None)


# Query Resolvers
class StatisticsQuery(graphene.ObjectType):
    # 1. Total Votes per Candidate in a Specific Election
    total_votes_per_candidate = graphene.List(
        TopCandidateType,
        election_id=graphene.ID(required=True)
    )

    def resolve_total_votes_per_candidate(self, info, election_id):
        candidates = Candidate.objects.filter(position__elections__id=election_id) \
            .annotate(total_votes=Count('votes'))

        return [
            TopCandidateType(
                student_username=candidate.student.user.username,
                total_votes=candidate.total_votes,
            )
            for candidate in candidates
        ]

    # 2. Vote Distribution Across Colleges in a University Election
    vote_distribution_across_colleges = graphene.List(
    VoteDistributionType,
    election_id=graphene.ID(required=True)
   )


    def resolve_vote_distribution_across_colleges(self, info, election_id):
        return College.objects.filter(students__votes__election__id=election_id) \
            .annotate(total_votes=Count('students__votes')) \
            .values('name', 'total_votes')

    # 3. Vote Trends Over Time for a Specific Election
    vote_trends_over_time = graphene.List(
        VoteTrendType,
        election_id=graphene.ID(required=True)
    )

    def resolve_vote_trends_over_time(self, info, election_id):
        votes = Vote.objects.filter(election__id=election_id) \
            .extra(select={'timestamp': "DATE(timestamp)"}) \
            .values('timestamp') \
            .annotate(total_votes=Count('id')) \
            .order_by('timestamp')

        return [
            VoteTrendType(
                timestamp=vote['timestamp'],
                total_votes=vote['total_votes']
            )
            for vote in votes
        ]

    # 4. Comparison of Vote Counts Between Hostels in a College Election
    vote_comparison_between_hostels = graphene.List(
    HostelVoteComparisonType,
    election_id=graphene.ID(required=True)
)


    def resolve_vote_comparison_between_hostels(self, info, election_id):
        return Hostel.objects.filter(college__students__votes__election__id=election_id) \
            .annotate(total_votes=Count('students__votes')) \
            .values('name', 'total_votes')

    # 5. Leader Ratings Over Time
    leader_ratings_over_time = graphene.List(
        graphene.JSONString,
        candidate_id=graphene.ID(required=True)
    )

    def resolve_leader_ratings_over_time(self, info, candidate_id):
        return LeaderRating.objects.filter(leader__id=candidate_id) \
            .extra(select={'timestamp': "DATE(timestamp)"}) \
            .values('timestamp') \
            .annotate(average_rating=Avg('rating'))

    # 6. Comparison of Average Ratings Between Candidates in a College
    average_ratings_comparison = graphene.List(
    AverageRatingType,
    college_id=graphene.ID(required=True)
    )

    def resolve_average_ratings_comparison(self, info, college_id):
        return Candidate.objects.filter(student__college__id=college_id) \
            .annotate(average_rating=Avg('ratings__rating')) \
            .values('student__user__username', 'average_rating')

    # 7. Promise Implementation Status for a Candidate
    promise_implementation_status = graphene.List(
        graphene.JSONString,
        candidate_id=graphene.ID(required=True)
    )

    def resolve_promise_implementation_status(self, info, candidate_id):
        return PromiseImplementation.objects.filter(promise__candidate__id=candidate_id) \
            .values('status') \
            .annotate(count=Count('id'))

    # 8. Voter Turnout by College in a University Election
    voter_turnout_by_college = graphene.List(
        VoterTurnoutType,
        election_id=graphene.ID(required=True)
    )

    def resolve_voter_turnout_by_college(self, info, election_id):
        return College.objects.filter(students__votes__election__id=election_id) \
            .annotate(
                total_voters=Count('students', distinct=True),
                total_votes=Count('students__votes')
            ) \
            .values('name', 'total_voters', 'total_votes')

    # 9. Top 5 Candidates by Votes in a Specific Election
    top_candidates_by_votes = graphene.List(
        TopCandidateType,
        election_id=graphene.ID(required=True)
    )

    def resolve_top_candidates_by_votes(self, info, election_id):
        return Candidate.objects.filter(position__elections__id=election_id) \
            .annotate(total_votes=Count('votes')) \
            .order_by('-total_votes')[:5] \
            .values('student__user__username', 'total_votes')

    # 10. Vote Distribution by Position in an Election
    vote_distribution_by_position = graphene.List(
        HostelVoteComparisonType,
        election_id=graphene.ID(required=True)
    )

    def resolve_vote_distribution_by_position(self, info, election_id):
        return Position.objects.filter(elections__id=election_id) \
            .annotate(total_votes=Count('candidates__votes')) \
            .values('name', 'total_votes')

    # 11. Comparison of Vote Counts Between Universities
    vote_comparison_between_universities = graphene.List(
        graphene.JSONString,
        election_id=graphene.ID(required=True)
    )

    def resolve_vote_comparison_between_universities(self, info, election_id):
        return University.objects.filter(students__votes__election__id=election_id) \
            .annotate(total_votes=Count('students__votes')) \
            .values('name', 'total_votes')

    # 12. Trend of Votes for a Candidate Over Multiple Elections
    votes_trend_for_candidate = graphene.List(
        graphene.JSONString,
        candidate_id=graphene.ID(required=True)
    )

    def resolve_votes_trend_for_candidate(self, info, candidate_id):
        return Vote.objects.filter(candidate__id=candidate_id) \
            .values('election__name') \
            .annotate(total_votes=Count('id'))

    promise_implementation_comparison = graphene.List(
        PromiseImplementationComparisonType,
        election_id=graphene.ID(required=True)
    )

    def resolve_promise_implementation_comparison(self, info, election_id):
        candidates = Candidate.objects.filter(position__elections__id=election_id) \
            .annotate(
                completed_promises=Count(
                    'promises__implementations',
                    filter=Q(promises__implementations__status='COMPLETED')
                ),
                pending_promises=Count(
                    'promises__implementations',
                    filter=Q(promises__implementations__status='PENDING')
                )
            )

        results = []
        for candidate in candidates:
            results.append(PromiseImplementationComparisonType(
                student_username=candidate.student.user.username,
                completed_promises=candidate.completed_promises,
                pending_promises=candidate.pending_promises,
            ))

        return results

    # 14. Voter Turnout by Hostel in a College Election
    voter_turnout_by_hostel = graphene.List(
    VoterTurnoutByHostelType,
    election_id=graphene.ID(required=True)
)


    def resolve_voter_turnout_by_hostel(self, info, election_id):
        return Hostel.objects.filter(college__students__votes__election__id=election_id) \
            .annotate(
                total_voters=Count('students', distinct=True),
                total_votes=Count('students__votes')
            ) \
            .values('name', 'total_voters', 'total_votes')

    # 15. Comparison of Ratings Between Hostel Leaders
    ratings_comparison_between_hostel_leaders = graphene.List(
    RatingsComparisonType,
    hostel_id=graphene.ID(required=True)
)


    def resolve_ratings_comparison_between_hostel_leaders(self, info, hostel_id):
        return Candidate.objects.filter(student__hostel__id=hostel_id) \
            .annotate(average_rating=Avg('ratings__rating')) \
            .values('student__user__username', 'average_rating')

    # 16. Trend of Ratings for a Leader Over Time
    ratings_trend_for_leader = graphene.List(
        graphene.JSONString,
        candidate_id=graphene.ID(required=True)
    )

    def resolve_ratings_trend_for_leader(self, info, candidate_id):
        return LeaderRating.objects.filter(leader__id=candidate_id) \
            .extra(select={'timestamp': "DATE(timestamp)"}) \
            .values('timestamp') \
            .annotate(average_rating=Avg('rating'))

    # 17. Comparison of Votes Between Candidates for a Specific Position
    votes_comparison_for_position = graphene.List(
        graphene.JSONString,
        position_id=graphene.ID(required=True)
    )

    def resolve_votes_comparison_for_position(self, info, position_id):
        return Candidate.objects.filter(position__id=position_id) \
            .annotate(total_votes=Count('votes')) \
            .values('student__user__username', 'total_votes')

    # 18. Voter Turnout by University in All Elections
    voter_turnout_by_university = graphene.List(
        VoterTurnoutByUniversityType
    )

    def resolve_voter_turnout_by_university(self, info):
        return University.objects.annotate(
            total_voters=Count('students', distinct=True),
            total_votes=Count('students__votes')
        ) \
            .values('name', 'total_voters', 'total_votes')

    # 19. Comparison of Votes Between Colleges in a University Election
    votes_comparison_between_colleges = graphene.List(
    VotesComparisonType,
    election_id=graphene.ID(required=True)
        )


    def resolve_votes_comparison_between_colleges(self, info, election_id):
        return College.objects.filter(students__votes__election__id=election_id) \
            .annotate(total_votes=Count('students__votes')) \
            .values('name', 'total_votes')

    # 20. Trend of Votes for a Position Over Multiple Elections
    votes_trend_for_position = graphene.List(
        VotesTrendForPositionType,
        position_id=graphene.ID(required=True)
    )

    def resolve_votes_trend_for_position(self, info, position_id):
        return Vote.objects.filter(candidate__position__id=position_id) \
            .values('election__name') \
            .annotate(total_votes=Count('id'))
            
    # 1. College List
    college_list = graphene.List(CollegeType)

    def resolve_college_list(self, info):
        return College.objects.all()

    # 2. College Details
    college_details = graphene.Field(CollegeType, college_id=graphene.ID(required=True))

    def resolve_college_details(self, info, college_id):
        return College.objects.get(id=college_id)

    # 3. Candidate List
    candidate_list = graphene.List(CandidateType)

    def resolve_candidate_list(self, info):
        return Candidate.objects.all()

    # 4. Candidate Details
    candidate_details = graphene.Field(CandidateType, candidate_id=graphene.ID(required=True))

    def resolve_candidate_details(self, info, candidate_id):
        return Candidate.objects.get(id=candidate_id)

    # 5. University Details
    university_details = graphene.Field(UniversityType, university_id=graphene.ID(required=True))

    def resolve_university_details(self, info, university_id):
        return University.objects.get(id=university_id)

    # 6. Hostel List
    hostel_list = graphene.List(HostelType)

    def resolve_hostel_list(self, info):
        return Hostel.objects.all()

    # 7. Hostel Details
    hostel_details = graphene.Field(HostelType, hostel_id=graphene.ID(required=True))

    def resolve_hostel_details(self, info, hostel_id):
        return Hostel.objects.get(id=hostel_id)

    # 8. Hostels for a Given College
    hostels_for_college = graphene.List(HostelType, college_id=graphene.ID(required=True))

    def resolve_hostels_for_college(self, info, college_id):
        return Hostel.objects.filter(college_id=college_id)

    # 9. Position List
    position_list = graphene.List(PositionType)

    def resolve_position_list(self, info):
        return Position.objects.all()

    # 10. Position Details
    position_details = graphene.Field(PositionType, position_id=graphene.ID(required=True))

    def resolve_position_details(self, info, position_id):
        return Position.objects.get(id=position_id)

    # 11. Election List
    election_list = graphene.List(ElectionType)

    def resolve_election_list(self, info):
        return Election.objects.all()

    # 12. Election Details
    election_details = graphene.Field(ElectionType, election_id=graphene.ID(required=True))

    def resolve_election_details(self, info, election_id):
        return Election.objects.get(id=election_id)
    
    # Won Leaders Query
    won_leaders = graphene.List(
        CandidateType,
        election_id=graphene.ID(required=True),
        college_id=graphene.ID()
    )

    def resolve_won_leaders(self, info, election_id, college_id=None):
        # Get all candidates with votes in this election
        base_query = Candidate.objects.filter(
            position__elections__id=election_id,
            votes__isnull=False
        ).annotate(
            vote_count=Count('votes')
        ).order_by('-vote_count')

        # Filter by college if specified
        if college_id:
            base_query = base_query.filter(student__college__id=college_id)

        # Get the winner for each position (highest vote count)
        winners = []
        positions = Position.objects.filter(elections__id=election_id)
        
        for position in positions:
            winner = base_query.filter(position=position).first()
            if winner:
                winners.append(winner)
                
        return winners

    # Hostel Leader Stats Query
    hostel_leader_stats = graphene.List(
        graphene.JSONString,
        hostel_id=graphene.ID(required=True)
    )

    def resolve_hostel_leader_stats(self, info, hostel_id):
        return Candidate.objects.filter(
            student__hostel__id=hostel_id,
            votes__isnull=False
        ).annotate(
            vote_count=Count('votes'),
            avg_rating=Avg('ratings__rating')
        ).values(
            'student__user__username',
            'position__name',
            'vote_count',
            'avg_rating'
        )


    # Vote Trends Over Time Query
        
    election_stats = graphene.Field(ElectionStats)

    def resolve_election_stats(self, info):
        return {
            'active_elections': Election.objects.filter(
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            ).count(),
            'total_votes': Vote.objects.count(),
            'registered_voters': User.objects.count(),
            'total_candidates': Candidate.objects.count(),
            'participation_rate': (Vote.objects.count() / max(User.objects.count(), 1)) * 100
        }
    all_won_leaders = graphene.Field(
        LeaderListType,
        filters=LeaderFilters()
    )

    def resolve_all_won_leaders(self, info, filters=None):
        # Base queryset - only won leaders
        queryset = Candidate.objects.filter(
            votes__isnull=False
        ).annotate(
            vote_count=Count('votes'),
            rating=Avg('ratings__rating'),
            promises_completed=Avg(
                Case(
                    When(promises__implementations__status='COMPLETED', then=1),
                    default=0,
                    output_field=FloatField()
                )
            ) * 100
        ).distinct()

        # Default pagination values
        offset = 0
        limit = 10

        # Mapping GraphQL sort fields (camelCase) to Django ORM fields (snake_case)
        sort_field_mapping = {
            'voteCount': 'vote_count',
            'rating': 'rating',
            'promisesCompleted': 'promises_completed',
            'student': 'student__user__username',
        }

        if filters:
            # Apply filters
            if filters.get('position'):
                queryset = queryset.filter(position__id=filters['position'])
            if filters.get('college'):
                queryset = queryset.filter(student__college__id=filters['college'])
            if filters.get('level'):
                queryset = queryset.filter(position__level=filters['level'])
            if filters.get('search'):
                queryset = queryset.filter(
                    Q(student__user__username__icontains=filters['search']) |
                    Q(student__user__first_name__icontains=filters['search']) |
                    Q(student__user__last_name__icontains=filters['search'])
                )

            # Apply sorting
            sort_by = filters.get('sort_by', 'voteCount')
            sort_field = sort_field_mapping.get(sort_by, 'vote_count')
            sort_order = filters.get('sort_order', 'DESC')

            if sort_order == 'ASC':
                queryset = queryset.order_by(sort_field)
            else:
                queryset = queryset.order_by(f'-{sort_field}')

            # Pagination
            limit = filters.get('limit', limit)
            offset = filters.get('offset', offset)

        paginated_queryset = queryset[offset:offset + limit]

        return LeaderListType(
            leaders=paginated_queryset,
            total_count=queryset.count()
        )

    leader_stats = graphene.Field(LeaderStatsType)

    def resolve_leader_stats(self, info):
        # Calculate various statistics about leaders
        total_leaders = Candidate.objects.filter(votes__isnull=False).count()
        
        avg_rating = Candidate.objects.filter(
            votes__isnull=False
        ).annotate(
            rating=Avg('ratings__rating')
        ).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating']

        avg_promise_completion = Candidate.objects.filter(
            votes__isnull=False
        ).annotate(
            completion=Avg(
                Case(
                    When(promises__implementations__status='COMPLETED', then=1),
                    default=0,
                    output_field=FloatField()
                )
            ) * 100
        ).aggregate(
            avg_completion=Avg('completion')
        )['avg_completion']

        total_positions = Position.objects.filter(
            candidates__votes__isnull=False
        ).distinct().count()

        return {
            'totalLeaders': total_leaders,
            'avgRating': avg_rating,
            'avgPromiseCompletion': avg_promise_completion,
            'totalPositions': total_positions
        }