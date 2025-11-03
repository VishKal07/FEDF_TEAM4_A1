-- InternConnect Database Schema
    CREATE DATABASE IF NOT EXISTS InternConnect;
    USE InternConnect;  
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    skills TEXT,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Internships table
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
);

-- Applications table
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    internship_id INTEGER NOT NULL,
    status TEXT DEFAULT 'Applied',
    applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (internship_id) REFERENCES internships (id),
    UNIQUE(user_id, internship_id)
);

-- Sample data for internships
INSERT OR IGNORE INTO internships 
(title, company, location, type, duration, stipend, description, skills_required)
VALUES 
('Frontend Developer Intern', 'TechCorp Solutions', 'San Francisco, CA', 'Remote', '3 months', '$3,000/month', 
 'Join our frontend team to build responsive web applications using React, JavaScript, and modern CSS frameworks.',
 'JavaScript,React,HTML,CSS'),

('Data Science Intern', 'DataInsights Inc.', 'New York, NY', 'Hybrid', '6 months', '$4,500/month',
 'Work with our data team to analyze large datasets and build predictive models using Python and machine learning libraries.',
 'Python,Machine Learning,SQL,Pandas'),

('UX/UI Design Intern', 'CreativeMinds Agency', 'Austin, TX', 'On-site', '4 months', '$2,800/month',
 'Design intuitive user interfaces for web and mobile applications. Collaborate with developers to implement designs.',
 'Figma,UI/UX Design,Wireframing,Prototyping'),

('Backend Developer Intern', 'ServerStack Technologies', 'Seattle, WA', 'Remote', '5 months', '$3,500/month',
 'Develop and maintain server-side applications using Node.js and MongoDB. Implement RESTful APIs and database schemas.',
 'Node.js,MongoDB,Express,REST APIs'),

('Marketing Intern', 'GrowthHackers Marketing', 'Chicago, IL', 'Hybrid', '3 months', '$2,500/month',
 'Assist in developing marketing campaigns, analyzing performance metrics, and creating content for social media channels.',
 'Digital Marketing,Social Media,Content Creation,Analytics'),

('Cybersecurity Intern', 'SecureNet Systems', 'Boston, MA', 'On-site', '6 months', '$4,000/month',
 'Learn about network security, vulnerability assessment, and ethical hacking techniques under expert supervision.',
 'Network Security,Ethical Hacking,Linux,Python');

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_internship_id ON applications(internship_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);