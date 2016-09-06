# Here for this project we will be analyzing Tweets about the
# Presidential Candidates by word, tokenizing them, and then using
# them to classify each overall tweet as either positive or negative
# For the tweets here I have already classified 300 out of the 400
# tweets as either positive, negative or neutral
# This will allow the algorithm to be trained on 200 data points 
# And tested on a test set of the remaining 100 data points
# 100 of the data points are unlabeled and predicted with the algorithm
# Here we will import the Scikit Learn libraries among others necessary

import pandas as pd
import csv
import sys
import random
import numpy as np
import time
import twython
from time import strftime
#from pandas.DataFrame import query
import matplotlib.pyplot as plt
#import seaborn
import pygal
from IPython.display import SVG

import nltk
from nltk import corpus
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
nltk.download('punkt')
nltk.download('stopwords')
from nltk.twitter import Twitter
 
from sklearn import datasets
from sklearn.naive_bayes import GaussianNB
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.linear_model import SGDClassifier
from sklearn import metrics
from sklearn.grid_search import GridSearchCV


file = "tweets.csv"
randomized_file = "randomized_tweets.csv"
training_data = "training_data.csv"
testing_data = "testing_data.csv"
unlabeled_data = "unlabeled.csv"
predicted_data_NB = "predicted_nb.csv"
predicted_data_LSVM = "predicted_lsvm.csv"

columns = [
    "row_id",
    "tweet_id",
    "timestamp",
    "president",
    "tweet",
    "label"
    ]

train_columns = [
    "row_id",
    "tweet_id",
    "day",
    "hour",
    "president",
    "tweet",
    "label"
    ]

test_columns = [
    "row_id",
    "tweet_id",
    "day",
    "hour",
    "president",
    "tweet",
    "label"
    ]

unlabeled_columns = [
    "row_id",
    "tweet_id",
    "day",
    "hour",
    "president",
    "tweet",
    "label"
    ]

categorical_columns = [
    "row_id",
    "tweet_id",
    "day",
    "hour",
    "president",
    "tweet",
    "label"
    ]
continuous_columns = []

labels = []

local_stopwords = []

"""
def get_tweets():
    tw = Twitter()
    
    # Sample from the public stream based on keyword
    tw.tweets(keywords='love, hate', limit=10) 
    
    # See what Donald Trump and Hillary Clinton are talking about
    # respectively 
    # Use numeric userIDs instead of handles
    
    tw.tweets(follow=['25073877', '1339835893'], limit=10) 
"""

def parse_csv():
    # Here we will parse a CSV file with the data on Row ID, Tweet ID,
    # Timestamp, President, Tweet

    training_file = csv.writer(open(training_data, "wb+"))
    testing_file = csv.writer(open(testing_data, "wb+"))
    unlabeled_file = csv.writer(open(unlabeled_data, "wb+"))
        
    # Now to randomize the data; this is how
    # Gotten from Github: 
    # (http://stackoverflow.com/questions/4618298/randomly-mix-lines-of-3-million-line-file)
    with open(file, 'rb') as source:
        data = [ (random.random(), line) for line in source ]
    data.sort()
    with open(randomized_file, 'wb+') as target:
        for _, line in data:
            target.write( line )
    
    prepped_tweet_file = csv.reader(open(randomized_file, "rb"))
    index = 0
    
    # Now we will iterate through the randomized file and extract data
    # We need to get rid of the decimal points in the seconds columns
    # And then split up the data (2/3 train and 1/3 test)
    for row in prepped_tweet_file:
        (row_id, tweet_id, timestamp, president, tweet, label) = row
        raw_timestamp = time.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
        correct_format  = "%Y-%m-%d %H:%M:%S"
        timestamp = strftime(correct_format, raw_timestamp)
        ratio = 3
        
        # Take care of unlabeled data
        if label == "1":
            print(row_id)
            tokenize_row_write(unlabeled_file, row_id, tweet_id, raw_timestamp.tm_wday, raw_timestamp.tm_hour, president, tweet, "")
            continue
        
        print(label)
        if index % ratio == 0:
            tokenize_row_write(testing_file, row_id, tweet_id, raw_timestamp.tm_wday, raw_timestamp.tm_hour, president, tweet, label)
        else:
            tokenize_row_write(training_file, row_id, tweet_id, raw_timestamp.tm_wday, raw_timestamp.tm_hour, president, tweet, label)
            
        index += 1

