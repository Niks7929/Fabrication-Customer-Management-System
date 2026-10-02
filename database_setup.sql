-- Apex Fabrication Customer Management System
-- MySQL WAMP Server Database Schema & Seed Data
-- Database Name: `fabrication_management`

CREATE DATABASE IF NOT EXISTS `fabrication_management` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `fabrication_management`;

-- 1. Roles Table
CREATE TABLE IF NOT EXISTS `roles` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(50) NOT NULL UNIQUE,
  `description` VARCHAR(255) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `roles` (`id`, `name`, `description`) VALUES
(1, 'admin', 'Master System Control, User Security, Quotas & Full Analytics'),
(2, 'manager', 'Project Manager: Enquiries, Quotes, Work Orders & Operations'),
(3, 'staff', 'Production Staff: Assigned Job Cards, Stages & Daily Labour Logs'),
(4, 'customer', 'Customer Portal: Enquiries, Quotation Approval & Order Tracking')
ON DUPLICATE KEY UPDATE `description` = VALUES(`description`);

-- 2. Users Table
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(80) NOT NULL UNIQUE,
  `email` VARCHAR(120) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `full_name` VARCHAR(100) NOT NULL,
  `phone` VARCHAR(20) NULL,
  `role` VARCHAR(20) NOT NULL DEFAULT 'customer',
  `role_id` INT NULL,
  `is_active` TINYINT(1) DEFAULT 1,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Master Admin Account (admin / admin123 hashed)
INSERT INTO `users` (`id`, `username`, `email`, `password_hash`, `full_name`, `phone`, `role`, `role_id`, `is_active`) VALUES
(1, 'admin', 'admin@apexsteel.com', 'scrypt:32768:8:1$C1WlJ9s3kK5pQ8zT$9b4d4554ee5b6d91599388031e51edc4e3650fdbd5faeec2ad647008cf3b1b6c160eb809ef8542ab46dbbeedefbbfdbbd0775d7b003a277ed2b8c5efb0e352b5', 'Master Admin', '+91 98765 43210', 'admin', 1, 1)
ON DUPLICATE KEY UPDATE `username` = VALUES(`username`);

-- 3. Employees Table
CREATE TABLE IF NOT EXISTS `employees` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `employee_code` VARCHAR(20) NOT NULL UNIQUE,
  `user_id` INT NULL,
  `department` VARCHAR(50) DEFAULT 'Production Workshop',
  `designation` VARCHAR(50) DEFAULT 'Fitter / Welder',
  `phone` VARCHAR(20) NOT NULL,
  `hourly_rate` DOUBLE DEFAULT 150.0,
  `joining_date` DATE NULL,
  `is_active` TINYINT(1) DEFAULT 1,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Customers Table
CREATE TABLE IF NOT EXISTS `customers` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `customer_code` VARCHAR(20) NOT NULL UNIQUE,
  `user_id` INT NULL,
  `customer_type` VARCHAR(20) DEFAULT 'Individual',
  `company_name` VARCHAR(120) NULL,
  `contact_person` VARCHAR(100) NOT NULL,
  `phone` VARCHAR(20) NOT NULL,
  `email` VARCHAR(120) NULL,
  `gst_number` VARCHAR(30) NULL,
  `address` TEXT NOT NULL,
  `city` VARCHAR(50) NULL,
  `state` VARCHAR(50) DEFAULT 'Maharashtra',
  `pincode` VARCHAR(10) NULL,
  `site_addresses` TEXT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Inventory Items Table
CREATE TABLE IF NOT EXISTS `inventory_items` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `item_code` VARCHAR(20) NOT NULL UNIQUE,
  `item_name` VARCHAR(150) NOT NULL,
  `category` VARCHAR(50) NOT NULL,
  `material_type` VARCHAR(50) NOT NULL,
  `dimensions` VARCHAR(100) NULL,
  `unit` VARCHAR(20) DEFAULT 'Kg',
  `unit_cost` DOUBLE DEFAULT 0.0,
  `quantity_in_stock` DOUBLE DEFAULT 0.0,
  `reorder_level` DOUBLE DEFAULT 10.0,
  `supplier_name` VARCHAR(100) NULL,
  `last_updated` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `inventory_items` (`id`, `item_code`, `item_name`, `category`, `material_type`, `dimensions`, `unit`, `unit_cost`, `quantity_in_stock`, `reorder_level`, `supplier_name`) VALUES
(1, 'MAT-5001', 'Mild Steel (MS) Plate 6mm', 'Raw Sheet', 'MS', '2500mm x 1250mm x 6mm', 'Sheet', 4800, 45, 10, 'Tata Steel Distributors'),
(2, 'MAT-5002', 'Stainless Steel (SS 304) Pipe 2 inch', 'Pipe/Tube', 'SS 304', '6 Meter Length, 2" OD, 2mm wall', 'Meter', 650, 120, 25, 'Jindal Stainless Ltd'),
(3, 'MAT-5003', 'Aluminium Section Heavy Architectural', 'Angle/Beam', 'Aluminium', '100mm x 50mm Channel', 'Kg', 240, 300, 50, 'Hindalco Extrusions')
ON DUPLICATE KEY UPDATE `item_code` = VALUES(`item_code`);

-- 6. Enquiries Table
CREATE TABLE IF NOT EXISTS `enquiries` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `enquiry_code` VARCHAR(20) NOT NULL UNIQUE,
  `customer_id` INT NOT NULL,
  `project_name` VARCHAR(150) NOT NULL,
  `fabrication_type` VARCHAR(50) NOT NULL,
  `project_category` VARCHAR(50) DEFAULT 'Commercial',
  `site_location` TEXT NULL,
  `description` TEXT NULL,
  `budget_estimate` DOUBLE DEFAULT 0.0,
  `required_completion_date` DATE NULL,
  `status` VARCHAR(30) DEFAULT 'Pending',
  `assigned_manager_id` INT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Audit Logs Table
CREATE TABLE IF NOT EXISTS `audit_logs` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NULL,
  `user_name` VARCHAR(100) NULL,
  `action` VARCHAR(100) NOT NULL,
  `category` VARCHAR(50) DEFAULT 'General',
  `details` TEXT NULL,
  `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
