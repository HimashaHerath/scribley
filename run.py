#!/usr/bin/env python
"""
Run script to start both the backend and frontend servers.
"""
import os
import subprocess
import sys
import time
import threading
import signal
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Global variables for processes
backend_process = None
frontend_process = None

def run_backend():
    """Run the backend server"""
    global backend_process
    try:
        logger.info("Starting backend server...")
        backend_process = subprocess.Popen(["python", "run_server.py"])
        logger.info(f"Backend server started with PID {backend_process.pid}")
    except Exception as e:
        logger.error(f"Failed to start backend server: {e}")
        sys.exit(1)

def run_frontend():
    """Run the frontend development server"""
    global frontend_process
    try:
        # Make sure client directory exists
        if not os.path.exists("client"):
            logger.error("Client directory not found.")
            sys.exit(1)
            
        # Make sure npm is installed
        try:
            subprocess.run(["npm", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("npm is not installed or not in PATH. Please install Node.js.")
            sys.exit(1)
        
        logger.info("Starting frontend development server...")
        frontend_process = subprocess.Popen(["npm", "run", "dev"], cwd="client")
        logger.info(f"Frontend server started with PID {frontend_process.pid}")
    except Exception as e:
        logger.error(f"Failed to start frontend server: {e}")
        # Kill backend if frontend fails
        if backend_process:
            backend_process.terminate()
        sys.exit(1)

def cleanup(signum, frame):
    """Clean up processes on exit"""
    logger.info("Stopping servers...")
    if frontend_process:
        logger.info(f"Terminating frontend server (PID {frontend_process.pid})...")
        frontend_process.terminate()
    if backend_process:
        logger.info(f"Terminating backend server (PID {backend_process.pid})...")
        backend_process.terminate()
    logger.info("All servers stopped.")
    sys.exit(0)

def main():
    """Main function to run both servers"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Start backend server
    backend_thread = threading.Thread(target=run_backend)
    backend_thread.daemon = True
    backend_thread.start()
    
    # Wait for backend to start
    time.sleep(2)
    
    # Start frontend server
    frontend_thread = threading.Thread(target=run_frontend)
    frontend_thread.daemon = True
    frontend_thread.start()
    
    logger.info("Servers started. Press Ctrl+C to stop.")
    logger.info("Backend server: http://localhost:8080")
    logger.info("Frontend server: http://localhost:5173")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup(None, None)

if __name__ == "__main__":
    main() 