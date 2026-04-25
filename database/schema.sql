DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS regional_crop_data;
DROP TABLE IF EXISTS market_products;
DROP TABLE IF EXISTS recommendations;
DROP TABLE IF EXISTS fertilizers;
DROP TABLE IF EXISTS soil_types;
DROP TABLE IF EXISTS crops;

CREATE TABLE crops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE soil_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE fertilizers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    cost_per_kg REAL NOT NULL,
    soil_impact TEXT NOT NULL,
    health_impact TEXT NOT NULL,
    yield_effect TEXT NOT NULL
);

CREATE TABLE recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_id INTEGER,
    soil_id INTEGER,
    fertilizer_id INTEGER,
    recommended_quantity TEXT,
    notes TEXT,
    FOREIGN KEY (crop_id) REFERENCES crops(id),
    FOREIGN KEY (soil_id) REFERENCES soil_types(id),
    FOREIGN KEY (fertilizer_id) REFERENCES fertilizers(id)
);

CREATE TABLE market_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fertilizer_id INTEGER,
    brand_name TEXT NOT NULL,
    price_per_bag REAL NOT NULL,
    bag_weight_kg REAL NOT NULL,
    FOREIGN KEY (fertilizer_id) REFERENCES fertilizers(id)
);

CREATE TABLE regional_crop_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_name TEXT NOT NULL,
    crop_id INTEGER NOT NULL,
    percentage REAL NOT NULL,
    FOREIGN KEY (crop_id) REFERENCES crops(id)
);

CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    message TEXT NOT NULL,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Initial Mock Data Based on User Idea
INSERT INTO crops (name) VALUES ('Wheat'), ('Rice'), ('Corn'), ('Sugarcane'), ('Tomato'), ('Onion'), ('Banana'), ('Chili'), ('Coriander'), ('Cotton');

INSERT INTO soil_types (name) VALUES ('Alluvial'), ('Black'), ('Red'), ('Laterite');

INSERT INTO fertilizers (name, type, cost_per_kg, soil_impact, health_impact, yield_effect) VALUES 
('Urea', 'Chemical', 25.0, 'Degrades over time', 'Harmful residue', 'High initially'),
('DAP', 'Chemical', 40.0, 'Hardens soil', 'Respiratory risks', 'High'),
('Neem Coated Urea', 'Organic-Chemical', 28.0, 'Improves retention', 'Safe', 'Moderate to High'),
('Vermicompost', 'Organic', 15.0, 'Improves health', 'Completely Safe', 'Moderate but sustainable'),
('Bio-fertilizer (Rhizobium)', 'Organic', 50.0, 'Fixes Nitrogen naturally', 'Safe', 'Long-term improvement'),
('NPK 10:26:26', 'Chemical', 45.0, 'Decreases soil pH', 'Harmful run-off', 'High');

INSERT INTO recommendations (crop_id, soil_id, fertilizer_id, recommended_quantity, notes) VALUES 
(1, 1, 3, '50 kg/acre', 'Neem coating helps slow release of nitrogen and prevents loss.'),
(1, 2, 4, '200 kg/acre', 'Vermicompost is great for moisture retention in black soil.'),
(2, 1, 5, '2 kg/acre mixed with manure', 'Bio-fertilizer is excellent for rice in alluvial soil.'),
(3, 3, 4, '150 kg/acre', 'Red soil needs organic matter, vermicompost is highly recommended.'),
(4, 2, 3, '100 kg/acre', 'Sugarcane needs high nitrogen, neem coated urea reduces leaching.');

INSERT INTO market_products (fertilizer_id, brand_name, price_per_bag, bag_weight_kg) VALUES
(1, 'IFFCO Urea', 266.50, 45),
(1, 'KRIBHCO Urea', 266.50, 45),
(1, 'Tata Urea', 280.00, 45),
(1, 'Local Brand Urea', 250.00, 45),
(2, 'Coromandel Gromor DAP', 1350.00, 50),
(2, 'IFFCO DAP', 1350.00, 50),
(2, 'Nutrien DAP', 1400.00, 50),
(2, 'Generic DAP', 1300.00, 50),
(3, 'NFL Neem Coated Urea', 266.50, 45),
(3, 'IPL Neem Coated Urea', 266.50, 45),
(3, 'Bharat Neem Urea', 275.00, 45),
(3, 'EcoNeem Urea', 260.00, 45),
(4, 'NatureSurge Vermicompost', 400.00, 25),
(4, 'TrustBasket Vermicompost', 150.00, 5),
(4, 'Organic Farms Compost', 350.00, 20),
(4, 'GreenEarth Vermi', 180.00, 10),
(5, 'IFFCO MC Bio-fertilizer', 100.00, 1),
(5, 'Multiplex Rhizobium', 150.00, 1),
(5, 'BioAgri Fertilizer', 120.00, 1),
(5, 'FarmBoost Bio', 140.00, 1),
(6, 'Mahadhan NPK 10:26:26', 1470.00, 50),
(6, 'IFFCO NPK 10:26:26', 1470.00, 50),
(6, 'Aries Agro NPK', 1500.00, 50),
(6, 'AgroKing NPK', 1450.00, 50);

-- Regional Crop Data Insertions
INSERT INTO regional_crop_data (region_name, crop_id, percentage) VALUES
('Ajra', 2, 12),
('Ajra', 1, 11),
('Ajra', 5, 31),
('Ajra', 10, 10),
('Ajra', 7, 36),
('Bhudargad', 7, 14),
('Bhudargad', 1, 24),
('Bhudargad', 9, 28),
('Bhudargad', 8, 6),
('Bhudargad', 2, 28),
('Chandgad', 4, 33),
('Chandgad', 9, 19),
('Chandgad', 7, 7),
('Chandgad', 2, 14),
('Chandgad', 10, 27),
('Gadhinglaj', 6, 14),
('Gadhinglaj', 5, 13),
('Gadhinglaj', 3, 30),
('Gadhinglaj', 2, 14),
('Gadhinglaj', 8, 29),
('Gaganbavda', 6, 28),
('Gaganbavda', 5, 10),
('Gaganbavda', 1, 21),
('Gaganbavda', 10, 9),
('Gaganbavda', 4, 32),
('Hatkanangle', 5, 11),
('Hatkanangle', 6, 23),
('Hatkanangle', 4, 27),
('Hatkanangle', 9, 14),
('Hatkanangle', 1, 25),
('Kagal', 2, 23),
('Kagal', 7, 14),
('Kagal', 5, 23),
('Kagal', 4, 22),
('Kagal', 6, 18),
('Karvir', 5, 17),
('Karvir', 2, 13),
('Karvir', 3, 26),
('Karvir', 10, 23),
('Karvir', 6, 21),
('Panhala', 9, 18),
('Panhala', 4, 9),
('Panhala', 6, 23),
('Panhala', 7, 27),
('Panhala', 1, 23),
('Radhanagari', 2, 25),
('Radhanagari', 4, 21),
('Radhanagari', 6, 24),
('Radhanagari', 10, 11),
('Radhanagari', 8, 19),
('Shahuwadi', 3, 21),
('Shahuwadi', 4, 26),
('Shahuwadi', 5, 19),
('Shahuwadi', 6, 18),
('Shahuwadi', 8, 16),
('Shirol', 3, 11),
('Shirol', 9, 13),
('Shirol', 8, 34),
('Shirol', 1, 13),
('Shirol', 7, 29);
