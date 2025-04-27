from typing import Optional, List, Dict, Union, Literal
from datetime import date, datetime
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum

# ====================== ENUM TYPES ======================

class InstitutionLevel(str, Enum):
    UNIVERSITY = "UNIVERSITY"
    COLLEGE = "COLLEGE"
    HOSTEL = "HOSTEL"

class ElectionStatus(str, Enum):
    UPCOMING = "UPCOMING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class PromiseStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# ====================== BASE TYPES ======================

class AcademicYearBase(BaseModel):
    name: str
    start_date: date
    end_date: date
    is_current: bool = False

    @root_validator
    def validate_dates(cls, values):
        if values['start_date'] > values['end_date']:
            raise ValueError("End date must be after start date")
        return values

class InstitutionLevelBase(BaseModel):
    level: InstitutionLevel

class InstitutionBase(BaseModel):
    name: str
    level: InstitutionLevel
    parent_id: Optional[int] = None
    description: Optional[str] = None

class PositionBase(BaseModel):
    name: str
    description: Optional[str] = None
    level: InstitutionLevel
    institution_id: Optional[int] = None
    voting_power: int = Field(1, ge=1)

class StudentBase(BaseModel):
    user_id: int
    registration_number: str
    institution_id: int
    academic_year_id: int
    is_active: bool = True

class ElectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: ElectionStatus = ElectionStatus.UPCOMING
    start_datetime: datetime
    end_datetime: datetime
    academic_year_id: int
    level: InstitutionLevel
    institution_id: Optional[int] = None

    @root_validator
    def validate_datetimes(cls, values):
        if values['start_datetime'] > values['end_datetime']:
            raise ValueError("End datetime must be after start datetime")
        return values

class CandidateBase(BaseModel):
    student_id: int
    election_position_id: int
    manifesto: Optional[str] = None
    is_approved: bool = False

class VoteBase(BaseModel):
    election_id: int
    candidate_id: int
    voter_id: int
    weight: int = Field(1, ge=1)

class PromiseBase(BaseModel):
    candidate_id: int
    title: str
    description: str

class PromiseUpdateBase(BaseModel):
    promise_id: int
    status: PromiseStatus = PromiseStatus.NOT_STARTED
    update: str

class RatingBase(BaseModel):
    leader_id: int
    student_id: int
    score: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

# ====================== CREATE TYPES ======================

class AcademicYearCreate(AcademicYearBase):
    pass

class InstitutionLevelCreate(InstitutionLevelBase):
    pass

class InstitutionCreate(InstitutionBase):
    pass

class PositionCreate(PositionBase):
    pass

class StudentCreate(StudentBase):
    pass

class ElectionCreate(ElectionBase):
    position_ids: List[int] = []

class ElectionPositionCreate(BaseModel):
    election_id: int
    position_id: int
    max_candidates: int = Field(1, ge=1)

class CandidateCreate(CandidateBase):
    pass

class VoteCreate(VoteBase):
    pass

class PromiseCreate(PromiseBase):
    pass

class PromiseUpdateCreate(PromiseUpdateBase):
    pass

class RatingCreate(RatingBase):
    pass

# ====================== READ TYPES ======================

class AcademicYearRead(AcademicYearBase):
    id: int
    class Config:
        orm_mode = True

class InstitutionLevelRead(InstitutionLevelBase):
    id: int
    class Config:
        orm_mode = True

class InstitutionRead(InstitutionBase):
    id: int
    parent: Optional['InstitutionRead'] = None
    children: List['InstitutionRead'] = []
    class Config:
        orm_mode = True

class PositionRead(PositionBase):
    id: int
    institution: Optional['InstitutionRead'] = None
    class Config:
        orm_mode = True

class StudentRead(StudentBase):
    id: int
    user: Dict  # Will be populated with user data
    institution: 'InstitutionRead'
    academic_year: 'AcademicYearRead'
    class Config:
        orm_mode = True

class ElectionPositionRead(BaseModel):
    id: int
    election_id: int
    position: 'PositionRead'
    max_candidates: int
    class Config:
        orm_mode = True

class ElectionRead(ElectionBase):
    id: int
    academic_year: 'AcademicYearRead'
    institution: Optional['InstitutionRead'] = None
    positions: List[ElectionPositionRead] = []
    class Config:
        orm_mode = True

