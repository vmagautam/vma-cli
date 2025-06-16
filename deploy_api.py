#!/usr/bin/env python3
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import subprocess
import re
import logging
import sys
import json
import os
import pwd

# Configure logging to output to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Enable CORS with more permissive settings for tunneled connections
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.route('/deploy', methods=['POST'])
def deploy():
    # Log the incoming request with detailed information
    logger.info(f"Received webhook request from: {request.remote_addr}")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Content-Type: {request.content_type}")
    
    try:
        # Parse request data with more flexibility
        if request.is_json:
            data = request.get_json(silent=True)
        else:
            # Try to parse as JSON even if Content-Type is not application/json
            try:
                data = json.loads(request.data.decode('utf-8'))
            except:
                data = None
        
        # Log the request data
        logger.info(f"Request payload: {json.dumps(data) if data else 'No data or invalid JSON'}")

        if not data:
            error_msg = 'No JSON data provided or invalid JSON format'
            logger.error(error_msg)
            return jsonify({
                'status': 'error',
                'backend_url': None,
                'frontend_url': None,
                'message': error_msg
            }), 400

        # Extract required parameters
        tenant = data.get('tenant')
        backend_repo_url = data.get('backend_repo_url')
        backend_branch = data.get('backend_branch')
        frontend_repo_url = data.get('frontend_repo_url')
        frontend_branch = data.get('frontend_branch')

        # Validate required parameters
        required_params = ['tenant', 'backend_repo_url', 'backend_branch', 'frontend_repo_url', 'frontend_branch']
        missing_params = [param for param in required_params if not data.get(param)]

        if missing_params:
            error_msg = f'Missing required parameters: {", ".join(missing_params)}'
            logger.error(error_msg)
            return jsonify({
                'status': 'error',
                'backend_url': None,
                'frontend_url': None,
                'message': error_msg
            }), 400

        # Deploy backend
        logger.info(f"Deploying backend for tenant: {tenant}")
        print(f"\n==== STARTING BACKEND DEPLOYMENT FOR {tenant} ====")
        
        # Always use the known working repository URL
        # This is based on the successful command you ran earlier
        if "vendor_portal_backend" in backend_repo_url:
            logger.info(f"Replacing repository URL {backend_repo_url} with known working URL")
            backend_repo_url = "git@github.com:vmalabs/vendor_portal_backeknd.git"
            print(f"Using working repository URL: {backend_repo_url}")
            
        backend_cmd = [
            'vma', 'deploy-backend',
            '--tenant', tenant,
            '--backend-repo-url', backend_repo_url,
            '--backend-branch', backend_branch
        ]
        
        # Run backend deployment with real-time output and SSH environment
        # Copy the current environment and ensure SSH agent is available
        env = os.environ.copy()
        
        # Test SSH connection before running the command
        print("Testing SSH connection to GitHub...")
        test_process = subprocess.run(
            ["ssh", "-T", "git@github.com"],
            capture_output=True,
            text=True
        )
        print(f"SSH test result: {test_process.stdout}")
        print(f"SSH test error: {test_process.stderr}")
        
        # Run backend deployment with real-time output
        print(f"Executing command: {' '.join(backend_cmd)}")
        backend_process = subprocess.Popen(
            backend_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=env,
            shell=False  # Use shell=False for security
        )
        
        backend_output = ""
        for line in backend_process.stdout:
            print(line, end='')  # Print to terminal in real-time
            backend_output += line
            sys.stdout.flush()  # Ensure output is displayed immediately
            
        backend_process.wait()
        print(f"==== BACKEND DEPLOYMENT COMPLETED WITH EXIT CODE {backend_process.returncode} ====\n")
        
        if backend_process.returncode != 0:
            error_msg = f"Backend deployment failed with exit code {backend_process.returncode}"
            logger.error(error_msg)
            return jsonify({
                'status': 'error',
                'backend_url': None,
                'frontend_url': None,
                'message': error_msg
            }), 500

        # Extract backend URL
        backend_url = None
        backend_url_match = re.search(r'Backend URL: (http[s]?://\S+)', backend_output)
        if backend_url_match:
            backend_url = backend_url_match.group(1)
            logger.info(f"Extracted backend URL: {backend_url}")
        else:
            logger.warning("Could not extract backend URL from output")

        # Deploy frontend
        logger.info(f"Deploying frontend for tenant: {tenant}")
        print(f"\n==== STARTING FRONTEND DEPLOYMENT FOR {tenant} ====")
        
        # Use the known working frontend repository URL if needed
        if "vsync_frontend" in frontend_repo_url:
            logger.info(f"Replacing frontend repository URL {frontend_repo_url} with known working URL")
            frontend_repo_url = "git@github.com:vmalabs/vsync_frontend.git"
            print(f"Using working frontend repository URL: {frontend_repo_url}")
            
        frontend_cmd = [
            'vma', 'deploy-frontend',
            '--tenant', tenant,
            '--frontend-repo-url', frontend_repo_url,
            '--frontend-branch', frontend_branch
        ]
        
        # Run frontend deployment with real-time output
        # Use the same environment as for backend deployment
        frontend_process = subprocess.Popen(
            frontend_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=env,
            shell=False  # Use shell=False for security
        )
        
        frontend_output = ""
        for line in frontend_process.stdout:
            print(line, end='')  # Print to terminal in real-time
            frontend_output += line
            sys.stdout.flush()  # Ensure output is displayed immediately
            
        frontend_process.wait()
        print(f"==== FRONTEND DEPLOYMENT COMPLETED WITH EXIT CODE {frontend_process.returncode} ====\n")
        
        if frontend_process.returncode != 0:
            error_msg = f"Frontend deployment failed with exit code {frontend_process.returncode}"
            logger.error(error_msg)
            return jsonify({
                'status': 'error',
                'backend_url': backend_url,
                'frontend_url': None,
                'message': error_msg
            }), 500

        # Extract frontend URL
        frontend_url = None
        frontend_url_match = re.search(r'Frontend URL: (http[s]?://\S+)', frontend_output)
        if frontend_url_match:
            frontend_url = frontend_url_match.group(1)
            logger.info(f"Extracted frontend URL: {frontend_url}")
        else:
            logger.warning("Could not extract frontend URL from output")

        # Prepare response
        response_data = {
            'status': 'success',
            'backend_url': backend_url,
            'frontend_url': frontend_url,
            'message': 'Deployment completed successfully'
        }
        
        logger.info(f"Deployment successful. Response: {json.dumps(response_data)}")
        return jsonify(response_data)

    except Exception as e:
        error_msg = f"Deployment failed with exception: {str(e)}"
        logger.exception(error_msg)
        return jsonify({
            'status': 'error',
            'backend_url': None,
            'frontend_url': None,
            'message': error_msg
        }), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint for basic connectivity testing"""
    logger.info(f"Root endpoint accessed from: {request.remote_addr}")
    return jsonify({
        'status': 'ok',
        'message': 'Deployment API root endpoint'
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint to verify the API is running"""
    logger.info(f"Health check accessed from: {request.remote_addr}")
    return jsonify({
        'status': 'ok',
        'message': 'Deployment API is running'
    })

