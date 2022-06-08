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
library(MASS)
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

ggplot(songs_df,aes(x=danceability)) +
  geom_histogram(binwidth=0.05,col="blue") + ggtitle("Danceability Distribution")
# slightly left skewed
hist(songs_df$energy) # slightly left skewed
hist(songs_df$song_key) # somewhat close to uniform
hist(songs_df$loudness) # slightly left skewed
hist(songs_df$valence) # bell-shaped
hist(songs_df$tempo) # slight bell shape, heavy middle
hist(songs_df$duration) # heavy middle
hist(songs_df$instrumentalness) # most values close to 0

hist(songs_df$song_mode) # binary; could be a factor variable
hist(songs_df$time_signature) # different categories; could be a factor variable

# right skewed; potential log transform
ggplot(songs_df,aes(x=speechiness)) +
  geom_histogram(binwidth=0.05,col="blue",fill="green") + ggtitle("Speechiness Distribution")

# right skewed; potential log transform
ggplot(songs_df,aes(x=acousticness)) +
  geom_histogram(binwidth=0.05,col="blue",fill="green") + ggtitle("Acousticness Distribution")

# right skewed; potential log transform
ggplot(songs_df,aes(x=liveness)) +
  geom_histogram(binwidth=0.05,col="blue",fill="green") + ggtitle("Liveness Distribution")


##################################################
# DATASET 3: full dataset
full_df <- left_join(chart_sum,songs_df,by=c("title","artist")) 


# MAKING CHANGES TO DATA: to be used for modeling purposes
full_new <- full_df %>% dplyr::select(-id)
# **this is the part that correctly removes NA's
full_new <- full_new[!is.na(full_new$danceability),] 

str(full_new)

# adding artist's name length variable
full_new$len <- nchar(full_new$artist_clean)

# CHANGING VARIABLE FORMATS IN MAIN DATASET***

# change 1: factor variables**
full_new$song_mode <- as.factor(full_new$song_mode)
full_new$time_signature <- as.factor(full_new$time_signature)

# change 2: log transforms for heavily skewed variables**
full_new$speechiness <- log(full_new$speechiness)
full_new$acousticness <- log(full_new$acousticness)
full_new$liveness <- log(full_new$liveness)

str(full_new)

##############################

# EDA 
# data to find correlations of only numeric variables with response (which is the longest streak)
full_corr <- full_new[,c(3:7,10:13,15:21,23)]

# CORRELATION INFO
cors1 <- cor(full_corr)

# correlation plot
cp <- corrplot(cors1) 

# correlation matrix for response only:
# top peak, speechiness are negatively correlated to response
# valence and sd(position) positively correlated to response
sort(cors1[-2,2])

##############################

# MODEL 1: includes the majority of variables (took out avg position due to overlap with top position)

full_new2 <- full_new %>% dplyr::select(-features) # taking out features since most are NA

m1 <- lm(streak ~ .-title-artist-artist_clean-avgpos,data=full_new2)

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

# given R^2 = 0.4536, RMSE = 8.754
results1 <- c(R2 = R2(pred1,test_num$streak), RMSE = RMSE(pred1,test_num$streak))
results1

# model surprisingly has low vifs despite high number of variables
car::vif(m1)


##############################

# MODEL 2: a transformed response (log) with stepwise regression

# less skewed distribution of response
hist(log(full_new$streak))

# log model
mlog <- lm(log(streak) ~ .-title-artist-artist_clean-avgpos,data=full_new2)

summary(mlog)


# training the model
mtrain <- lm(log(streak) ~ .-avgpos,data=train_num)
summary(mtrain)

# finding accuracy of model on test set
pred2 <- predict(mtrain,test_num)


# given R^2 = 0.3687, RMSE = 9.948
results2 <- c(R2 = R2(exp(pred2),test_num$streak), RMSE = RMSE(exp(pred2),test_num$streak))
results2



##############################

# MODEL 3: 

# using stepwise regression to reduce variables from 17 to 7
m2 <- regsubsets(streak ~ .-title-artist-artist_clean-avgpos,data=full_new2,nvmax=7,method="backward")

