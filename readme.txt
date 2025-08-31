Setup & Installation
Follow these steps to set up the project environment.

1. Backend Dependencies (Node.js)
Navigate to the backend directory and install the required npm packages:

cd /webserver/backend

IN terminal :- npm install express cors csv-parser


2. Frontend Dependencies (React)
Navigate to your frontend project directory and install the required npm packages:

cd /webserver/frontend

In terminal :- npm install react react-dom axios recharts


3. Python Environment Dependencies


Run the install_dependencies.bat / mac.sh script accordingly 

Running the Application
Start the Backend Server:
Open a terminal, navigate to the backend directory, and run:

IN terminal :- cd /webserver/backend
IN terminal :- node server.js

The server should now be running on http://localhost:5001.

Start the Frontend Development Server:
Open a separate terminal, navigate to your frontend directory, and run:

IN terminal :- cd /webserver/frontend
IN terminal :- npm Start OR npm run dev 

Your application should open in your default web browser, typically at http://localhost:3000.