# InternConnect

A platform connecting students with internship opportunities.

## Deployment Instructions

### Prerequisites
- Node.js installed
- Git installed
- GitHub account
- Vercel or Render account

### Deploy to Vercel
1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Login to Vercel:
```bash
vercel login
```

3. Deploy:
```bash
vercel
```

### Deploy to Render
1. Create a new Static Site on render.com
2. Connect your GitHub repository
3. Configure build settings:
   - Build Command: `npm run build`
   - Publish Directory: `dist`

### Local Development
1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

3. Open http://localhost:3000 in your browser

## Environment Variables
Create a `.env` file in the root directory:
```env
VITE_API_URL=your_api_url_here
```

## Project Structure
```
ProjectV2/
├── dist/           # Built files (generated)
├── node_modules/   # Dependencies
├── index.html      # Main HTML file
├── package.json    # Project configuration
├── vercel.json     # Vercel configuration
├── render.yaml     # Render configuration
└── README.md       # Documentation
```