class CandidateRead(CandidateBase):
    id: int
    student: 'StudentRead'
    election_position: 'ElectionPositionRead'
    votes_count: int = 0
    approved_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        orm_mode = True

class VoteRead(VoteBase):
    id: int
    election: 'ElectionRead'
    candidate: 'CandidateRead'
    voter: 'StudentRead'
    timestamp: datetime
    class Config:
        orm_mode = True

class PromiseRead(PromiseBase):
    id: int
    candidate: 'CandidateRead'
    created_at: datetime
    updates: List['PromiseUpdateRead'] = []
    class Config:
        orm_mode = True

class PromiseUpdateRead(PromiseUpdateBase):
    id: int
    promise: 'PromiseRead'
    timestamp: datetime
    class Config:
        orm_mode = True

class LeaderRead(BaseModel):
    id: int
    candidate: 'CandidateRead'
    position: 'PositionRead'
    institution: 'InstitutionRead'
    start_date: date
    end_date: date
    is_active: bool
    average_rating: Optional[float] = None
    class Config:
        orm_mode = True

class RatingRead(RatingBase):
    id: int
    leader: 'LeaderRead'
    student: 'StudentRead'
    timestamp: datetime
    class Config:
        orm_mode = True

class ElectionResultRead(BaseModel):
    election_id: int
    candidate: 'CandidateRead'
    total_votes: int
    percentage: float
    position_rank: int
    is_winner: bool
    class Config:
        orm_mode = True

class ElectionStatisticsRead(BaseModel):
    election: 'ElectionRead'
    total_voters: int
    total_votes_cast: int
    voter_turnout: float
    leading_candidate: Optional['CandidateRead'] = None
    results: List['ElectionResultRead'] = []
    class Config:
        orm_mode = True

# ====================== UPDATE TYPES ======================

class AcademicYearUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None

class InstitutionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[Union[int, Literal["unset"]]] = None

class PositionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    voting_power: Optional[int] = None

class StudentUpdate(BaseModel):
    institution_id: Optional[int] = None
    academic_year_id: Optional[int] = None
    is_active: Optional[bool] = None

class ElectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ElectionStatus] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None

class CandidateUpdate(BaseModel):
    manifesto: Optional[str] = None
    is_approved: Optional[bool] = None

class PromiseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

# ====================== COMBINED/COMPLEX TYPES ======================

class ElectionWithResults(BaseModel):
    election: ElectionRead
    results: List[ElectionResultRead]
    statistics: ElectionStatisticsRead

class LeaderWithPerformance(BaseModel):
    leader: LeaderRead
    promises: List[PromiseRead]
    ratings: List[RatingRead]
    average_rating: float

class InstitutionWithHierarchy(BaseModel):
    institution: InstitutionRead
    parent_chain: List[InstitutionRead]
    children: List['InstitutionWithHierarchy']

class ElectionCandidateStats(BaseModel):
    candidate: CandidateRead
    votes_by_institution: Dict[str, int]  # Institution name -> vote count
    votes_by_time: Dict[datetime, int]    # Time bucket -> vote count
    demographic_stats: Dict[str, float]   # Demographic category -> percentage

class RealTimeElectionData(BaseModel):
    election: ElectionRead
    current_results: List[ElectionResultRead]
    leading_candidates: List[CandidateRead]
    turnout_percentage: float
    last_updated: datetime
    votes_per_minute: float

# ====================== RESPONSE TYPES ======================

class PaginatedResponse(BaseModel):
    items: List[BaseModel]  # Will be replaced with concrete types
    total: int
    page: int
    size: int
    pages: int

class SuccessResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Union[BaseModel, Dict, List]] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Dict] = None
    code: Optional[int] = None

# Fix forward references
InstitutionRead.update_forward_refs()
PositionRead.update_forward_refs()
StudentRead.update_forward_refs()
ElectionPositionRead.update_forward_refs()
ElectionRead.update_forward_refs()
CandidateRead.update_forward_refs()
VoteRead.update_forward_refs()
PromiseRead.update_forward_refs()
PromiseUpdateRead.update_forward_refs()
LeaderRead.update_forward_refs()
RatingRead.update_forward_refs()
ElectionResultRead.update_forward_refs()
ElectionStatisticsRead.update_forward_refs()
InstitutionWithHierarchy.update_forward_refs()