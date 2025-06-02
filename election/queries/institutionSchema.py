import graphene
from graphene_django.types import DjangoObjectType
from django.db.models import Count, Q
from ..models import *

class InstitutionStatsType(graphene.ObjectType):
    total_students = graphene.Int()
    active_elections = graphene.Int()
    total_votes_cast = graphene.Int()
    voter_turnout = graphene.Float()
    positions_available = graphene.Int()
    current_leaders = graphene.Int()

class CollegeDistributionType(graphene.ObjectType):
    name = graphene.String()
    student_count = graphene.Int()
    percentage = graphene.Float()

class ElectionTrendType(graphene.ObjectType):
    year = graphene.String()
    elections = graphene.Int()
    voters = graphene.Int()
    turnout = graphene.Float()

# class InstitutionType(DjangoObjectType):
#     class Meta:
#         model = Institution
#         fields = "__all__"

class AcademicYearType(DjangoObjectType):
    class Meta:
        model = Institution
        fields = "__all__"

class CandidateType(DjangoObjectType):
    class Meta:
        model = Candidate
        fields = "__all__"

class ElectionType(DjangoObjectType):
    class Meta:
        model = Election
        fields = "__all__"

class InstitutionQuery(graphene.ObjectType):
    institution_details = graphene.Field(
        InstitutionStatsType,
        institution_id=graphene.ID(required=True))
    
    college_distribution = graphene.List(
        CollegeDistributionType,
        parent_institution_id=graphene.ID())
    
    election_trends = graphene.List(
        ElectionTrendType,
        institution_id=graphene.ID(required=True))
    
    def resolve_institution_details(self, info, institution_id):
        institution = Institution.objects.get(pk=institution_id)
        
        # Calculate stats
        total_students = Student.objects.filter(institution=institution).count()
        
        active_elections = Election.objects.filter(
            institution=institution,
            status='ACTIVE'
        ).count()
        
        total_votes_cast = Vote.objects.filter(
            election__institution=institution
        ).count()
        
        voter_turnout = (total_votes_cast / total_students * 100) if total_students > 0 else 0
        
        positions_available = Position.objects.filter(
            institution=institution
        ).count()
        
        current_leaders = Leader.objects.filter(
            institution=institution,
            is_active=True
        ).count()
        
        return InstitutionStatsType(
            total_students=total_students,
            active_elections=active_elections,
            total_votes_cast=total_votes_cast,
            voter_turnout=voter_turnout,
            positions_available=positions_available,
            current_leaders=current_leaders
        )
    
    def resolve_college_distribution(self, info, parent_institution_id=None):
        parent = Institution.objects.get(pk=parent_institution_id) if parent_institution_id else None
        
        if parent:
            colleges = Institution.objects.filter(parent=parent)
        else:
            # For university level, get all colleges
            colleges = Institution.objects.filter(
                level__level='COLLEGE'
            )
        
        total_students = Student.objects.filter(
            institution__in=colleges
        ).count()
        
        distribution = []
        for college in colleges:
            student_count = Student.objects.filter(institution=college).count()
            percentage = (student_count / total_students * 100) if total_students > 0 else 0
            
            distribution.append(CollegeDistributionType(
                name=college.name,
                student_count=student_count,
                percentage=percentage
            ))
        
        return distribution
    
    def resolve_election_trends(self, info, institution_id):
        institution = Institution.objects.get(pk=institution_id)
        
        # Group elections by academic year
        trends = Election.objects.filter(
            institution=institution
        ).values(
            'academic_year__name'
        ).annotate(
            election_count=Count('id'),
            voter_count=Count('votes', distinct=True),
            total_voters=Count('positions__candidates__student', distinct=True)
        ).order_by('academic_year__start_date')
        
        return [
            ElectionTrendType(
                year=trend['academic_year__name'],
                elections=trend['election_count'],
                voters=trend['voter_count'],
                turnout=(trend['voter_count'] / trend['total_voters'] * 100) if trend['total_voters'] > 0 else 0
            )
            for trend in trends
        ]
    

    institutions_by_level = graphene.List(
        InstitutionType,
        level=graphene.String(required=True)
    )
    
    academic_years = graphene.List(
        AcademicYearType,
        is_current=graphene.Boolean()
    )
    
    election_contestants = graphene.List(
        CandidateType,
        institution_id=graphene.ID(required=True),
        election_id=graphene.ID(),
        position_id=graphene.ID(),
        academic_year_id=graphene.ID()
    )
    
    def resolve_institutions_by_level(self, info, level):
        return Institution.objects.filter(
            level__level=level
        ).select_related('parent', 'level')
    
    def resolve_academic_years(self, info, is_current=None):
        queryset = AcademicYear.objects.all()
        if is_current is not None:
            queryset = queryset.filter(is_current=is_current)
        return queryset.order_by('-start_date')
    
    def resolve_election_contestants(self, info, institution_id, **kwargs):
        filters = {
            'election_position__election__institution_id': institution_id
        }
        
        if kwargs.get('election_id'):
            filters['election_position__election_id'] = kwargs['election_id']
        if kwargs.get('position_id'):
            filters['election_position__position_id'] = kwargs['position_id']
        if kwargs.get('academic_year_id'):
            filters['election_position__election__academic_year_id'] = kwargs['academic_year_id']
        
        return Candidate.objects.filter(**filters).select_related(
            'student__user',
            'election_position__election',
            'election_position__position'
        ).order_by('election_position__position__name')