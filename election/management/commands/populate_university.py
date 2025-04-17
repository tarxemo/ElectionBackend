from django.core.management.base import BaseCommand
from election.models import University, College, Hostel

class Command(BaseCommand):
    help = "Populate the database with UDOM university, colleges, and hostels"

    def handle(self, *args, **kwargs):
        university_name = "University of Dodoma (UDOM)"
        
        # Check if the university exists
        university, created = University.objects.get_or_create(name=university_name)

        if created:
            self.stdout.write(self.style.SUCCESS(f"University '{university_name}' created successfully!"))
        else:
            self.stdout.write(self.style.WARNING(f"University '{university_name}' already exists."))

        # Define colleges and their hostels
        colleges = {
            "College of Education (COED)": [f"Block {chr(i)}" for i in range(ord('A'), ord('T') + 1)],
            "College of Informatics and Virtual Education (CIVE)": [f"Block {i}" for i in range(1, 7)],
            "College of Earth Science (COES)": [f"Block {i}" for i in range(6, 10)],
            "College of Natural and Mathematical Sciences (CNMS)": [f"Block {i}" for i in range(10, 15)],
            "College of Business and Economics (COBE)": [f"Block {i}" for i in range(1, 20)],
            "College of Humanities and Social Sciences (CHSS)": [f"Block {i}" for i in range(1, 6)],
            "College of Health Sciences": ["Block 1", "Block 2"],
        }

        # Loop through colleges and add them
        for college_name, hostels in colleges.items():
            college, created = College.objects.get_or_create(name=college_name, university=university)
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"  College '{college_name}' added!"))
            else:
                self.stdout.write(self.style.WARNING(f"  College '{college_name}' already exists."))

            # Add hostels
            for hostel_name in hostels:
                hostel, created = Hostel.objects.get_or_create(name=hostel_name, college=college)
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f"    Hostel '{hostel_name}' added under {college_name}."))
                else:
                    self.stdout.write(self.style.WARNING(f"    Hostel '{hostel_name}' already exists in {college_name}."))

        self.stdout.write(self.style.SUCCESS("Database successfully populated with UDOM data!"))
