## load necessary packages 
library(RMySQL)
library(dplyr)
library(tidyr)

## begin connecting to DB
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
chart_sum <- charts_df %>% group_by(title,artist) %>% summarize(top_peak = min(peakPos),date = min(chart_date),
                                                                streak=max(weeks),entries=sum(isNew))



##################################################
# DATASET 2: songs dataset
xqstr2 <- "SELECT * FROM songs"
songs_df <- dbGetQuery(con,xqstr2) %>% distinct()


# DATASET 3: full dataset
full_df <- left_join(chart_sum,songs_df,by=c("title","artist")) 

# Data cleaning

library(lubridate)
full_df$year <- year(ymd(full_df$date))
full_df$chart_date <- as.numeric(as.Date(full_df$date))

# new full ds with column 9 removed to keep more data
full_new <- full_df[,-9] %>% na.omit()

### revised data: to be used for modeling purposes (originally AV set)
### full_new <- full_df %>% select(-id) %>% na.omit() -- also AV still keep to compare w test set


str(full_new)

# data to find correlations
#cors1data <- full_new[,9:18]
#keep num and int
cors2data <- full_new[,-c(1:2,4,7:8)]

#  correlations
cors1 <- cor(cors1data)
cors2 <- cor(cors2data)

# pretty cor plot
library("corrplot")
corrplot(cors2, method = "color")

# identifying recurring artists 

artistcount <-unlist(table(full_new$artist_clean))

######
#EDA

plot(full_new$top_peak, full_new$streak, main = "Top Peak ~ Streak", ylab = "Top Peak", xlab = "Streak")
hist(full_new$streak,  main = "Histogram of Artist Streaks", xlab = "Streak on Billboard")
hist(log(full_new$streak),  main = "Histogram of Artist Streaks", xlab = "Streak on Billboard") #log transform to better distribute

# data to find correlations
#cors1data <- full_new[,9:18]
#keep num and int
cors2data <- full_new[,-c(1:2,4,7:8)]

#  correlations
cors1 <- cor(cors1data)
cors2 <- cor(cors2data)

# pretty cor plot
library("corrplot")
corrplot(cors2, method = "color")

# identifying recurring artists 

artistcount <-unlist(table(full_new$artist_clean))

# top peak, entries are negatively correlated; valence and loudness positively correlated
sort(cors1[-2,2]) 

#best songs in 2017

yearlies <- full_df %>% filter(ymd(date) >= ymd("2017-01-01") & ymd(date) <= ymd("2017-12-31")) #%>% arrange(top_peak, desc(streak))

yearlies

#average danceability by year
full_df %>% group_by(year) %>% summarize(mean(danceability, na.rm = TRUE), sd(danceability, na.rm = TRUE))

#more EDA
plot(full_df$danceability, full_df$top_peak)

ggplot(full_df, aes(x=danceability, y= top_peak)) + geom_point()+geom_smooth(method="loess")

ggplot(full_df, aes(x=energy, y= top_peak)) + geom_point()+geom_smooth(method="loess")

#####
#Start Analysis

#Splitting Data into training & test sets - 80/20 split
train.index <- sample(1:3766, size = .8 * 3766)
test.index <- setdiff(1:3766, train.index)

train.data <- full_new[train.index,]
test.data <- full_new[test.index,]


#start fitting some lines
fit1 <- lm(top_peak ~ streak + duration + year, data = train.data)
fit2 <- lm(top_peak ~ streak + artist_clean + duration + year, data = train.data)
fit3 <- lm(top_peak ~ streak + entries + artist_clean + duration + year + speechiness + chart_date, data = train.data)
fit5 <- lm(top_peak ~ streak + entries + artist_clean + duration + year + log(speechiness) + chart_date, data = train.data)

#try smoothing load mgv library
library(mgcv)
fit4 <- gam(top_peak ~ s(streak) + s(duration) + year + entries, data = train.data)
# try lm again with log transformed speechiness variable - no difference :(
fit5 <- lm(top_peak ~ log(streak) + entries + artist_clean + duration + year + log(speechiness) + chart_date, data = train.data)


#review
summary(fit1)
summary(fit2)
summary(fit3)
summary(fit4)
summary(fit5)



#not much variance captured, assess prediction anyway.
predict1 <- predict(fit1, newdata = test.data)

MSE1 <- mean((predict1 - test.data$top_peak)^2)

MSE1

predict5 <- predict(fit5, newdata = test.data)

MSE5 <- mean((predict5 - test.data$top_peak)^2)

MSE5


#model plots
residuals <- resid(fit1)
plot(fitted(fit1), residuals)

dbDisconnect(con)
