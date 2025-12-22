import os
import json
import time
import shlex
import asyncio
import subprocess
import threading
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directories exist
os.makedirs('static/uploads/logos', exist_ok=True)
os.makedirs('static/uploads/backgrounds', exist_ok=True)
os.makedirs('static/uploads/payments', exist_ok=True)
os.makedirs('data', exist_ok=True)

# Configuration
DEFAULT_STORAGE_POOL = 'default'
CPU_THRESHOLD = 90
RAM_THRESHOLD = 90
CHECK_INTERVAL = 600
cpu_monitor_active = True

# OS Options for VPS creation/reinstall
OS_OPTIONS = {
    "ubuntu2404": "ubuntu:24.04",
    "ubuntu2204": "ubuntu:22.04",
    "debian12": "debian:12",
    "debian11": "debian:11"
}

# Data files
USERS_FILE = 'data/users.json'
VPS_FILE = 'data/vps_data.json'
SETTINGS_FILE = 'data/settings.json'
PENDING_PAYMENTS_FILE = 'data/pending_payments.json'

# VPS Plans
VPS_PLANS = {
    "starter": {
        "name": "Starter Plan",
        "emoji": "🔰",
        "ram": 4,
        "cpu": 2,
        "disk": 50,
        "price": "₹49/month",
        "color": "#00ff88"
    },
    "basic": {
        "name": "Basic Plan",
        "emoji": "⚡",
        "ram": 8,
        "cpu": 4,
        "disk": 100,
        "price": "₹99/month",
        "color": "#0099ff"
    },
    "pro": {
        "name": "Pro Plan",
        "emoji": "🚀",
        "ram": 16,
        "cpu": 6,
        "disk": 200,
        "price": "₹199/month",
        "color": "#ffaa00"
    },
    "enterprise": {
        "name": "Enterprise Plan",
        "emoji": "💎",
        "ram": 32,
        "cpu": 8,
        "disk": 300,
        "price": "₹250/month",
        "color": "#ff3300"
    },
    "ultimate": {
        "name": "Ultimate Plan",
        "emoji": "👑",
        "ram": 64,
        "cpu": 12,
        "disk": 300,
        "price": "₹399/month",
        "color": "#aa00aa"
    }
}

