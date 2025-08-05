from flask import current_app, render_template, flash, redirect, url_for, send_file, jsonify, request, session
from io import StringIO
import csv
import os
from datetime import datetime, date
import mysql.connector
from student_model import StudentModel, TeacherModel, DepartmentModel, SubjectModel, AdmissionModel, AttendanceModel, MarksModel

class StudentController:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'user': 'optimus',
            'password': 'Optimus22',
            'database': 'school_db'
        }

    def get_db_connection(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except mysql.connector.Error as e:
            print(f"Database connection error: {str(e)}")
            flash(f"Database connection error: {str(e)}", 'danger')
            raise

    def handle_login(self, request, session):
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT id, email, password, role FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                if user and user['password'] == password:  # Note: Use hashed passwords in production
                    session['user_id'] = user['id']
                    session['role'] = user['role']
                    print(f"User logged in: user_id {user['id']}, role {user['role']}")  # Debug log
                    if user['role'] == 'admin':
                        return redirect(url_for('admin'))
                    elif user['role'] == 'teacher':
                        return redirect(url_for('teacher'))
                    elif user['role'] == 'student':
                        # Check admission status
                        cursor.execute("SELECT id, status FROM admissions WHERE user_id = %s", (user['id'],))
                        admission = cursor.fetchone()
                        if not admission:
                            print(f"No admission found for user_id {user['id']}")  # Debug log
                            return redirect(url_for('admission_form'))
                        elif admission['status'] == 'pending':
                            print(f"Admission pending for user_id {user['id']}")  # Debug log
                            flash('Your admission is pending approval.', 'warning')
                            return redirect(url_for('login'))
                        elif admission['status'] == 'approved':
                            # Verify students table
                            cursor.execute("SELECT id FROM students WHERE user_id = %s", (user['id'],))
                            if cursor.fetchone():
                                print(f"Student profile found for user_id {user['id']}")  # Debug log
                                return redirect(url_for('student'))
                            else:
                                print(f"No student profile found for user_id {user['id']}")  # Debug log
                                flash('Student profile not found. Contact admin.', 'danger')
                                return redirect(url_for('login'))
                        else:
                            print(f"Admission rejected for user_id {user['id']}")  # Debug log
                            flash('Your admission was rejected. Contact admin.', 'danger')
                            return redirect(url_for('login'))
                    else:
                        flash('Invalid role', 'danger')
                        session.clear()
                        return redirect(url_for('login'))
                else:
                    flash('Invalid email or password', 'danger')
            except mysql.connector.Error as e:
                print(f"Database error in login: {str(e)}")  # Debug log
                flash(f'Error during login: {str(e)}', 'danger')
            finally:
                cursor.close()
                conn.close()
        return render_template('login.html')

    def handle_approve_admission(self, request, session, id):
        if session.get('role') != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM admissions WHERE id = %s AND status = 'pending'", (id,))
            admission_data = cursor.fetchone()
            if not admission_data:
                print(f"No pending admission found for ID {id}")  # Debug log
                flash('No pending admission found for this ID', 'danger')
                return redirect(url_for('manage_admissions'))
            if not admission_data.get('first_name') or not admission_data.get('last_name'):
                print(f"Missing first_name or last_name for admission ID {id}: {admission_data}")  # Debug log
                flash('Admission record is missing first_name or last_name', 'danger')
                return redirect(url_for('manage_admissions'))
            cursor.execute("SELECT COUNT(*) as count FROM students WHERE user_id = %s", (admission_data['user_id'],))
            if cursor.fetchone()['count'] > 0:
                print(f"Student already exists for user_id {admission_data['user_id']}")  # Debug log
                flash('Student already exists in the system.', 'danger')
                cursor.execute("UPDATE admissions SET status = 'approved' WHERE id = %s", (id,))
                conn.commit()
                return redirect(url_for('manage_admissions'))
            full_name = f"{admission_data['first_name']} {admission_data['last_name']}".strip()
            print(
                f"Approving admission ID {id} for student: {full_name}, user_id: {admission_data['user_id']}, profile_picture: {admission_data['profile_picture']}, department_id: {admission_data['department_id']}")  # Debug log
            cursor.execute("""
                           INSERT INTO students (user_id, name, dob, age, phone_number, address, city, country,
                                                 place_of_birth, region, nationality, last_school_attended, marks,
                                                 department_id,
                                                 profile_picture)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                           """, (
                               admission_data['user_id'], full_name,
                               admission_data['dob'], admission_data['age'], admission_data['phone_number'],
                               admission_data['address'], admission_data['city'], admission_data['country'],
                               admission_data['place_of_birth'], admission_data['region'],
                               admission_data['nationality'],
                               admission_data['last_school_attended'], admission_data['marks'],
                               admission_data['department_id'], admission_data['profile_picture']
                           ))
            cursor.execute("UPDATE admissions SET status = 'approved' WHERE id = %s", (id,))
            conn.commit()
            flash('Admission approved successfully', 'success')
        except mysql.connector.Error as e:
            conn.rollback()
            print(f"Database error in approve_admission: {str(e)}")  # Debug log
            flash(f'Error approving admission: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('manage_admissions'))

    def handle_logout(self, session):
        session.clear()
        flash('Logged out successfully', 'success')
        return redirect(url_for('login'))

    def handle_admin(self, session):
        if session.get('role') != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT COUNT(*) as student_count FROM students")
            student_count = cursor.fetchone()['student_count']
            cursor.execute("SELECT COUNT(*) as teacher_count FROM teachers")
            teacher_count = cursor.fetchone()['teacher_count']
            cursor.execute("SELECT COUNT(*) as pending_admissions FROM admissions WHERE status = 'pending'")
            pending_admissions = cursor.fetchone()['pending_admissions']
        except mysql.connector.Error as e:
            flash(f'Error fetching admin stats: {str(e)}', 'danger')
            student_count = teacher_count = pending_admissions = 0
        finally:
            cursor.close()
            conn.close()
        stats = {'student_count': student_count, 'teacher_count': teacher_count, 'pending_admissions': pending_admissions}
        return render_template('admin.html', stats=stats)

    def handle_view_students(self, request, session):
        if session.get('role') != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        search_query = request.form.get('search_query', '') if request.method == 'POST' else request.args.get(
            'search_query', '')
        page = int(request.args.get('page', 1))
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            per_page = 10
            offset = (page - 1) * per_page
            query = """
                    SELECT s.id, \
                           s.user_id, \
                           s.name, \
                           s.dob, \
                           s.age, \
                           s.phone_number, \
                           s.address, \
                           s.city,
                           s.country, \
                           s.place_of_birth, \
                           s.region, \
                           s.nationality, \
                           s.last_school_attended,
                           s.marks, \
                           s.department_id, \
                           s.profile_picture, \
                           s.subject_id, \
                           u.email
                    FROM students s
                             JOIN users u ON s.user_id = u.id
                    WHERE s.name LIKE %s \
                       OR u.email LIKE %s
                        LIMIT %s \
                    OFFSET %s \
                    """
            search_term = f"%{search_query}%"
            print(f"Executing query: {query % (search_term, search_term, per_page, offset)}")  # Debug log
            cursor.execute(query, (search_term, search_term, per_page, offset))
            students_data = cursor.fetchall()
            students = [StudentModel(student) for student in students_data]
            cursor.execute("SELECT CEIL(COUNT(*) / %s) as total_pages FROM students WHERE name LIKE %s",
                           (per_page, search_term))
            total_pages = int(cursor.fetchone()['total_pages'])
        except mysql.connector.Error as e:
            print(f"Database error: {str(e)}")  # Debug log
            flash(f'Error fetching students: {str(e)}', 'danger')
            students = []
            total_pages = 1
        finally:
            cursor.close()
            conn.close()
        return render_template('view-students.html', students=students, page=page, total_pages=total_pages, search_query=search_query)
    def handle_export_csv(self, session):
        if session.get('role') != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT s.*, u.email FROM students s JOIN users u ON s.user_id = u.id")
            students_data = cursor.fetchall()
        except mysql.connector.Error as e:
            flash(f'Error exporting students: {str(e)}', 'danger')
            students_data = []
        finally:
            cursor.close()
            conn.close()
        students = [StudentModel(student) for student in students_data]
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Name', 'DOB', 'Age', 'Email', 'Phone', 'Address', 'City', 'Country', 'Place of Birth', 'Region', 'Nationality', 'Last School Attended', 'Marks', 'Department ID'])
        for student in students:
            writer.writerow([
                student.id, student.name, student.dob, student.age, student.email,
                student.phone_number or '', student.address or '', student.city or '', student.country or '',
                student.place_of_birth or '', student.region or '', student.nationality or '', student.last_school_attended or '',
                student.marks or '', student.department_id or ''
            ])
        output.seek(0)
        return send_file(output, mimetype='text/csv', as_attachment=True, download_name='students.csv')

    def handle_edit_student(self, request, session, student_id):
        if session.get('role') != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        if request.method == 'POST':
            data = {
                'name': request.form.get('name'),
                'email': request.form.get('email'),
                'phone_number': request.form.get('phone_number'),
                'address': request.form.get('address'),
                'city': request.form.get('city'),
                'country': request.form.get('country')
            }
            if not all(data.values()):
                flash('All fields are required', 'danger')
                return redirect(url_for('edit_student', student_id=student_id))
            conn = self.get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE students s 
                    JOIN users u ON s.user_id = u.id 
                    SET s.name = %s, u.email = %s, s.phone_number = %s, 
                        s.address = %s, s.city = %s, s.country = %s
                    WHERE s.id = %s
                """, (data['name'], data['email'], data['phone_number'],
                      data['address'], data['city'], data['country'], student_id))
                conn.commit()
                flash('Student updated successfully', 'success')
                return redirect(url_for('view_students'))
            except mysql.connector.Error as e:
                conn.rollback()
                flash(f'Error updating student: {str(e)}', 'danger')
            finally:
                cursor.close()
                conn.close()
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT s.*, u.email FROM students s JOIN users u ON s.user_id = u.id WHERE s.id = %s", (student_id,))
            student_data = cursor.fetchone()
        except mysql.connector.Error as e:
            flash(f'Error fetching student: {str(e)}', 'danger')
            student_data = None
        finally:
            cursor.close()
            conn.close()
        student = StudentModel(student_data) if student_data else None
        if not student:
            flash('Student not found', 'danger')
            return redirect(url_for('view_students'))
        return render_template('edit-student.html', student=student)

    def handle_delete_student(self, session, student_id):
        if session.get('role') != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
            conn.commit()
            flash('Student deleted successfully', 'success')
        except mysql.connector.Error as e:
            conn.rollback()
            flash(f'Error deleting student: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('view_students'))

    def handle_add_teacher(self, request, session):
        if session.get('role') != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT s.*, d.name as department_name FROM subjects s JOIN departments d ON s.department_id = d.id")
            subjects_data = cursor.fetchall()
            subjects = [SubjectModel(subject) for subject in subjects_data]
            cursor.execute("""
                SELECT t.*, u.email, GROUP_CONCAT(ts.subject_id) as subject_ids
                FROM teachers t 
                JOIN users u ON t.user_id = u.id 
                LEFT JOIN teacher_subjects ts ON t.id = ts.teacher_id
                GROUP BY t.id
            """)
            teachers_data = cursor.fetchall()
            teachers = []
            for teacher in teachers_data:
                teacher_model = TeacherModel(teacher)
                if teacher['subject_ids']:
                    cursor.execute("""
                        SELECT s.*, d.name as department_name 
                        FROM subjects s 
                        JOIN departments d ON s.department_id = d.id 
                        WHERE s.id IN (%s)
                    """ % ','.join(['%s'] * len(teacher['subject_ids'].split(','))),
                    tuple(teacher['subject_ids'].split(',')))
                    teacher_model.subjects = [SubjectModel(sub) for sub in cursor.fetchall()]
                    teacher_model.subject_ids = [int(id) for id in teacher['subject_ids'].split(',')]
                else:
                    teacher_model.subjects = []
                    teacher_model.subject_ids = []
                teachers.append(teacher_model)
        except mysql.connector.Error as e:
            flash(f'Error fetching data: {str(e)}', 'danger')
            subjects = teachers = []
        finally:
            cursor.close()
            conn.close()
        if request.method == 'POST':
            data = {
                'name': request.form.get('name'),
                'email': request.form.get('email'),
                'password': request.form.get('password'),
                'profile_picture': request.files.get('profile_picture'),
                'subjects': request.form.getlist('subjects')
            }
            if not all([data['name'], data['email'], data['password']]):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': 'All fields are required'})
                flash('All fields are required', 'danger')
                return render_template('add_teacher.html', teachers=teachers, subjects=subjects)
            if len(data['password']) < 8 or not any(c.isdigit() for c in data['password']):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': 'Password must be at least 8 characters and contain a number'})
                flash('Password must be at least 8 characters and contain a number', 'danger')
                return render_template('add_teacher.html', teachers=teachers, subjects=subjects)
            conn = self.get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (email, password, role) VALUES (%s, %s, %s)", (data['email'], data['password'], 'teacher'))
                user_id = cursor.lastrowid
                profile_picture_path = None
                if data['profile_picture']:
                    filename = f"teacher_{user_id}_{data['profile_picture'].filename}"
                    data['profile_picture'].save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    profile_picture_path = filename
                cursor.execute("INSERT INTO teachers (user_id, name, profile_picture) VALUES (%s, %s, %s)", (user_id, data['name'], profile_picture_path))
                teacher_id = cursor.lastrowid
                for subject_id in data['subjects']:
                    cursor.execute("INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES (%s, %s)", (teacher_id, subject_id))
                conn.commit()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': True, 'message': 'Teacher added successfully'})
                flash('Teacher added successfully', 'success')
                return redirect(url_for('add_teacher'))
            except mysql.connector.Error as e:
                conn.rollback()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': f'Error adding teacher: {str(e)}'})
                flash(f'Error adding teacher: {str(e)}', 'danger')
            finally:
                cursor.close()
                conn.close()
        return render_template('add_teacher.html', teachers=teachers, subjects=subjects)

    def handle_delete_teacher(self, session, teacher_id):
        if session.get('role') != 'admin':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Unauthorized access'})
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id FROM teachers WHERE id = %s", (teacher_id,))
            result = cursor.fetchone()
            if not result:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': 'Teacher not found'})
                flash('Teacher not found', 'danger')
                return redirect(url_for('add_teacher'))
            user_id = result[0]
            cursor.execute("DELETE FROM teacher_subjects WHERE teacher_id = %s", (teacher_id,))
            cursor.execute("DELETE FROM teachers WHERE id = %s", (teacher_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': 'Teacher deleted successfully'})
            flash('Teacher deleted successfully', 'success')
        except mysql.connector.Error as e:
            conn.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'Error deleting teacher: {str(e)}'})
            flash(f'Error deleting teacher: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('add_teacher'))

    def handle_edit_teacher(self, request, session, teacher_id):
        if session.get('role') != 'admin':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Unauthorized access'})
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT t.*, u.email, GROUP_CONCAT(ts.subject_id) as subject_ids
                FROM teachers t 
                JOIN users u ON t.user_id = u.id 
                LEFT JOIN teacher_subjects ts ON t.id = ts.teacher_id
                WHERE t.id = %s
                GROUP BY t.id
            """, (teacher_id,))
            teacher_data = cursor.fetchone()
            if not teacher_data:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': 'Teacher not found'})
                flash('Teacher not found', 'danger')
                return redirect(url_for('add_teacher'))
            teacher = TeacherModel(teacher_data)
            teacher.subject_ids = [int(id) for id in teacher_data['subject_ids'].split(',')] if teacher_data['subject_ids'] else []
            cursor.execute("SELECT s.*, d.name as department_name FROM subjects s JOIN departments d ON s.department_id = d.id")
            subjects_data = cursor.fetchall()
            subjects = [SubjectModel(subject) for subject in subjects_data]
        except mysql.connector.Error as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'Error fetching teacher: {str(e)}'})
            flash(f'Error fetching teacher: {str(e)}', 'danger')
            return redirect(url_for('add_teacher'))
        finally:
            cursor.close()
            conn.close()
        if request.method == 'POST':
            data = {
                'name': request.form.get('name'),
                'email': request.form.get('email'),
                'password': request.form.get('password'),
                'profile_picture': request.files.get('profile_picture'),
                'subjects': request.form.getlist('subjects')
            }
            if not all([data['name'], data['email']]):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': 'Name and email are required'})
                flash('Name and email are required', 'danger')
                return render_template('edit_teacher.html', teacher=teacher, subjects=subjects)
            if data['password'] and (len(data['password']) < 8 or not any(c.isdigit() for c in data['password'])):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': 'Password must be at least 8 characters and contain a number'})
                flash('Password must be at least 8 characters and contain a number', 'danger')
                return render_template('edit_teacher.html', teacher=teacher, subjects=subjects)
            conn = self.get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT user_id FROM teachers WHERE id = %s", (teacher_id,))
                result = cursor.fetchone()
                if not result:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({'success': False, 'message': 'Teacher not found'})
                    flash('Teacher not found', 'danger')
                    return redirect(url_for('add_teacher'))
                user_id = result[0]
                cursor.execute("UPDATE users SET email = %s WHERE id = %s", (data['email'], user_id))
                if data['password']:
                    cursor.execute("UPDATE users SET password = %s WHERE id = %s", (data['password'], user_id))
                profile_picture_path = teacher.profile_picture
                if data['profile_picture']:
                    filename = f"teacher_{user_id}_{data['profile_picture'].filename}"
                    data['profile_picture'].save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    profile_picture_path = filename
                cursor.execute("UPDATE teachers SET name = %s, profile_picture = %s WHERE id = %s", (data['name'], profile_picture_path, teacher_id))
                cursor.execute("DELETE FROM teacher_subjects WHERE teacher_id = %s", (teacher_id,))
                for subject_id in data['subjects']:
                    cursor.execute("INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES (%s, %s)", (teacher_id, subject_id))
                conn.commit()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': True, 'message': 'Teacher updated successfully'})
                flash('Teacher updated successfully', 'success')
                return redirect(url_for('add_teacher'))
            except mysql.connector.Error as e:
                conn.rollback()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': f'Error updating teacher: {str(e)}'})
                flash(f'Error updating teacher: {str(e)}', 'danger')
                return render_template('edit_teacher.html', teacher=teacher, subjects=subjects)
            finally:
                cursor.close()
                conn.close()
        return render_template('edit_teacher.html', teacher=teacher, subjects=subjects)

    def handle_manage_departments(self, request, session):
        if session.get('role') != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        if request.method == 'POST':
            name = request.form.get('name')
            if not name:
                flash('Department name is required', 'danger')
                return render_template('manage_departments.html')
            conn = self.get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO departments (name) VALUES (%s)", (name,))
                conn.commit()
                flash('Department added successfully', 'success')
            except mysql.connector.Error as e:
                conn.rollback()
                flash(f'Error adding department: {str(e)}', 'danger')
            finally:
                cursor.close()
                conn.close()
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM departments")
            departments_data = cursor.fetchall()
        except mysql.connector.Error as e:
            flash(f'Error fetching departments: {str(e)}', 'danger')
            departments_data = []
        finally:
            cursor.close()
            conn.close()
        departments = [DepartmentModel(dept) for dept in departments_data]
        return render_template('manage_departments.html', departments=departments)

    def handle_manage_subjects(self, request, session):
        if session.get('role') != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        if request.method == 'POST':
            data = {
                'name': request.form.get('name'),
                'department_id': request.form.get('department_id')
            }
            if not all(data.values()):
                flash('All fields are required', 'danger')
                return render_template('manage_subjects.html')
            try:
                data['department_id'] = int(data['department_id'])
            except ValueError:
                flash('Invalid department selection', 'danger')
                return render_template('manage_subjects.html')
            conn = self.get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO subjects (name, department_id) VALUES (%s, %s)", (data['name'], data['department_id']))
                conn.commit()
                flash('Subject added successfully', 'success')
            except mysql.connector.Error as e:
                conn.rollback()
                flash(f'Error adding subject: {str(e)}', 'danger')
            finally:
                cursor.close()
                conn.close()
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM departments")
            departments_data = cursor.fetchall()
            cursor.execute("SELECT s.*, d.name as department_name FROM subjects s JOIN departments d ON s.department_id = d.id")
            subjects_data = cursor.fetchall()
        except mysql.connector.Error as e:
            flash(f'Error fetching subjects: {str(e)}', 'danger')
            departments_data = subjects_data = []
        finally:
            cursor.close()
            conn.close()
        departments = [DepartmentModel(dept) for dept in departments_data]
        subjects = [SubjectModel(sub) for sub in subjects_data]
        return render_template('manage_subjects.html', departments=departments, subjects=subjects)

    def handle_assign_subject(self, request, session, teacher_id):
        if session.get('role') != 'admin':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Unauthorized access'})
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # Fetch teacher details
            cursor.execute("SELECT t.*, u.email FROM teachers t JOIN users u ON t.user_id = u.id WHERE t.id = %s", (teacher_id,))
            teacher_data = cursor.fetchone()
            if not teacher_data:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': 'Teacher not found'})
                flash('Teacher not found', 'danger')
                return redirect(url_for('add_teacher'))
            teacher = TeacherModel(teacher_data)
            print(f"Teacher fetched: {teacher_data}")  # Debug log

            # Fetch assigned subjects
            cursor.execute("""
                SELECT s.*, d.name as department_name 
                FROM subjects s 
                JOIN departments d ON s.department_id = d.id 
                JOIN teacher_subjects ts ON s.id = ts.subject_id 
                WHERE ts.teacher_id = %s
            """, (teacher_id,))
            teacher.subjects = [SubjectModel(sub) for sub in cursor.fetchall()]
            print(f"Assigned subjects: {[sub.name for sub in teacher.subjects]}")  # Debug log

            # Fetch available subjects (not assigned to this teacher)
            cursor.execute("""
                SELECT s.*, d.name as department_name 
                FROM subjects s 
                JOIN departments d ON s.department_id = d.id 
                WHERE s.id NOT IN (
                    SELECT subject_id FROM teacher_subjects WHERE teacher_id = %s
                )
            """, (teacher_id,))
            available_subjects = [SubjectModel(sub) for sub in cursor.fetchall()]
            print(f"Available subjects: {[sub.name for sub in available_subjects]}")  # Debug log

            if request.method == 'POST':
                subject_ids = request.form.getlist('subjects')
                print(f"Submitted subject IDs: {subject_ids}")  # Debug log
                if subject_ids:
                    try:
                        for subject_id in subject_ids:
                            cursor.execute(
                                "INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES (%s, %s)",
                                (teacher_id, int(subject_id))
                            )
                        conn.commit()
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return jsonify({'success': True, 'message': 'Subjects assigned successfully'})
                        flash('Subjects assigned successfully', 'success')
                    except (ValueError, mysql.connector.Error) as e:
                        conn.rollback()
                        error_message = f'Error assigning subjects: {str(e)}'
                        print(error_message)  # Debug log
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return jsonify({'success': False, 'message': error_message})
                        flash(error_message, 'danger')
                else:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({'success': False, 'message': 'No subjects selected'})
                    flash('No subjects selected', 'danger')
                return redirect(url_for('assign_subject', teacher_id=teacher_id))

            return render_template('assign_subject.html', teacher=teacher, available_subjects=available_subjects)

        except mysql.connector.Error as e:
            conn.rollback()
            error_message = f'Error: {str(e)}'
            print(error_message)  # Debug log
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_message})
            flash(error_message, 'danger')
            return redirect(url_for('add_teacher'))
        finally:
            cursor.close()
            conn.close()

    def handle_unassign_subject(self, request, session, teacher_id, subject_id):
        if session.get('role') != 'admin':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Unauthorized access'})
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM teacher_subjects WHERE teacher_id = %s AND subject_id = %s",
                (teacher_id, subject_id)
            )
            if cursor.rowcount == 0:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': 'Subject not assigned to this teacher'})
                flash('Subject not assigned to this teacher', 'danger')
            else:
                conn.commit()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': True, 'message': 'Subject unassigned successfully'})
                flash('Subject unassigned successfully', 'success')
        except mysql.connector.Error as e:
            conn.rollback()
            error_message = f'Error unassigning subject: {str(e)}'
            print(error_message)  # Debug log
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_message})
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('assign_subject', teacher_id=teacher_id))

    def handle_manage_admissions(self, session):
        if session.get('role') != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT a.id, a.user_id, a.first_name, a.last_name, u.email, a.dob, a.age, a.phone_number, 
                       a.address, a.city, a.country, a.place_of_birth, a.region, a.nationality, 
                       a.last_school_attended, a.marks, a.department_id, a.profile_picture, 
                       a.status, d.name AS department_name
                FROM admissions a
                LEFT JOIN users u ON a.user_id = u.id
                LEFT JOIN departments d ON a.department_id = d.id
                WHERE a.status = 'pending'
            """
            cursor.execute(query)
            applications_data = cursor.fetchall()
            applications = []
            for app in applications_data:
                app_data = {
                    'id': app['id'],
                    'user_id': app['user_id'],
                    'name': f"{app['first_name']} {app['last_name']}",
                    'email': app.get('email', ''),
                    'dob': app['dob'],
                    'age': app['age'],
                    'phone_number': app['phone_number'],
                    'address': app['address'],
                    'city': app['city'],
                    'country': app['country'],
                    'place_of_birth': app['place_of_birth'],
                    'region': app['region'],
                    'nationality': app['nationality'],
                    'last_school_attended': app['last_school_attended'],
                    'marks': app['marks'],
                    'department_id': app['department_id'],
                    'profile_picture': app['profile_picture'],
                    'status': app['status'],
                    'department_name': app['department_name']
                }
                applications.append(AdmissionModel(app_data))
            cursor.close()
            conn.close()
            if not applications:
                flash('No pending admissions found.', 'info')
            return render_template('admissions.html', admissions=applications)
        except mysql.connector.Error as e:
            flash(f"Error fetching admissions: {str(e)}", 'danger')
            return render_template('admissions.html', admissions=[])

    def handle_approve_admission(self, request, session, id):
        if session.get('role') != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM admissions WHERE id = %s AND status = 'pending'", (id,))
            admission_data = cursor.fetchone()
            if not admission_data:
                print(f"No pending admission found for ID {id}")  # Debug log
                flash('No pending admission found for this ID', 'danger')
                return redirect(url_for('manage_admissions'))
            if not admission_data.get('first_name') or not admission_data.get('last_name'):
                print(f"Missing first_name or last_name for admission ID {id}: {admission_data}")  # Debug log
                flash('Admission record is missing first_name or last_name', 'danger')
                return redirect(url_for('manage_admissions'))
            cursor.execute("SELECT COUNT(*) as count FROM students WHERE user_id = %s", (admission_data['user_id'],))
            if cursor.fetchone()['count'] > 0:
                print(f"Student already exists for user_id {admission_data['user_id']}")  # Debug log
                flash('Student already exists in the system.', 'danger')
                cursor.execute("UPDATE admissions SET status = 'approved' WHERE id = %s", (id,))
                conn.commit()
                return redirect(url_for('manage_admissions'))
            full_name = f"{admission_data['first_name']} {admission_data['last_name']}".strip()
            print(
                f"Approving admission ID {id} for student: {full_name}, user_id: {admission_data['user_id']}")  # Debug log
            cursor.execute("""
                           INSERT INTO students (user_id, name, dob, age, phone_number, address, city, country,
                                                 place_of_birth, region, nationality, last_school_attended, marks,
                                                 department_id,
                                                 profile_picture)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                           """, (
                               admission_data['user_id'], full_name,
                               admission_data['dob'], admission_data['age'], admission_data['phone_number'],
                               admission_data['address'], admission_data['city'], admission_data['country'],
                               admission_data['place_of_birth'], admission_data['region'],
                               admission_data['nationality'],
                               admission_data['last_school_attended'], admission_data['marks'],
                               admission_data['department_id'], admission_data['profile_picture']
                           ))
            cursor.execute("UPDATE admissions SET status = 'approved' WHERE id = %s", (id,))
            conn.commit()
            flash('Admission approved successfully', 'success')
        except mysql.connector.Error as e:
            conn.rollback()
            print(f"Database error in approve_admission: {str(e)}")  # Debug log
            flash(f'Error approving admission: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('manage_admissions'))

    def handle_reject_admission(self, session, id):
        if session.get('role') != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT user_id FROM admissions WHERE id = %s AND status = 'pending'", (id,))
            admission = cursor.fetchone()
            if not admission:
                print(f"No pending admission found for ID {id}")  # Debug log
                flash('No pending admission found for this ID', 'danger')
                return redirect(url_for('manage_admissions'))
            print(f"Rejecting admission ID {id} for user_id {admission['user_id']}")  # Debug log
            cursor.execute("DELETE FROM admissions WHERE id = %s AND status = 'pending'", (id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (admission['user_id'],))
            conn.commit()
            flash('Admission rejected successfully', 'success')
        except mysql.connector.Error as e:
            conn.rollback()
            print(f"Database error in reject_admission: {str(e)}")  # Debug log
            flash(f'Error rejecting admission: {str(e)}', 'danger')
        except Exception as e:
            conn.rollback()
            print(f"Unexpected error in reject_admission: {str(e)}")  # Debug log
            flash(f'Unexpected error: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('manage_admissions'))

    def handle_student(self, session):
        if session.get('role') != 'student':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        user_id = session.get('user_id')
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                           SELECT s.*, u.email, d.name AS department_name
                           FROM students s
                                    JOIN users u ON s.user_id = u.id
                                    LEFT JOIN departments d ON s.department_id = d.id
                           WHERE s.user_id = %s
                           """, (user_id,))
            student_data = cursor.fetchone()
            if not student_data:
                print(f"No student found for user_id {user_id}")  # Debug log
                flash('Student profile not found. Ensure your admission is approved.', 'danger')
                return redirect(url_for('login'))
            student = StudentModel(student_data)
            print(f"Student data: {student_data}")  # Debug log
            # Fetch enrolled subjects
            cursor.execute("""
                           SELECT s.id, s.name, d.name AS department_name
                           FROM subjects s
                                    JOIN student_subjects ss ON s.id = ss.subject_id
                                    JOIN departments d ON s.department_id = d.id
                           WHERE ss.student_id = %s
                           """, (student_data['id'],))
            enrolled_subjects = [SubjectModel(sub) for sub in cursor.fetchall()]
            # Fetch attendance stats
            cursor.execute("""
                           SELECT COUNT(*) AS present_count
                           FROM attendance
                           WHERE student_id = %s
                             AND status = 'present'
                           """, (student_data['id'],))
            present_count = cursor.fetchone()['present_count']
            cursor.execute("""
                           SELECT COUNT(*) AS absent_count
                           FROM attendance
                           WHERE student_id = %s
                             AND status = 'absent'
                           """, (student_data['id'],))
            absent_count = cursor.fetchone()['absent_count']
            attendance_stats = {'present_count': present_count, 'absent_count': absent_count}
            # Fetch marks stats
            cursor.execute("""
                           SELECT SUM(m.marks) AS total_marks_obtained, COUNT(m.marks) * 100 AS total_marks_possible
                           FROM marks m
                           WHERE m.student_id = %s
                           """, (student_data['id'],))
            marks_data = cursor.fetchone()
            marks_stats = {
                'total_marks_obtained': marks_data['total_marks_obtained'] or 0,
                'total_marks_possible': marks_data['total_marks_possible'] or 0
            }
            print(f"Enrolled subjects: {[sub.name for sub in enrolled_subjects]}, "
                  f"Attendance: {attendance_stats}, Marks: {marks_stats}")  # Debug log
        except mysql.connector.Error as e:
            conn.rollback()
            print(f"Database error in handle_student: {str(e)}")  # Debug log
            flash(f'Error fetching student data: {str(e)}', 'danger')
            student = None
            enrolled_subjects = []
            attendance_stats = {'present_count': 0, 'absent_count': 0}
            marks_stats = {'total_marks_obtained': 0, 'total_marks_possible': 0}
        finally:
            cursor.close()
            conn.close()
        return render_template('student_portal.html', student=student, enrolled_subjects=enrolled_subjects,
                               attendance_stats=attendance_stats, marks_stats=marks_stats)

    def handle_admission_form(self, request, session):
        if session.get('role') != 'student':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM departments")
            departments_data = cursor.fetchall()
        except mysql.connector.Error as e:
            flash(f'Error fetching departments: {str(e)}', 'danger')
            departments_data = []
        finally:
            cursor.close()
            conn.close()
        departments = [DepartmentModel(dept) for dept in departments_data]
        if request.method == 'POST':
            data = {
                'user_id': session.get('user_id'),
                'first_name': request.form.get('first_name', '').strip(),
                'last_name': request.form.get('last_name', '').strip(),
                'dob': request.form.get('dob'),
                'place_of_birth': request.form.get('place_of_birth', '').strip(),
                'region': request.form.get('region', '').strip(),
                'nationality': request.form.get('nationality', '').strip(),
                'address': request.form.get('address', '').strip(),
                'city': request.form.get('city', '').strip(),
                'country': request.form.get('country', '').strip(),
                'last_school_attended': request.form.get('last_school_attended', '').strip(),
                'marks': request.form.get('marks'),
                'phone_number': request.form.get('phone_number', '').strip(),
                'profile_picture': request.files.get('profile_picture'),
                'department_id': request.form.get('department_id')
            }
            if not all([data['first_name'], data['last_name'], data['dob'], data['marks'], data['department_id']]):
                flash('All required fields must be filled', 'danger')
                return render_template('admission_form.html', departments=departments)
            try:
                marks = float(data['marks'])
                if not (0 <= marks <= 100):
                    flash('Marks must be between 0 and 100.', 'danger')
                    return render_template('admission_form.html', departments=departments)
                department_id = int(data['department_id'])
                # Verify department_id exists
                conn = self.get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT id FROM departments WHERE id = %s", (department_id,))
                if not cursor.fetchone():
                    flash('Invalid department selection.', 'danger')
                    cursor.close()
                    conn.close()
                    return render_template('admission_form.html', departments=departments)
            except ValueError:
                flash('Invalid marks or department selection.', 'danger')
                return render_template('admission_form.html', departments=departments)
            try:
                dob = datetime.strptime(data['dob'], '%Y-%m-%d')
            except ValueError:
                flash('Invalid date of birth format. Use YYYY-MM-DD.', 'danger')
                return render_template('admission_form.html', departments=departments)
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            profile_picture_path = None
            if data['profile_picture'] and data['profile_picture'].filename:
                if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                    os.makedirs(current_app.config['UPLOAD_FOLDER'])
                filename = f"admission_{data['user_id']}_{data['profile_picture'].filename}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                data['profile_picture'].save(file_path)
                profile_picture_path = filename
                print(f"Profile picture saved: {file_path}")  # Debug log
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT COUNT(*) as count FROM admissions WHERE user_id = %s", (data['user_id'],))
                if cursor.fetchone()['count'] > 0:
                    flash('An admission application already exists for this user.', 'danger')
                    cursor.close()
                    conn.close()
                    return render_template('admission_form.html', departments=departments)
                cursor.execute("""
                               INSERT INTO admissions (user_id, first_name, last_name, dob, age, phone_number, address,
                                                       city, country,
                                                       place_of_birth, region, nationality, last_school_attended, marks,
                                                       department_id, profile_picture, status)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                               """, (
                                   data['user_id'], data['first_name'], data['last_name'], data['dob'], age,
                                   data['phone_number'],
                                   data['address'], data['city'], data['country'], data['place_of_birth'],
                                   data['region'],
                                   data['nationality'], data['last_school_attended'], marks, department_id,
                                   profile_picture_path, 'pending'
                               ))
                conn.commit()
                flash('Admission application submitted successfully', 'success')
                print(
                    f"Admission submitted: user_id={data['user_id']}, profile_picture={profile_picture_path}, department_id={department_id}")  # Debug log
                return redirect(url_for('student'))
            except mysql.connector.Error as e:
                conn.rollback()
                flash(f'Error submitting application: {str(e)}', 'danger')
                print(f"Database error in admission_form: {str(e)}")  # Debug log
            finally:
                cursor.close()
                conn.close()
        return render_template('admission_form.html', departments=departments)

    def get_subjects(self, dept_id):
        try:
            dept_id = int(dept_id)
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name FROM subjects WHERE department_id = %s", (dept_id,))
            subjects_data = cursor.fetchall()
            cursor.close()
            conn.close()
            return jsonify(subjects_data)
        except Exception as e:
            flash(f'Error fetching subjects: {str(e)}', 'danger')
            return jsonify([]), 500

    def handle_teacher(self, session):
        if session.get('role') != 'teacher':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        user_id = session.get('user_id')
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # Fetch teacher details
            cursor.execute("""
                           SELECT t.*, u.email
                           FROM teachers t
                                    JOIN users u ON t.user_id = u.id
                           WHERE t.user_id = %s
                           """, (user_id,))
            teacher_data = cursor.fetchone()
            if not teacher_data:
                print(f"No teacher found for user_id {user_id}")  # Debug log
                flash('Teacher not found', 'danger')
                return redirect(url_for('login'))
            # Fetch assigned subjects
            cursor.execute("""
                           SELECT s.id, s.name, d.name AS department_name
                           FROM subjects s
                                    JOIN teacher_subjects ts ON s.id = ts.subject_id
                                    JOIN departments d ON s.department_id = d.id
                           WHERE ts.teacher_id = %s
                           """, (teacher_data['id'],))
            subjects = cursor.fetchall()
            # Fetch enrolled students for each subject
            enrolled_students = {}
            for subject in subjects:
                cursor.execute("""
                               SELECT s.id, s.name, u.email
                               FROM students s
                                        JOIN student_subjects ss ON s.id = ss.student_id
                                        JOIN users u ON s.user_id = u.id
                               WHERE ss.subject_id = %s
                               """, (subject['id'],))
                enrolled_students[subject['id']] = cursor.fetchall()
            print(
                f"Teacher data: {teacher_data}, Subjects: {subjects}, Enrolled students: {enrolled_students}")  # Debug log
        except mysql.connector.Error as e:
            print(f"Database error in handle_teacher: {str(e)}")  # Debug log
            flash(f'Error fetching teacher data: {str(e)}', 'danger')
            teacher_data = None
            subjects = []
            enrolled_students = {}
        finally:
            cursor.close()
            conn.close()
        return render_template('teacher_portal.html', teacher=teacher_data, subjects=subjects,
                               enrolled_students=enrolled_students)

    def handle_mark_attendance(self, request, session):
        if session.get('role') != 'teacher':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        user_id = session.get('user_id')
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # Fetch teacher ID
            cursor.execute("SELECT id FROM teachers WHERE user_id = %s", (user_id,))
            teacher = cursor.fetchone()
            if not teacher:
                flash('Teacher not found', 'danger')
                return redirect(url_for('login'))
            # Fetch assigned subjects
            cursor.execute("""
                           SELECT s.id, s.name, d.name AS department_name
                           FROM subjects s
                                    JOIN teacher_subjects ts ON s.id = ts.subject_id
                                    JOIN departments d ON s.department_id = d.id
                           WHERE ts.teacher_id = %s
                           """, (teacher['id'],))
            subjects = cursor.fetchall()
            # Fetch enrolled students for each subject
            enrolled_students = {}
            for subject in subjects:
                cursor.execute("""
                               SELECT s.id, s.name, u.email
                               FROM students s
                                        JOIN student_subjects ss ON s.id = ss.student_id
                                        JOIN users u ON s.user_id = u.id
                               WHERE ss.subject_id = %s
                               """, (subject['id'],))
                enrolled_students[subject['id']] = cursor.fetchall()
            if request.method == 'POST':
                subject_id = request.form.get('subject_id')
                date = request.form.get('date')
                student_statuses = request.form.to_dict(flat=False).get('status', [])
                student_ids = request.form.to_dict(flat=False).get('student_id', [])
                if not subject_id or not date or not student_statuses or not student_ids:
                    flash('Missing required fields', 'danger')
                    return redirect(url_for('mark_attendance'))
                # Validate subject
                cursor.execute("""
                               SELECT id
                               FROM subjects
                               WHERE id = %s
                                 AND id IN (SELECT subject_id
                                            FROM teacher_subjects
                                            WHERE teacher_id = %s)
                               """, (subject_id, teacher['id']))
                if not cursor.fetchone():
                    flash('Invalid subject', 'danger')
                    return redirect(url_for('mark_attendance'))
                # Insert attendance
                for student_id, status in zip(student_ids, student_statuses):
                    if status in ['present', 'absent']:
                        cursor.execute("""
                                       SELECT id
                                       FROM students
                                       WHERE id = %s
                                         AND id IN (SELECT student_id
                                                    FROM student_subjects
                                                    WHERE subject_id = %s)
                                       """, (student_id, subject_id))
                        if cursor.fetchone():
                            cursor.execute("""
                                           INSERT INTO attendance (student_id, subject_id, date, status)
                                           VALUES (%s, %s, %s, %s)
                                           """, (student_id, subject_id, date, status))
                conn.commit()
                print(
                    f"Attendance marked for subject ID {subject_id}, date: {date}, students: {student_ids}")  # Debug log
                flash('Attendance marked successfully', 'success')
        except mysql.connector.Error as e:
            conn.rollback()
            print(f"Database error in mark_attendance: {str(e)}")  # Debug log
            flash(f'Error marking attendance: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
        return render_template('mark_attendance.html', subjects=subjects, enrolled_students=enrolled_students)

    def handle_add_marks(self, request, session):
        if session.get('role') != 'teacher':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        user_id = session.get('user_id')
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # Fetch teacher ID
            cursor.execute("SELECT id FROM teachers WHERE user_id = %s", (user_id,))
            teacher = cursor.fetchone()
            if not teacher:
                flash('Teacher not found', 'danger')
                return redirect(url_for('login'))
            # Fetch assigned subjects
            cursor.execute("""
                           SELECT s.id, s.name, d.name AS department_name
                           FROM subjects s
                                    JOIN teacher_subjects ts ON s.id = ts.subject_id
                                    JOIN departments d ON s.department_id = d.id
                           WHERE ts.teacher_id = %s
                           """, (teacher['id'],))
            subjects = cursor.fetchall()
            # Fetch enrolled students for each subject
            enrolled_students = {}
            for subject in subjects:
                cursor.execute("""
                               SELECT s.id, s.name, u.email
                               FROM students s
                                        JOIN student_subjects ss ON s.id = ss.student_id
                                        JOIN users u ON s.user_id = u.id
                               WHERE ss.subject_id = %s
                               """, (subject['id'],))
                enrolled_students[subject['id']] = cursor.fetchall()
            print(
                f"Teacher ID {teacher['id']}, Subjects: {subjects}, Enrolled students: {enrolled_students}")  # Debug log
        except mysql.connector.Error as e:
            print(f"Database error in add_marks: {str(e)}")  # Debug log
            flash(f'Error fetching data: {str(e)}', 'danger')
            subjects = []
            enrolled_students = {}
        finally:
            cursor.close()
            conn.close()
        return render_template('add_marks.html', subjects=subjects, enrolled_students=enrolled_students)

    def handle_submit_marks(self, request, session):
        if session.get('role') != 'teacher':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        user_id = session.get('user_id')
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # Fetch teacher ID
            cursor.execute("SELECT id FROM teachers WHERE user_id = %s", (user_id,))
            teacher = cursor.fetchone()
            if not teacher:
                flash('Teacher not found', 'danger')
                return redirect(url_for('login'))
            # Get form data
            subject_id = request.form.get('subject_id')
            student_marks = request.form.to_dict(flat=False).get('marks', [])
            student_ids = request.form.to_dict(flat=False).get('student_id', [])
            if not subject_id or not student_marks or not student_ids:
                flash('Missing required fields', 'danger')
                return redirect(url_for('add_marks'))
            # Validate subject is assigned to teacher
            cursor.execute("""
                           SELECT id
                           FROM subjects
                           WHERE id = %s
                             AND id IN (SELECT subject_id
                                        FROM teacher_subjects
                                        WHERE teacher_id = %s)
                           """, (subject_id, teacher['id']))
            if not cursor.fetchone():
                flash('Invalid subject', 'danger')
                return redirect(url_for('add_marks'))
            # Insert or update marks
            for student_id, marks in zip(student_ids, student_marks):
                # Validate student is enrolled in subject
                cursor.execute("""
                               SELECT id
                               FROM students
                               WHERE id = %s
                                 AND id IN (SELECT student_id
                                            FROM student_subjects
                                            WHERE subject_id = %s)
                               """, (student_id, subject_id))
                if cursor.fetchone():
                    cursor.execute("""
                                   INSERT INTO marks (student_id, subject_id, marks)
                                   VALUES (%s, %s, %s) ON DUPLICATE KEY
                                   UPDATE marks = %s
                                   """, (student_id, subject_id, marks, marks))
            conn.commit()
            print(f"Marks submitted for subject ID {subject_id}, students: {student_ids}")  # Debug log
            flash('Marks submitted successfully', 'success')
        except mysql.connector.Error as e:
            conn.rollback()
            print(f"Database error in submit_marks: {str(e)}")  # Debug log
            flash(f'Error submitting marks: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('add_marks'))

    def handle_enroll_subjects(self, request, session):
        if session.get('role') != 'student':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        user_id = session.get('user_id')
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # Fetch student ID and department
            cursor.execute("SELECT id, department_id FROM students WHERE user_id = %s", (user_id,))
            student = cursor.fetchone()
            if not student:
                print(f"No student found for user_id {user_id}")  # Debug log
                flash('Student not found', 'danger')
                return redirect(url_for('login'))
            # Fetch available subjects
            cursor.execute("""
                           SELECT s.id, s.name, d.name AS department_name
                           FROM subjects s
                                    JOIN departments d ON s.department_id = d.id
                           WHERE s.department_id = %s
                             AND s.id NOT IN (SELECT subject_id
                                              FROM student_subjects
                                              WHERE student_id = %s)
                           """, (student['department_id'], student['id']))
            available_subjects = cursor.fetchall()
            if request.method == 'POST':
                subject_ids = request.form.getlist('subjects')
                if not subject_ids:
                    flash('No subjects selected', 'danger')
                    return redirect(url_for('enroll_subjects'))
                valid_subjects = []
                for subject_id in subject_ids:
                    cursor.execute("""
                                   SELECT s.id
                                   FROM subjects s
                                   WHERE s.id = %s
                                     AND s.department_id = %s
                                     AND s.id NOT IN (SELECT subject_id
                                                      FROM student_subjects
                                                      WHERE student_id = %s)
                                   """, (subject_id, student['department_id'], student['id']))
                    if cursor.fetchone():
                        valid_subjects.append(subject_id)
                if not valid_subjects:
                    flash('No valid subjects selected or already enrolled', 'danger')
                    return redirect(url_for('enroll_subjects'))
                for subject_id in valid_subjects:
                    cursor.execute("""
                                   INSERT INTO student_subjects (student_id, subject_id)
                                   VALUES (%s, %s)
                                   """, (student['id'], subject_id))
                conn.commit()
                print(f"Student ID {student['id']} enrolled in subjects: {valid_subjects}")  # Debug log
                flash('Successfully enrolled in selected subjects', 'success')
                return redirect(url_for('student'))
        except mysql.connector.Error as e:
            conn.rollback()
            print(f"Database error in enroll_subjects: {str(e)}")  # Debug log
            flash(f'Error enrolling subjects: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
        return render_template('enroll_subjects.html', available_subjects=available_subjects)

    def handle_student_marks(self, session):
        if session.get('role') != 'student':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('login'))
        user_id = session.get('user_id')
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # Fetch student ID
            cursor.execute("SELECT id FROM students WHERE user_id = %s", (user_id,))
            student = cursor.fetchone()
            if not student:
                print(f"No student found for user_id {user_id}")  # Debug log
                flash('Student not found', 'danger')
                return redirect(url_for('login'))
            # Fetch marks
            cursor.execute("""
                           SELECT m.subject_id, m.marks, s.name AS subject_name
                           FROM marks m
                                    JOIN subjects s ON m.subject_id = s.id
                           WHERE m.student_id = %s
                           """, (student['id'],))
            marks = cursor.fetchall()
            print(f"Marks for student ID {student['id']}: {marks}")  # Debug log
        except mysql.connector.Error as e:
            print(f"Database error in handle_student_marks: {str(e)}")  # Debug log
            flash(f'Error fetching marks: {str(e)}', 'danger')
            marks = []
        finally:
            cursor.close()
            conn.close()
        return render_template('student_marks.html', marks=marks)

    def handle_register(self, request):
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            print(f"Form data received: email={email}, password={password}")  # Debug log
            if not all([email, password]):
                flash('Email and password are required', 'danger')
                print("Validation failed: Missing required fields")  # Debug log
                return render_template('register.html')
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                # Check if email exists
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash('Email already registered', 'danger')
                    print(f"Email already registered: {email}")  # Debug log
                    return render_template('register.html')
                # Insert user
                cursor.execute("""
                    INSERT INTO users (email, password, role) 
                    VALUES (%s, %s, %s)
                """, (email, password, 'student'))
                user_id = cursor.lastrowid
                conn.commit()
                print(f"Registered user_id {user_id}, email: {email}")  # Debug log
                flash('Registration successful! You can now log in.', 'success')
                return redirect(url_for('login'))
            except mysql.connector.Error as e:
                conn.rollback()
                print(f"Database error in register: {str(e)}")  # Debug log
                flash(f'Error during registration: {str(e)}', 'danger')
                return render_template('register.html')
            finally:
                cursor.close()
                conn.close()
        return render_template('register.html')