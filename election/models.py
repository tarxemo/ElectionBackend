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
    # registration_number = models.CharField(max_length=50)
    institution = models.ForeignKey(Institution, on_delete=models.PROTECT)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    is_candidate = models.BooleanField(default=False)
    class Meta:
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.academic_year})"

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
    positions = models.ManyToManyField(
        Position, 
        through='ElectionPosition', 
        related_name='elections' 
    )   
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
    # academic_year = models.DateField(null=True, blank=True)
    class Meta:
        unique_together = ('student', 'election_position')
        ordering = ['election_position', 'student']
    
    def __str__(self):
        return f"{self.student} for {self.election_position.position}"

class Vote(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='votes')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes')
    voter = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='votes_cast')
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
    
    promise = models.ForeignKey(Promise, on_delete=models.CASCADE, related_name="promise_updates")
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
