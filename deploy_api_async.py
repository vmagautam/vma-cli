#!/usr/bin/env python3
from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import re
import logging
import sys
import json
import os
import threading
import uuid
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# In-memory store for deployment status
deployments = {}

# Deployment queue
deployment_queue = []

# Queue processing flag
is_processing_queue = False

# Counter for deployment IDs
deployment_counter = 0

def generate_deployment_id():
    """Generate a deployment ID with format CD00001, CD00002, etc."""
    global deployment_counter
    deployment_counter += 1
    return f"CD{deployment_counter:05d}"

def process_deployment_queue():
    """Process deployments in the queue one by one"""
    global is_processing_queue

    if is_processing_queue:
        return  # Already processing

    is_processing_queue = True

    try:
        while deployment_queue:
            # Get the next deployment from the queue
            deployment_data = deployment_queue[0]

            # Run the deployment
            run_deployment(
                deployment_data['id'],
                deployment_data['tenant'],
                deployment_data['backend_repo_url'],
                deployment_data['backend_branch'],
                deployment_data['frontend_repo_url'],
                deployment_data['frontend_branch']
            )

            # Remove from queue after processing
            deployment_queue.pop(0)

    finally:
        is_processing_queue = False

def extract_url(output, url_type):
    """Extract URL from command output"""
    # Try different patterns to match URLs in the output
    patterns = [
        rf'{url_type} URL: (http[s]?://\S+)',  # Standard format
        rf'{url_type} via domain: (http[s]?://\S+)',  # Alternative format
        rf'{url_type} via localhost: (http[s]?://\S+)'  # Localhost format
    ]

    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            return match.group(1)

    # If no match found, look for any URL in the output
    general_url_pattern = r'(http[s]?://[^\s]+)'
    urls = re.findall(general_url_pattern, output)

    # Filter URLs based on type
    if url_type.lower() == 'backend':
        backend_urls = [url for url in urls if 'api' in url.lower()]
        if backend_urls:
            return backend_urls[0]
    elif url_type.lower() == 'frontend':
        frontend_urls = [url for url in urls if 'api' not in url.lower()]
        if frontend_urls:
            return frontend_urls[0]

    return None

