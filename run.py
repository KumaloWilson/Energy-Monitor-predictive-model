from app import create_app, db
from scheduler import setup_scheduler
import os

# Create app instance
app = create_app(os.getenv('FLASK_ENV', 'default'))

# Set up scheduler
scheduler = setup_scheduler(app)

if __name__ == '__main__':
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()
    
    # Run the app
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
