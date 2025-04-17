import graphene
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from .models import Student, Hostel, College, University
from .inputs import StudentRegistrationInput

User = get_user_model()

class RegisterStudent(graphene.Mutation):
    class Arguments:
        input = StudentRegistrationInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, input):
        # Extract user data
        username = input.username
        email = input.email
        password = input.password

        # Extract student data
        hostel_id = input.hostel_id
        college_id = input.college_id
        university_id = input.university_id
        is_candidate = input.is_candidate

        # Check if the user already exists
        if User.objects.filter(username=username).exists():
            return RegisterStudent(success=False, message="Username already exists.")

        if User.objects.filter(email=email).exists():
            return RegisterStudent(success=False, message="Email already exists.")

        # Create the user
        user = User(
            username=username,
            email=email,
            password=make_password(password),  # Hash the password
        )
        user.save()

        # Fetch related objects
        try:
            hostel = Hostel.objects.get(id=hostel_id)
            college = College.objects.get(id=college_id)
            university = University.objects.get(id=university_id)
        except (Hostel.DoesNotExist, College.DoesNotExist, University.DoesNotExist):
            user.delete()  # Rollback user creation if related objects don't exist
            return RegisterStudent(success=False, message="Invalid hostel, college, or university ID.")

        # Create the student
        student = Student(
            user=user,
            hostel=hostel,
            college=college,
            university=university,
            is_candidate=is_candidate,
        )
        student.save()

        return RegisterStudent(success=True, message="Student registered successfully.")

class Mutation(graphene.ObjectType):
    register_student = RegisterStudent.Field()