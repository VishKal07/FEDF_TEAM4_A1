from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
import json
import os
import re
from datetime import datetime
import uuid
import PyPDF2
import docx

app = Flask(__name__)
CORS(app)

# MySQL database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Kal78048',  # Password for XAMPP
    'database': 'IC1'
}

# Database initialization with better error handling
def init_db():
    conn = None
    try:
        print("🔧 Attempting to connect to MySQL...")
        
        # First try to connect without database
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        
        print("✅ Connected to MySQL server")
        
        # Create database if not exists
        cursor.execute("CREATE DATABASE IF NOT EXISTS InternConnect")
        cursor.close()
        
        # Reconnect to the specific database
        conn.close()
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("✅ Database created/selected successfully")
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                skills TEXT,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Users table created/verified")
        
        # Internships table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS internships (
                id INT PRIMARY KEY AUTO_INCREMENT,
                title VARCHAR(255) NOT NULL,
                company VARCHAR(255) NOT NULL,
                location VARCHAR(255) NOT NULL,
                type VARCHAR(100) NOT NULL,
                duration VARCHAR(100) NOT NULL,
                stipend VARCHAR(100) NOT NULL,
                description TEXT NOT NULL,
                skills_required TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Internships table created/verified")
        
        # Applications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                internship_id INT NOT NULL,
                status VARCHAR(50) DEFAULT 'Applied',
                applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (internship_id) REFERENCES internships (id) ON DELETE CASCADE,
                UNIQUE(user_id, internship_id)
            )
        ''')
        print("✅ Applications table created/verified")
        
        # Search tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_tracking (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                platform VARCHAR(100) NOT NULL,
                skills TEXT NOT NULL,
                search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        print("✅ Search tracking table created/verified")
        
        # Insert sample internships - Use a fresh cursor for this operation
        cursor.close()
        cursor = conn.cursor()
        
        sample_internships = [
            ("Frontend Developer Intern", "TechCorp Solutions", "San Francisco, CA", "Remote", "3 months", "$3,000/month", 
             "Join our frontend team to build responsive web applications using React, JavaScript, and modern CSS frameworks.",
             "JavaScript,React,HTML,CSS"),
            
            ("Data Science Intern", "DataInsights Inc.", "New York, NY", "Hybrid", "6 months", "$4,500/month",
             "Work with our data team to analyze large datasets and build predictive models using Python and machine learning libraries.",
             "Python,Machine Learning,SQL,Pandas"),
            
            ("UX/UI Design Intern", "CreativeMinds Agency", "Austin, TX", "On-site", "4 months", "$2,800/month",
             "Design intuitive user interfaces for web and mobile applications. Collaborate with developers to implement designs.",
             "Figma,UI/UX Design,Wireframing,Prototyping"),
            
            ("Backend Developer Intern", "ServerStack Technologies", "Seattle, WA", "Remote", "5 months", "$3,500/month",
             "Develop and maintain server-side applications using Node.js and MongoDB. Implement RESTful APIs and database schemas.",
             "Node.js,MongoDB,Express,REST APIs"),
            
            ("Marketing Intern", "GrowthHackers Marketing", "Chicago, IL", "Hybrid", "3 months", "$2,500/month",
             "Assist in developing marketing campaigns, analyzing performance metrics, and creating content for social media channels.",
             "Digital Marketing,Social Media,Content Creation,Analytics"),
            
            ("Cybersecurity Intern", "SecureNet Systems", "Boston, MA", "On-site", "6 months", "$4,000/month",
             "Learn about network security, vulnerability assessment, and ethical hacking techniques under expert supervision.",
             "Network Security,Ethical Hacking,Linux,Python")
        ]
        
        # Insert each internship individually with duplicate check
        inserted_count = 0
        for internship in sample_internships:
            try:
                # Use a fresh cursor for each check and insert
                check_cursor = conn.cursor()
                check_cursor.execute('SELECT id FROM internships WHERE title = %s AND company = %s', (internship[0], internship[1]))
                result = check_cursor.fetchone()
                check_cursor.close()
                
                if not result:
                    insert_cursor = conn.cursor()
                    insert_cursor.execute('''
                        INSERT INTO internships 
                        (title, company, location, type, duration, stipend, description, skills_required)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ''', internship)
                    insert_cursor.close()
                    inserted_count += 1
                    print(f"✅ Added internship: {internship[0]} at {internship[1]}")
            except Error as e:
                print(f"⚠️ Error inserting internship {internship[0]}: {e}")
                continue
        
        print(f"📊 Inserted {inserted_count} new internships")
        
        # Create indexes for better performance
        cursor = conn.cursor()
        indexes = [
            'CREATE INDEX idx_applications_user_id ON applications(user_id)',
            'CREATE INDEX idx_applications_internship_id ON applications(internship_id)',
            'CREATE INDEX idx_applications_status ON applications(status)',
            'CREATE INDEX idx_users_email ON users(email)',
            'CREATE INDEX idx_search_tracking_user_id ON search_tracking(user_id)'
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"✅ Created index: {index_sql.split('ON')[1].strip()}")
            except Error as e:
                if "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"ℹ️ Index already exists: {index_sql.split('ON')[1].strip()}")
                else:
                    print(f"⚠️ Could not create index: {e}")
        
        conn.commit()
        print("🎉 Database initialization completed successfully!")
        
    except Error as e:
        print(f"❌ Database initialization error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()
            print("🔒 Database connection closed")

# Database helper function for MySQL
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"❌ Database connection error: {e}")
        return None

# Initialize database on startup
init_db()

# Test endpoint
@app.route('/api/test-db', methods=['GET'])
def test_db():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Check tables
        cursor.execute("SHOW TABLES")
        tables = [table['Tables_in_InternConnect'] for table in cursor.fetchall()]
        
        # Count records in each table
        counts = {}
        for table in tables:
            count_cursor = conn.cursor(dictionary=True)
            count_cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            result = count_cursor.fetchone()
            counts[table] = result['count'] if result else 0
            count_cursor.close()
        
        return jsonify({
            'success': True, 
            'message': 'Database connection working',
            'tables': tables,
            'counts': counts
        })
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# User authentication endpoints
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    print("📨 Received signup data:", data)
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE email = %s', (data['email'],))
        existing_user = cursor.fetchone()
        
        if existing_user:
            return jsonify({'success': False, 'message': 'User already exists with this email'}), 400
        
        # Hash password
        password_hash = generate_password_hash(data.get('password', 'default123'))
        print("🔐 Password hashed")
        
        # Insert new user
        cursor.execute('''
            INSERT INTO users (name, phone, email, skills, password_hash)
            VALUES (%s, %s, %s, %s, %s)
        ''', (data['name'], data['phone'], data['email'], 
              ','.join(data['skills']), password_hash))
        
        user_id = cursor.lastrowid
        print("✅ User inserted with ID:", user_id)
        
        conn.commit()
        
        # Return user data (without password)
        user = {
            'id': user_id,
            'name': data['name'],
            'phone': data['phone'],
            'email': data['email'],
            'skills': data['skills']
        }
        
        return jsonify({'success': True, 'user': user})
        
    except Error as e:
        print("❌ MySQL Error:", str(e))
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    print("📨 Received login data:", data)
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Find user by email
        cursor.execute('SELECT * FROM users WHERE email = %s', (data['email'],))
        user = cursor.fetchone()
        
        if not user or not check_password_hash(user['password_hash'], data['password']):
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
        
        # Return user data (without password)
        user_data = {
            'id': user['id'],
            'name': user['name'],
            'phone': user['phone'],
            'email': user['email'],
            'skills': user['skills'].split(',') if user['skills'] else []
        }
        
        return jsonify({'success': True, 'user': user_data})
        
    except Error as e:
        print("❌ MySQL Error:", str(e))
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# Apply for internship endpoint
@app.route('/api/apply', methods=['POST'])
def apply_for_internship():
    data = request.get_json()
    user_id = data.get('user_id')
    internship_id = data.get('internship_id')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Check if already applied
        cursor.execute('''
            SELECT id FROM applications 
            WHERE user_id = %s AND internship_id = %s
        ''', (user_id, internship_id))
        existing_application = cursor.fetchone()
        
        if existing_application:
            return jsonify({'success': False, 'message': 'You have already applied for this internship'}), 400
        
        # Create application
        cursor.execute('''
            INSERT INTO applications (user_id, internship_id, status)
            VALUES (%s, %s, 'Applied')
        ''', (user_id, internship_id))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Application submitted successfully'})
        
    except Error as e:
        print("❌ MySQL Error:", str(e))
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# Internship endpoints
@app.route('/api/internships', methods=['GET'])
def get_internships():
    filter_type = request.args.get('filter', 'All')
    user_id = request.args.get('user_id')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        
        # First get user skills
        cursor.execute('SELECT skills FROM users WHERE id = %s', (user_id,))
        user_row = cursor.fetchone()
        
        if not user_row:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user_skills = user_row['skills'].split(',') if user_row['skills'] else []
        
        if filter_type == 'All':
            # Get all internships that match user skills
            if user_skills:
                # Build query with skill matching
                skill_conditions = []
                params = [user_id]
                
                for skill in user_skills[:3]:  # Limit to first 3 skills for performance
                    skill_conditions.append("i.skills_required LIKE %s")
                    params.append(f'%{skill}%')
                
                where_clause = " OR ".join(skill_conditions)
                
                cursor.execute(f'''
                    SELECT i.*, 
                           COALESCE(a.status, 'Available') as status,
                           COALESCE(a.applied_date, '') as applied_date
                    FROM internships i
                    LEFT JOIN applications a ON i.id = a.internship_id AND a.user_id = %s
                    WHERE {where_clause}
                ''', params)
            else:
                # No skills specified, return all internships
                cursor.execute('''
                    SELECT i.*, 
                           COALESCE(a.status, 'Available') as status,
                           COALESCE(a.applied_date, '') as applied_date
                    FROM internships i
                    LEFT JOIN applications a ON i.id = a.internship_id AND a.user_id = %s
                ''', (user_id,))
        else:
            # Get filtered internships that match user skills
            if user_skills:
                skill_conditions = []
                params = [user_id, filter_type]
                
                for skill in user_skills[:3]:
                    skill_conditions.append("i.skills_required LIKE %s")
                    params.append(f'%{skill}%')
                
                where_clause = " OR ".join(skill_conditions)
                
                cursor.execute(f'''
                    SELECT i.*, a.status, a.applied_date
                    FROM internships i
                    JOIN applications a ON i.id = a.internship_id
                    WHERE a.user_id = %s AND a.status = %s AND ({where_clause})
                ''', params)
            else:
                cursor.execute('''
                    SELECT i.*, a.status, a.applied_date
                    FROM internships i
                    JOIN applications a ON i.id = a.internship_id
                    WHERE a.user_id = %s AND a.status = %s
                ''', (user_id, filter_type))
        
        internships = []
        for row in cursor.fetchall():
            internship = dict(row)
            internship['skills'] = internship['skills_required'].split(',')
            internships.append(internship)
        
        return jsonify(internships)
        
    except Error as e:
        print("❌ MySQL Error:", str(e))
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# Get user applications
@app.route('/api/applications', methods=['GET'])
def get_user_applications():
    user_id = request.args.get('user_id')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT a.*, i.title, i.company, i.location, i.type, i.stipend
            FROM applications a
            JOIN internships i ON a.internship_id = i.id
            WHERE a.user_id = %s
            ORDER BY a.applied_date DESC
        ''', (user_id,))
        
        applications = cursor.fetchall()
        return jsonify({'success': True, 'applications': applications})
        
    except Error as e:
        print("❌ MySQL Error:", str(e))
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# Resume analysis endpoint
@app.route('/api/analyze-resume', methods=['POST'])
def analyze_resume():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    try:
        # Extract text from file
        text = extract_text_from_file(file)
        
        # Analyze resume
        analysis = analyze_resume_text(text)
        
        return jsonify({'success': True, 'analysis': analysis})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def extract_text_from_file(file):
    filename = file.filename.lower()
    
    if filename.endswith('.pdf'):
        pdf_reader = PyPDF2.PdfReader(file)
        text = ''
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    
    elif filename.endswith(('.doc', '.docx')):
        doc = docx.Document(file)
        text = ''
        for paragraph in doc.paragraphs:
            text += paragraph.text + '\n'
        return text
    
    elif filename.endswith('.txt'):
        return file.read().decode('utf-8')
    
    else:
        raise ValueError('Unsupported file format')

