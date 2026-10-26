CREATE DATABASE IF NOT EXISTS careerpath;
USE careerpath;
CREATE TABLE students (
  student_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  degree VARCHAR(100),
  is_admin TINYINT DEFAULT 0
);
CREATE TABLE student_skills (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  skill_name VARCHAR(100) NOT NULL,
  skill_level INT NOT NULL,
  UNIQUE (student_id, skill_name),
  FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);
CREATE TABLE careers (
  career_id INT AUTO_INCREMENT PRIMARY KEY,
  career_name VARCHAR(100) NOT NULL,
  description TEXT,
  required_skills TEXT NOT NULL
);
CREATE TABLE courses (
  course_id INT AUTO_INCREMENT PRIMARY KEY,
  course_name VARCHAR(150) NOT NULL,
  skill_name VARCHAR(100) NOT NULL,
  course_url VARCHAR(255)
);
CREATE TABLE recommendations (
  recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  career_id INT NOT NULL,
  match_score DECIMAL(5,2),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
  FOREIGN KEY (career_id) REFERENCES careers(career_id) ON DELETE CASCADE
);
INSERT INTO careers (career_name, description, required_skills) VALUES
('Web Developer','Builds and maintains websites and web applications.','HTML/CSS,JavaScript,Python,SQL'),
('Data Analyst','Collects, cleans and interprets data to support decisions.','SQL,Python,Statistics,Communication'),
('Software Engineer','Designs and builds software systems.','Python,Java,SQL,Problem Solving'),
('Python Full-Stack Developer','Builds both front end and back end using Python frameworks.','Python,HTML/CSS,JavaScript,SQL,Flask');
INSERT INTO courses (course_name, skill_name, course_url) VALUES
('Python for Everybody','Python','https://www.py4e.com'),
('freeCodeCamp Responsive Web Design','HTML/CSS','https://www.freecodecamp.org'),
('The Modern JavaScript Tutorial','JavaScript','https://javascript.info'),
('SQLBolt Interactive SQL','SQL','https://sqlbolt.com'),
('Flask Mega-Tutorial','Flask','https://blog.miguelgrinberg.com'),
('Khan Academy Statistics','Statistics','https://www.khanacademy.org'),
('Java Programming Basics','Java','https://dev.java/learn'),
('Communication Skills Practice','Communication','https://www.coursera.org'),
('Problem Solving Practice','Problem Solving','https://leetcode.com');
-- Admin account: register normally, then run: UPDATE students SET is_admin=1 WHERE email='you@example.com';
