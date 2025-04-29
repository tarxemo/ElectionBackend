# election/queries/macqueries.py
import graphene
from graphene_django import DjangoObjectType
from django.db.models import Prefetch, Q
from ..models import (
    Institution, Candidate, Position, ElectionResult,
    Vote, Student, User, ElectionPosition,
    InstitutionLevel, AcademicYear, Election
)

# ====================
# TYPE DEFINITIONS
# ====================

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email')

class AcademicYearType(DjangoObjectType):
    class Meta:
        model = AcademicYear
        fields = '__all__'

class InstitutionLevelType(DjangoObjectType):
    class Meta:
        model = InstitutionLevel
        fields = '__all__'

class ElectionResultType(DjangoObjectType):
    class Meta:
        model = ElectionResult
        fields = ('total_votes', 'percentage', 'position_rank', 'is_winner')

class VoteType(DjangoObjectType):
    class Meta:
        model = Vote
        fields = '__all__'

class ElectionPositionType(DjangoObjectType):
    class Meta:
        model = ElectionPosition
        fields = '__all__'

class ElectionType(DjangoObjectType):
    class Meta:
        model = Election
        fields = '__all__'

class PositionType(DjangoObjectType):
    class Meta:
        model = Position
        fields = '__all__'

class StudentType(DjangoObjectType):
    class Meta:
        model = Student
        fields = '__all__'
    
    user = graphene.Field(UserType)
    
    def resolve_user(self, info):
        return self.user

class CandidateType(DjangoObjectType):
    class Meta:
        model = Candidate
        fields = '__all__'
    
    vote_count = graphene.Int()
    election_result = graphene.Field(ElectionResultType)
    
    def resolve_vote_count(self, info):
        return self.vote_set.count()
    
    def resolve_election_result(self, info):
        return self.electionresult_set.first()

class InstitutionType(DjangoObjectType):
    class Meta:
        model = Institution
        fields = '__all__'
    
    candidates = graphene.List(
        CandidateType,
        academic_year_id=graphene.ID(required=True)
    )
    
    def resolve_candidates(self, info, academic_year_id):
        return Candidate.objects.filter(
            student__institution=self,
            student__academic_year_id=academic_year_id,
            is_approved=True
        ).select_related(
            'student__user',
            'election_position__position',
            'election_position__election'
        ).prefetch_related('vote_set')

# ====================
# QUERY DEFINITIONS
# ====================

class Query(graphene.ObjectType):
    colleges_with_candidates = graphene.List(
        InstitutionType,
        academic_year_id=graphene.ID(required=True),
        election_id=graphene.ID()
    )
    
    def resolve_colleges_with_candidates(self, info, academic_year_id, election_id=None):
        qs = Institution.objects.filter(level__level="COLLEGE")
        
        if election_id:
            qs = qs.filter(
                student__candidate__election_position__election_id=election_id
            ).distinct()
        
        return qs.prefetch_related(
            Prefetch('student_set',
                queryset=Student.objects.filter(
                    academic_year_id=academic_year_id
                ).select_related('user')
            ),
            Prefetch('student_set__candidate_set',
                queryset=Candidate.objects.filter(
                    is_approved=True
                ).select_related(
                    'election_position__position',
                    'election_position__election'
                ).prefetch_related('vote_set')
            )
        )

schema = graphene.Schema(query=Query)