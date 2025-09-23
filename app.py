import os
import pandas as pd
from flask import Flask, redirect, url_for

app = Flask(__name__)
app.secret_key = 'ecommerce_secret_key_123'

# Import blueprints AFTER creating app to avoid circular imports
from routes.users import users_bp
from routes.products import products_bp
from routes.orders import orders_bp

# Register blueprints
app.register_blueprint(users_bp, url_prefix='/users')
app.register_blueprint(products_bp, url_prefix='/products')
app.register_blueprint(orders_bp, url_prefix='/orders')

def init_excel_db():
    if not os.path.exists('data_new.xlsx'):
        with pd.ExcelWriter('data_new.xlsx', engine='openpyxl') as writer:
            users_df = pd.DataFrame(columns=['UserID', 'Username', 'Password', 'Email', 'Role'])
            products_df = pd.DataFrame(columns=['ProductID', 'Name', 'Price', 'Stock', 'SellerID'])
            orders_df = pd.DataFrame(columns=['OrderID', 'UserID', 'ProductID', 'Quantity', 'OrderDate'])
            users_df.to_excel(writer, sheet_name='Users', index=False)
            products_df.to_excel(writer, sheet_name='Products', index=False)
            orders_df.to_excel(writer, sheet_name='Orders', index=False)

@app.route('/')
def home():
    return redirect(url_for('products.home'))

if __name__ == '__main__':
    init_excel_db()
    app.run(debug=True)