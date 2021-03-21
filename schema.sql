-- data

CREATE TABLE `teilnehmer` (
  `id` varchar(255),
  `email` varchar(255),
  `name` varchar(255),
  PRIMARY KEY (id)
) ENGINE = INNODB;

CREATE TABLE `fragen` (
  `id` int AUTO_INCREMENT,
  `frage` varchar(255),
  `sichtbar` int DEFAULT 0,
  `abgeschlossen` int DEFAULT 0,
  PRIMARY KEY (id)
) ENGINE = INNODB;

CREATE TABLE `antworten` (
  `id` int AUTO_INCREMENT,
  `fragen_id` int,
  `antwort` varchar(255),
  PRIMARY KEY (id)
) ENGINE = INNODB;


CREATE TABLE `teilgenommen` (
  `teilnehmer_id` varchar(255),
  `fragen_id` int
) ENGINE = INNODB;

CREATE TABLE `auswertung` (
  `antwort_id` int,
  `fragen_id` int
) ENGINE = INNODB;



