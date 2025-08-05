CREATE DATABASE school_db;
USE school_db;
CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    reg_no VARCHAR(50),
    dob DATE,
    age INT,
    grade VARCHAR(10),
    email VARCHAR(100),
    phone_number VARCHAR(20),
    address VARCHAR(255),
    profile_picture VARCHAR(255)
);

INSERT INTO students (name, reg_no, dob, age, grade, email, phone_number, address, profile_picture)
VALUES
('Ali Khan', 'REG202501', '2002-05-14', 23, 'A', 'ali.khan@example.com', '+923001234567', '123 Main St, Karachi, Pakistan', NULL),
('Sara Ahmed', 'REG202502', '2003-08-21', 22, 'B+', 'sara.ahmed@example.com', '+923001234568', '456 Elm St, Lahore, Pakistan', NULL),
('Usman Tariq', 'REG202503', '2001-11-30', 24, 'A-', 'usman.tariq@example.com', '+923001234569', '789 Pine St, Islamabad, Pakistan', NULL),
('Fatima Noor', 'REG202504', '2004-01-17', 21, 'B', 'fatima.noor@example.com', '+923001234570', '101 Oak St, Peshawar, Pakistan', NULL),
('Zain Raza', 'REG202505', '2002-12-05', 22, 'A+', 'zain.raza@example.com', '+923001234571', '202 Cedar St, Quetta, Pakistan', NULL);

 CREATE TABLE admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255),
    role ENUM('student') DEFAULT 'student'
);

INSERT INTO admins (email, password) VALUES
('admin@example.com', 'admin@123');
 
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department_id INT,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE teachers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    profile_picture VARCHAR(255)
);

CREATE TABLE teacher_subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT,
    subject_id INT,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

CREATE TABLE student_subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    subject_id INT,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    subject_id INT,
    date DATE,
    status ENUM('present', 'absent') NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

CREATE TABLE marks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    subject_id INT,
    marks INT,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

CREATE TABLE admission_applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

ALTER TABLE users ADD COLUMN admission_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending';

	
	drop table admins;