def clean_word(word):
    return word not in stopwords.words('english') and word not in local_stopwords

def tokenized_string(sent):
    tokenizer = RegexpTokenizer(r'\w+')
    words = [word.lower() for word in tokenizer.tokenize(sent)]
    words = [word for word in words if clean_word(word)]
    
    return words

# Tokenize the title and description, then write everything to the corresponding
# csv file
def tokenize_row_write(file_csv_writer, row_id, tweet_id, day, hour, president, tweet, label):
    words_tweet = tokenized_string(tweet)

    file_csv_writer.writerow([row_id] + [tweet_id] + [day] + [hour] + [president]+ [words_tweet] + [label])
    
 
def extract_and_train():
    
    train = pd.read_csv(training_data, names = train_columns)
    test = pd.read_csv(testing_data, names = test_columns)
    
    x_train = np.array((train['row_id'], train['tweet_id'], train['day'], train['hour'], train['president'], train['tweet']))
    y_train = np.array(train['label'])
    
    x_test = np.array((test['row_id'], test['tweet_id'], test['day'], test['hour'], test['president'], test['tweet']))
    y_test = np.array(test['label'])
    
    train_words = np.array(train['tweet'])
    test_words = np.array(test['tweet'])
    print("Data read")
    
    """ Extract features from text files """
    
    count_vect = CountVectorizer()
    X_train_counts = count_vect.fit_transform(train_words)
    print(X_train_counts.shape)
    
    tfidf_transformer = TfidfTransformer()
    X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)
    print(X_train_tfidf.shape)
    
    """ Training a classifer """
    
    clf = MultinomialNB().fit(X_train_tfidf, y_train)
    print("Model fitted")
    
    test_sentence = ['Our plan promises to revive the economy and build jobs. Trump will destroy the middle class and feed his pockets']
    X_new_counts = count_vect.transform(test_sentence)
    X_new_tfidf = tfidf_transformer.transform(X_new_counts)
    print("Test data transformed")
    
    predicted = clf.predict(X_new_tfidf)
    print("Test data predicted")

    for words, category in zip(test_words, predicted):
        print('%r => %s' % (words, category))
        
    naive_bayes(train_words, y_train, test_words, y_test)
    linear_svm(train_words, y_train, test_words, y_test)

def naive_bayes(x_train, y_train, x_test, y_test):
    """ Building a Pipeline; this does all of the work in extract_and_train() for you """ 
    
    text_clf = Pipeline([('vect', CountVectorizer()),
                         ('tfidf', TfidfTransformer()),
                         ('clf', MultinomialNB()),
                         ])
 
    text_clf = text_clf.fit(x_train, y_train)
    print("Model trained")
    
    """ Evaluate performance on test set """
    
    predicted = text_clf.predict(x_test)
    print("The accuracy of a Naive Bayes algorithm is: ") 
    print(np.mean(predicted == y_test))
    #print("The accuracy of a Naive Bayes algorithm is: %d" % (1 - float(((y_test != predicted).sum()) / x_test.shape[0])))
    print("Number of mislabeled points out of a total %d points for the Naive Bayes algorithm : %d"
          % (x_test.shape[0],(y_test != predicted).sum()))
    
    # Tune parameters
    parameter_tuning(text_clf, x_train, y_train)
    # Predict unlabeled tweets
    predict_unlabeled_tweets(text_clf, predicted_data_NB)

def linear_svm(x_train, y_train, x_test, y_test):
    """ Let's try a Linear Support Vector Machine (SVM) """

    text_clf_two = Pipeline([('vect', CountVectorizer()),
                             ('tfidf', TfidfTransformer()),
                             ('clf', SGDClassifier(
                                 loss='hinge',
                                 penalty='l2',
                                 alpha=1e-3,
                                 n_iter=5,
                                 random_state=42)),
    ])
    text_clf_two = text_clf_two.fit(x_train, y_train)
    predicted_two = text_clf_two.predict(x_test)
    print("The accuracy of a Linear SVM is: ")
    print(np.mean(predicted_two == y_test))
    print("Number of mislabeled points out of a total %d points for the Linear SVM algorithm: %d"
          % (x_test.shape[0],(y_test != predicted_two).sum()))
    
    # Tune parameters
    parameter_tuning(text_clf_two, x_train, y_train)
    # Predict unlabeled tweets
    predict_unlabeled_tweets(text_clf_two, predicted_data_LSVM)

