-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1:3308
-- Tiempo de generación: 24-12-2025 a las 00:12:45
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

CREATE DATABASE IF NOT EXISTS `vestra` CHARACTER SET utf8mb4;
USE `vestra`;


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `vestra`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `carrito_items`
--

CREATE TABLE `carrito_items` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `cantidad` int(11) NOT NULL DEFAULT 1,
  `precio_unitario` int(11) NOT NULL,
  `fecha_agregado` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `carrito_items`
--

INSERT INTO `carrito_items` (`id`, `usuario_id`, `producto_id`, `cantidad`, `precio_unitario`, `fecha_agregado`) VALUES
(15, 1, 8, 3, 29990, '2025-12-22 13:36:40');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `categorias`
--

CREATE TABLE `categorias` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `slug` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `categorias`
--

INSERT INTO `categorias` (`id`, `nombre`, `slug`) VALUES
(1, 'Poleras', 'poleras'),
(2, 'Polerones', 'polerones'),
(3, 'Pantalones', 'pantalones'),
(4, 'Jeans', 'jeans'),
(5, 'Zapatillas', 'zapatillas'),
(6, 'Chaquetas', 'chaquetas'),
(7, 'Accesorios', 'accesorios'),
(8, 'Camisas', 'camisas'),
(9, 'Ropa Deportiva', 'ropa-deportiva'),
(10, 'Ropa de Mujer', 'ropa-de-mujer'),
(11, 'Perfumes', 'perfumes'),
(12, 'Relojes', 'relojes');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `favoritos`
--

CREATE TABLE `favoritos` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `creado_en` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `favoritos`
--

