from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class AcademicYear(models.Model):
    name = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return self.name

class InstitutionLevel(models.Model):
    LEVEL_CHOICES = [
        ('UNIVERSITY', 'University'),
        ('COLLEGE', 'College'),
        ('HOSTEL', 'Hostel'),
    ]
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, unique=True)
    
    def __str__(self):
        return self.get_level_display()

class Institution(models.Model):
    name = models.CharField(max_length=255)
    level = models.ForeignKey(InstitutionLevel, on_delete=models.PROTECT)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('name', 'level', 'parent')
        ordering = ['level', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.level})"

class Position(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    level = models.ForeignKey(InstitutionLevel, on_delete=models.PROTECT)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, null=True, blank=True)
    voting_power = models.PositiveIntegerField(default=1)  # For weighted votes
    
    class Meta:
        unique_together = ('name', 'level', 'institution')
    
    def __str__(self):
        return f"{self.name} ({self.level})"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    registration_number = models.CharField(max_length=50, unique=True)
    institution = models.ForeignKey(Institution, on_delete=models.PROTECT)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.registration_number})"

class Election(models.Model):
    STATUS_CHOICES = [
        ('UPCOMING', 'Upcoming'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UPCOMING')
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    positions = models.ManyToManyField(Position, through='ElectionPosition')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT)
    level = models.ForeignKey(InstitutionLevel, on_delete=models.PROTECT)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-start_datetime']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

class ElectionPosition(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    max_candidates = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ('election', 'position')
    
    def __str__(self):
        return f"{self.position.name} in {self.election.name}"

class Candidate(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    election_position = models.ForeignKey(ElectionPosition, on_delete=models.CASCADE)
    manifesto = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('student', 'election_position')
        ordering = ['election_position', 'student']
    
    def __str__(self):
        return f"{self.student} for {self.election_position.position}"

class Vote(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    voter = models.ForeignKey(Student, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    weight = models.PositiveIntegerField(default=1)  # For weighted voting
    
    class Meta:
        unique_together = ('election', 'voter', 'candidate')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Vote by {self.voter} for {self.candidate}"

class ElectionResult(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    total_votes = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    position_rank = models.PositiveIntegerField()
    is_winner = models.BooleanField(default=False)
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('election', 'candidate')
        ordering = ['election', 'position_rank']
    
    def __str__(self):
        return f"Result for {self.candidate}: {self.total_votes} votes"

class Leader(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['position', '-start_date']
    
    def __str__(self):
        return f"{self.candidate.student} as {self.position}"

class Promise(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['candidate', '-created_at']
    
    def __str__(self):
        return f"{self.title} by {self.candidate}"

class PromiseUpdate(models.Model):
    STATUS_CHOICES = [
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    promise = models.ForeignKey(Promise, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NOT_STARTED')
    update = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['promise', '-timestamp']
    
    def __str__(self):
        return f"Update for {self.promise}: {self.get_status_display()}"

class Rating(models.Model):
    leader = models.ForeignKey(Leader, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('leader', 'student')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Rating {self.score} for {self.leader} by {self.student}"

class ElectionStatistics(models.Model):
    election = models.OneToOneField(Election, on_delete=models.CASCADE)
    total_voters = models.PositiveIntegerField()
    total_votes_cast = models.PositiveIntegerField()
    voter_turnout = models.DecimalField(max_digits=5, decimal_places=2)
    leading_candidate = models.ForeignKey(Candidate, on_delete=models.SET_NULL, null=True)
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Stats for {self.election}: {self.voter_turnout}% turnout"
# from django.db import models
# from django.contrib.auth.models import User

# class University(models.Model):
#     name = models.CharField(max_length=255, unique=True)
#     description = models.TextField(blank=True, null=True)

#     def __str__(self):
#         return self.name

# class College(models.Model):
#     name = models.CharField(max_length=255)
#     university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='colleges')
#     description = models.TextField(blank=True, null=True)

#     def __str__(self):
#         return f"{self.name} ({self.university.name})"

# class Hostel(models.Model):
#     name = models.CharField(max_length=255)
#     college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='hostels')
#     description = models.TextField(blank=True, null=True)

#     def __str__(self):
#         return f"{self.name} ({self.college.name})"

# class Student(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
#     hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='students')
#     college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='students')
#     university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='students')
#     is_candidate = models.BooleanField(default=False)

#     def __str__(self):
#         return f"{self.user.get_full_name()} ({self.hostel.name})"

# class Position(models.Model):
#     name = models.CharField(max_length=255)
#     description = models.TextField(blank=True, null=True)

#     # Foreign keys to Hostel, College, and University
#     hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, null=True, blank=True, related_name='positions')
#     college = models.ForeignKey(College, on_delete=models.CASCADE, null=True, blank=True, related_name='positions')
#     university = models.ForeignKey(University, on_delete=models.CASCADE, null=True, blank=True, related_name='positions')

#     def __str__(self):
#         return f"{self.name}"

#     def level(self):
#         """Determine the level based on which foreign key is set."""
#         if self.hostel:
#             return 'Hostel'
#         elif self.college:
#             return 'College'
#         elif self.university:
#             return 'University'
#         return 'No level assigned'


# class Candidate(models.Model):
#     student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='candidatures')
#     position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='candidates')
#     manifesto = models.TextField(blank=True, null=True)

#     def __str__(self):
#         return f"{self.student.user.get_full_name()} for {self.position.name}"

# class Election(models.Model):
#     LEVEL_CHOICES = [
#         ('HOSTEL', 'Hostel Level'),
#         ('COLLEGE', 'College Level'),
#         ('UNIVERSITY', 'University Level'),
#     ]
#     name = models.CharField(max_length=255)
#     level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
#     start_date = models.DateTimeField()
#     end_date = models.DateTimeField()
#     positions = models.ManyToManyField(Position, related_name='elections')
#     description = models.TextField(blank=True, null=True)

#     def __str__(self):
#         return f"{self.name} ({self.get_level_display()})"

# class Vote(models.Model):
#     student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='votes')
#     candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes')
#     election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='votes')
#     timestamp = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Vote by {self.student.user.get_full_name()} for {self.candidate.student.user.get_full_name()} in {self.election.name}"

# class LeaderPromise(models.Model):
#     candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='promises')
#     promise = models.TextField(null=True, blank=True)
#     timestamp = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Promise by {self.candidate.student.user.get_full_name()}: {self.promise[:50]}..."

# class PromiseImplementation(models.Model):
#     STATUS_CHOICES = [
#         ('PENDING', 'Pending'),
#         ('IN_PROGRESS', 'In Progress'),
#         ('COMPLETED', 'Completed'),
#         ('FAILED', 'Failed'),
#     ]
#     promise = models.ForeignKey(LeaderPromise, on_delete=models.CASCADE, related_name='implementations')
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
#     update = models.TextField(blank=True, null=True)
#     timestamp = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Implementation of {self.promise.promise[:50]}... ({self.get_status_display()})"

# class LeaderRating(models.Model):
#     RATING_CHOICES = [
#         (1, '1 - Poor'),
#         (2, '2 - Fair'),
#         (3, '3 - Good'),
#         (4, '4 - Very Good'),
#         (5, '5 - Excellent'),
#     ]
#     leader = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='ratings')
#     student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='ratings_given')
#     rating = models.IntegerField(choices=RATING_CHOICES)
#     comment = models.TextField(blank=True, null=True)
#     timestamp = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Rating {self.rating} by {self.student.user.get_full_name()} for {self.leader.student.user.get_full_name()}"