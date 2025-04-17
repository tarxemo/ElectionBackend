import graphene
from election.statistics import StatisticsQuery
from election.views import Mutation
from election.schema import Query

class RootQuery(Query, StatisticsQuery, graphene.ObjectType):
    pass

class RootMutation(Mutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=RootQuery, mutation=RootMutation)
