import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from graphql import GraphQLError
from functools import wraps

def get_user_from_token(auth_header):
    """
    Extracts user from the JWT token in the Authorization header.
    """
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split("Bearer ")[1]

    try:
        # Decode the token
        decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_data.get("user_id")
        if not user_id:
            return None

        # Fetch the user
        User = get_user_model()
        return User.objects.filter(id=user_id).first()

    except jwt.ExpiredSignatureError:
        raise GraphQLError("Token has expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise GraphQLError("Invalid authentication token.")

def login_required_resolver(func):
    """
    Decorator to check authentication before executing a resolver.
    """
    @wraps(func)
    def wrapper(self, info, *args, **kwargs):
        auth_header = info.context.headers.get("Authorization")
        user = get_user_from_token(auth_header)

        if not user:
            raise GraphQLError("Authentication required.")

        info.context.user = user  # Attach user to the context

        return func(self, info, *args, **kwargs)

    return wrapper