def check_ssh_agent():
    """Check if SSH agent is running and has keys loaded"""
    try:
        # Check if SSH_AUTH_SOCK is set
        ssh_auth_sock = os.environ.get('SSH_AUTH_SOCK')
        if not ssh_auth_sock:
            print("WARNING: SSH_AUTH_SOCK environment variable not set. SSH agent might not be running.")
            return False
            
        # Check if ssh-add -l works
        result = subprocess.run(['ssh-add', '-l'], capture_output=True, text=True)
        if result.returncode != 0:
            print("WARNING: ssh-add -l failed. SSH agent might not be running or has no keys.")
            print(f"Error: {result.stderr}")
            return False
            
        if "The agent has no identities" in result.stdout:
            print("WARNING: SSH agent is running but has no keys loaded.")
            return False
            
        print("SSH agent is running and has keys loaded:")
        print(result.stdout)
        return True
    except Exception as e:
        print(f"Error checking SSH agent: {str(e)}")
        return False

if __name__ == '__main__':
    import os
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 9000))
    
    print(f"Starting Deployment API server on http://0.0.0.0:{port}")
    print("Use /deploy endpoint for deployment webhook")
    print("Use /health endpoint to check if server is running")
    print("Forwarded URL: https://njnlxn1g-9000.inc1.devtunnels.ms/")
    
    # Check SSH agent status
    check_ssh_agent()
    
    # Print current user for debugging
    current_user = pwd.getpwuid(os.getuid()).pw_name
    print(f"Running as user: {current_user}")
    
    # Print SSH environment variables
    print(f"SSH_AUTH_SOCK: {os.environ.get('SSH_AUTH_SOCK')}")
    print(f"SSH_AGENT_PID: {os.environ.get('SSH_AGENT_PID')}")
    
    # Important settings for tunneled connections:
    # - host='0.0.0.0' to bind to all network interfaces
    # - debug=False for production use
    # - threaded=True for concurrent requests
    app.run(
        host='0.0.0.0',  # Bind to all interfaces
        port=port,
        debug=False,     # Disable debug mode for production
        threaded=True    # Enable threading
    )
