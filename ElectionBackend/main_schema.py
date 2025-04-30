from  election.queries.colleges import CollegesQuery
from election.mutations.mutations import Mutation
# from election.queries.candidate import CandidateQuery
from election.queries.positions import PositionQuery
from election.queries.institutionSchema import InstitutionQuery

import graphene
# from election.statistics import StatisticsQuery
# from election.views import Mutation
# from election.schema import Query
class RootQuery(InstitutionQuery,PositionQuery, CollegesQuery, graphene.ObjectType):
    pass

class RootMutation(Mutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=RootQuery, mutation=RootMutation)