def run_deployment(deployment_id, tenant, backend_repo_url, backend_branch, frontend_repo_url, frontend_branch):
    """Run deployment in a separate thread"""
    try:
        # Print deployment start message to terminal
        print(f"\n{'='*80}")
        print(f"STARTING DEPLOYMENT {deployment_id} FOR TENANT {tenant}")
        print(f"{'='*80}\n")

        # Update deployment status
        deployments[deployment_id]['status'] = 'running'
        deployments[deployment_id]['start_time'] = datetime.now().isoformat()

        # Use the known working repository URLs
        if "vendor_portal_backend" in backend_repo_url:
            backend_repo_url = "git@github.com:vmalabs/vendor_portal_backeknd.git"
            logger.info(f"Using working backend repository URL: {backend_repo_url}")

        # Deploy backend
        logger.info(f"Deploying backend for tenant: {tenant}")
        print(f"\n==== STARTING BACKEND DEPLOYMENT FOR {tenant} ====")

        backend_cmd = [
            'vma', 'deploy-backend',
            '--tenant', tenant,
            '--backend-repo-url', backend_repo_url,
            '--backend-branch', backend_branch
        ]

        # Run backend deployment directly to terminal
        env = os.environ.copy()
        print(f"Executing command: {' '.join(backend_cmd)}")

        # Use direct terminal output
        backend_process = subprocess.run(
            backend_cmd,
            env=env,
            check=False  # Don't raise exception on non-zero exit
        )

        # Get output for URL extraction by running a command to get tenant info
        info_cmd = ['vma', 'tenant-info', '--tenant', tenant]
        info_process = subprocess.run(
            info_cmd,
            capture_output=True,
            text=True,
            env=env,
            check=False
        )

        backend_output = info_process.stdout

        print(f"==== BACKEND DEPLOYMENT COMPLETED WITH EXIT CODE {backend_process.returncode} ====\n")

        # Extract backend URL
        backend_url = extract_url(backend_output, 'Backend')
        logger.info(f"Extracted backend URL: {backend_url}")

        # Update deployment status
        deployments[deployment_id]['backend_complete'] = True
        deployments[deployment_id]['backend_success'] = (backend_process.returncode == 0)
        deployments[deployment_id]['backend_url'] = backend_url
        deployments[deployment_id]['backend_output'] = backend_output

        if backend_process.returncode != 0:
            deployments[deployment_id]['status'] = 'failed'
            deployments[deployment_id]['message'] = f"Backend deployment failed with exit code {backend_process.returncode}"
            return

        # Use the known working frontend repository URL
        if "vsync_frontend" in frontend_repo_url:
            frontend_repo_url = "git@github.com:vmalabs/vsync_frontend.git"
            logger.info(f"Using working frontend repository URL: {frontend_repo_url}")

        # Deploy frontend
        logger.info(f"Deploying frontend for tenant: {tenant}")
        print(f"\n==== STARTING FRONTEND DEPLOYMENT FOR {tenant} ====")

        frontend_cmd = [
            'vma', 'deploy-frontend',
            '--tenant', tenant,
            '--frontend-repo-url', frontend_repo_url,
            '--frontend-branch', frontend_branch
        ]

        # Run frontend deployment directly to terminal
        print(f"Executing command: {' '.join(frontend_cmd)}")

        # Use direct terminal output
        frontend_process = subprocess.run(
            frontend_cmd,
            env=env,
            check=False  # Don't raise exception on non-zero exit
        )

        # Get output for URL extraction
        frontend_output = info_process.stdout  # Reuse the tenant info output

        print(f"==== FRONTEND DEPLOYMENT COMPLETED WITH EXIT CODE {frontend_process.returncode} ====\n")

        # Extract frontend URL
        frontend_url = extract_url(frontend_output, 'Frontend')
        logger.info(f"Extracted frontend URL: {frontend_url}")

        # Update deployment status
        deployments[deployment_id]['frontend_complete'] = True
        deployments[deployment_id]['frontend_success'] = (frontend_process.returncode == 0)
        deployments[deployment_id]['frontend_url'] = frontend_url
        deployments[deployment_id]['frontend_output'] = frontend_output

        if frontend_process.returncode != 0:
            deployments[deployment_id]['status'] = 'failed'
            deployments[deployment_id]['message'] = f"Frontend deployment failed with exit code {frontend_process.returncode}"
            return

        # Update final status
        deployments[deployment_id]['status'] = 'completed'
        deployments[deployment_id]['message'] = 'Deployment completed successfully'
        deployments[deployment_id]['end_time'] = datetime.now().isoformat()

    except Exception as e:
        logger.exception(f"Deployment failed with exception: {str(e)}")
        deployments[deployment_id]['status'] = 'failed'
        deployments[deployment_id]['message'] = f"Deployment failed with exception: {str(e)}"
        deployments[deployment_id]['end_time'] = datetime.now().isoformat()

