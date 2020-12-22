-- MySQL dump 10.13  Distrib 5.6.48-88.0, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: slack_archive
-- ------------------------------------------------------
-- Server version	5.6.48-88.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `tbl_channels`
--

DROP TABLE IF EXISTS `tbl_channels`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tbl_channels` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `team_id` tinyint(4) NOT NULL,
  `slack_channel_id` varchar(16) NOT NULL,
  `channel_name` varchar(64) NOT NULL,
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tbl_files`
--

DROP TABLE IF EXISTS `tbl_files`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tbl_files` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `message_id` bigint(20) unsigned NOT NULL,
  `mimetype` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `thumb_800` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `permalink` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `permalink_public` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `thumb_80` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6428 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tbl_messages`
--

DROP TABLE IF EXISTS `tbl_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tbl_messages` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `team_id` tinyint(4) NOT NULL,
  `user_id` tinyint(4) NOT NULL,
  `channel_id` smallint(6) NOT NULL,
  `timestamp` int(11) NOT NULL,
  `text` text COLLATE utf8mb4_unicode_ci,
  `client_msg_id` varchar(40) DEFAULT NULL,
  `archive_url` varchar(128) DEFAULT NULL,
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `team_id` (`team_id`,`user_id`,`channel_id`,`timestamp`,`text`(127)),
  KEY `idx_channel_name_timestamp` (`channel_id`,`timestamp`),
  FULLTEXT KEY `text` (`text`)
) ENGINE=InnoDB AUTO_INCREMENT=260311 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tbl_teams`
--

DROP TABLE IF EXISTS `tbl_teams`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tbl_teams` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `slack_team_id` varchar(16) NOT NULL,
  `team_name` varchar(16) NOT NULL,
  `team_url` varchar(40) DEFAULT NULL,
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tbl_users`
--

DROP TABLE IF EXISTS `tbl_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tbl_users` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(32) NOT NULL,
  `full_name` varchar(32) NOT NULL,
  `slack_user_id` varchar(16) NOT NULL,
  `team_id` tinyint(4) NOT NULL,
  `avatar_url` varchar(255) DEFAULT NULL,
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=77 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2020-12-03 17:31:09
