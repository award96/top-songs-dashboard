options(width=90, xtable.comment = FALSE)

library(RMySQL)
library(dplyr)
library(tidyr)
drv <- dbDriver("MySQL")
########################################
xdbsock <- ""

xdbuser <- "ROuser"
xpw     <- "hillgallfallstall"
xdbname <-"MyDB"
xdbhost <- "database-1.ctdynirvmpfi.us-west-1.rds.amazonaws.com"
xdbport <- 3306

con <- dbConnect(drv, 
                 user=xdbuser, 
                 password=xpw, 
                 dbname=xdbname, 
                 host=xdbhost, 
                 port=xdbport, unix.sock=xdbsock)

dbListTables(con)
dbGetInfo(con)

# DATASET 1: charts dataset
xqstr <- "SELECT * FROM charts"
charts_df <- dbGetQuery(con, xqstr)

# summary of charts dataset, for exploratory analysis
chart_sum <- charts_df %>% group_by(title,artist) %>% summarize(top_peak = min(peakPos),
             streak=max(weeks),entries=sum(isNew))

##################################################
# DATASET 2: songs dataset
xqstr2 <- "SELECT * FROM songs"
songs_df <- dbGetQuery(con,xqstr2) %>% distinct()

hist(songs_df$danceability) # slightly left skewed
hist(songs_df$energy) # left skewed

hist(songs_df$tempo) # slight bell shape, heavy middle; may not matter as much
hist(songs_df$speechiness) # right skewed


# DATASET 3: full dataset
full_df <- left_join(chart_sum,songs_df,by=c("title","artist")) 
full_df$chart_date <- as.Date(full_df$chart_date)

# revised data: to be used for modeling purposes
full_new <- full_df %>% select(-id) %>% na.omit()

str(full_new)



# data to find correlations with response (which is the longest streak)
full_corr <- full_new[,3:18]

# CORRELATION MATRIX
cors1 <- cor(full_corr)
# top peak, entries are negatively correlated; valence and loudness positively correlated
sort(cors1[-2,2]) 

# the full model

m1 <- lm(streak ~ .-title-artist,data=full_new)

summary(m1)






dbDisconnect(con)


