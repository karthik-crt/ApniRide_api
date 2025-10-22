ApniRide Django Project
How to Run ApniRide
1. Clone the Repository
git clone <your-repo-url>
cd ApniRide

2. Create Virtual Environment & Install Dependencies
python -m venv venv
venv\Scripts\activate  # On Windows
# OR
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt

3. Set Up Environment Variables
Create a .env file in the project root and add the following credentials:
SECRET_KEY=your_secret_key
DEBUG=True
DB_NAME=apniride_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
REDIS_HOST=localhost
REDIS_PORT=6379
RAZORPAY_KEY_ID=your_razorpay_key
RAZORPAY_KEY_SECRET=your_razorpay_secret
FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/firebase_service_account.json

4. Apply Migrations & Create Superuser
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

5. Run the Development Server
python manage.py runserver 0.0.0.0:9000

Access the site at: http://localhost:9000
6. Run with Daphne (Production/ASGI)
daphne -b 0.0.0.0 -p 8000 ApniRide.asgi:application
# Or with a specific server IP
daphne -b 192.168.0.10 -p 9000 ApniRide.asgi:application

7. Run Celery & Celery Beat
Start Celery workers:
celery -A ApniRide worker --loglevel=info

Start Celery Beat scheduler:
celery -A ApniRide beat --loglevel=info

8. (Optional) Run Redis Server
redis-server

Project Ready
Your ApniRide backend should now be running successfully. Ensure all services (Redis, database, etc.) are properly configured and running before starting the server.