def analyze_resume_text(text):
    score = 0
    suggestions = []
    
    sections = {
        'contact_info': r'\b(phone|email|contact|address)\b',
        'education': r'\b(education|university|college|degree|bachelor|master)\b',
        'experience': r'\b(experience|work|employment|internship|project)\b',
        'skills': r'\b(skills|technical|programming|languages|tools)\b'
    }
    
    found_sections = {}
    for section, pattern in sections.items():
        if re.search(pattern, text, re.IGNORECASE):
            found_sections[section] = True
            score += 15
        else:
            found_sections[section] = False
            suggestions.append(f"Add a {section.replace('_', ' ')} section")
    
    tech_keywords = [
        'python', 'javascript', 'java', 'c++', 'react', 'node', 'sql', 'html', 'css',
        'machine learning', 'data analysis', 'web development', 'api', 'git', 'linux'
    ]
    
    found_keywords = []
    for keyword in tech_keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
            found_keywords.append(keyword)
    
    keyword_score = min(len(found_keywords) * 3, 30)
    score += keyword_score
    
    if len(found_keywords) < 5:
        suggestions.append("Add more technical skills and keywords relevant to your target internships")
    
    word_count = len(text.split())
    if word_count < 200:
        suggestions.append("Resume seems too short. Add more details about your projects and experience")
        score -= 10
    elif word_count > 800:
        suggestions.append("Resume might be too long. Consider condensing to 1-2 pages")
        score -= 5
    else:
        score += 10
    
    if score >= 90:
        category = "Excellent"
    elif score >= 80:
        category = "Good"
    elif score >= 70:
        category = "Fair"
    elif score >= 60:
        category = "Poor"
    else:
        category = "Needs Improvement"
    
    keyword_analysis = {
        'technical_skills': {
            'found': found_keywords,
            'missing': [k for k in tech_keywords if k not in found_keywords][:10]
        },
        'sections': {
            'found': [k for k, v in found_sections.items() if v],
            'missing': [k for k, v in found_sections.items() if not v]
        }
    }
    
    return {
        'ats_score': score,
        'score_category': category,
        'suggestions': suggestions[:5],
        'keyword_analysis': keyword_analysis,
        'word_count': word_count,
        'sections_found': len([v for v in found_sections.values() if v])
    }

