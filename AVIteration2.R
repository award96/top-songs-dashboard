options(width=90, xtable.comment = FALSE)

library(RMySQL)
library(dplyr)
library(tidyr)
library(ggplot2)
library(corrplot)
library(car)
library(faraway)
library(caret)
library(leaps)
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

# data is from beginning of 2016 to now

# DATASET 1: charts dataset
xqstr <- "SELECT * FROM charts"
charts_df <- dbGetQuery(con, xqstr)

# summary of charts dataset, for exploratory analysis
chart_sum <- charts_df %>% group_by(title,artist) %>% summarize(top_peak = min(peakPos),
             streak=max(weeks),entries=sum(isNew),avgpos=mean(chart_rank),sdpos=sd(chart_rank))

##################################################
# DATASET 2: songs dataset
xqstr2 <- "SELECT * FROM songs"
songs_df <- dbGetQuery(con,xqstr2) %>% distinct()

# EDA

hist(songs_df$danceability) # slightly left skewed
hist(songs_df$energy) # slightly left skewed
hist(songs_df$song_key) # somewhat close to uniform
hist(songs_df$loudness) # slightly left skewed
hist(songs_df$valence) # bell-shaped
hist(songs_df$tempo) # slight bell shape, heavy middle
hist(songs_df$duration) # heavy middle
hist(songs_df$instrumentalness) # most values close to 0

hist(songs_df$song_mode) # binary; could be a factor variable
hist(songs_df$time_signature) # different categories; could be a factor variable

hist(songs_df$speechiness) # right skewed; potential log transform
hist(songs_df$acousticness) # right skewed; potential log transform
hist(log(songs_df$liveness)) # right skewed; potential log transform


##################################################
# DATASET 3: full dataset
full_df <- left_join(chart_sum,songs_df,by=c("title","artist")) 


# revised data: to be used for modeling purposes
full_new <- full_df %>% select(-id)
# **this is the part that correctly removes NA's
full_new <- full_new[!is.na(full_new$danceability),] 

str(full_new)

# CHANGING VARIABLE FORMATS IN MAIN DATASET***

# change 1: factor variables
full_new$song_mode <- as.factor(full_new$song_mode)
full_new$time_signature <- as.factor(full_new$time_signature)

# change 2: log transforms for heavily skewed variables
full_new$speechiness <- log(full_new$speechiness)
full_new$acousticness <- log(full_new$acousticness)
full_new$liveness <- log(full_new$liveness)

str(full_new)

##############################

# EDA 
# data to find correlations of only numeric variables with response (which is the longest streak)
full_corr <- full_new[,c(3:7,10:13,15:21)]

# CORRELATION MATRIX
cors1 <- cor(full_corr)
summary(full_new$instrumentalness)
corrplot(cors1)
# top peak, avg position, speechiness are negatively correlated; valence and sd(position) positively correlated
sort(cors1[-2,2]) 

##############################

# MODEL 1: includes the majority of variables (took out avg position due to overlap with top position)

m1 <- lm(streak ~ .-title-artist-artist_clean-features-avgpos,data=full_new)

summary(m1)

# test train splits for cv; 80% train, 20% test
set.seed(834)
train_index <- createDataPartition(full_new$streak, p = 0.8,list=FALSE)

train <- full_new[train_index, ]
train_num <- train[,-c(1:2,8:9)] # taking out non-numeric variables

test <- full_new[-train_index, ]
test_num <- test[,-c(1:2,8:9)] # taking out non-numeric variables

# training the model
mtrain <- lm(streak ~ .-avgpos,data=train_num)
summary(mtrain)

# finding accuracy of model on test set
pred1 <- predict(mtrain,test_num)

# given R^2 = 0.4367, RMSE = 8.4813
results1 <- c(R2 = R2(pred1,test_num$streak), RMSE = RMSE(pred1,test_num$streak))
results1

# model surprisingly has low vifs despite high number of variables
car::vif(m1)


##############################

# MODEL 2: a transformed response (log) with stepwise regression

# less skewed distribution of response
hist(log(full_new$streak))




mlog <- lm(log(streak) ~ .-title-artist-artist_clean-features-avgpos,data=full_new)

summary(mlog)

# using stepwise regression to reduce variables from 15 to 7
m2 <- regsubsets(log(streak) ~ .-title-artist-artist_clean-features-avgpos,data=hnum,nvmax=7,method="backward")


# training the model
mtrain <- lm(log(streak) ~ .-avgpos,data=train_num)
summary(mtrain)

# finding accuracy of model on test set
pred2 <- predict(mtrain,test_num)
head(pred2)
head(log(test_num$streak))


# given R^2 = 0.501, RMSE = 0.932 (becomes 2.54 in non-log terms)
results2 <- c(R2 = R2(pred2,log(test_num$streak)), RMSE = RMSE(pred2,log(test_num$streak)))
results2
exp(results2[2]) # finding RMSE in non-log terms; 2.54 is the result



trial_df <- data.frame(pred2 = pred2,test_streak = log(test_num$streak))

trial_df <- trial_df %>% mutate(logdiffs = test_streak - pred2,logexp = exp(logdiffs))

summary(trial_df)
##############################

# MODEL 3: 





# to do: implement weighting system using charts_df






dbDisconnect(con)




