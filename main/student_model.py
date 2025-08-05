class StudentModel:
    def __init__(self, data):
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.first_name = data.get('first_name')
        self.last_name = data.get('last_name')
        self.dob = data.get('dob')
        self.age = data.get('age')
        self.grade = data.get('grade')
        self.email = data.get('email')
        self.phone_number = data.get('phone_number')
        self.address = data.get('address')
        self.city = data.get('city')
        self.country = data.get('country')
        self.place_of_birth = data.get('place_of_birth')
        self.region = data.get('region')
        self.nationality = data.get('nationality')
        self.last_school_attended = data.get('last_school_attended')
        self.marks = data.get('marks')
        self.department_id = data.get('department_id')
        self.subject_id = data.get('subject_id')
        self.profile_picture = data.get('profile_picture')
        self.subject_name = data.get('subject_name')
        self.reg_no = data.get('reg_no', data.get('user_id'))  # Use user_id as reg_no if not provided

class TeacherModel:
    def __init__(self, data):
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.name = data.get('name')
        self.email = data.get('email')
        self.profile_picture = data.get('profile_picture')

class DepartmentModel:
    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')

class SubjectModel:
    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.department_id = data.get('department_id')
        self.department_name = data.get('department_name')

class AdmissionModel:
    def __init__(self, data):
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.first_name = data.get('first_name')
        self.last_name = data.get('last_name')
        self.dob = data.get('dob')
        self.age = data.get('age')
        self.phone_number = data.get('phone_number')
        self.address = data.get('address')
        self.city = data.get('city')
        self.country = data.get('country')
        self.place_of_birth = data.get('place_of_birth')
        self.region = data.get('region')
        self.nationality = data.get('nationality')
        self.last_school_attended = data.get('last_school_attended')
        self.marks = data.get('marks')
        self.department_id = data.get('department_id')
        self.subject_id = data.get('subject_id')
        self.profile_picture = data.get('profile_picture')
        self.status = data.get('status')
        self.email = data.get('email')
        self.department_name = data.get('department_name')
        self.subject_name = data.get('subject_name')

class AttendanceModel:
    def __init__(self, data):
        self.student_id = data.get('student_id')
        self.subject_id = data.get('subject_id')
        self.date = data.get('date')
        self.status = data.get('status')

class MarksModel:
    def __init__(self, data):
        self.student_id = data.get('student_id')
        self.subject_id = data.get('subject_id')
        self.marks = data.get('marks')