from django.db import models
from django.contrib.auth.models import User

class University(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class College(models.Model):
    name = models.CharField(max_length=255)
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='colleges')
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.university.name})"

class Hostel(models.Model):
    name = models.CharField(max_length=255)
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='hostels')
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.college.name})"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='students')
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='students')
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='students')
    is_candidate = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.hostel.name})"

class Position(models.Model):
    LEVEL_CHOICES = [
        ('HOSTEL', 'Hostel Level'),
        ('COLLEGE', 'College Level'),
        ('UNIVERSITY', 'University Level'),
    ]
    name = models.CharField(max_length=255)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"

class Candidate(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='candidatures')
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='candidates')
    manifesto = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.user.get_full_name()} for {self.position.name}"

class Election(models.Model):
    LEVEL_CHOICES = [
        ('HOSTEL', 'Hostel Level'),
        ('COLLEGE', 'College Level'),
        ('UNIVERSITY', 'University Level'),
    ]
    name = models.CharField(max_length=255)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    positions = models.ManyToManyField(Position, related_name='elections')
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"

class Vote(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='votes')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes')
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='votes')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Vote by {self.student.user.get_full_name()} for {self.candidate.student.user.get_full_name()} in {self.election.name}"

class LeaderPromise(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='promises')
    promise = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Promise by {self.candidate.student.user.get_full_name()}: {self.promise[:50]}..."

class PromiseImplementation(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    promise = models.ForeignKey(LeaderPromise, on_delete=models.CASCADE, related_name='implementations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    update = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Implementation of {self.promise.promise[:50]}... ({self.get_status_display()})"

class LeaderRating(models.Model):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    leader = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='ratings')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='ratings_given')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating {self.rating} by {self.student.user.get_full_name()} for {self.leader.student.user.get_full_name()}"