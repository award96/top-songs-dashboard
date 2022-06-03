update songs set artist_clean = replace(replace(replace(
replace(artist, ' Featuring', ','),
 ' &', ','),
 ' X ', ', '),
 ' x ', ', ');
 
update songs set features =  substring(artist_clean,locate(',',artist_clean)+2,LENGTH(artist_clean))
where artist_clean like '%, %';

update songs set artist_clean =  SUBSTRING_INDEX(artist_clean, ', ',  1);
