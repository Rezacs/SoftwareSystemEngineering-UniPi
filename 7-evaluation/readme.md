Here are the brief, step-by-step instructions to get the Evaluation System up and running:
1. Install Dependencies Open your terminal and ensure you have the required Python packages installed:
pip install flask flask-restful pandas matplotlib
2. Start the Server Navigate to your main project folder in the terminal and run the initialization script:
python -m src.__init__
3. Verify it is Running Look at your terminal output. You should see messages confirming the database is connected and the system is actively listening:
Initializing Evaluation System...
Database connection established...
Starting REST server... Listening on 0.0.0.0:8001
4. Send Data (Ready for Action!) The system is now live and waiting in the background. now start sending POST requests with JSON payloads to the specific endpoints:
•	Ingestion Data: http://127.0.0.1:8001/evaluation/expert-labels
•	Classifier Data: http://127.0.0.1:8001/evaluation/classifier-labels
•	Human Decision: http://127.0.0.1:8001/evaluation/decision
