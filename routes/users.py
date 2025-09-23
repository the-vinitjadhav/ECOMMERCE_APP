from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd

# Create the Blueprint - THIS LINE MUST EXIST
users_bp = Blueprint('users', __name__)

# Helper functions
def read_sheet(sheet_name):
    try:
        return pd.read_excel('data_new.xlsx', sheet_name=sheet_name)
    except:
        return pd.DataFrame()

def write_sheet(sheet_name, df):
    with pd.ExcelWriter('data_new.xlsx', engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

def get_next_id(sheet_name):
    df = read_sheet(sheet_name)
    if df.empty:
        return 1
    return df.iloc[-1][f'{sheet_name[:-1]}ID'] + 1 if f'{sheet_name[:-1]}ID' in df.columns else 1

# Routes
@users_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        role = request.form['role']
        
        users_df = read_sheet('Users')
        
        if not users_df.empty and username in users_df['Username'].values:
            flash('Username already exists', 'error')
            return redirect(url_for('users.register'))
        
        hashed_password = generate_password_hash(password)
        new_user = {
            'UserID': get_next_id('Users'),
            'Username': username,
            'Password': hashed_password,
            'Email': email,
            'Role': role
        }
        
        users_df = pd.concat([users_df, pd.DataFrame([new_user])], ignore_index=True)
        write_sheet('Users', users_df)
        
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('users.login'))
    
    return render_template('users/register.html')

@users_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users_df = read_sheet('Users')
        
        if users_df.empty:
            flash('Invalid username or password', 'error')
            return redirect(url_for('users.login'))
        
        user = users_df[users_df['Username'] == username]
        
        if user.empty or not check_password_hash(user.iloc[0]['Password'], password):
            flash('Invalid username or password', 'error')
            return redirect(url_for('users.login'))
        
        session['user_id'] = int(user.iloc[0]['UserID'])
        session['username'] = user.iloc[0]['Username']
        session['role'] = user.iloc[0]['Role']
        
        flash('Login successful', 'success')
        return redirect(url_for('users.dashboard'))
    
    return render_template('users/login.html')

@users_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('users.login'))
    
    role = session['role']
    
    if role == 'Customer':
        return render_template('users/dashboard.html', role=role)
    elif role == 'Seller':
        products_df = read_sheet('Products')
        seller_products = products_df[products_df['SellerID'] == session['user_id']].to_dict('records') if not products_df.empty else []
        return render_template('users/dashboard.html', role=role, products=seller_products)
    elif role == 'Admin':
        users_df = read_sheet('Users')
        products_df = read_sheet('Products')
        orders_df = read_sheet('Orders')
        
        users = users_df.to_dict('records') if not users_df.empty else []
        products = products_df.to_dict('records') if not products_df.empty else []
        orders = orders_df.to_dict('records') if not orders_df.empty else []
        
        return render_template('users/dashboard.html', role=role, users=users, products=products, orders=orders)
    
    return redirect(url_for('products.home'))

@users_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('products.home'))