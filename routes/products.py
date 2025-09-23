from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import pandas as pd

# Create the Blueprint
products_bp = Blueprint('products', __name__)

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

@products_bp.route('/')
def home():
    products_df = read_sheet('Products')
    products = products_df.to_dict('records') if not products_df.empty else []
    return render_template('products/products.html', products=products)

@products_bp.route('/add', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session or session['role'] != 'Seller':
        flash('Access denied', 'error')
        return redirect(url_for('products.home'))
    
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        
        products_df = read_sheet('Products')
        
        new_product = {
            'ProductID': get_next_id('Products'),
            'Name': name,
            'Price': price,
            'Stock': stock,
            'SellerID': session['user_id']
        }
        
        products_df = pd.concat([products_df, pd.DataFrame([new_product])], ignore_index=True)
        write_sheet('Products', products_df)
        
        flash('Product added successfully', 'success')
        return redirect(url_for('users.dashboard'))
    
    return render_template('products/add_product.html')

@products_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'user_id' not in session or session['role'] != 'Seller':
        flash('Access denied', 'error')
        return redirect(url_for('products.home'))
    
    products_df = read_sheet('Products')
    product = products_df[products_df['ProductID'] == product_id]
    
    if product.empty or product.iloc[0]['SellerID'] != session['user_id']:
        flash('Product not found or access denied', 'error')
        return redirect(url_for('users.dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        
        products_df.loc[products_df['ProductID'] == product_id, 'Name'] = name
        products_df.loc[products_df['ProductID'] == product_id, 'Price'] = price
        products_df.loc[products_df['ProductID'] == product_id, 'Stock'] = stock
        
        write_sheet('Products', products_df)
        
        flash('Product updated successfully', 'success')
        return redirect(url_for('users.dashboard'))
    
    return render_template('products/edit_product.html', product=product.iloc[0])