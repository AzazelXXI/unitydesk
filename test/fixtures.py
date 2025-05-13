import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import enum
from src.models.user import (
    User, 
    UserProfile, 
    UserRole, 
    Department, 
    Position, 
    DepartmentMembership
)

@pytest.fixture
async def sample_data(test_session: AsyncSession):
    """Creates sample data for testing purposes"""
    
    print("Creating sample data for tests...")
    
    # Create departments first
    eng_dept = Department(
        name="Engineering",
        code="ENG",
        description="Software Engineering Department",
        is_active=True,
        order_index=1,
        path="/engineering"
    )
    
    hr_dept = Department(
        name="Human Resources",
        code="HR",
        description="Human Resources Department",
        is_active=True,
        order_index=2,
        path="/hr"
    )
    
    marketing_dept = Department(
        name="Marketing",
        code="MKT",
        description="Marketing Department",
        is_active=True,
        order_index=3,
        path="/marketing"
    )
    
    # Create a sub-department
    mobile_dept = Department(
        name="Mobile Development",
        code="ENGMOB",
        description="Mobile Development Team",
        is_active=True,
        order_index=1,
        path="/engineering/mobile"
    )
    
    test_session.add_all([eng_dept, hr_dept, marketing_dept, mobile_dept])
    await test_session.flush()
    
    # Update parent relationships
    mobile_dept.parent_id = eng_dept.id
    await test_session.flush()
    
    # Create positions
    cto_position = Position(
        title="Chief Technology Officer",
        department_id=eng_dept.id,
        description="Company-wide technical leadership",
        responsibilities="Technical strategy, architecture oversight",
        required_skills="15+ years experience, leadership",
        grade_level=10,
        is_managerial=True
    )
    
    lead_dev_position = Position(
        title="Lead Developer",
        department_id=eng_dept.id,
        description="Team technical leadership",
        responsibilities="Code reviews, technical mentoring",
        required_skills="8+ years experience",
        grade_level=8,
        is_managerial=True
    )
    
    senior_dev_position = Position(
        title="Senior Developer",
        department_id=eng_dept.id,
        description="Senior development role",
        responsibilities="Feature development, mentoring",
        required_skills="5+ years experience",
        grade_level=6,
        is_managerial=False
    )
    
    mobile_lead_position = Position(
        title="Mobile Team Lead",
        department_id=mobile_dept.id,
        description="Mobile team leadership",
        responsibilities="Mobile development strategy",
        required_skills="7+ years mobile experience",
        grade_level=7,
        is_managerial=True
    )
    
    hr_manager_position = Position(
        title="HR Manager",
        department_id=hr_dept.id,
        description="HR Department leadership",
        responsibilities="HR strategy, policy development",
        required_skills="10+ years HR experience",
        grade_level=8,
        is_managerial=True
    )
    
    marketing_director_position = Position(
        title="Marketing Director",
        department_id=marketing_dept.id,
        description="Marketing Department leadership",
        responsibilities="Marketing strategy, brand management",
        required_skills="10+ years marketing experience",
        grade_level=9,
        is_managerial=True
    )
    
    test_session.add_all([
        cto_position, 
        lead_dev_position, 
        senior_dev_position, 
        mobile_lead_position,
        hr_manager_position,
        marketing_director_position
    ])
    await test_session.flush()
    
    # Set reporting relationships
    lead_dev_position.reports_to_position_id = cto_position.id
    senior_dev_position.reports_to_position_id = lead_dev_position.id
    mobile_lead_position.reports_to_position_id = cto_position.id
    await test_session.flush()
    
    # Create users
    cto_user = User(
        email="cto@example.com",
        username="cto",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        department_id=eng_dept.id,
        position_id=cto_position.id,
        employee_id="EMP001",
        hire_date=datetime.utcnow() - timedelta(days=1095)  # 3 years ago
    )
    
    lead_dev_user = User(
        email="leaddev@example.com",
        username="leaddev",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
        role=UserRole.MANAGER,
        is_active=True,
        is_verified=True,
        department_id=eng_dept.id,
        position_id=lead_dev_position.id,
        employee_id="EMP002",
        hire_date=datetime.utcnow() - timedelta(days=730)  # 2 years ago
    )
    
    senior_dev_user = User(
        email="seniordev@example.com",
        username="seniordev",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
        department_id=eng_dept.id,
        position_id=senior_dev_position.id,
        employee_id="EMP003",
        hire_date=datetime.utcnow() - timedelta(days=365)  # 1 year ago
    )
    
    mobile_lead_user = User(
        email="mobilelead@example.com",
        username="mobilelead",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
        role=UserRole.MANAGER,
        is_active=True,
        is_verified=True,
        department_id=mobile_dept.id,
        position_id=mobile_lead_position.id,
        employee_id="EMP004",
        hire_date=datetime.utcnow() - timedelta(days=547)  # ~1.5 years ago
    )
    
    hr_manager_user = User(
        email="hrmanager@example.com",
        username="hrmanager",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
        role=UserRole.MANAGER,
        is_active=True,
        is_verified=True,
        department_id=hr_dept.id,
        position_id=hr_manager_position.id,
        employee_id="EMP005",
        hire_date=datetime.utcnow() - timedelta(days=912)  # ~2.5 years ago
    )
    
    marketing_director_user = User(
        email="marketingdirector@example.com",
        username="marketingdir",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
        role=UserRole.MANAGER,
        is_active=True,
        is_verified=True,
        department_id=marketing_dept.id,
        position_id=marketing_director_position.id,
        employee_id="EMP006",
        hire_date=datetime.utcnow() - timedelta(days=640)  # ~1.75 years ago
    )
    
    test_session.add_all([
        cto_user, 
        lead_dev_user, 
        senior_dev_user, 
        mobile_lead_user,
        hr_manager_user,
        marketing_director_user
    ])
    await test_session.flush()
    
    # Update department heads
    eng_dept.head_user_id = cto_user.id
    hr_dept.head_user_id = hr_manager_user.id
    marketing_dept.head_user_id = marketing_director_user.id
    mobile_dept.head_user_id = mobile_lead_user.id
    
    # Set manager relationships
    lead_dev_user.manager_id = cto_user.id
    senior_dev_user.manager_id = lead_dev_user.id
    mobile_lead_user.manager_id = cto_user.id
    await test_session.flush()
    
    # Create user profiles
    cto_profile = UserProfile(
        user_id=cto_user.id,
        first_name="John",
        last_name="Tech",
        display_name="John Tech",
        avatar_url="https://example.com/avatars/johntech.jpg",
        bio="Experienced CTO with strong technical background",
        phone="+84123456789",
        location="Ho Chi Minh City",
        timezone="Asia/Ho_Chi_Minh"
    )
    
    lead_dev_profile = UserProfile(
        user_id=lead_dev_user.id,
        first_name="Alice",
        last_name="Lead",
        display_name="Alice Lead",
        avatar_url="https://example.com/avatars/alicelead.jpg",
        bio="Lead developer with focus on back-end technologies",
        phone="+84987654321",
        location="Ho Chi Minh City",
        timezone="Asia/Ho_Chi_Minh"
    )
    
    senior_dev_profile = UserProfile(
        user_id=senior_dev_user.id,
        first_name="Bob",
        last_name="Developer",
        display_name="Bob Dev",
        avatar_url="https://example.com/avatars/bobdev.jpg",
        bio="Senior developer with 5+ years experience",
        phone="+84564738291",
        location="Da Nang",
        timezone="Asia/Ho_Chi_Minh"
    )
    
    mobile_lead_profile = UserProfile(
        user_id=mobile_lead_user.id,
        first_name="Carol",
        last_name="Mobile",
        display_name="Carol Mobile",
        avatar_url="https://example.com/avatars/carolmobile.jpg",
        bio="Mobile development specialist with focus on React Native",
        phone="+84678912345",
        location="Ho Chi Minh City",
        timezone="Asia/Ho_Chi_Minh"
    )
    
    hr_manager_profile = UserProfile(
        user_id=hr_manager_user.id,
        first_name="David",
        last_name="HR",
        display_name="David HR",
        avatar_url="https://example.com/avatars/davidhr.jpg",
        bio="HR professional with 10+ years experience",
        phone="+84345678912",
        location="Ha Noi",
        timezone="Asia/Ho_Chi_Minh"
    )
    
    marketing_director_profile = UserProfile(
        user_id=marketing_director_user.id,
        first_name="Eva",
        last_name="Marketing",
        display_name="Eva Marketing",
        avatar_url="https://example.com/avatars/evamarketing.jpg",
        bio="Marketing director with experience in digital marketing",
        phone="+84891234567",
        location="Ho Chi Minh City",
        timezone="Asia/Ho_Chi_Minh"
    )
    
    test_session.add_all([
        cto_profile,
        lead_dev_profile,
        senior_dev_profile,
        mobile_lead_profile,
        hr_manager_profile,
        marketing_director_profile
    ])
    await test_session.flush()
    
    # Create department memberships
    cto_eng_membership = DepartmentMembership(
        user_id=cto_user.id,
        department_id=eng_dept.id,
        is_primary=True,
        start_date=datetime.utcnow() - timedelta(days=1095),
        position_title="Chief Technology Officer",
        timezone="Asia/Ho_Chi_Minh"
    )
    
    # CTO is also part of mobile department (secondary)
    cto_mobile_membership = DepartmentMembership(
        user_id=cto_user.id,
        department_id=mobile_dept.id,
        is_primary=False,
        start_date=datetime.utcnow() - timedelta(days=547),
        position_title="Technical Advisor",
        timezone="Asia/Ho_Chi_Minh"
    )
    
    lead_dev_membership = DepartmentMembership(
        user_id=lead_dev_user.id,
        department_id=eng_dept.id,
        is_primary=True,
        start_date=datetime.utcnow() - timedelta(days=730),
        position_title="Lead Developer",
        timezone="Asia/Ho_Chi_Minh"
    )
    
    senior_dev_membership = DepartmentMembership(
        user_id=senior_dev_user.id,
        department_id=eng_dept.id,
        is_primary=True,
        start_date=datetime.utcnow() - timedelta(days=365),
        position_title="Senior Developer",
        timezone="Asia/Ho_Chi_Minh"
    )
    
    mobile_lead_membership = DepartmentMembership(
        user_id=mobile_lead_user.id,
        department_id=mobile_dept.id,
        is_primary=True,
        start_date=datetime.utcnow() - timedelta(days=547),
        position_title="Mobile Team Lead",
        timezone="Asia/Ho_Chi_Minh"
    )
    
    # Mobile lead is also part of main engineering department
    mobile_lead_eng_membership = DepartmentMembership(
        user_id=mobile_lead_user.id,
        department_id=eng_dept.id,
        is_primary=False,
        start_date=datetime.utcnow() - timedelta(days=547),
        position_title="Senior Mobile Developer",
        timezone="Asia/Ho_Chi_Minh"
    )
    
    hr_manager_membership = DepartmentMembership(
        user_id=hr_manager_user.id,
        department_id=hr_dept.id,
        is_primary=True,
        start_date=datetime.utcnow() - timedelta(days=912),
        position_title="HR Manager",
        timezone="Asia/Ho_Chi_Minh"
    )
    
    marketing_director_membership = DepartmentMembership(
        user_id=marketing_director_user.id,
        department_id=marketing_dept.id,
        is_primary=True,
        start_date=datetime.utcnow() - timedelta(days=640),
        position_title="Marketing Director",
        timezone="Asia/Ho_Chi_Minh"
    )
    
    test_session.add_all([
        cto_eng_membership,
        cto_mobile_membership,
        lead_dev_membership,
        senior_dev_membership,
        mobile_lead_membership,
        mobile_lead_eng_membership,
        hr_manager_membership,
        marketing_director_membership
    ])
    
    # Commit all data
    await test_session.commit()
    
    print(f"Sample data created successfully with {len([cto_user, lead_dev_user, senior_dev_user, mobile_lead_user, hr_manager_user, marketing_director_user])} users")
    
    # Return all created entities in a dictionary
    return {
        "departments": {
            "engineering": eng_dept,
            "hr": hr_dept,
            "marketing": marketing_dept,
            "mobile": mobile_dept
        },
        "positions": {
            "cto": cto_position,
            "lead_dev": lead_dev_position,
            "senior_dev": senior_dev_position,
            "mobile_lead": mobile_lead_position,
            "hr_manager": hr_manager_position,
            "marketing_director": marketing_director_position
        },
        "users": {
            "cto": cto_user,
            "lead_dev": lead_dev_user,
            "senior_dev": senior_dev_user,
            "mobile_lead": mobile_lead_user,
            "hr_manager": hr_manager_user,
            "marketing_director": marketing_director_user
        },
        "profiles": {
            "cto": cto_profile,
            "lead_dev": lead_dev_profile,
            "senior_dev": senior_dev_profile,
            "mobile_lead": mobile_lead_profile,
            "hr_manager": hr_manager_profile,
            "marketing_director": marketing_director_profile
        },
        "memberships": {
            "cto_eng": cto_eng_membership,
            "cto_mobile": cto_mobile_membership,
            "lead_dev": lead_dev_membership,
            "senior_dev": senior_dev_membership,
            "mobile_lead": mobile_lead_membership,
            "mobile_lead_eng": mobile_lead_eng_membership,
            "hr_manager": hr_manager_membership,
            "marketing_director": marketing_director_membership
        }
    }