# Chat endpoint
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '').lower()
    
    if any(word in message for word in ['hello', 'hi', 'hey', 'greetings']):
        response = "Hello! I'm your InternConnect assistant. I can help you with resume analysis, internship recommendations, and career advice. How can I assist you today?"
    elif any(word in message for word in ['resume', 'ats', 'cv', 'curriculum']):
        response = "I can analyze your resume for ATS (Applicant Tracking System) compatibility. Please upload your resume using the paperclip icon, and I'll give you a score and suggestions for improvement."
    elif any(word in message for word in ['internship', 'job', 'position', 'opportunity']):
        response = "I can help you find internship opportunities! Make sure your profile is updated with your skills. You can also browse available internships in your dashboard."
    elif any(word in message for word in ['skill', 'learn', 'improve']):
        response = "Based on current market trends, I recommend learning: Python, JavaScript, React, SQL, and cloud technologies. These are highly sought after in internship positions."
    elif any(word in message for word in ['thank', 'thanks', 'appreciate']):
        response = "You're welcome! I'm happy to help. Let me know if you need anything else for your internship search."
    elif any(word in message for word in ['bye', 'goodbye', 'exit']):
        response = "Goodbye! Good luck with your internship search. Don't hesitate to come back if you need more assistance."
    else:
        response = "I'm here to help with your internship search! I can analyze resumes, suggest internships, or provide career advice. What would you like to know?"
    
    return jsonify({'response': response})

