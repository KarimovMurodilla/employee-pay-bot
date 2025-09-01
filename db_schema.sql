
-- Telegram Bot Database Schema
-- Architecture for employee payment system with QR codes

-- Departments table for organizing employees
CREATE TABLE departments (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User roles enum
CREATE TYPE user_role AS ENUM ('employee', 'establishment', 'admin');

-- Users table (employees, establishments, admins)
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(255),
    role user_role NOT NULL DEFAULT 'employee',
    department_id BIGINT REFERENCES departments(id),
    balance DECIMAL(15,2) DEFAULT 0.00,
    daily_limit DECIMAL(15,2) DEFAULT 0.00,
    monthly_limit DECIMAL(15,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Establishments table
CREATE TABLE establishments (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    address TEXT,
    qr_code VARCHAR(255) UNIQUE NOT NULL, -- QR code identifier
    owner_user_id BIGINT REFERENCES users(id), -- Restaurant owner/manager
    max_order_amount DECIMAL(15,2) DEFAULT 0.00, -- Maximum amount per order
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transaction types
CREATE TYPE transaction_type AS ENUM ('payment', 'refund', 'balance_top_up', 'balance_adjustment');

-- Transaction status
CREATE TYPE transaction_status AS ENUM ('pending', 'completed', 'failed', 'cancelled');

-- Transactions table
CREATE TABLE transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    establishment_id BIGINT REFERENCES establishments(id),
    amount DECIMAL(15,2) NOT NULL,
    type transaction_type NOT NULL DEFAULT 'payment',
    status transaction_status NOT NULL DEFAULT 'pending',
    description TEXT,
    receipt_data JSONB, -- Store receipt information
    created_by BIGINT REFERENCES users(id), -- Who created/approved the transaction
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Balance history for tracking all balance changes
CREATE TABLE balance_history (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    transaction_id BIGINT REFERENCES transactions(id),
    amount_change DECIMAL(15,2) NOT NULL, -- Positive for additions, negative for deductions
    balance_before DECIMAL(15,2) NOT NULL,
    balance_after DECIMAL(15,2) NOT NULL,
    description TEXT,
    created_by BIGINT REFERENCES users(id), -- Admin who made the change
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reports table for storing generated reports
CREATE TABLE reports (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL, -- 'daily', 'monthly', 'custom', 'establishment', 'department'
    format VARCHAR(10) NOT NULL, -- 'PDF', 'Excel'
    parameters JSONB, -- Store report parameters (date range, filters, etc.)
    file_path VARCHAR(500), -- Path to generated file
    generated_by BIGINT NOT NULL REFERENCES users(id),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP -- When to delete the file
);

-- System settings
CREATE TABLE settings (
    id BIGSERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    updated_by BIGINT REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notifications table for establishment notifications
CREATE TABLE notifications (
    id BIGSERIAL PRIMARY KEY,
    recipient_id BIGINT NOT NULL REFERENCES users(id),
    transaction_id BIGINT REFERENCES transactions(id),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_department ON users(department_id);
CREATE INDEX idx_establishments_qr_code ON establishments(qr_code);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_establishment_id ON transactions(establishment_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_transactions_type_status ON transactions(type, status);
CREATE INDEX idx_balance_history_user_id ON balance_history(user_id);
CREATE INDEX idx_balance_history_created_at ON balance_history(created_at);
CREATE INDEX idx_notifications_recipient ON notifications(recipient_id);
CREATE INDEX idx_notifications_read ON notifications(is_read);
