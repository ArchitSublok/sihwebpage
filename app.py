import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

# --- Basic Setup ---
app = Flask(__name__)
# Enable Cross-Origin Resource Sharing (CORS) to allow your frontend to communicate with this backend
CORS(app)
DATABASE = 'glamar.db'

# --- Database Helper Functions ---

def get_db_connection():
    """Establishes a connection to the database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn

# ==============================================================================
# === AUTHENTICATION ROUTES ====================================================
# ==============================================================================

@app.route('/api/signup', methods=['POST'])
def signup():
    """Handles new user registration."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password are required"}), 400

    hashed_password = generate_password_hash(password)
    
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, hashed_password)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"status": "error", "message": "This email address is already registered"}), 409
    finally:
        conn.close()

    return jsonify({"status": "success", "message": "Account created successfully!"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    """Handles user login."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password are required"}), 400

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        # In a real app, you would return a session token (JWT) here
        return jsonify({
            "status": "success",
            "message": "Login successful!",
            "user": {"email": user['email']} # You can add more user data here
        }), 200
    
    return jsonify({"status": "error", "message": "Invalid email or password"}), 401


# ==============================================================================
# === PRODUCT & CART ROUTES ====================================================
# ==============================================================================

@app.route('/api/products', methods=['GET'])
def get_products():
    """Fetches all products, optionally filtering by category."""
    category = request.args.get('category')
    conn = get_db_connection()
    
    if category:
        products_cursor = conn.execute("SELECT * FROM products WHERE category = ?", (category,))
    else:
        products_cursor = conn.execute("SELECT * FROM products")
        
    products = [dict(row) for row in products_cursor.fetchall()]
    conn.close()
    
    return jsonify({"status": "success", "products": products}), 200


# NOTE: For a real cart, you'd associate it with a logged-in user.
# For simplicity, this is a generic cart.
@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    """Adds a product to the cart."""
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1) # Default to 1 if not provided

    if not product_id:
        return jsonify({"status": "error", "message": "Product ID is required"}), 400

    conn = get_db_connection()
    # First, check if the item is already in the cart
    item = conn.execute("SELECT * FROM cart WHERE product_id = ?", (product_id,)).fetchone()
    if item:
        # If it exists, update the quantity
        new_quantity = item['quantity'] + quantity
        conn.execute("UPDATE cart SET quantity = ? WHERE product_id = ?", (new_quantity, product_id))
    else:
        # If not, insert a new row
        conn.execute("INSERT INTO cart (product_id, quantity) VALUES (?, ?)", (product_id, quantity))
    
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Item added to cart"}), 200

@app.route('/api/cart', methods=['GET'])
def get_cart():
    """Fetches all items in the cart with their product details."""
    conn = get_db_connection()
    # Join cart and products tables to get full details for cart items
    cart_items_cursor = conn.execute("""
        SELECT 
            p.id, p.name, p.price, p.image_url, c.quantity
        FROM cart c
        JOIN products p ON c.product_id = p.id
    """)
    cart_items = [dict(row) for row in cart_items_cursor.fetchall()]
    conn.close()
    
    return jsonify({"status": "success", "cart": cart_items}), 200

# ==============================================================================
# === OTHER ROUTES =============================================================
# ==============================================================================

@app.route('/api/contact', methods=['POST'])
def handle_contact():
    """Handles submission from the contact form."""
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')

    if not all([name, email, message]):
        return jsonify({"status": "error", "message": "All fields are required"}), 400

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)",
        (name, email, message)
    )
    conn.commit()
    conn.close()

    print(f"--- New Contact Message from {name} ({email}) ---")
    print(f"Message: {message}")
    
    return jsonify({"status": "success", "message": "Your message has been sent successfully!"}), 200

# --- Main Execution ---
if __name__ == '__main__':
    # Make sure the database exists before running
    if not os.path.exists(DATABASE):
        print(f"Database '{DATABASE}' not found. Please run 'python database_setup.py' first.")
    else:
        app.run(host='0.0.0.0', port=5000, debug=True)
