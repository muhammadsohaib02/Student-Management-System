from flask import request, session

def register_routes(app, controller):
    @app.route('/')
    def root():
        return controller.handle_login(request, session)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        return controller.handle_login(request, session)


    @app.route('/register', methods=['GET', 'POST'])
    def register():
        return controller.handle_register(request)

    @app.route('/logout')
    def logout():
        return controller.handle_logout(session)

    @app.route('/admin')
    def admin():
        return controller.handle_admin(session)

    @app.route('/view-students', methods=['GET', 'POST'])
    def view_students():
        return controller.handle_view_students(request, session)

    @app.route('/export-csv')
    def export_csv():
        return controller.handle_export_csv(session)

    @app.route('/edit-student/<int:student_id>', methods=['GET', 'POST'])
    def edit_student(student_id):
        return controller.handle_edit_student(request, session, student_id)

    @app.route('/delete-student/<int:student_id>')
    def delete_student(student_id):
        return controller.handle_delete_student(session, student_id)

    @app.route('/add-teacher', methods=['GET', 'POST'])
    def add_teacher():
        return controller.handle_add_teacher(request, session)

    @app.route('/delete-teacher/<int:teacher_id>', methods=['POST'])
    def delete_teacher(teacher_id):
        return controller.handle_delete_teacher(session, teacher_id)

    @app.route('/edit-teacher/<int:teacher_id>', methods=['GET', 'POST'])
    def edit_teacher(teacher_id):
        return controller.handle_edit_teacher(request, session, teacher_id)

    @app.route('/manage-departments', methods=['GET', 'POST'])
    def manage_departments():
        return controller.handle_manage_departments(request, session)

    @app.route('/manage-subjects', methods=['GET', 'POST'])
    def manage_subjects():
        return controller.handle_manage_subjects(request, session)

    @app.route('/assign-subject/<int:teacher_id>', methods=['GET', 'POST'])
    def assign_subject(teacher_id):
        return controller.handle_assign_subject(request, session, teacher_id)

    @app.route('/unassign-subject/<int:teacher_id>/<int:subject_id>', methods=['POST'])
    def unassign_subject(teacher_id, subject_id):
        return controller.handle_unassign_subject(request, session, teacher_id, subject_id)

    @app.route('/manage-admissions')
    def manage_admissions():
        return controller.handle_manage_admissions(session)

    @app.route('/approve-admission/<int:id>', methods=['POST'])
    def approve_admission(id):
        return controller.handle_approve_admission(request, session, id)

    @app.route('/reject-admission/<int:id>', methods=['POST'])
    def reject_admission(id):
        return controller.handle_reject_admission(session, id)

    @app.route('/student')
    def student():
        return controller.handle_student(session)

    @app.route('/admission-form', methods=['GET', 'POST'])
    def admission_form():
        return controller.handle_admission_form(request, session)

    @app.route('/get-subjects/<int:dept_id>')
    def get_subjects(dept_id):
        return controller.get_subjects(dept_id)

    @app.route('/teacher')
    def teacher():
        return controller.handle_teacher(session)

    @app.route('/mark-attendance', methods=['GET', 'POST'])
    def mark_attendance():
        return controller.handle_mark_attendance(request, session)

    @app.route('/add-marks', methods=['GET', 'POST'])
    def add_marks():
        return controller.handle_add_marks(request, session)

    @app.route('/submit-marks', methods=['POST'])
    def submit_marks():
        return controller.handle_submit_marks(request, session)

    @app.route('/student/marks')
    def student_marks():
        return controller.handle_student_marks(session)

    @app.route('/student/attendance')
    def student_attendance():
        return controller.handle_student_attendance(session)

    @app.route('/enroll-subjects', methods=['GET', 'POST'])
    def enroll_subjects():
        return controller.handle_enroll_subjects(request, session)