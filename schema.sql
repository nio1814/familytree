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