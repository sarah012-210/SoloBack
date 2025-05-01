-- Patients Table
CREATE TABLE patients (
  patient_id SERIAL PRIMARY KEY,
  full_name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  gender CHAR NOT NULL,
  address TEXT NOT NULL,
  profile_picture TEXT NOT NULL,
  date_of_birth DATE NOT NULL,
  emergency_contact VARCHAR(20) NOT NULL,
  medical_history TEXT NOT NULL,
  family_history TEXT NOT NULL,
  current_medications TEXT NOT NULL,
  allergies TEXT NOT NULL,
  insurance VARCHAR(100) NOT NULL
);


-- Doctors Table
CREATE TABLE doctors (
  doctor_id SERIAL PRIMARY KEY,
  full_name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  gender CHAR NOT NULL,
  address TEXT NOT NULL,
  profile_picture TEXT NOT NULL,
  specialization VARCHAR(255) NOT NULL,
  qualifications TEXT NOT NULL,
  hospital_or_clinic VARCHAR(255) NOT NULL,
  years_of_experience INT NOT NULL,
  license_number VARCHAR(20) UNIQUE NOT NULL
);


-- Appointments Table
CREATE TABLE appointments (
  appointment_id SERIAL PRIMARY KEY,
  patient_id INT NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
  doctor_id INT NOT NULL REFERENCES doctors(doctor_id) ON DELETE CASCADE,
  date_time DATE NOT NULL,
  doctor_schedule VARCHAR(20) NOT NULL,
  status VARCHAR(50) NOT NULL -- scheduled, accepted, rejected, done
);


-- Visits Table
CREATE TABLE visits (
  visit_id SERIAL PRIMARY KEY,
  appointment_id INT NOT NULL REFERENCES appointments(appointment_id) ON DELETE CASCADE,
  diagnosis TEXT NOT NULL,
  treatment TEXT NOT NULL,
  notes TEXT
);


-- Medications Table
CREATE TABLE medications (
  med_id SERIAL PRIMARY KEY,
  visit_id INT NOT NULL REFERENCES visits(visit_id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  dosage VARCHAR(100) NOT NULL,
  duration VARCHAR(100) NOT NULL
);


-- Medical Reports Table
CREATE TABLE medical_reports (
  report_id SERIAL PRIMARY KEY,
  patient_id INT NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
  uploaded_by_doctor_id INT REFERENCES doctors(doctor_id) ON DELETE SET NULL,
  visit_id INT REFERENCES visits(visit_id) ON DELETE SET NULL,
  report_type VARCHAR(100) NOT NULL,
  report_file TEXT NOT NULL,
  upload_date DATE NOT NULL,
  notes TEXT
);