def parameter_tuning(text_clf, x_train, y_train):
    """ Classifiers can have many different parameters that can make the                                                                                                                   
    algorithm more accurate (MultinomialNB() has a smoothing                                                                                                                               
    parameter, SGDClassifier has a penalty parameter, etc.). Here we                                                                                                                       
    will run an exhaustive list of the best possible parameter values """
    
    parameters = {'vect__ngram_range': [(1, 1), (1, 2)],
                  'tfidf__use_idf': (True, False),
                  'clf__alpha': (1e-2, 1e-3),
                  }
    
    gs_clf = GridSearchCV(text_clf, parameters, n_jobs=-1)
    
    gs_clf = gs_clf.fit(x_train, y_train)
    
    best_parameters, score, _ = max(gs_clf.grid_scores_, key=lambda x: x[1])
    for param_name in sorted(parameters.keys()):
        print("%s: %r" % (param_name, best_parameters[param_name]))
        
        
        print(score)
        
        """                                                                                                                                                                                    
        print(metrics.classification_report(y_test, predicted,                                                                                                                                 
        target_names=twenty_test.target_names))                                                                                                                                                
        """

def predict_unlabeled_tweets(classifier, output):
    # Make predictions
    unlabeled_tweets = pd.read_csv(unlabeled_data, names = unlabeled_columns)
    unlabeled_words = np.array(unlabeled_tweets["tweet"])
    predictions = classifier.predict(unlabeled_words)
    print(predictions)
    
    # Create new file for predictions
    # And utilize csv module to iterate through csv
    predicted_tweets = csv.writer(open(output, "wb+"))
    unlabeled_tweets = csv.reader(open(unlabeled_data, "rb+"))
    
    # Iterate through csv and get president and tweet
    # Add prediction to end
    # Also recieved from Github:
    # http://stackoverflow.com/questions/23682236/add-a-new-column-to-an-existing-csv-file
    index = 0
    for row in unlabeled_tweets:
        (row_id, tweet_id, day, hour, president, tweet, label) = row
        predicted_tweets.writerow([president] + [tweet] + [predictions[index]])
        index += 1

def compare_predictions():
    names = ["president", "tweet", "prediction"]
    naive_bayes = pd.read_csv(predicted_data_NB, names = names) 
    linear_svm = pd.read_csv(predicted_data_LSVM, names = names) 

    naive_bayes_pred = np.array(naive_bayes["prediction"])
    linear_svm_pred = np.array(linear_svm["prediction"])
    
    print("The precent similarity between a Multinomial Naive Bayes Algorithm and a Linear SVM algorithm with a SGD Classifier is: ")
    print(np.mean(naive_bayes_pred == linear_svm_pred))

    plot_predictions(naive_bayes_pred)
    plot_predictions(linear_svm_pred)

def plot_predictions(predictions):
    
    pos_sent = len([k for k in predictions if k == "positive"]) / len(predictions)
    neg_sent = len([k for k in predictions if k == "negative"]) / len(predictions)
    neu_sent = len([k for k in predictions if k == "neutral"]) / len(predictions)

    chart = pygal.HorizontalBar()
    chart.title = 'Positive, Negative & Neutral Sentiment'
    chart.add('Positive', pos_sent * 100)
    chart.add('Negative', neg_sent * 100)
    chart.add('Neutral', neu_sent * 100)
    chart.render_to_file('sentiment.svg')
    SVG(filename='sentiment.svg')

if __name__ == '__main__':
    if len(sys.argv) == 2:
        if sys.argv[1] == 'tweets':
            get_tweets()
        elif sys.argv[1] == 'parse':
            parse_csv()
        elif sys.argv[1] == 'train':
            extract_and_train()
        elif sys.argv[1] == 'compare':
            compare_predictions()







