CREATE TABLE config(
	name varchar(255),
	value varchar(255)
	);

INSERT INTO config(name,value) VALUES ('capture_interval','1');


CREATE TABLE `projects` ( 
`name` VARCHAR(200) NOT NULL , 
`capture_interval` INT NOT NULL DEFAULT '1' , 
`frame_count` INT NOT NULL DEFAULT '0' ,
`last_capture` DATETIME NULL DEFAULT NULL,
`resolution_x` INT NOT NULL DEFAULT '1024' ,
`resolution_y` INT NOT NULL DEFAULT '768' ,
`render_start_frame` INT NOT NULL DEFAULT '0',
`render_end_frame` INT NOT NULL DEFAULT '0',
`render_frame_rate`  INT NOT NULL DEFAULT '30',
`render_codec` VARCHAR(25) NOT NULL DEFAUlT 'mp4', 
`status` VARCHAR(25) NOT NULL DEFAULT 'created',
 UNIQUE (`name`));