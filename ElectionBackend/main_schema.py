from election.mutations.mutations import Mutation
from election.queries.positions import PositionQuery
from election.queries.institutionSchema import InstitutionQuery

import graphene
# from election.statistics import StatisticsQuery
# from election.views import Mutation
# from election.schema import Query

class RootQuery(InstitutionQuery,PositionQuery, graphene.ObjectType):
    pass

class RootMutation(Mutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=RootQuery, mutation=RootMutation)
