# urls.py

from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.contrib import admin
from graphene_django.views import GraphQLView
from django.conf import settings
# from election.backups import *

urlpatterns = [
    path("gql/", csrf_exempt(GraphQLView.as_view(graphiql=settings.DEBUG))),
    path('admin/', admin.site.urls),
    
    # path("upload-students/", import_students_from_csv, name="upload_students"),#create sudents
    # path("select-candidates/", select_candidates, name="select_candidates"),#
    # path("random-voting/", random_voting, name="random_voting"),
    # path("random-ratings/", random_leader_ratings, name="random_leader_ratings"),
    # path('randomize-timestamps-to-votes/', randomize_vote_timestamps, name='randomize_votes'),
]
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# SELECT 
#     t.table_schema,
#     t.table_name,
#     psut.n_live_tup AS total_rows
# FROM 
#     information_schema.tables t
# LEFT JOIN 
#     pg_stat_user_tables psut
#     ON t.table_schema = psut.schemaname
#     AND t.table_name = psut.relname
# WHERE 
#     t.table_type = 'BASE TABLE'
#     AND t.table_schema NOT IN ('information_schema', 'pg_catalog')
# ORDER BY 
#     total_rows DESC;
