import pandas as pd
from django.db.models import Count
import joblib
from io import StringIO
from datetime import datetime, timedelta
from election.models import *
from django.db.models import Count, Sum, Avg, Q

class ElectionPredictor:
    def __init__(self, model_path='election_winner_predictor.joblib'):
        self.model = joblib.load(model_path)
    
    def prepare_prediction_data(self, election_position, candidates, position):
        """Prepare all necessary data for prediction"""
        # Get current votes
        current_votes = Vote.objects.filter(
            election=election_position.election,
            candidate__election_position=election_position
        ).values('candidate').annotate(vote_count=Count('id'))
        
        vote_counts = {v['candidate']: v['vote_count'] for v in current_votes}
        total_votes = sum(vote_counts.values()) if vote_counts else 1
        
        # Prepare data for each candidate
        prediction_data = []
        for candidate in candidates:
            # Get candidate's historical performance
            previous_wins = ElectionResult.objects.filter(
                candidate__student=candidate.student,
                is_winner=True
            ).count()
            
            previous_losses = ElectionResult.objects.filter(
                candidate__student=candidate.student,
                is_winner=False
            ).count()
            
            # Check if incumbent
            is_incumbent = Leader.objects.filter(
                candidate=candidate,
                position=election_position.position,
                start_date__lt=election_position.election.start_datetime
            ).exists()
            
            # Get institution data
            institution = candidate.student.institution
            inst_turnout_avg = ElectionStatistics.objects.filter(
                election__institution=institution
            ).aggregate(avg=Avg('voter_turnout'))['avg'] or 0
            
            # Create candidate data row
            prediction_data.append({
            'election_id': election_position.election.id,
            'election_name': election_position.election.name,
            'election_year': election_position.election.start_datetime.year,
            'election_month': election_position.election.start_datetime.month,
            'election_day_of_week': election_position.election.start_datetime.strftime('%A'),
            'election_duration_hours': (election_position.election.end_datetime - election_position.election.start_datetime).total_seconds() / 3600,
            'academic_year': election_position.election.academic_year.name,
            'institution_level': position.level.level,
            'institution_name': institution.name if institution else 'None',
            'position_id': position.id,
            'position_name': position.name,
            'position_institution': position.institution.name if position.institution else 'None',
            'max_candidates': election_position.max_candidates,
            'candidate_id': candidate.id,
            'candidate_institution': institution.name,
            'candidate_academic_year': candidate.student.academic_year.name,
            'candidate_is_incumbent': int(is_incumbent),
            'candidate_previous_wins': previous_wins,
            'candidate_previous_losses': previous_losses,
            # These would be calculated from historical data in a real implementation
            'position_avg_voters': 1000,  # Placeholder - should calculate from history
            'position_avg_turnout': 65.0, # Placeholder
            'position_winner_institution_last_3': institution.name,  # Placeholder
            'position_winner_academic_year_last_3': candidate.student.academic_year.name,  # Placeholder
            # Current votes will be added below
            'votes_received': 0,
            'vote_percentage': 0.0,
            'institution_voter_turnout_avg': inst_turnout_avg,
            'institution_votes_for_own_candidates_pct': 70.0,  # Placeholder
            'votes_first_hour_pct': 0.0,
            'votes_last_hour_pct': 0.0,
            'votes_peak_hour_pct': 0.0,
            'closest_competitor_vote_diff': 0,
            'second_competitor_vote_diff': 0,
            'fraud_risk_avg': 0.0,
            'fraud_indicators_count': 0

            })
        
        return pd.DataFrame(prediction_data)
    
    def predict_winner(self, election_position, candidates, position):
        """Predict the likely winner for a position"""
        try:
            # Prepare data
            prediction_df = self.prepare_prediction_data(election_position, candidates, position)
            
            if prediction_df.empty:
                return None, None
            
            # Make predictions
            predictions = self.model.predict_proba(prediction_df)
            prediction_df['win_probability'] = predictions[:, 1]
            
            # Get predicted winner
            predicted_winner = prediction_df.loc[prediction_df['win_probability'].idxmax()]
            print(predicted_winner['candidate_id'])
            print("winner above")
            return predicted_winner['candidate_id'], predicted_winner['win_probability'] * 10000000
        except Exception as e:
            print(f"Prediction error: {str(e)}")
            return None, None

# Singleton predictor instance
predictor = ElectionPredictor()