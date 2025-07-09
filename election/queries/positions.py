# schema.py
import decimal
import graphene
from graphene_django import DjangoObjectType
from election.types import CandidateType, DashboardStatsType, ElectionResultType, ElectionStatisticsType, ElectionTrendType, ElectionType, InstitutionDetails, InstitutionStatsType, InstitutionType, LeaderType, PositionStatsType, VoteRateType
from election.models import Candidate, ElectionPosition, ElectionResult, ElectionStatistics, InstitutionLevel, Leader, Position, Institution, AcademicYear, Election, Promise, PromiseUpdate, Rating, Student, Vote
from django.db.models import Q, F
import datetime
from django.db.models import Avg
from django.contrib.auth.models import User  # Assuming you're using the default User model
from django.db.models import Count, DateTimeField
from django.db.models.functions import TruncHour
from collections import defaultdict
from django.db.models.functions import TruncDay 
from django.db.models.functions import TruncDate  # Import this
from django.db.models import Count, DateTimeField
from django.db.models.functions import Trunc

from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncDate

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

        
# schema.py

class ElectionSummaryType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    status = graphene.String()
    start_datetime = graphene.DateTime()
    end_datetime = graphene.DateTime()
    academic_year = graphene.Field(AcademicYearType)
    level = graphene.Field(InstitutionLevelType)
    institution = graphene.Field(InstitutionType)
    total_candidates = graphene.Int()
    total_voters = graphene.Int()
    total_votes_cast = graphene.Int()
    voter_turnout = graphene.Float()
    leading_candidate = graphene.String()

class ElectionListType(graphene.ObjectType):
    elections = graphene.List(ElectionSummaryType)
    status_distribution = graphene.JSONString()
    level_distribution = graphene.JSONString()
    yearly_turnout = graphene.JSONString()
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
    predicted_winner= graphene.Field(CandidateType)  # New field
    prediction_confidence = graphene.Decimal()
    def resolve_candidates(parent, info):
        candidates = parent.get('candidates', [])
        predicted_winner = parent.get('predicted_winner', None)

        # Inject is_predicted_winner into each candidate object
        for c in candidates:
            setattr(c, 'is_predicted_winner', predicted_winner and c.id == predicted_winner.id)
        return candidates

class PositionFilterInput(graphene.InputObjectType):
    search = graphene.String()
    level = graphene.String()
    institution_id = graphene.ID()
    academic_year_id = graphene.ID()
    has_elections = graphene.Boolean()
    has_candidates = graphene.Boolean()

# class PositionStatsType(graphene.ObjectType):
#     level = graphene.String()
#     count = graphene.Int()
#     with_elections = graphene.Int()
#     with_candidates = graphene.Int()

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
    
# class ElectionType(DjangoObjectType):
#     class Meta:
#         model = Election
#         fields = '__all__'

class ElectionPositionType(DjangoObjectType):
    class Meta:
        model = ElectionPosition
        fields = '__all__'
    level = graphene.Field(InstitutionLevelType)
    def resolve_revel(self, info):
        return self.position.level
    
# class ElectionResultType(DjangoObjectType):
#     class Meta:
#         model = ElectionResult
#         fields = '__all__'


class RatingType(DjangoObjectType):
    class Meta:
        model = Rating
        fields = '__all__'

class PromiseUpdateType(DjangoObjectType):
    class Meta:
        model = PromiseUpdate
        fields = '__all__'
        
class PromiseType(DjangoObjectType):
    class Meta:
        model = Promise
        fields = '__all__'
    promise_updates = graphene.List(PromiseUpdateType)
    def resolve_promise_updates(self, info):
        return self.promise_updates.all()
    
class CandidateDetails(graphene.ObjectType):
    candidate = graphene.Field(CandidateType)
    election_details = graphene.Field(ElectionType)
    position_details = graphene.Field(PositionType)
    competitors = graphene.List(CandidateType)
    election_results = graphene.Field(ElectionResultType)
    vote_statistics = graphene.Field(VoteStatistics)
    leader_info = graphene.Field(LeaderType)
    ratings = graphene.List(RatingType)
    promises = graphene.List(PromiseType)
    
    
    
    
    
def get_vote_statistics(candidate, election_position):
    return VoteStatistics(
        vote_time_series=get_time_series_data(candidate, election_position),
        vote_distribution=get_vote_distribution(candidate, election_position),
        cumulative_votes=get_cumulative_votes(candidate, election_position),
        institutional_breakdown=get_institutional_breakdown(candidate, election_position)
    )
    
