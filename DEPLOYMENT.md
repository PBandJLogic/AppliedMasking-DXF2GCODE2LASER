# Replit Deployment Guide

## Steps to Deploy to Replit

### 1. Create a New Replit Project
1. Go to [replit.com](https://replit.com)
2. Click "Create Repl"
3. Choose "Import from GitHub"
4. Enter your GitHub repository URL
5. Select "Python" as the language

### 2. Configure the Project
The project is already configured with the necessary files:
- ✅ `main.py` - Entry point
- ✅ `.replit` - Replit configuration
- ✅ `replit.nix` - Environment setup
- ✅ `requirements.txt` - Dependencies

### 3. Run the Application
1. Click the "Run" button in Replit
2. The application will start on port 8080
3. Replit will provide a public URL for your app

### 4. Access Your Application
- The app will be available at the Replit-provided URL
- Example: `https://your-repl-name.your-username.repl.co`

## Configuration Details

### Environment
- **Python Version**: 3.11
- **Port**: 8080 (automatically configured)
- **Host**: 0.0.0.0 (accessible from outside)

### Dependencies
All required packages are listed in `requirements.txt`:
- Flask (web framework)
- matplotlib (plotting)
- ezdxf (DXF processing)
- Pillow (image processing)
- numpy (numerical operations)

### File Structure
```
├── main.py              # Entry point for Replit
├── app.py               # Main Flask application
├── requirements.txt     # Python dependencies
├── .replit             # Replit configuration
├── replit.nix          # Replit environment
├── templates/
│   └── index.html      # Web interface
└── README.md           # Documentation
```

## Troubleshooting

### If the app doesn't start:
1. Check the Replit console for error messages
2. Ensure all dependencies are installed
3. Verify the port is not blocked

### If DXF files don't load:
1. Check file format (must be valid DXF)
2. Ensure file size is reasonable
3. Check browser console for errors

### If G-code preview doesn't work:
1. Ensure elements are marked for engraving (automatic)
2. Check G-code settings are valid
3. Verify workspace limits are set correctly

## Customization

### Changing the Port
Edit `main.py`:
```python
app.run(host="0.0.0.0", port=8080, debug=False)
```

### Adding Environment Variables
Create a `.env` file in Replit:
```
FLASK_ENV=production
SECRET_KEY=your-secret-key
```

### Updating Dependencies
Edit `requirements.txt` and restart the Repl.

## Security Notes

- The app runs in debug=False mode for production
- No authentication is implemented (add if needed)
- File uploads are processed temporarily
- Consider adding rate limiting for production use
