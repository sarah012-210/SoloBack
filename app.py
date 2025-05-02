from flask import Flask, request, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_cors import CORS



app = Flask(__name__)
CORS(app)
app.secret_key = 'do not interrupt'

# Global database connection
neon_db_url = "postgresql://internaldb_owner:npg_H1dD9tZGczli@ep-shy-frog-a45zu3n3-pooler.us-east-1.aws.neon.tech/internaldb?sslmode=require"
def get_db_connection():
    return psycopg2.connect(neon_db_url, cursor_factory=RealDictCursor)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
@app.route('/')
def home():
    return jsonify({"message": "Welcome to the API. Use /signup/patient or /signup/doctor to register."}), 200

@app.route('/signup/patient', methods=['POST'])
def signup_patient():
    data = request.form
    file = request.files.get('profile_picture')

    required_fields = [
        'full_name', 'email', 'password', 'confirm_password', 'phone', 'gender',
        'address', 'date_of_birth', 'emergency_contact','insurance'
    ]
    missing_fields = [f for f in required_fields if not data.get(f)]
    if not file:
        missing_fields.append("profile_picture")
    if missing_fields:
        return jsonify({"message": f"Please fill all required fields: {', '.join(missing_fields)}"}), 200

    if data['password'] != data['confirm_password']:
        return jsonify({"message": "Password and Confirm Password do not match"}), 200

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    conn = get_db_connection()

    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM patients WHERE email = %s", (data['email'],))
        if cur.fetchone():
            return jsonify({"message": "Email already registered as patient"}), 200

        cur.execute("""INSERT INTO patients (full_name, email, password, phone, gender, address,
                                  profile_picture, date_of_birth, emergency_contact,
                                   insurance)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING patient_id;
        """, (
            data['full_name'],
            data['email'],
            generate_password_hash(data['password']),
            data['phone'],
            data['gender'],
            data['address'],
            filename,
            data['date_of_birth'],
            data['emergency_contact'],
            data['insurance']
        ))
        patient_id = cur.fetchone()['patient_id']
        conn.commit()
        return jsonify({"message": "Patient signed up successfully", "patient_id": patient_id}), 201
    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({"error": "Database error: " + str(e)}), 400
    finally:
        cur.close()

@app.route('/signup/doctor', methods=['POST'])
def signup_doctor():
    data = request.form
    file = request.files.get('profile_picture')

    required_fields = [
        'full_name', 'email', 'password', 'confirm_password', 'phone', 'gender',
        'address', 'specialization', 'qualifications',
        'hospital_or_clinic', 'years_of_experience', 'license_number'
    ]
    missing_fields = [f for f in required_fields if not data.get(f)]
    if not file:
        missing_fields.append("profile_picture")
    if missing_fields:
        return jsonify({"message": f"Please fill all required fields: {', '.join(missing_fields)}"}), 200

    if data['password'] != data['confirm_password']:
        return jsonify({"message": "Password and Confirm Password do not match"}), 200

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    conn = get_db_connection()

    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM doctors WHERE email = %s", (data['email'],))
        if cur.fetchone():
            return jsonify({"message": "Email already registered as doctor"}), 200

        cur.execute("SELECT 1 FROM doctors WHERE license_number = %s", (data['license_number'],))
        if cur.fetchone():
            return jsonify({"message": "License number already exists"}), 200

        cur.execute("""
            INSERT INTO doctors (full_name, email, password, phone, gender, address,
                                 profile_picture, specialization, qualifications,
                                 hospital_or_clinic, years_of_experience, license_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING doctor_id;
        """, (
            data['full_name'],
            data['email'],
            generate_password_hash(data['password']),
            data['phone'],
            data['gender'],
            data['address'],
            filename,
            data['specialization'],
            data['qualifications'],
            data['hospital_or_clinic'],
            data['years_of_experience'],
            data['license_number']
        ))
        doctor_id = cur.fetchone()['doctor_id']
        conn.commit()
        return jsonify({"message": "Doctor signed up successfully", "doctor_id": doctor_id}), 201
    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({"error": "Database error: " + str(e)}), 400
    finally:
        cur.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 200

    conn = get_db_connection()

    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM patients WHERE email = %s", (email,))
        patient = cur.fetchone()
        if patient and check_password_hash(patient['password'], password):
            profile_url = f"/profile/patient/{patient['patient_id']}"
            return jsonify({
                "message": "Login successful",
                "user_type": "patient",
                "user_id": patient['patient_id'],
                "profile_url": profile_url
            }), 200

        cur.execute("SELECT * FROM doctors WHERE email = %s", (email,))
        doctor = cur.fetchone()
        if doctor and check_password_hash(doctor['password'], password):
            profile_url = f"/profile/doctor/{doctor['doctor_id']}"
            return jsonify({
                "message": "Login successful",
                "user_type": "doctor",
                "user_id": doctor['doctor_id'],
                "profile_url": profile_url
            }), 200

        return jsonify({"message": "Invalid email or password"}), 200
    except psycopg2.Error as e:
        return jsonify({"error": "Database error: " + str(e)}), 400
    finally:
        cur.close()
