CREATE TABLE IF NOT EXISTS "people" (
	"ID"	INTEGER,
	"FirstFirstName"	text,
	"FirstName"	text,
	"MiddleName"	text,
	"LastName"	text,
	"BirthLastName"	text,
	"Nickname"	TEXT,
	"Birthdate"	text,
	"Deathdate"	INTEGER,
	"Husband"	int,
	"Wife"	int,
	"Father"	int,
	"Mother"	int,
	PRIMARY KEY("ID" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "Stay" (
	"LocationID"	INTEGER,
	"Start"	TEXT,
	"End"	TEXT,
	"PersonID"	INTEGER
);

CREATE TABLE IF NOT EXISTS "Location" (
	"ID"	INTEGER,
	"City"	TEXT,
	"State"	TEXT,
	"Country"	TEXT,
	PRIMARY KEY("ID" AUTOINCREMENT)
);