# for the 7-variable model: 
# valence, liveness, speechiness, top_peak, entries, sdpos, loudness
# **speechiness and liveness are log transformed in this model
summary(m2)


# training the model
mtrain <- lm(streak ~ valence + liveness + speechiness + top_peak + entries + sdpos + loudness,data=train_num)
summary(mtrain)

# finding accuracy of model on test set
pred3 <- predict(mtrain,test_num)

# given R^2 = 0.4599, RMSE = 8.707
results3 <- c(R2 = R2(pred3,test_num$streak), RMSE = RMSE(pred3,test_num$streak))
results3

# still can't get RMSE that low, probably due to outliers above 40 weeks

sbp <- boxplot(full_new$streak,main="Boxplot of Streaks",col="light blue",ylab="Streak Length in Weeks")

#############################


## NEW METHOD OF ANALYSIS: BINNING
# try to predict whether a song is in one of 3 categories: short, medium, or long streak

# bins are [0,1], (1,12], (12,inf]
quantile(full_new$streak,probs=c(1/3,2/3))

# duplicate full_new2
full_new3 <- full_new2

# ORGANIZING DATA: creating a category variable that is the new response variable
full_new3$cat <- 0

for(i in 1:nrow(full_new3)){
  if(full_new3$streak[i] <= 1){
    full_new3$cat[i] <- "short"
  } else if(full_new3$streak[i] > 1 & full_new3$streak[i] <= 12){
    full_new3$cat[i] <- "medium"
  } else{
    full_new3$cat[i] <- "long"
  }
}

full_new3$cat <- factor(full_new3$cat)


# 1269 songs in short category, 1170 in medium, 1172 in long
summary(full_new3$cat)

# MORE EDA; looking at summaries of predictors across each group

catsummary <- full_new3 %>% group_by(cat) %>% 
summarize(val = mean(valence),
          live = mean(liveness),
          speech = mean(speechiness), 
          peak = median(top_peak),
          enter = median(entries),
          sdp = mean(sdpos),
          loud = mean(loudness)
          )

speechplot <- ggplot(full_new3,aes(x=factor(cat,ordered=TRUE,levels=c("short","medium","long")),y=speechiness)) +
  geom_boxplot(size=0.75,col="blue") + ggtitle("Speechiness across Song Groups") + xlab("Time Song is in Top 100")
  
peakplot <- ggplot(full_new3,aes(x=factor(cat,ordered=TRUE,levels=c("short","medium","long")),y=top_peak)) +
  geom_boxplot(size=0.75,col="blue") + ggtitle("Top Peaks across Song Groups") + xlab("Time Song is in Top 100") + ylab("Top Peak")


# ****FINAL BINNING MODEL****: ordinal logistic regression; using variables from stepwise 

olr <- polr(cat ~ valence + liveness + speechiness + top_peak + sdpos + loudness,data=full_new3,Hess=TRUE)

summary(olr)

coef(olr)

cint <- confint(olr)

# exponentiated coefficients and confidence intervals for each predictor
exp(cbind(coef(olr),cint))

# test train splits for cv; 80% train, 20% test
set.seed(834)
train_index <- createDataPartition(full_new3$cat, p = 0.8,list=FALSE)

train <- full_new3[train_index, ]
train_num <- train[,-c(1:2,8)] # taking out non-numeric variables

test <- full_new3[-train_index, ]
test_num <- test[,-c(1:2,8)] # taking out non-numeric variables


# training the model
mtrain <- polr(cat ~ valence + liveness + speechiness + top_peak + sdpos + loudness,data=train_num,Hess=TRUE)
summary(mtrain)

# finding predicted categories for test set
pred4 <- predict(mtrain,test_num)

# predicted counts were somewhat even among the groups
summary(as.factor(pred4))

# accuracy of predictions on test set
results4 <- mean(pred4 == test_num$cat)
results4 # accuracy of 0.653

# A 3-way contingency table showing predictions across groups
table(pred4,test_num$cat)





##############################


# info on ordinal logistic regression from: https://stats.oarc.ucla.edu/r/dae/ordinal-logistic-regression/

dbDisconnect(con)