INSERT INTO `favoritos` (`id`, `usuario_id`, `producto_id`, `creado_en`) VALUES
(17, 1, 10, '2025-12-22 12:54:34'),
(19, 1, 20, '2025-12-22 13:04:19');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ordenes`
--

CREATE TABLE `ordenes` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `total` decimal(10,2) NOT NULL,
  `estado` varchar(50) DEFAULT 'confirmada',
  `creado_en` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `ordenes`
--

INSERT INTO `ordenes` (`id`, `usuario_id`, `total`, `estado`, `creado_en`) VALUES
(3, 1, 12990.00, 'completada', '2025-12-16 14:30:02'),
(6, 1, 12990.00, 'completada', '2025-12-18 14:54:18');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `orden_items`
--

CREATE TABLE `orden_items` (
  `id` int(11) NOT NULL,
  `orden_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `nombre_producto` varchar(255) DEFAULT NULL,
  `precio` decimal(10,2) DEFAULT NULL,
  `cantidad` int(11) DEFAULT NULL,
  `subtotal` decimal(10,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `orden_items`
--

INSERT INTO `orden_items` (`id`, `orden_id`, `producto_id`, `nombre_producto`, `precio`, `cantidad`, `subtotal`) VALUES
(3, 3, 1, 'Polera Basic Blanca', 12990.00, 1, 12990.00),
(6, 6, 1, 'Polera Basic Blanca', 12990.00, 1, 12990.00);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `productos`
--

CREATE TABLE `productos` (
  `id` int(11) NOT NULL,
  `nombre` varchar(150) NOT NULL,
  `descripcion` text NOT NULL,
  `precio` int(11) NOT NULL,
  `stock` int(11) NOT NULL,
  `imagen` varchar(255) DEFAULT NULL,
  `categoria_id` int(11) NOT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `productos`
--

INSERT INTO `productos` (`id`, `nombre`, `descripcion`, `precio`, `stock`, `imagen`, `categoria_id`, `fecha_creacion`) VALUES
(1, 'Polera Basic Blanca', 'Polera algodón corte clásico', 12990, 18, 'descarga_2.jfif', 1, '2025-12-12 12:47:37'),
(2, 'Polera Oversize Negra', 'Polera urbana oversize', 15990, 15, 'descarga_31.jfif', 1, '2025-12-12 12:47:37'),
(3, 'Polera Graphic Street', 'Estampado urbano premium', 17990, 11, 'images_6.jfif', 1, '2025-12-12 12:47:37'),
(4, 'Polera Slim Fit', 'Ajuste slim moderno', 14990, 18, 'descarga.jfif', 1, '2025-12-12 12:47:37'),
(5, 'Polerón Hoodie Negro', 'Polerón con capucha algodón', 34990, 10, 'descarga_1.jfif', 2, '2025-12-12 12:47:37'),
(6, 'Polerón Oversize', 'Corte ancho estilo street', 37990, 8, 'descarga_2.jfif', 2, '2025-12-12 12:47:37'),
(7, 'Polerón Zip', 'Polerón con cierre frontal', 32990, 12, 'descarga_32.jfif', 2, '2025-12-12 12:47:37'),
(8, 'Polerón Básico', 'Polerón liso minimalista', 29990, 15, 'descarga_3.jfif', 2, '2025-12-12 12:47:37'),
(9, 'Pantalón Cargo', 'Pantalón cargo urbano', 39990, 14, 'images.jfif', 3, '2025-12-12 12:47:37'),
(10, 'Pantalón Jogger', 'Jogger deportivo', 27990, 20, 'descarga_4.jfif', 3, '2025-12-12 12:47:37'),
(11, 'Pantalón Slim', 'Corte moderno slim', 35990, 10, 'descarga_5.jfif', 3, '2025-12-12 12:47:37'),
(12, 'Pantalón Relax', 'Corte cómodo diario', 31990, 16, 'descarga_6.jfif', 3, '2025-12-12 12:47:37'),
(13, 'Jean Skinny', 'Jean ajustado azul', 42990, 12, 'descarga_7.jfif', 4, '2025-12-12 12:47:37'),
(14, 'Jean Recto', 'Corte clásico', 39990, 14, 'descarga_8.jfif', 4, '2025-12-12 12:47:37'),
(15, 'Jean Destroyed', 'Estilo rasgado urbano', 45990, 8, 'descarga_10.jfif', 4, '2025-12-12 12:47:37'),
(16, 'Jean Black', 'Jean negro premium', 44990, 10, 'descarga_11.jfif', 4, '2025-12-12 12:47:37'),
(17, 'Zapatilla Urban', 'Zapatilla urbana blanca', 69990, 10, 'images_1.jfif', 5, '2025-12-12 12:47:37'),
(18, 'Zapatilla Street', 'Diseño streetwear', 74990, 8, 'images_2.jfif', 5, '2025-12-12 12:47:37'),
(19, 'Zapatilla Running', 'Ideal para running', 79990, 6, 'descarga_13.jfif', 5, '2025-12-12 12:47:37'),
(20, 'Zapatilla Casual', 'Uso diario cómodo', 65990, 12, 'descarga_14.jfif', 5, '2025-12-12 12:47:37'),
(21, 'Chaqueta Bomber', 'Chaqueta bomber urbana', 59990, 7, 'descarga_15.jfif', 6, '2025-12-12 12:47:37'),
(22, 'Chaqueta Denim', 'Chaqueta de mezclilla', 54990, 9, 'descarga_16.jfif', 6, '2025-12-12 12:47:37'),
(23, 'Chaqueta Parka', 'Parka invierno', 79990, 5, 'descarga_17.jfif', 6, '2025-12-12 12:47:37'),
(24, 'Chaqueta Ligera', 'Chaqueta liviana', 49990, 11, 'images_3.jfif', 6, '2025-12-12 12:47:37'),
(25, 'Gorro Beanie', 'Gorro urbano', 12990, 30, 'images_4.jfif', 7, '2025-12-12 12:47:37'),
(26, 'Mochila Street', 'Mochila resistente', 39990, 10, 'descarga_18.jfif', 7, '2025-12-12 12:47:37'),
(27, 'Cinturón Casual', 'Cinturón cuero sintético', 15990, 20, 'descarga_19.jfif', 7, '2025-12-12 12:47:37'),
(28, 'Lentes Urban', 'Lentes de sol', 19990, 15, 'descarga_20.jfif', 7, '2025-12-12 12:47:37'),
(29, 'Camisa Casual', 'Camisa algodón', 29990, 12, 'descarga_21.jfif', 8, '2025-12-12 12:47:37'),
(30, 'Camisa Slim', 'Corte slim elegante', 32990, 10, 'descarga_22.jfif', 8, '2025-12-12 12:47:37'),
(31, 'Camisa Cuadros', 'Estilo leñador', 27990, 14, 'descarga_23.jfif', 8, '2025-12-12 12:47:37'),
(32, 'Camisa Blanca', 'Formal clásica', 31990, 8, 'descarga_22.jfif', 8, '2025-12-12 12:47:37'),
(33, 'Short Deportivo', 'Short entrenamiento', 18990, 20, 'descarga_24.jfif', 9, '2025-12-12 12:47:37'),
(34, 'Polera DryFit', 'Secado rápido', 21990, 15, 'descarga_25.jfif', 9, '2025-12-12 12:47:37'),
(35, 'Calza Sport', 'Calza deportiva', 24990, 12, 'descarga_26.jfif', 9, '2025-12-12 12:47:37'),
(36, 'Buzo Training', 'Buzo completo', 45990, 6, 'descarga_27.jfif', 9, '2025-12-12 12:47:37'),
(37, 'Vestido Casual', 'Vestido urbano', 34990, 10, 'descarga_28.jfif', 10, '2025-12-12 12:47:37'),
(38, 'Blusa Elegante', 'Blusa formal', 27990, 12, 'images_5.jfif', 10, '2025-12-12 12:47:37'),
(39, 'Falda Denim', 'Falda jean', 29990, 9, 'descarga_29.jfif', 9, '2025-12-12 12:47:37'),
(40, 'Top Urbano', 'Top moderno', 19990, 18, 'descarga_30.jfif', 10, '2025-12-12 12:47:37');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `correo` varchar(150) NOT NULL,
  `password` varchar(255) NOT NULL,
  `rol` enum('usuario','admin') DEFAULT 'usuario',
  `intentos` int(11) DEFAULT 0,
  `fecha_registro` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `carrito_items`
--
ALTER TABLE `carrito_items`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_usuario_producto` (`usuario_id`,`producto_id`),
  ADD KEY `producto_id` (`producto_id`);

--
-- Indices de la tabla `categorias`
--
ALTER TABLE `categorias`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nombre` (`nombre`);

--
-- Indices de la tabla `favoritos`
--
ALTER TABLE `favoritos`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `usuario_id` (`usuario_id`,`producto_id`),
  ADD KEY `producto_id` (`producto_id`);

--
-- Indices de la tabla `ordenes`
--
ALTER TABLE `ordenes`
  ADD PRIMARY KEY (`id`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Indices de la tabla `orden_items`
--
ALTER TABLE `orden_items`
  ADD PRIMARY KEY (`id`),
  ADD KEY `orden_id` (`orden_id`),
  ADD KEY `producto_id` (`producto_id`);

--
-- Indices de la tabla `productos`
--
ALTER TABLE `productos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `categoria_id` (`categoria_id`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `correo` (`correo`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `carrito_items`
--
ALTER TABLE `carrito_items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT de la tabla `categorias`
--
ALTER TABLE `categorias`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT de la tabla `favoritos`
--
ALTER TABLE `favoritos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

--
-- AUTO_INCREMENT de la tabla `ordenes`
--
ALTER TABLE `ordenes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `orden_items`
--
ALTER TABLE `orden_items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `productos`
--
ALTER TABLE `productos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=41;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `carrito_items`
--
ALTER TABLE `carrito_items`
  ADD CONSTRAINT `carrito_items_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `carrito_items_ibfk_2` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `favoritos`
--
ALTER TABLE `favoritos`
  ADD CONSTRAINT `favoritos_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `favoritos_ibfk_2` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `ordenes`
--
ALTER TABLE `ordenes`
  ADD CONSTRAINT `ordenes_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `orden_items`
--
ALTER TABLE `orden_items`
  ADD CONSTRAINT `orden_items_ibfk_1` FOREIGN KEY (`orden_id`) REFERENCES `ordenes` (`id`),
  ADD CONSTRAINT `orden_items_ibfk_2` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`);

--
-- Filtros para la tabla `productos`
--
ALTER TABLE `productos`
  ADD CONSTRAINT `productos_ibfk_1` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
