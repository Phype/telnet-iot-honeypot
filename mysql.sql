CREATE TABLE `samples` (
`id` INT NOT NULL AUTO_INCREMENT ,
`sha256` VARCHAR( 32 ) NOT NULL ,
`date` INT NOT NULL ,
`name` VARCHAR( 64 ) NOT NULL ,
`file` VARCHAR( 64 ) NOT NULL ,
`length` INT NOT NULL ,
`result` VARCHAR( 64 ) ,
PRIMARY KEY ( `id` )
) ENGINE = MYISAM ;

CREATE TABLE `urls` (
`id` INT NOT NULL AUTO_INCREMENT ,
`url` VARCHAR( 256 ) NOT NULL ,
`date` INT NOT NULL ,
`sample` ,
PRIMARY KEY ( `id` )
) ENGINE = MYISAM ;
 
CREATE TABLE `conns` (
`id` INT NOT NULL AUTO_INCREMENT ,
`ip` VARCHAR( 16 ) NOT NULL ,
`date` INT NOT NULL ,
`user` VARCHAR( 64 ) NOT NULL ,
`pass` VARCHAR( 64 ) NOT NULL ,
PRIMARY KEY ( `id` )
) ENGINE = MYISAM ;

CREATE TABLE .`conns_urls` (
`id_conn` INT NOT NULL ,
`id_url` INT NOT NULL
) ENGINE = MYISAM;

ALTER TABLE `conns_urls` ADD PRIMARY KEY ( `id_conn` , `id_url` );