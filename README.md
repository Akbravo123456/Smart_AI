The Smart AI Platform is an intelligent web application designed to provide seamless interaction between users and AI-powered services. It leverages cutting-edge technologies to deliver highly responsive and efficient solutions for real-world problems, incorporating both frontend and backend systems for a complete user experience.

Frontend: Interactive and User-Friendly Interface:
*Built with React.js for dynamic and modular UI components.
*Styled using Tailwind CSS to ensure a modern and responsive design.
*Real-time data rendering for an intuitive user experience.
*Accessible across all devices with a mobile-first design.

Backend: Robust AI-Powered Processing
*Developed using FastAPI for fast and asynchronous backend processes.
*Integrated PyTorch and Torchaudio libraries for advanced machine learning tasks.
*Hugging Face Model: facebook/opt-1.3b
*Secure and efficient data handling with RESTful API endpoints.
*Dockerized backend for consistent deployment across environments.

Backend Sample credentials for testing:
username:sample
password:sample

Backend Environment SetUp:
python -m venv myenv
.\myenv\Scripts\activate 

Install required dependencies:
pip install -r requirements.txt

Run the FastAPI backend:
uvicorn main:app --reload

Frontend Commands:
Install required dependencies (from package.json):
npm install

Start the React development server:
npm run dev