# External internships search endpoint
@app.route('/api/external-internships', methods=['GET'])
def get_external_internships():
    user_id = request.args.get('user_id')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('SELECT skills FROM users WHERE id = %s', (user_id,))
        user_row = cursor.fetchone()
        
        if not user_row:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user_skills = user_row['skills'].split(',') if user_row['skills'] else []
        primary_skill = user_skills[0] if user_skills else 'intern'
        
        platforms = [
            {
                'name': 'LinkedIn',
                'url': f"https://www.linkedin.com/jobs/search/?keywords={primary_skill}+intern+fresher+no+experience&f_AL=true&f_E=1&f_WT=2",
                'description': 'Entry-level internships matching your skills'
            },
            {
                'name': 'Naukri.com',
                'url': f"https://www.naukri.com/{primary_skill}-internship-jobs?experience=0",
                'description': 'Fresher internship opportunities'
            },
            {
                'name': 'Glassdoor',
                'url': f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={primary_skill}+intern&jobType=internship",
                'description': 'Internship positions with company reviews'
            },
            {
                'name': 'Internshala',
                'url': f"https://internshala.com/internships/{primary_skill}-internship",
                'description': 'Student-focused internship platform'
            }
        ]
        
        return jsonify({
            'success': True,
            'platforms': platforms,
            'user_skills': user_skills
        })
        
    except Error as e:
        print("❌ MySQL Error:", str(e))
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# Search tracking endpoint
@app.route('/api/track-search', methods=['POST'])
def track_search():
    data = request.get_json()
    user_id = data.get('user_id')
    platform = data.get('platform')
    skills = data.get('skills', [])
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            INSERT INTO search_tracking (user_id, platform, skills)
            VALUES (%s, %s, %s)
        ''', (user_id, platform, ','.join(skills)))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Search tracked successfully'})
        
    except Error as e:
        print("❌ MySQL Error:", str(e))
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# Get all users
@app.route('/api/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('SELECT id, name, email, phone, skills, created_at FROM users')
        users = cursor.fetchall()
        return jsonify({'success': True, 'users': users})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# Serve the frontend
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'Project.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'InternConnect API is running'})

if __name__ == '__main__':
    print("🚀 Starting Flask app with MySQL...")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)