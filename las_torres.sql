-- BARBACOA LAS TORRES | Datos de ejemplo para demostración
-- Los precios, costos, cantidades y ventas son ilustrativos; reemplázalos por datos del negocio.
-- IMPORTAR EN PHPMYADMIN: archivo completo, en servidor MySQL local.
CREATE DATABASE IF NOT EXISTS las_torres CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE las_torres;
CREATE TABLE IF NOT EXISTS empresas (id_empresa INT AUTO_INCREMENT PRIMARY KEY,nombre VARCHAR(120) NOT NULL);
CREATE TABLE IF NOT EXISTS usuarios (id_usuario INT AUTO_INCREMENT PRIMARY KEY,id_empresa INT NOT NULL,nombre VARCHAR(100) NOT NULL,correo VARCHAR(150) NOT NULL,password_hash VARCHAR(255) NOT NULL,rol VARCHAR(40) NOT NULL,FOREIGN KEY(id_empresa) REFERENCES empresas(id_empresa));
CREATE TABLE IF NOT EXISTS productos (id_producto INT AUTO_INCREMENT PRIMARY KEY,id_empresa INT NOT NULL,nombre VARCHAR(100) NOT NULL,descripcion VARCHAR(255),precio DECIMAL(12,2) NOT NULL,costo DECIMAL(12,2) NOT NULL,stock INT NOT NULL DEFAULT 0,stock_minimo INT NOT NULL DEFAULT 5,fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(id_empresa) REFERENCES empresas(id_empresa));
CREATE TABLE IF NOT EXISTS ventas (id_venta INT AUTO_INCREMENT PRIMARY KEY,id_empresa INT NOT NULL,id_usuario INT NOT NULL,fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,total DECIMAL(12,2) NOT NULL,metodo_pago VARCHAR(30) NOT NULL,FOREIGN KEY(id_empresa) REFERENCES empresas(id_empresa),FOREIGN KEY(id_usuario) REFERENCES usuarios(id_usuario));
CREATE TABLE IF NOT EXISTS detalle_ventas (id_detalle INT AUTO_INCREMENT PRIMARY KEY,id_venta INT NOT NULL,id_producto INT NOT NULL,cantidad INT NOT NULL,precio_unitario DECIMAL(12,2) NOT NULL,costo_unitario DECIMAL(12,2) NOT NULL,subtotal DECIMAL(12,2) NOT NULL,FOREIGN KEY(id_venta) REFERENCES ventas(id_venta),FOREIGN KEY(id_producto) REFERENCES productos(id_producto));
CREATE TABLE IF NOT EXISTS gastos (id_gasto INT AUTO_INCREMENT PRIMARY KEY,id_empresa INT NOT NULL,concepto VARCHAR(150) NOT NULL,categoria VARCHAR(80) NOT NULL,monto DECIMAL(12,2) NOT NULL,fecha DATE NOT NULL,FOREIGN KEY(id_empresa) REFERENCES empresas(id_empresa));
CREATE TABLE IF NOT EXISTS movimientos_inventario (id_movimiento INT AUTO_INCREMENT PRIMARY KEY,id_empresa INT NOT NULL,id_producto INT NOT NULL,tipo VARCHAR(20) NOT NULL,cantidad INT NOT NULL,motivo VARCHAR(255),fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(id_empresa) REFERENCES empresas(id_empresa),FOREIGN KEY(id_producto) REFERENCES productos(id_producto));
-- Evita duplicar el catálogo al importar por segunda vez.
INSERT INTO empresas(id_empresa,nombre) VALUES (1,'Barbacoa Las Torres') ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);
INSERT INTO usuarios(id_usuario,id_empresa,nombre,correo,password_hash,rol) VALUES (1,1,'Caja principal','caja@lastorres.local','SIN_ACCESO_WEB','administrador') ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);
INSERT INTO productos(id_producto,id_empresa,nombre,descripcion,precio,costo,stock,stock_minimo) VALUES (1,1,'Taco de barbacoa','Taco con cilantro y cebolla',35,17,90,15) ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);
INSERT INTO productos(id_producto,id_empresa,nombre,descripcion,precio,costo,stock,stock_minimo) VALUES (2,1,'Taco dorado de barbacoa','Taco dorado con barbacoa',40,20,60,10) ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);
INSERT INTO productos(id_producto,id_empresa,nombre,descripcion,precio,costo,stock,stock_minimo) VALUES (3,1,'Barbacoa 1/4 kg','Barbacoa por cuarto de kilo',155,90,24,5) ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);
INSERT INTO productos(id_producto,id_empresa,nombre,descripcion,precio,costo,stock,stock_minimo) VALUES (4,1,'Barbacoa 1/2 kg','Barbacoa por medio kilo',295,175,18,4) ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);
INSERT INTO productos(id_producto,id_empresa,nombre,descripcion,precio,costo,stock,stock_minimo) VALUES (5,1,'Barbacoa 1 kg','Barbacoa por kilo',570,340,12,3) ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);
INSERT INTO productos(id_producto,id_empresa,nombre,descripcion,precio,costo,stock,stock_minimo) VALUES (6,1,'Consomé chico','Consomé tradicional 250 ml',25,9,55,10) ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);
INSERT INTO productos(id_producto,id_empresa,nombre,descripcion,precio,costo,stock,stock_minimo) VALUES (7,1,'Consomé grande','Consomé tradicional 500 ml',40,15,35,8) ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);
INSERT INTO productos(id_producto,id_empresa,nombre,descripcion,precio,costo,stock,stock_minimo) VALUES (8,1,'Quesadilla de barbacoa','Quesadilla de maíz con barbacoa',55,28,32,8) ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);
INSERT INTO productos(id_producto,id_empresa,nombre,descripcion,precio,costo,stock,stock_minimo) VALUES (9,1,'Refresco 600 ml','Bebida embotellada',28,17,48,12) ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);
INSERT INTO productos(id_producto,id_empresa,nombre,descripcion,precio,costo,stock,stock_minimo) VALUES (10,1,'Agua natural 600 ml','Agua embotellada',20,10,35,10) ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);
INSERT INTO productos(id_producto,id_empresa,nombre,descripcion,precio,costo,stock,stock_minimo) VALUES (11,1,'Agua de horchata','Vaso 500 ml',30,12,25,7) ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);
INSERT INTO productos(id_producto,id_empresa,nombre,descripcion,precio,costo,stock,stock_minimo) VALUES (12,1,'Paquete familiar','Medio kilo, tortillas y consomé',360,215,8,3) ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);
-- Operaciones ilustrativas de apertura (se insertan una sola vez).
INSERT INTO ventas(id_venta,id_empresa,id_usuario,fecha,total,metodo_pago) VALUES
(1,1,1,'2026-11-12 09:10:00',175,'efectivo'),
(2,1,1,'2026-11-12 11:30:00',360,'transferencia'),
(3,1,1,'2026-11-13 10:15:00',210,'efectivo'),
(4,1,1,'2026-11-13 12:45:00',295,'tarjeta'),
(5,1,1,'2026-11-14 09:35:00',165,'efectivo'),
(6,1,1,'2026-11-14 13:20:00',570,'transferencia')
ON DUPLICATE KEY UPDATE total=VALUES(total);
INSERT INTO detalle_ventas(id_detalle,id_venta,id_producto,cantidad,precio_unitario,costo_unitario,subtotal) VALUES
(1,1,1,5,35,17,175),(2,2,12,1,360,215,360),(3,3,1,6,35,17,210),
(4,4,4,1,295,175,295),(5,5,6,1,25,9,25),(6,5,1,4,35,17,140),(7,6,5,1,570,340,570)
ON DUPLICATE KEY UPDATE subtotal=VALUES(subtotal);
INSERT INTO gastos(id_gasto,id_empresa,concepto,categoria,monto,fecha) VALUES
(1,1,'Gas para preparación','Servicios',420,'2026-11-12'),
(2,1,'Empaques y servilletas','Otros',185,'2026-11-13'),
(3,1,'Transporte de insumos','Otros',240,'2026-11-14')
ON DUPLICATE KEY UPDATE concepto=VALUES(concepto);
