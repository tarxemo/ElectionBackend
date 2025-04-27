# schema.py
import graphene
from graphene_django import DjangoObjectType
from election.models import Candidate, InstitutionLevel, Position, Institution, AcademicYear, Election
from django.db.models import Q

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
        levels = InstitutionLevel.objects.all()
        
        for level in levels:
            positions = Position.objects.filter(level=level)
            stats.append({
                'level': level.get_level_display(),
                'count': positions.count(),
                'with_elections': positions.filter(elections__isnull=False).distinct().count(),
                'with_candidates': positions.filter(
                    electionposition__candidate__isnull=False
                ).distinct().count()
            })
        
        return stats

    def resolve_all_institutions(self, info):
        return Institution.objects.filter(parent__isnull=True)

    def resolve_academic_years(self, info):
        return AcademicYear.objects.all()