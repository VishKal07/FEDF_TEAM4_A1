from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json
import os
import re
from datetime import datetime
import uuid
import PyPDF2
import docx

app = Flask(__name__)
CORS(app)

# Database initialization
def init_db():
    conn = sqlite3.connect('internconnect.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            skills TEXT,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Internships table
    c.execute('''
        CREATE TABLE IF NOT EXISTS internships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            type TEXT NOT NULL,
            duration TEXT NOT NULL,
            stipend TEXT NOT NULL,
            description TEXT NOT NULL,
            skills_required TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Applications table
    c.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            internship_id INTEGER NOT NULL,
            status TEXT DEFAULT 'Applied',
            applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (internship_id) REFERENCES internships (id),
            UNIQUE(user_id, internship_id)
        )
    ''')
    
    # Search tracking table
    c.execute('''
        CREATE TABLE IF NOT EXISTS search_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            skills TEXT NOT NULL,
            search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Insert sample internships
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
    
    c.executemany('''
        INSERT OR IGNORE INTO internships 
        (title, company, location, type, duration, stipend, description, skills_required)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_internships)
    
    # Indexes for better performance
    c.execute('CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_applications_internship_id ON applications(internship_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_search_tracking_user_id ON search_tracking(user_id)')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect('internconnect.db')
    conn.row_factory = sqlite3.Row
    return conn

# User authentication endpoints
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (data['email'],))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'User already exists with this email'}), 400
        
        # Hash password
        password_hash = generate_password_hash(data.get('password', 'default123'))
        
        # Insert new user
        cursor.execute('''
            INSERT INTO users (name, phone, email, skills, password_hash)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['name'], data['phone'], data['email'], 
              ','.join(data['skills']), password_hash))
        
        user_id = cursor.lastrowid
        
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
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Find user by email
        cursor.execute('SELECT * FROM users WHERE email = ?', (data['email'],))
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
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

# Apply for internship endpoint
@app.route('/api/apply', methods=['POST'])
def apply_for_internship():
    data = request.get_json()
    user_id = data.get('user_id')
    internship_id = data.get('internship_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if already applied
        cursor.execute('''
            SELECT id FROM applications 
            WHERE user_id = ? AND internship_id = ?
        ''', (user_id, internship_id))
        
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'You have already applied for this internship'}), 400
        
        # Create application
        cursor.execute('''
            INSERT INTO applications (user_id, internship_id, status)
            VALUES (?, ?, 'Applied')
        ''', (user_id, internship_id))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Application submitted successfully'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

# Internship endpoints
@app.route('/api/internships', methods=['GET'])
def get_internships():
    filter_type = request.args.get('filter', 'All')
    user_id = request.args.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First get user skills
        cursor.execute('SELECT skills FROM users WHERE id = ?', (user_id,))
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
                    skill_conditions.append("i.skills_required LIKE ?")
                    params.append(f'%{skill}%')
                
                where_clause = " OR ".join(skill_conditions)
                
                cursor.execute(f'''
                    SELECT i.*, 
                           COALESCE(a.status, 'Available') as status,
                           COALESCE(a.applied_date, '') as applied_date
                    FROM internships i
                    LEFT JOIN applications a ON i.id = a.internship_id AND a.user_id = ?
                    WHERE {where_clause}
                ''', params)
            else:
                # No skills specified, return no internships
                cursor.execute('SELECT 1 WHERE 1=0')
        else:
            # Get filtered internships that match user skills
            if user_skills:
                skill_conditions = []
                params = [user_id, filter_type]
                
                for skill in user_skills[:3]:
                    skill_conditions.append("i.skills_required LIKE ?")
                    params.append(f'%{skill}%')
                
                where_clause = " OR ".join(skill_conditions)
                
                cursor.execute(f'''
                    SELECT i.*, a.status, a.applied_date
                    FROM internships i
                    JOIN applications a ON i.id = a.internship_id
                    WHERE a.user_id = ? AND a.status = ? AND ({where_clause})
                ''', params)
            else:
                # No skills specified, return no internships
                cursor.execute('SELECT 1 WHERE 1=0')
        
        internships = []
        for row in cursor.fetchall():
            internship = dict(row)
            internship['skills'] = internship['skills_required'].split(',')
            internships.append(internship)
        
        return jsonify(internships)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
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
        # Extract text from PDF
        pdf_reader = PyPDF2.PdfReader(file)
        text = ''
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    
    elif filename.endswith(('.doc', '.docx')):
        # Extract text from Word document
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
    # ATS scoring algorithm
    score = 0
    suggestions = []
    
    # Check for key sections
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
    
    # Check for keywords (common in tech internships)
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
    
    # Check length
    word_count = len(text.split())
    if word_count < 200:
        suggestions.append("Resume seems too short. Add more details about your projects and experience")
        score -= 10
    elif word_count > 800:
        suggestions.append("Resume might be too long. Consider condensing to 1-2 pages")
        score -= 5
    else:
        score += 10
    
    # Determine score category
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
    
    # Keyword analysis
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
        'suggestions': suggestions[:5],  # Limit to 5 suggestions
        'keyword_analysis': keyword_analysis,
        'word_count': word_count,
        'sections_found': len([v for v in found_sections.values() if v])
    }

# Chat endpoint
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '').lower()
    
    # Simple rule-based responses
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
    cursor = conn.cursor()
    
    try:
        # Get user skills
        cursor.execute('SELECT skills FROM users WHERE id = ?', (user_id,))
        user_row = cursor.fetchone()
        
        if not user_row:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user_skills = user_row['skills'].split(',') if user_row['skills'] else []
        primary_skill = user_skills[0] if user_skills else 'intern'
        
        # Generate search URLs for different platforms
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
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

# Search tracking endpoint
@app.route('/api/track-search', methods=['POST'])
def track_search():
    data = request.get_json()
    user_id = data.get('user_id')
    platform = data.get('platform')
    skills = data.get('skills', [])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Log the search
        cursor.execute('''
            INSERT INTO search_tracking (user_id, platform, skills)
            VALUES (?, ?, ?)
        ''', (user_id, platform, ','.join(skills)))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Search tracked successfully'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

# Serve the frontend
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'Project.html')

# Health check endpoint for Render
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'InternConnect API is running'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)