@app.route('/profile/patient/<int:patient_id>', methods=['GET', 'PUT'])
def patient_profile(patient_id):
    conn = get_db_connection()

    cur = conn.cursor()
    try:
        if request.method == 'GET':
            cur.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
            patient = cur.fetchone()
            if not patient:
                return jsonify({"message": "Patient not found"}), 200

            # Don't include password in the response
            patient_dict = dict(patient)
            patient_dict.pop("password", None)
            return jsonify(patient_dict), 200

        if request.method == 'PUT':
            # Use form for text fields and files for images
            data = request.form
            file = request.files.get('profile_picture')

            # First, get the current patient data
            cur.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
            existing = cur.fetchone()
            if not existing:
                return jsonify({"message": "Patient not found"}), 200

            # Use existing values if field not in request
            update_fields = [
                'full_name', 'phone', 'gender', 'address',
                'emergency_contact', 'medical_history',
                'family_history', 'current_medications',
                'allergies', 'insurance'
            ]
            updated_values = [data.get(f, existing[f]) or existing[f] for f in update_fields]

            # Update non-image fields
            cur.execute("""
                UPDATE patients SET full_name           = %s,phone = %s,gender = %s,address = %s,
                                    emergency_contact   = %s,medical_history = %s,family_history = %s,
                                    current_medications = %s,allergies = %s,insurance = %s
                WHERE patient_id = %s
            """, (*updated_values, patient_id))

            # If new profile picture provided
            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                cur.execute("UPDATE patients SET profile_picture = %s WHERE patient_id = %s", (filename, patient_id))

            conn.commit()
            return jsonify({"message": "Patient profile updated"}), 200

    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()


@app.route('/profile/doctor/<int:doctor_id>', methods=['GET', 'PUT'])
def doctor_profile(doctor_id):
    conn = get_db_connection()

    cur = conn.cursor()
    try:
        if request.method == 'GET':
            cur.execute("SELECT * FROM doctors WHERE doctor_id = %s", (doctor_id,))
            doctor = cur.fetchone()
            if not doctor:
                return jsonify({"message": "Doctor not found"}), 200

            # Don't include password in the response
            doctor_dict = dict(doctor)
            doctor_dict.pop("password", None)
            return jsonify(doctor_dict), 200

        if request.method == 'PUT':
            data = request.form
            file = request.files.get('profile_picture')

            # Fetch existing doctor data
            cur.execute("SELECT * FROM doctors WHERE doctor_id = %s", (doctor_id,))
            existing = cur.fetchone()
            if not existing:
                return jsonify({"message": "Doctor not found"}), 200

            # Fields to update based on the provided table structure
            update_fields = [
                'full_name', 'phone', 'gender', 'address',
                'specialization', 'qualifications', 'hospital_or_clinic',
                'years_of_experience', 'license_number'
            ]

            updated_values = []
            for field in update_fields:
                if field in data:  # Only update if the field is in the form data
                    updated_values.append(data.get(field) or existing.get(field))  # Use provided data or keep existing value
                else:
                    updated_values.append(existing.get(field))  # Keep the existing value

            # Update the doctor record
            cur.execute("""
                UPDATE doctors SET full_name = %s, phone = %s, gender = %s, address = %s,
                                  specialization = %s, qualifications = %s, hospital_or_clinic = %s,
                                  years_of_experience = %s, license_number = %s
                WHERE doctor_id = %s
            """, (*updated_values, doctor_id))

            # Handle profile picture if provided
            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                cur.execute("UPDATE doctors SET profile_picture = %s WHERE doctor_id = %s", (filename, doctor_id))

            conn.commit()
            return jsonify({"message": "Doctor profile updated"}), 200

    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
