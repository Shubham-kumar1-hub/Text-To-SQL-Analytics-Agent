-- Customers who place orders
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    signup_date DATE NOT NULL,
    loyalty_tier VARCHAR(20) DEFAULT 'bronze'  -- bronze, silver, gold
);

-- Delivery addresses, one customer can have many
CREATE TABLE addresses (
    address_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    city VARCHAR(50),
    state VARCHAR(50),
    country VARCHAR(50),
    postal_code VARCHAR(20)
);

-- Product categories (parent_category_id allows sub-categories)
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    parent_category_id INT REFERENCES categories(category_id)
);

-- Brands that make products
CREATE TABLE brands (
    brand_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    country VARCHAR(50)
);

-- Suppliers that deliver products to us
CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    country VARCHAR(50),
    contact_email VARCHAR(100)
);

-- Products for sale (price = selling price, cost = what we paid)
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category_id INT REFERENCES categories(category_id),
    brand_id INT REFERENCES brands(brand_id),
    supplier_id INT REFERENCES suppliers(supplier_id),
    price NUMERIC(10,2) NOT NULL,
    cost NUMERIC(10,2) NOT NULL,
    created_at DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Current stock level for each product
CREATE TABLE inventory (
    product_id INT PRIMARY KEY REFERENCES products(product_id),
    stock_quantity INT NOT NULL,
    reorder_level INT NOT NULL,
    last_restocked DATE
);

-- Discount coupons
CREATE TABLE coupons (
    coupon_id SERIAL PRIMARY KEY,
    code VARCHAR(30) UNIQUE NOT NULL,
    discount_percent INT NOT NULL,
    valid_from DATE,
    valid_to DATE
);

-- Customer orders
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    address_id INT REFERENCES addresses(address_id),
    order_date TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL  -- placed, shipped, delivered, cancelled
);

-- Products inside each order
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id),
    product_id INT REFERENCES products(product_id),
    quantity INT NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL  -- price at the time of purchase
);

-- Which coupons were used on which orders
CREATE TABLE order_coupons (
    order_id INT REFERENCES orders(order_id),
    coupon_id INT REFERENCES coupons(coupon_id),
    PRIMARY KEY (order_id, coupon_id)
);

-- Payments made for orders
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id),
    amount NUMERIC(10,2) NOT NULL,
    method VARCHAR(20) NOT NULL,          -- card, upi, netbanking, cod
    payment_status VARCHAR(20) NOT NULL,  -- paid, failed, refunded
    paid_at TIMESTAMP
);

-- Shipping details for orders
CREATE TABLE shipments (
    shipment_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id),
    carrier VARCHAR(30),
    shipped_date DATE,
    delivered_date DATE,
    tracking_number VARCHAR(40)
);

-- Product reviews written by customers
CREATE TABLE reviews (
    review_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    customer_id INT REFERENCES customers(customer_id),
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    review_date DATE
);

-- Returned items and refunds
CREATE TABLE returns (
    return_id SERIAL PRIMARY KEY,
    order_item_id INT REFERENCES order_items(order_item_id),
    reason VARCHAR(100),
    return_date DATE,
    refund_amount NUMERIC(10,2)
);