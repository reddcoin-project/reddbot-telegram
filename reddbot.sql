-- MySQL dump
-- ------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Create and set database
--

DROP DATABASE IF EXISTS reddbotv4;
CREATE DATABASE reddbotv4;
USE reddbotv4;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `account_id` bigint NOT NULL AUTO_INCREMENT,
  `user_name` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `first_name` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `last_name` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `balance` decimal(20,8) DEFAULT NULL,
  `create_date` datetime DEFAULT current_timestamp(),
  `modify_date` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `delete_date` datetime DEFAULT NULL,
  PRIMARY KEY (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

ALTER TABLE `users` ADD UNIQUE user_name_unique_index (`user_name`);
--
-- Table structure for table `users_autowithdrawal`
--

DROP TABLE IF EXISTS `users_autowithdrawals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_autowithdrawals` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `account_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `threshold` decimal(20,8) DEFAULT NULL,
  `address` varchar(34) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `create_date` datetime DEFAULT current_timestamp(),
  `modify_date` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `delete_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


--
-- Table structure for table `users_transactions`
--

DROP TABLE IF EXISTS `users_transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_transactions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_name` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `address` varchar(34) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `amount` decimal(20,8) DEFAULT NULL,
  `balance` decimal(20,8) DEFAULT NULL,
  `tx_type` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tx_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `affected_user_name` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `create_date` datetime DEFAULT current_timestamp(),
  `modify_date` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `delete_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

ALTER TABLE `users_transactions` ADD INDEX user_name_index (`user_name`);

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

--
-- Grants for user root (all tables)
--

GRANT ALL PRIVILEGES ON reddbotv4.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