@app.route('/deploy', methods=['POST'])
def deploy():
    """Start an asynchronous deployment"""
    try:
        # Log the incoming request
        logger.info(f"Received webhook request from: {request.remote_addr}")

        # Parse request data
        if request.is_json:
            data = request.get_json(silent=True)
        else:
            try:
                data = json.loads(request.data.decode('utf-8'))
            except:
                data = None
            logger.info(f"data:  {data}")
        if not data:
            return jsonify({
                'data': data,
                'status': 'error',
                'message': 'No JSON data provided or invalid JSON format'
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
        print(f"Missing parameters: {missing_params}")
        if missing_params:
            return jsonify({
                'status': 'error',
                'message': f'Missing required parameters: {", ".join(missing_params)}'
            }), 400

        # Generate a unique ID for this deployment with format CD00001
        deployment_id = generate_deployment_id()

        # Initialize deployment status
        deployments[deployment_id] = {
            'id': deployment_id,
            'tenant': tenant,
            'status': 'pending',
            'message': 'Deployment queued',
            'backend_complete': False,
            'backend_success': False,
            'backend_url': None,
            'frontend_complete': False,
            'frontend_success': False,
            'frontend_url': None,
            'created_at': datetime.now().isoformat()
        }

        return jsonify({
            'status': 'pending',
            'message': 'Deployment started',
            'deployment_id': deployment_id,
            'tenant': tenant,
            'created_at': datetime.now().isoformat(),
            'product': 'vsync'
        })

        # Add deployment to queue
        deployment_queue.append({
            'id': deployment_id,
            'tenant': tenant,
            'backend_repo_url': backend_repo_url,
            'backend_branch': backend_branch,
            'frontend_repo_url': frontend_repo_url,
            'frontend_branch': frontend_branch
        })

        # Start queue processing in a separate thread if not already running
        if not is_processing_queue:
            thread = threading.Thread(target=process_deployment_queue)
            thread.daemon = True
            thread.start()

        # Return immediately with the deployment ID
        return jsonify({
            'status': 'pending',
            'message': 'Deployment started',
            'deployment_id': deployment_id,
            'tenant': tenant,
            'created_at': datetime.now().isoformat(),
            'product': 'vsync'
        })

    except Exception as e:
        logger.exception(f"Error starting deployment: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error starting deployment: {str(e)}'
        }), 500

@app.route('/deployments/<deployment_id>', methods=['GET'])
def get_deployment_status(deployment_id):
    """Get the status of a deployment"""
    if deployment_id not in deployments:
        return jsonify({
            'status': 'error',
            'message': 'Deployment not found'
        }), 404

    deployment = deployments[deployment_id]

    # Return the deployment status
    return jsonify({
        'status': deployment['status'],
        'message': deployment['message'],
        'tenant': deployment['tenant'],
        'backend_complete': deployment['backend_complete'],
        'backend_success': deployment['backend_success'],
        'backend_url': deployment['backend_url'],
        'frontend_complete': deployment['frontend_complete'],
        'frontend_success': deployment['frontend_success'],
        'frontend_url': deployment['frontend_url'],
        'created_at': deployment['created_at'],
        'start_time': deployment.get('start_time'),
        'end_time': deployment.get('end_time')
    })

@app.route('/deployments', methods=['GET'])
def list_deployments():
    """List all deployments"""
    deployment_list = []

    # Add completed/in-progress deployments
    for deployment_id, deployment in deployments.items():
        deployment_list.append({
            'id': deployment_id,
            'tenant': deployment['tenant'],
            'status': deployment['status'],
            'message': deployment['message'],
            'created_at': deployment['created_at'],
            'backend_url': deployment['backend_url'],
            'frontend_url': deployment['frontend_url'],
            'product': 'vsync'
        })

    # Add queued deployments
    queue_position = 1
    for queued in deployment_queue:
        if queued['id'] not in deployments:
            continue  # Skip if already in deployments list

        deployment_list.append({
            'id': queued['id'],
            'tenant': queued['tenant'],
            'status': 'queued',
            'message': f'Deployment queued (position {queue_position})',
            'created_at': deployments[queued['id']]['created_at'],
            'backend_url': None,
            'frontend_url': None,
            'product': 'vsync',
            'queue_position': queue_position
        })
        queue_position += 1

    return jsonify({
        'deployments': deployment_list,
        'queue_length': len(deployment_queue)
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Deployment API is running'
    })

@app.route('/queue', methods=['GET'])
def get_queue():
    """Get the current deployment queue"""
    queue_items = []

    for i, item in enumerate(deployment_queue):
        queue_items.append({
            'id': item['id'],
            'tenant': item['tenant'],
            'position': i + 1,
            'created_at': deployments[item['id']]['created_at'] if item['id'] in deployments else None
        })

    return jsonify({
        'queue_length': len(deployment_queue),
        'is_processing': is_processing_queue,
        'queue': queue_items
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Deployment API root endpoint',
        'endpoints': {
            '/deploy': 'POST - Start a new deployment',
            '/deployments/<id>': 'GET - Get deployment status',
            '/deployments': 'GET - List all deployments',
            '/queue': 'GET - View deployment queue',
            '/health': 'GET - Health check'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9000))
    print(f"Starting Async Deployment API on http://0.0.0.0:{port}")
    print("This API handles long-running deployments asynchronously")
    app.run(host='0.0.0.0', port=port, threaded=True)
