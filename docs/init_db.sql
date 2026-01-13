DROP DATABASE IF EXISTS gameinventory;

CREATE DATABASE gameinventory CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

USE gameinventory;

CREATE TABLE juego (
  id         INT NOT NULL AUTO_INCREMENT,
  codigo     VARCHAR(50) UNIQUE,
  titulo     VARCHAR(200) NOT NULL,
  plataforma VARCHAR(50) NOT NULL,
  genero     VARCHAR(80),
  precio     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  stock      INT NOT NULL DEFAULT 0,
  estado     TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (id)
);

INSERT INTO juego (codigo, titulo, plataforma, genero, precio, stock)
VALUES
('SKU-003', 'God of War Ragnarök', 'PS5', 'Acción', 79.99, 4),
('SKU-004', 'The Last of Us Part II', 'PS4', 'Acción', 39.99, 6),
('SKU-005', 'Cyberpunk 2077', 'PC', 'RPG', 29.99, 8),
('SKU-006', 'Red Dead Redemption 2', 'Xbox One', 'Aventura', 49.99, 5),
('SKU-007', 'Super Mario Odyssey', 'Switch', 'Plataformas', 59.99, 7),
('SKU-008', 'Hollow Knight', 'PC', 'Metroidvania', 14.99, 12),
('SKU-009', 'FIFA 24', 'PS5', 'Deportes', 69.99, 10),
('SKU-010', 'Resident Evil 4 Remake', 'PS5', 'Terror', 59.99, 3);

SELECT * FROM juego;