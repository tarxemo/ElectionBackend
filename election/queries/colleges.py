# election/queries/colleges.py
import graphene
from graphene_django import DjangoObjectType
from election.models import Institution, InstitutionLevel, Student, Leader, User
from django.db.models import Q

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email')  # Add other fields you need

class StudentType(DjangoObjectType):
    class Meta:
        model = Student
        fields = ('id', 'is_active')
    
    user = graphene.Field(UserType)  # Explicitly define the user field
    
    def resolve_user(self, info):
        return self.user

class CollegeType(DjangoObjectType):
    class Meta:
        model = Institution
        fields = '__all__'
    
    student_count = graphene.Int()
    leader_count = graphene.Int()
    students = graphene.List(StudentType)
    
    def resolve_students(self, info):
        return self.student_set.filter(is_active=True).select_related('user').all()
    
    def resolve_student_count(self, info):
        return self.student_set.filter(is_active=True).count()
    
    def resolve_leader_count(self, info):
        return self.leader_set.count()

class CollegesQuery(graphene.ObjectType):
    all_colleges = graphene.List(
        CollegeType,
        parent_id=graphene.ID(),
        with_candidates=graphene.Boolean(default_value=False),
        academic_year_id=graphene.ID()
    )
    
    def resolve_all_colleges(self, info, parent_id=None, with_candidates=False, academic_year_id=None, **kwargs):
        college_level = InstitutionLevel.objects.get(level='COLLEGE')
        qs = Institution.objects.filter(level=college_level)
        
        if parent_id:
            qs = qs.filter(parent__id=parent_id)
        
        if with_candidates:
            qs = qs.filter(
                Q(position__electionposition__candidate__isnull=False) |
                Q(student__candidate__isnull=False)
            ).distinct()
        
        if academic_year_id:
            qs = qs.filter(
                Q(position__electionposition__election__academic_year__id=academic_year_id) |
                Q(student__academic_year__id=academic_year_id)
            ).distinct()
        
        return qs