# def get_vote_statistics(self, candidate, election_position):
#     return VoteStatistics(
#         vote_time_series=self._get_time_series_data(candidate, election_position),
#         vote_distribution=self._get_vote_distribution(candidate, election_position),
#         cumulative_votes=self._get_cumulative_votes(candidate, election_position),
#         institutional_breakdown=self._get_institutional_breakdown(candidate, election_position)
#     )

def get_time_series_data(candidate, election_position):
    thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
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

def get_vote_distribution(candidate, election_position):
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

def get_cumulative_votes(candidate, election_position):
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

def get_institutional_breakdown(candidate, election_position):
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

    
    
class DistributionItemType(graphene.ObjectType):
    key = graphene.String()
    value = graphene.Int()
    status = graphene.String()
    count = graphene.Int()
    level = graphene.String()

class YearlyTurnoutItemType(graphene.ObjectType):
    year = graphene.String()
    turnout = graphene.Float()
    election_count = graphene.Int()

class ElectionListType(graphene.ObjectType):
    elections = graphene.List(ElectionSummaryType)
    status_distribution = graphene.List(DistributionItemType)
    level_distribution = graphene.List(DistributionItemType)
    yearly_turnout = graphene.List(YearlyTurnoutItemType)
    
class ElectionObjectType(DjangoObjectType):
    class Meta:
        model = Election
        fields = "__all__"

    positions = graphene.List(ElectionPositionType)
    statistics = graphene.Field(ElectionStatisticsType)
    candidate_performance = graphene.JSONString()
    time_series_data = graphene.JSONString()
    institution_breakdown = graphene.JSONString()

    def resolve_positions(self, info):
        return self.electionposition_set.all()

    def resolve_statistics(self, info):
        return ElectionStatistics.objects.filter(election=self).first()

    def resolve_candidate_performance(self, info):
        results = ElectionResult.objects.filter(
            election=self
        ).select_related('candidate__student__user', 'candidate__election_position__position')
        
        return [{
            'candidate_id': result.candidate.id,
            'name': f"{result.candidate.student.user.first_name} {result.candidate.student.user.last_name}",
            'position': result.candidate.election_position.position.name,
            'votes': result.total_votes,
            'percentage': float(result.percentage),
            'rank': result.position_rank,
            'is_winner': result.is_winner
        } for result in results]

    def resolve_time_series_data(self, info):
        votes = Vote.objects.filter(
            election=self
        ).order_by('timestamp')
        
        if not votes.exists():
            return None

        # Create hourly buckets
        start_time = self.start_datetime
        end_time = self.end_datetime
        time_delta = end_time - start_time
        hours = int(time_delta.total_seconds() / 3600) + 1
        
        time_series = []
        for i in range(hours):
            current_hour = start_time + datetime.timedelta(hours=i)
            next_hour = current_hour + datetime.timedelta(hours=1)
            
            hour_votes = votes.filter(
                timestamp__gte=current_hour,
                timestamp__lt=next_hour
            ).count()
            
            time_series.append({
                'hour': current_hour.strftime('%Y-%m-%d %H:00'),
                'votes': hour_votes,
                'cumulative_votes': votes.filter(timestamp__lt=next_hour).count()
            })
        
        return time_series

    def resolve_institution_breakdown(self, info):
        votes = Vote.objects.filter(election=self)
        institutions = Institution.objects.filter(
            student__votes_cast__election=self
        ).distinct().annotate(
            vote_count=Count('student__votes_cast')
        )
        
        return [{
            'institution_id': inst.id,
            'name': inst.name,
            'level': inst.level.level,
            'votes': inst.vote_count,
            'percentage': (inst.vote_count / votes.count()) * 100 if votes.count() > 0 else 0
        } for inst in institutions]