# Data Loading Functions
def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
            # Ensure balance exists for all users
            for u in users.values():
                if 'balance' not in u:
                    u['balance'] = 0.0
            save_users(users)
            return users
    except (FileNotFoundError, json.JSONDecodeError):
        default_users = {
            "admin": {
                "username": "admin",
                "email": "admin@svmpanel.com",
                "password": generate_password_hash("admin"),
                "role": "admin",
                "created_at": datetime.now().isoformat(),
                "theme": "dark",
                "banned": False,
                "suspended": False,
                "balance": 0.0
            }
        }
        save_users(default_users)
        return default_users

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def load_vps_data():
    try:
        with open(VPS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_vps_data(data):
    with open(VPS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_settings():
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        default_settings = {
            "logo": None,
            "background": None,
            "announcement": "Welcome To SVM PANEL",
            "panel_name": "SVM Panel"
        }
        save_settings(default_settings)
        return default_settings

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def load_pending_payments():
    try:
        with open(PENDING_PAYMENTS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_pending_payments(data):
    with open(PENDING_PAYMENTS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Initialize data
users = load_users()
vps_data = load_vps_data()
settings = load_settings()
pending_payments = load_pending_payments()

# LXC Command Execution
def execute_lxc_sync(command, timeout=120):
    """Execute LXC command synchronously"""
    try:
        cmd = shlex.split(command)
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True
        )
        if result.returncode != 0:
            raise Exception(result.stderr or "Command failed")
        return result.stdout.strip() if result.stdout else True
    except subprocess.TimeoutExpired:
        raise Exception(f"Command timed out after {timeout} seconds")
    except Exception as e:
        raise Exception(str(e))

# Container Stats Functions
def get_container_status(container_name):
    try:
        output = execute_lxc_sync(f"lxc info {container_name}")
        for line in output.splitlines():
            if line.startswith("Status: "):
                return line.split(": ", 1)[1].strip()
        return "Unknown"
    except:
        return "Unknown"

def get_container_cpu(container_name):
    try:
        result = subprocess.run(
            ["lxc", "exec", container_name, "--", "top", "-bn1"],
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout
        for line in output.splitlines():
            if '%Cpu(s):' in line:
                words = line.split()
                for i, word in enumerate(words):
                    if word == 'id,':
                        idle_str = words[i-1].rstrip(',')
                        try:
                            idle = float(idle_str)
                            usage = 100.0 - idle
                            return f"{usage:.1f}%"
                        except ValueError:
                            pass
                break
        return "0.0%"
    except:
        return "0.0%"

def get_container_memory(container_name):
    try:
        result = subprocess.run(
            ["lxc", "exec", container_name, "--", "free", "-m"],
            capture_output=True,
            text=True,
            timeout=10
        )
        lines = result.stdout.splitlines()
        if len(lines) > 1:
            parts = lines[1].split()
            total = int(parts[1])
            used = int(parts[2])
            usage_pct = (used / total * 100) if total > 0 else 0
            return f"{used}/{total} MB ({usage_pct:.1f}%)"
        return "Unknown"
    except:
        return "Unknown"

def get_container_disk(container_name):
    try:
        result = subprocess.run(
            ["lxc", "exec", container_name, "--", "df", "-h", "/"],
            capture_output=True,
            text=True,
            timeout=10
        )
        lines = result.stdout.splitlines()
        for line in lines:
            if '/dev/' in line and ' /' in line:
                parts = line.split()
                if len(parts) >= 5:
                    used = parts[2]
                    size = parts[1]
                    perc = parts[4]
                    return f"{used}/{size} ({perc})"
        return "Unknown"
    except:
        return "Unknown"

def get_uptime():
    try:
        result = subprocess.run(['uptime'], capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "Unknown"

def get_cpu_usage():
    """Get current CPU usage percentage"""
    try:
        result = subprocess.run(['top', '-bn1'], capture_output=True, text=True)
        output = result.stdout
        for line in output.split('\n'):
            if '%Cpu(s):' in line:
                words = line.split()
                for i, word in enumerate(words):
                    if word == 'id,':
                        idle_str = words[i-1].rstrip(',')
                        try:
                            idle = float(idle_str)
                            usage = 100.0 - idle
                            return usage
                        except ValueError:
                            pass
                break
        return 0.0
    except Exception:
        return 0.0

# CPU Monitor Thread
def cpu_monitor():
    """Monitor CPU usage and stop all VPS if threshold is exceeded"""
    global cpu_monitor_active
    while cpu_monitor_active:
        try:
            cpu_usage = get_cpu_usage()
            if cpu_usage > CPU_THRESHOLD:
                subprocess.run(['lxc', 'stop', '--all', '--force'], check=True)
                vps_data = load_vps_data()
                for user_id, vps_list in vps_data.items():
                    for vps in vps_list:
                        if vps.get('status') == 'running':
                            vps['status'] = 'stopped'
                save_vps_data(vps_data)
            time.sleep(60)
        except Exception:
            time.sleep(60)

# Start CPU monitoring
cpu_thread = threading.Thread(target=cpu_monitor, daemon=True)
cpu_thread.start()

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        users = load_users()
        if users[session['username']]['role'] != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        users = load_users()
        if username in users:
            user = users[username]
            if user.get('banned'):
                flash('Your account has been banned', 'error')
                return redirect(url_for('login'))
            if user.get('suspended'):
                flash('Your account has been suspended', 'error')
                return redirect(url_for('login'))
            if check_password_hash(user['password'], password):
                session['username'] = username
                session['role'] = user['role']
                session['theme'] = user.get('theme', 'dark')
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
        
        flash('Invalid username or password', 'error')
    
    settings = load_settings()
    return render_template('login.html', settings=settings)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        users = load_users()
        if username in users:
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        for user in users.values():
            if user['email'] == email:
                flash('Email already registered', 'error')
                return redirect(url_for('register'))
        
        users[username] = {
            "username": username,
            "email": email,
            "password": generate_password_hash(password),
            "role": "user",
            "created_at": datetime.now().isoformat(),
            "theme": "dark",
            "banned": False,
            "suspended": False,
            "balance": 0.0
        }
        save_users(users)
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    settings = load_settings()
    return render_template('register.html', settings=settings)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    username = session['username']
    users = load_users()
    user = users[username]
    vps_data = load_vps_data()
    settings = load_settings()
    
    user_vps = vps_data.get(username, [])
    
    # Calculate totals
    total_ram = 0
    total_cpu = 0
    total_disk = 0
    active_vps = 0
    
    for vps in user_vps:
        ram_gb = int(vps['ram'].replace('GB', ''))
        disk_gb = int(vps['storage'].replace('GB', ''))
        total_ram += ram_gb
        total_cpu += int(vps['cpu'])
        total_disk += disk_gb
        if vps.get('status') == 'running' and not vps.get('suspended'):
            active_vps += 1
    
    uptime = get_uptime()
    
    return render_template('dashboard.html', 
                         user=user, 
                         balance=user['balance'],  # Explicitly pass balance for display
                         vps_list=user_vps,
                         total_ram=total_ram,
                         total_cpu=total_cpu,
                         total_disk=total_disk,
                         active_vps=active_vps,
                         uptime=uptime,
                         settings=settings,
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/vps/manage/<vps_id>')
@login_required
def manage_vps(vps_id):
    username = session['username']
    users = load_users()
    user = users[username]
    vps_data = load_vps_data()
    settings = load_settings()
    
    user_vps = vps_data.get(username, [])
    vps = None
    
    for v in user_vps:
        if v['container_name'] == vps_id:
            vps = v
            break
    
    if not vps:
        flash('VPS not found', 'error')
        return redirect(url_for('dashboard'))
    
    # Get live stats
    status = get_container_status(vps_id)
    cpu_usage = get_container_cpu(vps_id)
    memory_usage = get_container_memory(vps_id)
    disk_usage = get_container_disk(vps_id)
    
    return render_template('manage_vps.html',
                         user=user,
                         vps=vps,
                         status=status,
                         cpu_usage=cpu_usage,
                         memory_usage=memory_usage,
                         disk_usage=disk_usage,
                         settings=settings)

@app.route('/vps/action/<vps_id>/<action>', methods=['POST'])
@login_required
def vps_action(vps_id, action):
    username = session['username']
    vps_data = load_vps_data()
    
    user_vps = vps_data.get(username, [])
    vps = None
    
    for v in user_vps:
        if v['container_name'] == vps_id:
            vps = v
            break
    
    if not vps:
        return jsonify({'success': False, 'message': 'VPS not found'})
    
    if vps.get('suspended') and action != 'stats':
        return jsonify({'success': False, 'message': 'VPS is suspended'})
    
    try:
        if action == 'start':
            execute_lxc_sync(f"lxc start {vps_id}")
            vps['status'] = 'running'
            save_vps_data(vps_data)
            return jsonify({'success': True, 'message': 'VPS started successfully'})
        
        elif action == 'stop':
            execute_lxc_sync(f"lxc stop {vps_id}")
            vps['status'] = 'stopped'
            save_vps_data(vps_data)
            return jsonify({'success': True, 'message': 'VPS stopped successfully'})
        
        elif action == 'restart':
            execute_lxc_sync(f"lxc restart {vps_id}")
            vps['status'] = 'running'
            save_vps_data(vps_data)
            return jsonify({'success': True, 'message': 'VPS restarted successfully'})
        
        elif action == 'stats':
            stats = {
                'status': get_container_status(vps_id),
                'cpu': get_container_cpu(vps_id),
                'memory': get_container_memory(vps_id),
                'disk': get_container_disk(vps_id)
            }
            return jsonify({'success': True, 'stats': stats})
        
        elif action == 'ssh':
            # Install tmate if not exists
            try:
                execute_lxc_sync(f"lxc exec {vps_id} -- which tmate")
            except:
                execute_lxc_sync(f"lxc exec {vps_id} -- sudo apt-get update -y")
                execute_lxc_sync(f"lxc exec {vps_id} -- sudo apt-get install tmate -y")
            
            # Create SSH session
            session_name = f"svm-session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            execute_lxc_sync(f"lxc exec {vps_id} -- tmate -S /tmp/{session_name}.sock new-session -d")
            time.sleep(3)
            
            # Get SSH link
            result = subprocess.run(
                ["lxc", "exec", vps_id, "--", "tmate", "-S", f"/tmp/{session_name}.sock", "display", "-p", "#{tmate_ssh}"],
                capture_output=True,
                text=True
            )
            ssh_url = result.stdout.strip() if result.stdout else None
            
            if ssh_url:
                return jsonify({'success': True, 'ssh_url': ssh_url})
            else:
                return jsonify({'success': False, 'message': 'Failed to generate SSH link'})
        
        else:
            return jsonify({'success': False, 'message': 'Invalid action'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/plans')
@login_required
def plans():
    username = session['username']
    users = load_users()
    user = users[username]
    settings = load_settings()
    
    return render_template('plans.html', 
                         user=user,
                         plans=VPS_PLANS,
                         settings=settings)

@app.route('/buy/<plan_key>')
@login_required
def buy_plan(plan_key):
    if plan_key not in VPS_PLANS:
        flash('Invalid plan', 'error')
        return redirect(url_for('plans'))
    
    username = session['username']
    plan = VPS_PLANS[plan_key]
    
    # Generate buy ID
    buy_id = ''.join([str(secrets.randbelow(10)) for _ in range(10)])
    
    pending_payments = load_pending_payments()
    pending_payments[buy_id] = {
        "user": username,
        "plan": plan_key,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    save_pending_payments(pending_payments)
    
    flash(f'Your Buy ID: {buy_id}. Please send payment and submit proof.', 'success')
    return redirect(url_for('payment_proof', buy_id=buy_id))

@app.route('/payment/<buy_id>', methods=['GET', 'POST'])
@login_required
def payment_proof(buy_id):
    username = session['username']
    users = load_users()
    user = users[username]
    settings = load_settings()
    
    pending_payments = load_pending_payments()
    if buy_id not in pending_payments:
        flash('Invalid Buy ID', 'error')
        return redirect(url_for('plans'))
    
    payment = pending_payments[buy_id]
    if payment['user'] != username:
        flash('This is not your order', 'error')
        return redirect(url_for('plans'))
    
    plan = VPS_PLANS[payment['plan']]
    
    if request.method == 'POST':
        if 'screenshot' not in request.files:
            flash('No screenshot uploaded', 'error')
            return redirect(url_for('payment_proof', buy_id=buy_id))
        
        file = request.files['screenshot']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('payment_proof', buy_id=buy_id))
        
        if file:
            filename = secure_filename(f"{buy_id}_{file.filename}")
            filepath = os.path.join('static/uploads/payments', filename)
            file.save(filepath)
            
            payment['screenshot'] = filepath
            payment['status'] = 'submitted'
            save_pending_payments(pending_payments)
            
            flash('Payment proof submitted! Waiting for admin approval.', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('payment_proof.html',
                         user=user,
                         buy_id=buy_id,
                         plan=plan,
                         settings=settings)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    username = session['username']
    users = load_users()
    user = users[username]
    settings = load_settings()
    
    if request.method == 'POST':
        email = request.form.get('email')
        theme = request.form.get('theme')
        new_password = request.form.get('new_password')
        
        if email:
            user['email'] = email
        if theme:
            user['theme'] = theme
            session['theme'] = theme
        if new_password:
            user['password'] = generate_password_hash(new_password)
        
        save_users(users)
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html',
                         user=user,
                         settings=settings)

# Admin Routes
@app.route('/admin')
@admin_required
def admin_panel():
    username = session['username']
    users = load_users()
    user = users[username]
    settings = load_settings()
    vps_data = load_vps_data()
    pending_payments = load_pending_payments()
    
    # Calculate stats
    total_users = len(users)
    total_vps = sum(len(vps_list) for vps_list in vps_data.values())
    total_ram = 0
    total_cpu = 0
    total_disk = 0
    running_vps = 0
    
    for vps_list in vps_data.values():
        for vps in vps_list:
            ram_gb = int(vps['ram'].replace('GB', ''))
            disk_gb = int(vps['storage'].replace('GB', ''))
            total_ram += ram_gb
            total_cpu += int(vps['cpu'])
            total_disk += disk_gb
            if vps.get('status') == 'running' and not vps.get('suspended'):
                running_vps += 1
    
    pending_count = len([p for p in pending_payments.values() if p['status'] == 'submitted'])
    
    return render_template('admin/dashboard.html',
                         user=user,
                         settings=settings,
                         total_users=total_users,
                         total_vps=total_vps,
                         total_ram=total_ram,
                         total_cpu=total_cpu,
                         total_disk=total_disk,
                         running_vps=running_vps,
                         pending_count=pending_count,
                         uptime=get_uptime())

@app.route('/admin/users', methods=['GET', 'POST'])
@admin_required
def admin_users():
    username = session['username']
    users = load_users()
    user = users[username]
    settings = load_settings()
    vps_data_global = load_vps_data()
    uptime = get_uptime()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if not action:  # Add new user form
            new_username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role', 'user')
            
            if not all([new_username, email, password]):
                flash('All fields are required.', 'error')
            elif new_username in users:
                flash('Username already exists.', 'error')
            elif any(u['email'] == email for u in users.values()):
                flash('Email already exists.', 'error')
            else:
                users[new_username] = {
                    "username": new_username,
                    "email": email,
                    "password": generate_password_hash(password),
                    "role": role,
                    "created_at": datetime.now().isoformat(),
                    "theme": "dark",
                    "banned": False,
                    "suspended": False,
                    "balance": 0.0
                }
                save_users(users)
                flash(f'User {new_username} added successfully', 'success')
                return redirect(url_for('admin_users'))
        
        elif action == 'add_balance':
            target_username = request.form.get('username')
            amount_str = request.form.get('amount')
            try:
                amount = float(amount_str)
                if target_username in users and amount > 0:
                    users[target_username]['balance'] += amount
                    save_users(users)
                    return jsonify({'success': True, 'message': f'Added ₹{amount} to {target_username}\'s balance.'})
                else:
                    return jsonify({'success': False, 'message': 'Invalid user or amount.'})
            except ValueError:
                return jsonify({'success': False, 'message': 'Invalid amount.'})
        
        elif action == 'edit':
            target_username = request.form.get('target_username')
            new_email = request.form.get('email')
            new_role = request.form.get('role')
            new_password = request.form.get('password')
            
            if target_username not in users:
                return jsonify({'success': False, 'message': 'User not found.'})
            
            updated = False
            
            if new_email:
                # Check email uniqueness excluding self
                if any(u['email'] == new_email for u_name, u in users.items() if u_name != target_username):
                    return jsonify({'success': False, 'message': 'Email already exists.'})
                users[target_username]['email'] = new_email
                updated = True
            
            if new_role and new_role in ['user', 'admin']:
                if new_role == 'user' and target_username == session['username']:
                    return jsonify({'success': False, 'message': 'Cannot demote yourself.'})
                if users[target_username]['role'] != new_role:
                    users[target_username]['role'] = new_role
                    updated = True
            
            if new_password:
                users[target_username]['password'] = generate_password_hash(new_password)
                updated = True
            
            if updated:
                save_users(users)
                return jsonify({'success': True, 'message': 'User updated successfully.'})
            else:
                return jsonify({'success': False, 'message': 'No changes made.'})
        
        elif action == 'delete':
            target_username = request.form.get('username')
            if target_username in users and users[target_username]['role'] != 'admin':
                # Delete VPS first
                vps_data = load_vps_data()
                if target_username in vps_data:
                    for vps in vps_data[target_username]:
                        try:
                            execute_lxc_sync(f"lxc delete {vps['container_name']} --force")
                        except:
                            pass
                    del vps_data[target_username]
                    save_vps_data(vps_data)
                del users[target_username]
                save_users(users)
                return jsonify({'success': True, 'message': f'User {target_username} deleted.'})
            else:
                return jsonify({'success': False, 'message': 'Cannot delete admin or invalid user.'})
        
        elif action == 'toggle_role':
            target_username = request.form.get('username')
            target_role = request.form.get('target_role')
            if target_username in users and target_role in ['user', 'admin']:
                if users[target_username]['role'] == target_role:
                    return jsonify({'success': False, 'message': 'No change needed.'})
                if target_role == 'user' and target_username == session['username']:
                    return jsonify({'success': False, 'message': 'Cannot demote yourself.'})
                users[target_username]['role'] = target_role
                save_users(users)
                # Update session if self
                if target_username == session['username']:
                    session['role'] = target_role
                return jsonify({'success': True, 'message': f'Role changed to {target_role} for {target_username}.'})
            else:
                return jsonify({'success': False, 'message': 'Invalid user or role.'})
        
        return redirect(url_for('admin_users'))
    
    # GET: Render template - Pass all users including admins for selects
    all_users = {k: v for k, v in users.items()}  # Include all, including admins
    return render_template('admin/users.html',
                         user=user,
                         settings=settings,
                         users=users,
                         all_users=all_users,  # For selects in template
                         vps_data=vps_data_global,
                         uptime=uptime)

@app.route('/admin/users/delete/<target_username>')
@admin_required
def admin_delete_user(target_username):
    users = load_users()
    if target_username in users:
        del users[target_username]
        save_users(users)
        flash(f'User {target_username} deleted successfully', 'success')
    else:
        flash('User not found', 'error')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/ban/<target_username>')
@admin_required
def admin_ban_user(target_username):
    users = load_users()
    if target_username in users:
        users[target_username]['banned'] = True
        save_users(users)
        flash(f'User {target_username} banned', 'success')
    else:
        flash('User not found', 'error')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/unban/<target_username>')
@admin_required
def admin_unban_user(target_username):
    users = load_users()
    if target_username in users:
        users[target_username]['banned'] = False
        save_users(users)
        flash(f'User {target_username} unbanned', 'success')
    else:
        flash('User not found', 'error')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/suspend/<target_username>')
@admin_required
def admin_suspend_user(target_username):
    users = load_users()
    if target_username in users:
        users[target_username]['suspended'] = True
        save_users(users)
        flash(f'User {target_username} suspended', 'success')
    else:
        flash('User not found', 'error')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/unsuspend/<target_username>')
@admin_required
def admin_unsuspend_user(target_username):
    users = load_users()
    if target_username in users:
        users[target_username]['suspended'] = False
        save_users(users)
        flash(f'User {target_username} unsuspended', 'success')
    else:
        flash('User not found', 'error')
    return redirect(url_for('admin_users'))

@app.route('/admin/vps')
@admin_required
def admin_vps():
    username = session['username']
    users = load_users()
    user = users[username]
    settings = load_settings()
    vps_data = load_vps_data()
    
    # Pass all users including admins for select dropdown
    all_users = {k: v for k, v in users.items()}
    
    return render_template('admin/vps.html',
                         user=user,
                         settings=settings,
                         vps_data=vps_data,
                         users=users,
                         all_users=all_users,  # Explicitly pass all users including admins
                         os_options=OS_OPTIONS)  # Pass OS options for template

@app.route('/admin/vps/create', methods=['POST'])
@admin_required
def admin_create_vps():
    target_username = request.form.get('username')
    hostname = request.form.get('hostname')
    ram = int(request.form.get('ram'))
    cpu = int(request.form.get('cpu'))
    disk = int(request.form.get('disk'))
    os_key = request.form.get('os', 'ubuntu2204')  # Default to Ubuntu 22.04
    
    os_image = OS_OPTIONS.get(os_key, 'ubuntu:22.04')
    
    vps_data = load_vps_data()
    if target_username not in vps_data:
        vps_data[target_username] = []
    
    vps_count = len(vps_data[target_username]) + 1
    container_name = f"svm-{hostname}-{vps_count}" if hostname else f"svm-vps-{target_username}-{vps_count}"
    ram_mb = ram * 1024
    
    try:
        execute_lxc_sync(f"lxc init {os_image} {container_name} --storage {DEFAULT_STORAGE_POOL}")
        execute_lxc_sync(f"lxc config set {container_name} limits.memory {ram_mb}MB")
        execute_lxc_sync(f"lxc config set {container_name} limits.cpu {cpu}")
        execute_lxc_sync(f"lxc config device set {container_name} root size {disk}GB")
        execute_lxc_sync(f"lxc start {container_name}")
        
        config_str = f"{ram}GB RAM / {cpu} CPU / {disk}GB Disk"
        vps_info = {
            "container_name": container_name,
            "hostname": hostname or container_name,
            "ram": f"{ram}GB",
            "cpu": str(cpu),
            "storage": f"{disk}GB",
            "config": config_str,
            "status": "running",
            "suspended": False,
            "suspension_history": [],
            "created_at": datetime.now().isoformat(),
            "shared_with": [],
            "os": os_key  # Store selected OS
        }
        vps_data[target_username].append(vps_info)
        save_vps_data(vps_data)
        
        flash(f'VPS {container_name} created successfully for {target_username}', 'success')
    except Exception as e:
        flash(f'Failed to create VPS: {str(e)}', 'error')
    
    return redirect(url_for('admin_vps'))

@app.route('/admin/vps/delete/<owner>/<vps_id>')
@admin_required
def admin_delete_vps(owner, vps_id):
    vps_data = load_vps_data()
    if owner in vps_data:
        user_vps = vps_data[owner]
        for i, vps in enumerate(user_vps):
            if vps['container_name'] == vps_id:
                try:
                    execute_lxc_sync(f"lxc delete {vps_id} --force")
                    del user_vps[i]
                    save_vps_data(vps_data)
                    flash(f'VPS {vps_id} deleted successfully', 'success')
                except Exception as e:
                    flash(f'Failed to delete VPS: {str(e)}', 'error')
                break
    return redirect(url_for('admin_vps'))

@app.route('/admin/vps/suspend/<owner>/<vps_id>', methods=['POST'])
@admin_required
def admin_suspend_vps(owner, vps_id):
    reason = request.form.get('reason', 'Admin action')
    vps_data = load_vps_data()
    
    if owner in vps_data:
        for vps in vps_data[owner]:
            if vps['container_name'] == vps_id:
                try:
                    execute_lxc_sync(f"lxc stop {vps_id}")
                    vps['status'] = 'suspended'
                    vps['suspended'] = True
                    if 'suspension_history' not in vps:
                        vps['suspension_history'] = []
                    vps['suspension_history'].append({
                        'time': datetime.now().isoformat(),
                        'reason': reason,
                        'by': session['username']
                    })
                    save_vps_data(vps_data)
                    flash(f'VPS {vps_id} suspended', 'success')
                except Exception as e:
                    flash(f'Failed to suspend VPS: {str(e)}', 'error')
                break
    return redirect(url_for('admin_vps'))

@app.route('/admin/vps/unsuspend/<owner>/<vps_id>')
@admin_required
def admin_unsuspend_vps(owner, vps_id):
    vps_data = load_vps_data()
    
    if owner in vps_data:
        for vps in vps_data[owner]:
            if vps['container_name'] == vps_id:
                try:
                    execute_lxc_sync(f"lxc start {vps_id}")
                    vps['status'] = 'running'
                    vps['suspended'] = False
                    save_vps_data(vps_data)
                    flash(f'VPS {vps_id} unsuspended', 'success')
                except Exception as e:
                    flash(f'Failed to unsuspend VPS: {str(e)}', 'error')
                break
    return redirect(url_for('admin_vps'))

@app.route('/admin/vps/action/<owner>/<vps_id>/<action>', methods=['POST'])
@admin_required
def admin_vps_action(owner, vps_id, action):
    """Handle VPS control actions from admin panel"""
    vps_data = load_vps_data()
    
    if owner not in vps_data:
        return jsonify({'success': False, 'message': 'User not found'})
    
    vps = None
    for v in vps_data[owner]:
        if v['container_name'] == vps_id:
            vps = v
            break
    
    if not vps:
        return jsonify({'success': False, 'message': 'VPS not found'})
    
    try:
        if action == 'start':
            execute_lxc_sync(f"lxc start {vps_id}")
            vps['status'] = 'running'
            save_vps_data(vps_data)
            return jsonify({'success': True, 'message': 'VPS started successfully'})
        
        elif action == 'stop':
            execute_lxc_sync(f"lxc stop {vps_id}")
            vps['status'] = 'stopped'
            save_vps_data(vps_data)
            return jsonify({'success': True, 'message': 'VPS stopped successfully'})
        
        elif action == 'restart':
            execute_lxc_sync(f"lxc restart {vps_id}")
            vps['status'] = 'running'
            save_vps_data(vps_data)
            return jsonify({'success': True, 'message': 'VPS restarted successfully'})
        
        elif action == 'reinstall':
            # Get OS from form, default to ubuntu:22.04
            os_key = request.form.get('os', 'ubuntu2204')
            os_image = OS_OPTIONS.get(os_key, 'ubuntu:22.04')
            
            # Backup current config
            ram = vps['ram']
            cpu = vps['cpu']
            disk = vps['storage']
            
            # Delete and recreate
            execute_lxc_sync(f"lxc delete {vps_id} --force")
            execute_lxc_sync(f"lxc init {os_image} {vps_id} --storage {DEFAULT_STORAGE_POOL}")
            
            # Reapply config
            ram_mb = int(ram.replace('GB', '')) * 1024
            execute_lxc_sync(f"lxc config set {vps_id} limits.memory {ram_mb}MB")
            execute_lxc_sync(f"lxc config set {vps_id} limits.cpu {cpu}")
            execute_lxc_sync(f"lxc config device set {vps_id} root size {disk}")
            execute_lxc_sync(f"lxc start {vps_id}")
            
            vps['status'] = 'running'
            vps['os'] = os_key  # Update OS
            save_vps_data(vps_data)
            return jsonify({'success': True, 'message': 'VPS reinstalled successfully'})
        
        else:
            return jsonify({'success': False, 'message': 'Invalid action'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/vps/details/<owner>/<vps_id>')
@admin_required
def admin_vps_details(owner, vps_id):
    """Get detailed VPS statistics"""
    try:
        status = get_container_status(vps_id)
        cpu = get_container_cpu(vps_id)
        memory = get_container_memory(vps_id)
        disk = get_container_disk(vps_id)
        
        # Get uptime
        try:
            result = subprocess.run(
                ['lxc', 'exec', vps_id, '--', 'uptime', '-p'],
                capture_output=True,
                text=True,
                timeout=10
            )
            uptime = result.stdout.strip()
        except:
            uptime = 'Unknown'
        
        return jsonify({
            'success': True,
            'details': {
                'status': status,
                'cpu': cpu,
                'memory': memory,
                'disk': disk,
                'uptime': uptime
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/vps/ssh/<owner>/<vps_id>', methods=['POST'])
@admin_required
def admin_vps_ssh(owner, vps_id):
    """Generate SSH session for VPS"""
    try:
        # Install tmate if not exists
        try:
            execute_lxc_sync(f"lxc exec {vps_id} -- which tmate")
        except:
            execute_lxc_sync(f"lxc exec {vps_id} -- sudo apt-get update -y", timeout=300)
            execute_lxc_sync(f"lxc exec {vps_id} -- sudo apt-get install tmate -y", timeout=300)
        
        # Create SSH session
        session_name = f"svm-session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        execute_lxc_sync(f"lxc exec {vps_id} -- tmate -S /tmp/{session_name}.sock new-session -d")
        time.sleep(3)
        
        # Get SSH command - Fixed f-string for tmate_ssh
        ssh_cmd = execute_lxc_sync(f"lxc exec {vps_id} -- tmate -S /tmp/{session_name}.sock display -p '#{{tmate_ssh}}'")
        
        return jsonify({
            'success': True,
            'ssh_command': ssh_cmd
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/vps/resize/<owner>/<vps_id>', methods=['POST'])
@admin_required
def admin_vps_resize(owner, vps_id):
    """Resize VPS resources"""
    ram = int(request.form.get('ram'))
    cpu = int(request.form.get('cpu'))
    disk = int(request.form.get('disk'))
    
    vps_data = load_vps_data()
    
    if owner not in vps_data:
        flash('User not found', 'error')
        return redirect(url_for('admin_vps'))
    
    vps = None
    for v in vps_data[owner]:
        if v['container_name'] == vps_id:
            vps = v
            break
    
    if not vps:
        flash('VPS not found', 'error')
        return redirect(url_for('admin_vps'))
    
    try:
        # Stop VPS if running
        was_running = vps.get('status') == 'running'
        if was_running:
            execute_lxc_sync(f"lxc stop {vps_id}")
        
        # Update resources
        ram_mb = ram * 1024
        execute_lxc_sync(f"lxc config set {vps_id} limits.memory {ram_mb}MB")
        execute_lxc_sync(f"lxc config set {vps_id} limits.cpu {cpu}")
        execute_lxc_sync(f"lxc config device set {vps_id} root size {disk}GB")
        
        # Restart if it was running
        if was_running:
            execute_lxc_sync(f"lxc start {vps_id}")
        
        # Update data
        vps['ram'] = f"{ram}GB"
        vps['cpu'] = str(cpu)
        vps['storage'] = f"{disk}GB"
        vps['config'] = f"{ram}GB RAM / {cpu} CPU / {disk}GB Disk"
        save_vps_data(vps_data)
        
        flash(f'VPS {vps_id} resized successfully', 'success')
    except Exception as e:
        flash(f'Failed to resize VPS: {str(e)}', 'error')
    
    return redirect(url_for('admin_vps'))

@app.route('/admin/vps/command/<owner>/<vps_id>', methods=['POST'])
@admin_required
def admin_vps_command(owner, vps_id):
    """Execute command in VPS"""
    try:
        data = request.get_json()
        command = data.get('command', '')
        
        if not command:
            return jsonify({'success': False, 'message': 'No command provided'})
        
        # Execute command in container
        result = subprocess.run(
            ['lxc', 'exec', vps_id, '--', 'bash', '-c', command],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        output = result.stdout if result.stdout else result.stderr
        if not output:
            output = 'Command executed successfully (no output)'
        
        return jsonify({
            'success': True,
            'output': output
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': 'Command timeout'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/payments')
@admin_required
def admin_payments():
    username = session['username']
    users = load_users()
    user = users[username]
    settings = load_settings()
    pending_payments = load_pending_payments()
    
    return render_template('admin/payments.html',
                         user=user,
                         settings=settings,
                         payments=pending_payments,
                         plans=VPS_PLANS)

@app.route('/admin/payments/approve/<buy_id>')
@admin_required
def admin_approve_payment(buy_id):
    pending_payments = load_pending_payments()
    
    if buy_id not in pending_payments:
        flash('Payment not found', 'error')
        return redirect(url_for('admin_payments'))
    
    payment = pending_payments[buy_id]
    plan_data = VPS_PLANS[payment['plan']]
    target_user = payment['user']
    
    vps_data = load_vps_data()
    if target_user not in vps_data:
        vps_data[target_user] = []
    
    container_name = f"svm-vps-{target_user}-{int(time.time())}"
    ram_mb = plan_data['ram'] * 1024
    os_image = OS_OPTIONS.get('ubuntu2204', 'ubuntu:22.04')  # Default OS for payments
    
    try:
        execute_lxc_sync(f"lxc init {os_image} {container_name} --storage {DEFAULT_STORAGE_POOL}")
        execute_lxc_sync(f"lxc config set {container_name} limits.memory {ram_mb}MB")
        execute_lxc_sync(f"lxc config set {container_name} limits.cpu {plan_data['cpu']}")
        execute_lxc_sync(f"lxc config device set {container_name} root size {plan_data['disk']}GB")
        execute_lxc_sync(f"lxc start {container_name}")
        
        vps_data[target_user].append({
            "container_name": container_name,
            "hostname": container_name,
            "ram": f"{plan_data['ram']}GB",
            "cpu": str(plan_data['cpu']),
            "storage": f"{plan_data['disk']}GB",
            "config": f"{plan_data['ram']}GB RAM / {plan_data['cpu']} CPU / {plan_data['disk']}GB Disk",
            "status": "running",
            "suspended": False,
            "suspension_history": [],
            "created_at": datetime.now().isoformat(),
            "shared_with": [],
            "plan": plan_data['name'],
            "os": 'ubuntu2204'  # Default OS
        })
        save_vps_data(vps_data)
        
        del pending_payments[buy_id]
        save_pending_payments(pending_payments)
        
        flash(f'Payment approved and VPS created for {target_user}', 'success')
    except Exception as e:
        flash(f'Failed to create VPS: {str(e)}', 'error')
    
    return redirect(url_for('admin_payments'))

@app.route('/admin/payments/reject/<buy_id>')
@admin_required
def admin_reject_payment(buy_id):
    pending_payments = load_pending_payments()
    if buy_id in pending_payments:
        del pending_payments[buy_id]
        save_pending_payments(pending_payments)
        flash('Payment rejected', 'success')
    return redirect(url_for('admin_payments'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    username = session['username']
    users = load_users()
    user = users[username]
    settings = load_settings()
    
    if request.method == 'POST':
        panel_name = request.form.get('panel_name')
        announcement = request.form.get('announcement')
        
        if panel_name:
            settings['panel_name'] = panel_name
        if announcement:
            settings['announcement'] = announcement
        
        # Handle logo upload
        if 'logo' in request.files:
            file = request.files['logo']
            if file.filename != '':
                filename = secure_filename(file.filename)
                filepath = os.path.join('static/uploads/logos', filename)
                file.save(filepath)
                settings['logo'] = f'/static/uploads/logos/{filename}'
        
        # Handle background upload
        if 'background' in request.files:
            file = request.files['background']
            if file.filename != '':
                filename = secure_filename(file.filename)
                filepath = os.path.join('static/uploads/backgrounds', filename)
                file.save(filepath)
                settings['background'] = f'/static/uploads/backgrounds/{filename}'
        
        save_settings(settings)
        flash('Settings updated successfully', 'success')
        return redirect(url_for('admin_settings'))
    
    return render_template('admin/settings.html',
                         user=user,
                         settings=settings)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
