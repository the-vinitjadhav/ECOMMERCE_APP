from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import pandas as pd

# Create the Blueprint
orders_bp = Blueprint('orders', __name__)

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

@orders_bp.route('/place/<int:product_id>', methods=['GET', 'POST'])
def place_order(product_id):
    if 'user_id' not in session or session['role'] != 'Customer':
        flash('Access denied', 'error')
        return redirect(url_for('products.home'))
    
    products_df = read_sheet('Products')
    product = products_df[products_df['ProductID'] == product_id]
    
    if product.empty:
        flash('Product not found', 'error')
        return redirect(url_for('products.home'))
    
    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        
        if quantity <= 0:
            flash('Quantity must be positive', 'error')
            return redirect(url_for('orders.place_order', product_id=product_id))
        
        if product.iloc[0]['Stock'] < quantity:
            flash('Not enough stock available', 'error')
            return redirect(url_for('orders.place_order', product_id=product_id))
        
        products_df.loc[products_df['ProductID'] == product_id, 'Stock'] = product.iloc[0]['Stock'] - quantity
        write_sheet('Products', products_df)
        
        orders_df = read_sheet('Orders')
        
        new_order = {
            'OrderID': get_next_id('Orders'),
            'UserID': session['user_id'],
            'ProductID': product_id,
            'Quantity': quantity,
            'OrderDate': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        orders_df = pd.concat([orders_df, pd.DataFrame([new_order])], ignore_index=True)
        write_sheet('Orders', orders_df)
        
        flash('Order placed successfully', 'success')
        return redirect(url_for('products.home'))
    
    return render_template('orders/place_order.html', product=product.iloc[0])

@orders_bp.route('/')
def view_orders():
    if 'user_id' not in session:
        return redirect(url_for('users.login'))
    
    orders_df = read_sheet('Orders')
    products_df = read_sheet('Products')
    
    if session['role'] == 'Customer':
        user_orders = orders_df[orders_df['UserID'] == session['user_id']]
    elif session['role'] == 'Seller':
        seller_products = products_df[products_df['SellerID'] == session['user_id']]
        if not seller_products.empty:
            user_orders = orders_df[orders_df['ProductID'].isin(seller_products['ProductID'])]
        else:
            user_orders = pd.DataFrame()
    elif session['role'] == 'Admin':
        user_orders = orders_df
    else:
        user_orders = pd.DataFrame()
    
    if not user_orders.empty and not products_df.empty:
        orders_with_details = pd.merge(user_orders, products_df, on='ProductID', how='left')
        orders = orders_with_details.to_dict('records')
    else:
        orders = []
    
    return render_template('orders/orders.html', orders=orders)