class PositionQuery(graphene.ObjectType):
    all_institutions = graphene.List(InstitutionType)
    academic_years = graphene.List(AcademicYearType)
    dashboard_stats = graphene.Field(DashboardStatsType)
    positions_with_most_contests = graphene.List(PositionStatsType)
    institutions_with_most_activity = graphene.List(InstitutionStatsType)
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
        from .election_utils import predictor  # Import the predictor instance

        # Fetch the position object
        position = Position.objects.get(id=position_id)
        
        # Build the base query for election position
        election_position_query = position.electionposition_set.all().order_by("election__academic_year")
        
        # Filter by election_id if provided
        if academic_year_id:
            election_position_query = election_position_query.filter(election__academic_year__id=academic_year_id)
        if election_id:
            election_position_query = election_position_query.filter(election__id=election_id)
        
        election_position = election_position_query.first()

        if not election_position:
            return None

        candidates = Candidate.objects.filter(election_position=election_position)

        # =============================================
        # NEW: Simple AI prediction integration
        # =============================================
        predicted_winner_id, prediction_confidence = predictor.predict_winner(
            election_position, 
            candidates,
            position
        )
        
        predicted_winner = None
        if predicted_winner_id:
            try:
                predicted_winner = Candidate.objects.get(id=predicted_winner_id)
                print(predicted_winner.student.user.username)
            except Candidate.DoesNotExist:
                print("candidate does not exists")
                pass

        # =============================================
        # Original resolver logic remains unchanged
        # =============================================
        from django.utils import timezone
        now = timezone.now()
        if election_position.election.status == 'ACTIVE':
            time_threshold = now - datetime.timedelta(hours=24)
            time_window = datetime.timedelta(hours=1)
        else:
            time_threshold = election_position.election.start_datetime
            time_window = datetime.timedelta(hours=6)

        votes = Vote.objects.filter(
            election=election_position.election,
            candidate__election_position=election_position,
            timestamp__gte=time_threshold
        ).order_by('timestamp')

        current_window_start = time_threshold
        vote_counts = {candidate.id: 0 for candidate in candidates}
        vote_time_series = []

        for vote in votes:
            while vote.timestamp >= current_window_start + time_window:
                for candidate in candidates:
                    hours = time_window.total_seconds() / 3600
                    vote_rate = vote_counts[candidate.id] / hours
                    vote_time_series.append({
                        'timestamp': current_window_start,
                        'candidate_id': candidate.id,
                        'vote_count': vote_counts[candidate.id],
                        'vote_rate_per_hour': vote_rate,
                        'is_predicted_winner': candidate.id == predicted_winner_id
                    })
                current_window_start += time_window
                vote_counts = {candidate.id: 0 for candidate in candidates}
            
            vote_counts[vote.candidate.id] += 1

        for candidate in candidates:
            hours = time_window.total_seconds() / 3600
            vote_rate = vote_counts[candidate.id] / hours
            vote_time_series.append({
                'timestamp': current_window_start,
                'candidate_id': candidate.id,
                'vote_count': vote_counts[candidate.id],
                'vote_rate_per_hour': vote_rate,
                'is_predicted_winner': candidate.id == predicted_winner_id
            })

        if position.level.level == 'HOSTEL':
            total_voters = Student.objects.filter(
                institution=position.institution
            ).count()
        elif position.level.level == 'COLLEGE':
            total_voters = Student.objects.filter(
                institution=position.institution.parent
            ).count()
        else:
            total_voters = Student.objects.count()
        
        total_votes = Vote.objects.filter(
            election=election_position.election,
            candidate__election_position=election_position
        ).count()
        
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
            'winner': winner,
            'predicted_winner': predicted_winner,
            'prediction_confidence': decimal.Decimal(str(prediction_confidence)) if prediction_confidence is not None else None
        }

    candidate_details = graphene.Field(
        CandidateDetails,
        candidate_id=graphene.ID(required=True)
    )

    def resolve_candidate_details(root, info, candidate_id):
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

        election_position = candidate.election_position
        election = election_position.election
        position = election_position.position

        competitors = Candidate.objects.filter(
            election_position=election_position
        ).exclude(id=candidate.id).select_related(
            'student__user',
            'student__institution'
        )

        election_results = ElectionResult.objects.filter(
            election=election,
            candidate=candidate
        ).first()

        vote_statistics = get_vote_statistics(candidate, election_position)

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
            )
            # .prefetch_related('promiseupdate_set')

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
    all_elections = graphene.List(ElectionType)

    def resolve_all_elections(root, info):
        return Election.objects.all().order_by('-start_datetime')


    institution_details = graphene.Field(
        InstitutionDetails,
        institution_id=graphene.ID(required=True)
    )
    
    def resolve_institution_details(root, info, institution_id):
        try:
            institution = Institution.objects.select_related('level', 'parent').get(id=institution_id)
        except Institution.DoesNotExist:
            return None
        
        parent = institution.parent
        children = Institution.objects.filter(parent=institution)
        
        # Build hierarchy path
        hierarchy = []
        current = institution
        while current:
            hierarchy.insert(0, {
                'id': current.id,
                'name': current.name,
                'level': current.level.level
            })
            current = current.parent
        
        return InstitutionDetails(
            institution=institution,
            parent_institution=parent,
            child_institutions=children,
            hierarchy=hierarchy
        )

    election_trends = graphene.List(
        ElectionTrendType,
        institution_id=graphene.ID(required=True)
    )

    def resolve_election_trends(self, info, institution_id):
        # Filter elections by institution
        elections = Election.objects.filter(institution_id=institution_id)

        # Annotate year from start_datetime
        trends = {}
        for election in elections:
            year = election.start_datetime.year
            if year not in trends:
                trends[year] = {
                    'elections': 0,
                    'voters': 0,
                    'turnout_total': 0.0,
                    'turnout_count': 0
                }
            trends[year]['elections'] += 1

            try:
                stats = ElectionStatistics.objects.get(election=election)
                trends[year]['voters'] += stats.total_voters
                trends[year]['turnout_total'] += float(stats.voter_turnout)
                trends[year]['turnout_count'] += 1
            except ElectionStatistics.DoesNotExist:
                pass

        # Format the results
        result = []
        for year, data in trends.items():
            avg_turnout = (
                data['turnout_total'] / data['turnout_count']
                if data['turnout_count'] > 0 else 0.0
            )
            result.append(ElectionTrendType(
                year=str(year),
                elections=data['elections'],
                voters=data['voters'],
                turnout=round(avg_turnout, 2)
            ))

        # Sort by year descending
        return sorted(result, key=lambda x: x.year, reverse=True)
    

    election_details = graphene.Field(
        ElectionObjectType,
        election_id=graphene.ID(required=True)
    )
    
    def resolve_election_details(root, info, election_id):
        try:
            return Election.objects.select_related(
                'academic_year',
                'level',
                'institution'
            ).prefetch_related(
                'electionposition_set__position',
                'electionposition_set__candidate_set__student__user'
            ).get(id=election_id)
        except Election.DoesNotExist:
            return None


    election_list = graphene.Field(
        ElectionListType,
        level=graphene.String(),
        status=graphene.String(),
        academic_year=graphene.ID()
    )

    def resolve_election_list(root, info, level=None, status=None, academic_year=None):
        # Base query
        elections = Election.objects.select_related(
            'academic_year',
            'level',
            'institution'
        ).prefetch_related(
            'electionposition_set__candidate_set'
        )

        # Apply filters
        if level:
            elections = elections.filter(level__level=level)
        if status:
            elections = elections.filter(status=status)
        if academic_year:
            elections = elections.filter(academic_year__id=academic_year)

        # Get statistics for each election
        election_summaries = []
        for election in elections:
            stats = ElectionStatistics.objects.filter(election=election).first()
            total_candidates = sum(
                ep.candidate_set.count() 
                for ep in election.electionposition_set.all()
            )
            
            summary = {
                'id': election.id,
                'name': election.name,
                'status': election.status,
                'start_datetime': election.start_datetime,
                'end_datetime': election.end_datetime,
                'academic_year': election.academic_year,
                'level': election.level,
                'institution': election.institution,
                'total_candidates': total_candidates,
                'total_voters': stats.total_voters if stats else 0,
                'total_votes_cast': stats.total_votes_cast if stats else 0,
                'voter_turnout': float(stats.voter_turnout) if stats else 0,
                'leading_candidate': (
                    f"{stats.leading_candidate.student.user.first_name} {stats.leading_candidate.student.user.last_name}"
                    if stats and stats.leading_candidate else None
                )
            }
            election_summaries.append(summary)

        # Calculate distributions
        status_distribution = (
            Election.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        level_distribution = (
            Election.objects.values('level__level')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # Calculate yearly turnout
        yearly_turnout = (
            ElectionStatistics.objects
            .values('election__academic_year__name')
            .annotate(
                avg_turnout=Avg('voter_turnout'),
                election_count=Count('id')
            )
            .order_by('election__academic_year__start_date')
        )

        return ElectionListType(
            elections=election_summaries,
            status_distribution=[
                {'status': item['status'], 'count': item['count']}
                for item in status_distribution
            ],
            level_distribution=[
                {'level': item['level__level'], 'count': item['count']}
                for item in level_distribution
            ],
            yearly_turnout=[
                {
                    'year': item['election__academic_year__name'],
                    'turnout': float(item['avg_turnout']),
                    'election_count': item['election_count']
                }
                for item in yearly_turnout
            ]
        )
        
    
    def resolve_dashboard_stats(self, info, **kwargs):
        # Calculate basic stats
        total_elections = Election.objects.count()
        active_elections = Election.objects.filter(status='ACTIVE').count()
        completed_elections = Election.objects.filter(status='COMPLETED').count()
        upcoming_elections = Election.objects.filter(status='UPCOMING').count()
        
        # Get voter statistics
        total_voters = Student.objects.filter(is_active=True).count()
        total_votes_cast = Vote.objects.count()
        voter_turnout = (total_votes_cast / total_voters * 100) if total_voters > 0 else 0
        
        # Get recent elections
        recent_elections = Election.objects.order_by('-start_datetime')[:5]
        
        # Get active elections with their stats
        active_elections_with_stats = []
        for election in Election.objects.filter(status='ACTIVE'):
            stats = ElectionStatistics.objects.filter(election=election).first()
            leading_candidates = []
            
            if stats and stats.leading_candidate:
                leading_candidates.append(stats.leading_candidate)
                
            active_elections_with_stats.append({
                'election': election,
                'stats': stats,
                'leading_candidates': leading_candidates
            })
        
        # Get positions with most contests
        positions_with_most_contests = Position.objects.annotate(
            election_count=Count('elections')
        ).order_by('-election_count')[:5]
        
        # Get institutions with most activity
        institutions_with_most_activity = Institution.objects.annotate(
            election_count=Count('election'),
            vote_count=Count('election__votes')
        ).order_by('-election_count', '-vote_count')[:5]
        
        return {
            'total_elections': total_elections,
            'active_elections': active_elections,
            'completed_elections': completed_elections,
            'upcoming_elections': upcoming_elections,
            'total_voters': total_voters,
            'total_votes_cast': total_votes_cast,
            'voter_turnout': voter_turnout/Election.objects.count(),
            'recent_elections': recent_elections,
            'active_elections_with_stats': active_elections_with_stats,
            'positions_with_most_contests': positions_with_most_contests,
            'institutions_with_most_activity': institutions_with_most_activity
        }
        
# from django.db.models import Count, Avg

    def resolve_positions_with_most_contests(self, info, **kwargs):
        # Get positions with most elections
        positions = Position.objects.annotate(
            election_count=Count('elections', distinct=True)
        ).order_by('-election_count')[:10]

        position_stats = []
        for position in positions:
            # Average votes per election (for this position)
            avg_votes = ElectionPosition.objects.filter(
                position=position
            ).annotate(
                vote_count=Count('election__votes')
            ).aggregate(
                avg_votes=Avg('vote_count')
            )['avg_votes'] or 0

            # Most contested election for this position
            most_contested = Election.objects.filter(
                electionposition__position=position
            ).annotate(
                candidate_count=Count('electionposition__candidates', distinct=True),
                vote_count=Count('votes', distinct=True)
            ).order_by('-candidate_count', '-vote_count').first()

            position_stats.append({
                'position': position,
                'election_count': position.election_count,
                'candidate_count': getattr(most_contested, 'candidate_count', 0),
                'average_votes_per_election': avg_votes,
                'most_contested_election': most_contested
            })

        return position_stats


    def resolve_institutions_with_most_activity(self, info, **kwargs):
        # Get institutions with most elections and votes
        institutions = Institution.objects.annotate(
            election_count=Count('elections', distinct=True),
            vote_count=Count('elections__votes', distinct=True),
        ).order_by('-election_count', '-vote_count')[:10]  # Get top 10
        
        institution_stats = []
        for institution in institutions:
            # Calculate average turnout for this institution
            avg_turnout = Election.objects.filter(
                institution=institution
            ).annotate(
                turnout=F('total_votes_cast') * 100.0 / F('total_voters')
            ).aggregate(
                avg_turnout=Avg('turnout')
            )['avg_turnout'] or 0
            
            # Get most active election for this institution
            most_active = Election.objects.filter(
                institution=institution
            ).annotate(
                vote_count=Count('votes')
            ).order_by('-vote_count').first()
            
            institution_stats.append({
                'institution': institution,
                'election_count': institution.election_count,
                'vote_count': institution.vote_count,
                'average_turnout': avg_turnout,
                'most_active_election': most_active
            })
        
        return institution_stats